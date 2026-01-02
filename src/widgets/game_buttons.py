"""
Game Buttons Widget

A/B/X/Y button layout similar to game controllers.
"""

from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.properties import (
    NumericProperty, ListProperty, StringProperty,
    BooleanProperty, ObjectProperty
)
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from kivy.app import App


class GameButton(Widget):
    """
    A single game controller button.
    
    Features:
    - Customizable color and label
    - Press and release events
    - Visual feedback
    - Hold detection
    """
    
    label = StringProperty('A')
    button_color = ListProperty([0.3, 0.6, 0.3, 1])  # Green by default
    text_color = ListProperty([1, 1, 1, 1])
    pressed_color = ListProperty([0.5, 0.8, 0.5, 1])
    is_pressed = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Register events
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        self.register_event_type('on_hold')
        
        self._hold_event = None
        self._hold_time = 0.5
        
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self.bind(is_pressed=self._update_canvas)
        Clock.schedule_once(lambda dt: self._update_canvas())
    
    def _update_canvas(self, *args):
        """Update button appearance."""
        self.canvas.clear()
        
        color = self.pressed_color if self.is_pressed else self.button_color
        
        with self.canvas:
            # Button background
            Color(*color)
            Ellipse(pos=self.pos, size=self.size)
            
            # Border
            Color(1, 1, 1, 0.3)
            Line(ellipse=[self.x, self.y, self.width, self.height], width=2)
        
        # Draw label
        self._draw_label()
    
    def _draw_label(self):
        """Draw the button label."""
        from kivy.core.text import Label as CoreLabel
        
        label = CoreLabel(
            text=self.label,
            font_size=self.height * 0.5,
            color=self.text_color
        )
        label.refresh()
        
        texture = label.texture
        if texture:
            with self.canvas:
                Color(*self.text_color)
                from kivy.graphics import Rectangle
                tex_width, tex_height = texture.size
                pos_x = self.center_x - tex_width / 2
                pos_y = self.center_y - tex_height / 2
                Rectangle(
                    texture=texture,
                    pos=(pos_x, pos_y),
                    size=texture.size
                )
    
    def on_touch_down(self, touch):
        """Handle touch press."""
        if not self.collide_point(*touch.pos):
            return False
        
        touch.grab(self)
        self.is_pressed = True
        self.dispatch('on_press')
        
        # Schedule hold detection
        self._hold_event = Clock.schedule_once(
            lambda dt: self._on_hold(),
            self._hold_time
        )
        
        # Haptic feedback
        app = App.get_running_app()
        if app and app.haptic_service:
            app.haptic_service.tap_feedback()
        
        return True
    
    def on_touch_up(self, touch):
        """Handle touch release."""
        if touch.grab_current is not self:
            return False
        
        touch.ungrab(self)
        self.is_pressed = False
        
        # Cancel hold event
        if self._hold_event:
            self._hold_event.cancel()
            self._hold_event = None
        
        self.dispatch('on_release')
        return True
    
    def _on_hold(self):
        """Handle hold event."""
        self.dispatch('on_hold')
        
        app = App.get_running_app()
        if app and app.haptic_service:
            app.haptic_service.button_press_feedback()
        
        self._hold_event = None
    
    def on_press(self):
        """Called when button is pressed."""
        pass
    
    def on_release(self):
        """Called when button is released."""
        pass
    
    def on_hold(self):
        """Called when button is held."""
        pass


class GameButtons(RelativeLayout):
    """
    A/B/X/Y button layout in diamond formation.
    
    Layout:
           Y
        X     A
           B
    
    Events:
    - on_button_press: A button was pressed (button_name)
    - on_button_release: A button was released (button_name)
    """
    
    button_size = NumericProperty(60)
    spacing = NumericProperty(10)
    
    # Colors for each button
    a_color = ListProperty([0.3, 0.7, 0.3, 1])  # Green
    b_color = ListProperty([0.7, 0.3, 0.3, 1])  # Red
    x_color = ListProperty([0.3, 0.3, 0.7, 1])  # Blue
    y_color = ListProperty([0.7, 0.7, 0.3, 1])  # Yellow
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.register_event_type('on_button_press')
        self.register_event_type('on_button_release')
        
        # Create buttons
        self._create_buttons()
        
        self.bind(
            size=self._update_layout,
            button_size=self._update_layout,
            spacing=self._update_layout
        )
    
    def _create_buttons(self):
        """Create the A/B/X/Y buttons."""
        self.button_a = GameButton(label='A', button_color=self.a_color)
        self.button_b = GameButton(label='B', button_color=self.b_color)
        self.button_x = GameButton(label='X', button_color=self.x_color)
        self.button_y = GameButton(label='Y', button_color=self.y_color)
        
        # Bind events
        for btn, name in [
            (self.button_a, 'A'),
            (self.button_b, 'B'),
            (self.button_x, 'X'),
            (self.button_y, 'Y')
        ]:
            btn.bind(
                on_press=lambda inst, n=name: self.dispatch('on_button_press', n),
                on_release=lambda inst, n=name: self.dispatch('on_button_release', n)
            )
            self.add_widget(btn)
    
    def _update_layout(self, *args):
        """Update button positions."""
        size = self.button_size
        spacing = self.spacing
        
        # Calculate center of widget
        cx = self.width / 2
        cy = self.height / 2
        
        # Position buttons in diamond formation
        # Y at top
        self.button_y.pos = (cx - size/2, cy + spacing)
        self.button_y.size = (size, size)
        
        # B at bottom
        self.button_b.pos = (cx - size/2, cy - spacing - size)
        self.button_b.size = (size, size)
        
        # X at left
        self.button_x.pos = (cx - spacing - size, cy - size/2)
        self.button_x.size = (size, size)
        
        # A at right
        self.button_a.pos = (cx + spacing, cy - size/2)
        self.button_a.size = (size, size)
    
    def on_button_press(self, button_name):
        """Called when a button is pressed."""
        pass
    
    def on_button_release(self, button_name):
        """Called when a button is released."""
        pass


