"""
Touch Pad Widget

A touch surface widget that captures swipes, taps, and holds.
Similar to the Siri Remote touch surface.
"""

from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, BooleanProperty, ObjectProperty,
    ListProperty, StringProperty
)
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.app import App


class TouchPad(Widget):
    """
    Touch surface widget for game controller input.
    
    Features:
    - Swipe detection with direction and velocity
    - Tap and double-tap detection
    - Long press detection
    - Multi-touch support
    - Visual feedback
    
    Events:
    - on_tap: Single tap detected
    - on_double_tap: Double tap detected
    - on_long_press: Long press detected
    - on_swipe: Swipe gesture detected (direction, velocity)
    - on_touch_move: Touch movement (for continuous input)
    """
    
    # Visual properties
    background_color = ListProperty([0.15, 0.15, 0.18, 1])
    border_color = ListProperty([0.3, 0.3, 0.35, 1])
    touch_indicator_color = ListProperty([0.4, 0.6, 1.0, 0.5])
    border_width = NumericProperty(2)
    corner_radius = NumericProperty(20)
    
    # Touch settings
    tap_threshold = NumericProperty(10)  # Max movement for tap (pixels)
    double_tap_time = NumericProperty(0.3)  # Time window for double tap
    long_press_time = NumericProperty(0.5)  # Time for long press
    swipe_threshold = NumericProperty(50)  # Min distance for swipe
    
    # State
    is_touched = BooleanProperty(False)
    
    # Coordinate system (0-1000 for pyatv compatibility)
    coord_scale = NumericProperty(1000)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Touch tracking
        self._touch_start = None
        self._touch_start_time = None
        self._last_tap_time = 0
        self._long_press_event = None
        self._current_touch = None
        
        # Register events (using on_pad_* to avoid conflicts with Kivy's on_touch_* events)
        self.register_event_type('on_tap')
        self.register_event_type('on_double_tap')
        self.register_event_type('on_long_press')
        self.register_event_type('on_swipe')
        self.register_event_type('on_pad_move')
        self.register_event_type('on_pad_start')
        self.register_event_type('on_pad_end')
        
        # Bind to size/position changes
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(lambda dt: self._update_canvas())
    
    def _update_canvas(self, *args):
        """Update the visual representation."""
        self.canvas.before.clear()
        
        with self.canvas.before:
            # Background
            Color(*self.background_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.corner_radius]
            )
            
            # Border
            Color(*self.border_color)
            Line(
                rounded_rectangle=[
                    self.x, self.y,
                    self.width, self.height,
                    self.corner_radius
                ],
                width=self.border_width
            )
    
    def _draw_touch_indicator(self, x, y):
        """Draw a visual indicator at touch position."""
        self.canvas.after.clear()
        
        with self.canvas.after:
            Color(*self.touch_indicator_color)
            Ellipse(
                pos=(x - 30, y - 30),
                size=(60, 60)
            )
    
    def _clear_touch_indicator(self):
        """Clear the touch indicator."""
        self.canvas.after.clear()
    
    def _pos_to_coord(self, touch_pos):
        """Convert touch position to scaled coordinates (0-1000)."""
        rel_x = (touch_pos[0] - self.x) / self.width
        rel_y = (touch_pos[1] - self.y) / self.height
        
        # Clamp to [0, 1]
        rel_x = max(0, min(1, rel_x))
        rel_y = max(0, min(1, rel_y))
        
        # Scale to coord system
        coord_x = int(rel_x * self.coord_scale)
        coord_y = int(rel_y * self.coord_scale)
        
        return (coord_x, coord_y)
    
    def on_touch_down(self, touch):
        """Handle touch start."""
        if not self.collide_point(*touch.pos):
            return False
        
        # Grab the touch
        touch.grab(self)
        self._current_touch = touch
        
        # Store touch start info
        self._touch_start = touch.pos
        self._touch_start_time = Clock.get_time()
        self.is_touched = True
        
        # Visual feedback
        self._draw_touch_indicator(*touch.pos)
        
        # Schedule long press detection
        self._long_press_event = Clock.schedule_once(
            self._on_long_press_timeout,
            self.long_press_time
        )
        
        # Dispatch touch start event
        coord = self._pos_to_coord(touch.pos)
        self.dispatch('on_pad_start', coord)
        
        # Haptic feedback
        app = App.get_running_app()
        if app and app.haptic_service:
            app.haptic_service.tap_feedback()
        
        return True
    
    def on_touch_move(self, touch):
        """Handle touch movement."""
        if touch.grab_current is not self:
            return False
        
        # Update visual indicator
        self._draw_touch_indicator(*touch.pos)
        
        # Cancel long press if moved too much
        if self._touch_start:
            dx = touch.pos[0] - self._touch_start[0]
            dy = touch.pos[1] - self._touch_start[1]
            distance = (dx*dx + dy*dy) ** 0.5
            
            if distance > self.tap_threshold and self._long_press_event:
                self._long_press_event.cancel()
                self._long_press_event = None
        
        # Dispatch move event
        coord = self._pos_to_coord(touch.pos)
        self.dispatch('on_pad_move', coord)
        
        return True
    
    def on_touch_up(self, touch):
        """Handle touch end."""
        if touch.grab_current is not self:
            return False
        
        touch.ungrab(self)
        self._current_touch = None
        self.is_touched = False
        
        # Clear visual indicator
        self._clear_touch_indicator()
        
        # Cancel long press timer
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        
        # Calculate touch metrics
        if self._touch_start:
            dx = touch.pos[0] - self._touch_start[0]
            dy = touch.pos[1] - self._touch_start[1]
            distance = (dx*dx + dy*dy) ** 0.5
            duration = Clock.get_time() - self._touch_start_time
            
            # Determine gesture type
            if distance < self.tap_threshold:
                # It's a tap
                current_time = Clock.get_time()
                
                if current_time - self._last_tap_time < self.double_tap_time:
                    # Double tap
                    coord = self._pos_to_coord(touch.pos)
                    self.dispatch('on_double_tap', coord)
                    self._last_tap_time = 0
                else:
                    # Single tap (schedule to allow for double tap)
                    self._last_tap_time = current_time
                    coord = self._pos_to_coord(touch.pos)
                    Clock.schedule_once(
                        lambda dt: self._dispatch_tap_if_not_double(coord),
                        self.double_tap_time
                    )
            
            elif distance >= self.swipe_threshold:
                # It's a swipe
                velocity = distance / max(duration, 0.001)
                direction = self._get_swipe_direction(dx, dy)
                
                start_coord = self._pos_to_coord(self._touch_start)
                end_coord = self._pos_to_coord(touch.pos)
                
                self.dispatch('on_swipe', direction, velocity, start_coord, end_coord)
                
                # Haptic feedback for swipe
                app = App.get_running_app()
                if app and app.haptic_service:
                    app.haptic_service.swipe_feedback()
        
        # Dispatch touch end event
        coord = self._pos_to_coord(touch.pos)
        self.dispatch('on_pad_end', coord)
        
        self._touch_start = None
        self._touch_start_time = None
        
        return True
    
    def _dispatch_tap_if_not_double(self, coord):
        """Dispatch tap event if no double tap occurred."""
        if self._last_tap_time != 0:
            self.dispatch('on_tap', coord)
            self._last_tap_time = 0
    
    def _on_long_press_timeout(self, dt):
        """Handle long press timeout."""
        if self._touch_start and self._current_touch:
            coord = self._pos_to_coord(self._current_touch.pos)
            self.dispatch('on_long_press', coord)
            
            # Haptic feedback
            app = App.get_running_app()
            if app and app.haptic_service:
                app.haptic_service.button_press_feedback()
        
        self._long_press_event = None
    
    def _get_swipe_direction(self, dx, dy):
        """Determine swipe direction from delta values."""
        import math
        
        angle = math.atan2(dy, dx) * 180 / math.pi
        
        # Normalize to 0-360
        if angle < 0:
            angle += 360
        
        # Determine direction (with 45-degree sectors)
        if 337.5 <= angle or angle < 22.5:
            return 'right'
        elif 22.5 <= angle < 67.5:
            return 'up_right'
        elif 67.5 <= angle < 112.5:
            return 'up'
        elif 112.5 <= angle < 157.5:
            return 'up_left'
        elif 157.5 <= angle < 202.5:
            return 'left'
        elif 202.5 <= angle < 247.5:
            return 'down_left'
        elif 247.5 <= angle < 292.5:
            return 'down'
        else:
            return 'down_right'
    
    # Event handlers (to be overridden or bound)
    
    def on_tap(self, coord):
        """Called when a tap is detected."""
        pass
    
    def on_double_tap(self, coord):
        """Called when a double tap is detected."""
        pass
    
    def on_long_press(self, coord):
        """Called when a long press is detected."""
        pass
    
    def on_swipe(self, direction, velocity, start_coord, end_coord):
        """Called when a swipe is detected."""
        pass
    
    def on_pad_move(self, coord):
        """Called when touch moves."""
        pass

    def on_pad_start(self, coord):
        """Called when touch starts."""
        pass

    def on_pad_end(self, coord):
        """Called when touch ends."""
        pass