class DPad(Widget):
    """
    D-Pad widget for directional input.
    
    Features:
    - Up/Down/Left/Right buttons
    - Diagonal support (optional)
    - Visual feedback
    """
    
    size_hint = (None, None)
    button_color = ListProperty([0.25, 0.25, 0.28, 1])
    pressed_color = ListProperty([0.4, 0.4, 0.45, 1])
    border_color = ListProperty([0.35, 0.35, 0.4, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.register_event_type('on_direction')
        self.register_event_type('on_direction_release')
        
        self._current_direction = None
        
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(lambda dt: self._update_canvas())
    
    def _update_canvas(self, *args):
        """Draw the D-pad."""
        self.canvas.clear()
        
        with self.canvas:
            # Calculate dimensions
            w, h = self.size
            unit = min(w, h) / 3  # Each button is 1/3 of the widget
            
            # Draw the cross shape
            # Horizontal bar
            Color(*self.button_color)
            from kivy.graphics import Rectangle, RoundedRectangle
            
            # Up button
            RoundedRectangle(
                pos=(self.x + unit, self.y + unit * 2),
                size=(unit, unit),
                radius=[5, 5, 0, 0]
            )
            
            # Down button
            RoundedRectangle(
                pos=(self.x + unit, self.y),
                size=(unit, unit),
                radius=[0, 0, 5, 5]
            )
            
            # Left button
            RoundedRectangle(
                pos=(self.x, self.y + unit),
                size=(unit, unit),
                radius=[5, 0, 0, 5]
            )
            
            # Right button
            RoundedRectangle(
                pos=(self.x + unit * 2, self.y + unit),
                size=(unit, unit),
                radius=[0, 5, 5, 0]
            )
            
            # Center
            Rectangle(
                pos=(self.x + unit, self.y + unit),
                size=(unit, unit)
            )
            
            # Border
            Color(*self.border_color)
            Line(
                points=[
                    # Top of up button
                    self.x + unit, self.y + unit * 3,
                    self.x + unit * 2, self.y + unit * 3,
                    # Right side down
                    self.x + unit * 2, self.y + unit * 2,
                    self.x + unit * 3, self.y + unit * 2,
                    # Bottom of right button
                    self.x + unit * 3, self.y + unit,
                    # Bottom side
                    self.x + unit * 2, self.y + unit,
                    self.x + unit * 2, self.y,
                    self.x + unit, self.y,
                    # Left side
                    self.x + unit, self.y + unit,
                    self.x, self.y + unit,
                    self.x, self.y + unit * 2,
                    # Back to start
                    self.x + unit, self.y + unit * 2,
                    self.x + unit, self.y + unit * 3
                ],
                width=1.5
            )
    
    def _get_direction(self, touch_pos):
        """Determine which direction was pressed."""
        rel_x = touch_pos[0] - self.x
        rel_y = touch_pos[1] - self.y
        unit = min(self.width, self.height) / 3
        
        # Check which button was pressed
        if unit <= rel_x < unit * 2:
            if rel_y >= unit * 2:
                return 'up'
            elif rel_y < unit:
                return 'down'
        if unit <= rel_y < unit * 2:
            if rel_x < unit:
                return 'left'
            elif rel_x >= unit * 2:
                return 'right'
        
        return None
    
    def on_touch_down(self, touch):
        """Handle touch press."""
        if not self.collide_point(*touch.pos):
            return False
        
        touch.grab(self)
        direction = self._get_direction(touch.pos)
        
        if direction:
            self._current_direction = direction
            self.dispatch('on_direction', direction)
            
            # Haptic feedback
            app = App.get_running_app()
            if app and app.haptic_service:
                app.haptic_service.tap_feedback()
        
        return True
    
    def on_touch_up(self, touch):
        """Handle touch release."""
        if touch.grab_current is not self:
            return False
        
        touch.ungrab(self)
        
        if self._current_direction:
            self.dispatch('on_direction_release', self._current_direction)
            self._current_direction = None
        
        return True
    
    def on_direction(self, direction):
        """Called when a direction is pressed."""
        pass
    
    def on_direction_release(self, direction):
        """Called when a direction is released."""
        pass
