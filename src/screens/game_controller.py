"""
Game Controller Screen

Full game controller interface with motion controls.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, Ellipse, Line

from ..widgets.touch_pad import TouchPad
from ..widgets.game_buttons import GameButtons, DPad


class MotionIndicator(FloatLayout):
    """Visual indicator for motion/tilt controls."""
    
    pitch = NumericProperty(0)  # Forward/backward tilt
    roll = NumericProperty(0)   # Left/right tilt
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pitch=self._update_canvas,
            roll=self._update_canvas,
            size=self._update_canvas,
            pos=self._update_canvas
        )
        Clock.schedule_once(lambda dt: self._update_canvas())
    
    def _update_canvas(self, *args):
        """Draw the motion indicator."""
        self.canvas.clear()
        
        cx = self.center_x
        cy = self.center_y
        radius = min(self.width, self.height) / 2 - 10
        
        with self.canvas:
            # Background circle
            Color(0.2, 0.2, 0.25, 1)
            Ellipse(
                pos=(cx - radius, cy - radius),
                size=(radius * 2, radius * 2)
            )
            
            # Border
            Color(0.35, 0.35, 0.4, 1)
            Line(
                ellipse=[cx - radius, cy - radius, radius * 2, radius * 2],
                width=2
            )
            
            # Crosshairs
            Color(0.3, 0.3, 0.35, 1)
            Line(points=[cx - radius, cy, cx + radius, cy], width=1)
            Line(points=[cx, cy - radius, cx, cy + radius], width=1)
            
            # Calculate indicator position based on pitch/roll
            # Clamp values to reasonable range (-45 to 45 degrees)
            max_angle = 45
            norm_roll = max(-1, min(1, self.roll / max_angle))
            norm_pitch = max(-1, min(1, self.pitch / max_angle))
            
            # Map to position
            ind_x = cx + norm_roll * (radius - 15)
            ind_y = cy + norm_pitch * (radius - 15)
            
            # Indicator dot
            Color(0.4, 0.7, 1.0, 1)
            Ellipse(
                pos=(ind_x - 12, ind_y - 12),
                size=(24, 24)
            )


class GameControllerScreen(Screen):
    """
    Game controller screen with full gaming controls.
    
    Features:
    - Large touch pad for game input
    - Motion controls (accelerometer/gyroscope)
    - A/B/X/Y buttons
    - D-pad
    - Menu/Home buttons
    """
    
    device_name = StringProperty("Not Connected")
    motion_enabled = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._motion_callback = None
        self._build_ui()
    
    def _build_ui(self):
        """Build the game controller UI."""
        # Main layout - we'll use a custom arrangement
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Header
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=40,
            spacing=10
        )
        
        # Back button
        back_btn = Button(
            text='< Remote',
            size_hint_x=None,
            width=100,
            background_color=(0.3, 0.3, 0.35, 1)
        )
        back_btn.bind(on_press=self._on_back)
        header.add_widget(back_btn)
        
        # Device name
        header.add_widget(Label(text='Game Mode', font_size='16sp'))
        
        # Motion toggle
        self.motion_btn = Button(
            text='Motion: ON',
            size_hint_x=None,
            width=100,
            background_color=(0.3, 0.6, 0.3, 1)
        )
        self.motion_btn.bind(on_press=self._toggle_motion)
        header.add_widget(self.motion_btn)
        
        main_layout.add_widget(header)
        
        # Game controls area
        controls_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.85),
            spacing=10
        )
        
        # Left side - D-pad and motion indicator
        left_side = BoxLayout(
            orientation='vertical',
            size_hint_x=0.35,
            spacing=10
        )
        
        # Motion indicator
        self.motion_indicator = MotionIndicator(
            size_hint=(1, 0.4)
        )
        left_side.add_widget(self.motion_indicator)
        
        # D-pad
        dpad_container = BoxLayout(size_hint=(1, 0.6), padding=10)
        self.dpad = DPad(size_hint=(None, None), size=(150, 150))
        self.dpad.bind(
            on_direction=self._on_dpad_direction,
            on_direction_release=self._on_dpad_release
        )
        dpad_container.add_widget(self.dpad)
        left_side.add_widget(dpad_container)
        
        controls_layout.add_widget(left_side)
        
        # Center - Touch pad
        center_side = BoxLayout(
            orientation='vertical',
            size_hint_x=0.35,
            padding=5
        )
        
        self.touch_pad = TouchPad()
        self.touch_pad.bind(
            on_tap=self._on_tap,
            on_double_tap=self._on_double_tap,
            on_swipe=self._on_swipe,
            on_long_press=self._on_long_press,
            on_pad_move=self._on_pad_move,
            on_pad_start=self._on_pad_start,
            on_pad_end=self._on_pad_end
        )
        center_side.add_widget(self.touch_pad)
        
        controls_layout.add_widget(center_side)
        
        # Right side - Game buttons
        right_side = BoxLayout(
            orientation='vertical',
            size_hint_x=0.3,
            spacing=10
        )
        
        # System buttons at top
        system_btns = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.15,
            spacing=5
        )
        
        menu_btn = Button(
            text='Menu',
            background_color=(0.25, 0.25, 0.28, 1)
        )
        menu_btn.bind(on_press=self._on_menu)
        system_btns.add_widget(menu_btn)
        
        home_btn = Button(
            text='Home',
            background_color=(0.25, 0.25, 0.28, 1)
        )
        home_btn.bind(on_press=self._on_home)
        system_btns.add_widget(home_btn)
        
        right_side.add_widget(system_btns)
        
        # Game buttons
        buttons_container = BoxLayout(size_hint_y=0.85, padding=10)
        self.game_buttons = GameButtons(
            size_hint=(1, 1),
            button_size=55
        )
        self.game_buttons.bind(
            on_button_press=self._on_button_press,
            on_button_release=self._on_button_release
        )
        buttons_container.add_widget(self.game_buttons)
        right_side.add_widget(buttons_container)
        
        controls_layout.add_widget(right_side)
        
        main_layout.add_widget(controls_layout)
        
        # Play/Pause button at bottom
        playback_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10,
            padding=(50, 0)
        )
        
        play_btn = Button(
            text='Play / Pause',
            background_color=(0.3, 0.3, 0.35, 1)
        )
        play_btn.bind(on_press=self._on_play_pause)
        playback_layout.add_widget(play_btn)
        
        main_layout.add_widget(playback_layout)
        
        self.add_widget(main_layout)
    
    def on_enter(self):
        """Called when the screen is displayed."""
        app = App.get_running_app()
        
        if app.atv_service:
            self.device_name = app.atv_service.current_device_name or "Apple TV"
        
        # Start motion sensing
        if self.motion_enabled and app.sensor_service:
            self._motion_callback = self._on_motion_update
            app.sensor_service.register_callback(self._motion_callback)
            app.sensor_service.start()
    
    def on_leave(self):
        """Called when leaving the screen."""
        app = App.get_running_app()
        
        # Stop motion sensing
        if app.sensor_service:
            if self._motion_callback:
                app.sensor_service.unregister_callback(self._motion_callback)
                self._motion_callback = None
            app.sensor_service.stop()
    
    def _get_service(self):
        """Get the Apple TV service."""
        app = App.get_running_app()
        return app.atv_service if app else None
    
    # Navigation
    
    def _on_back(self, instance):
        """Go back to remote screen."""
        app = App.get_running_app()
        if app:
            app.switch_to_remote()
    
    def _toggle_motion(self, instance):
        """Toggle motion controls."""
        app = App.get_running_app()
        self.motion_enabled = not self.motion_enabled
        
        if self.motion_enabled:
            self.motion_btn.text = 'Motion: ON'
            self.motion_btn.background_color = (0.3, 0.6, 0.3, 1)
            if app.sensor_service:
                self._motion_callback = self._on_motion_update
                app.sensor_service.register_callback(self._motion_callback)
                app.sensor_service.start()
        else:
            self.motion_btn.text = 'Motion: OFF'
            self.motion_btn.background_color = (0.5, 0.3, 0.3, 1)
            if app.sensor_service:
                if self._motion_callback:
                    app.sensor_service.unregister_callback(self._motion_callback)
                    self._motion_callback = None
                app.sensor_service.stop()
            # Reset motion indicator
            self.motion_indicator.pitch = 0
            self.motion_indicator.roll = 0
    
    # Motion handlers
    
    def _on_motion_update(self, motion_data):
        """Handle motion sensor updates."""
        # Update the visual indicator
        self.motion_indicator.pitch = motion_data.pitch
        self.motion_indicator.roll = motion_data.roll
        
        # Send motion data to Apple TV if supported
        # Note: This would need to be implemented based on
        # how the specific game handles motion input
        # For now, we could map tilt to swipe gestures
        
        service = self._get_service()
        if service:
            # Map significant tilts to directional swipes
            # This is a simplified approach - real implementation
            # would depend on the game's requirements
            threshold = 15  # degrees
            
            if abs(motion_data.roll) > threshold or abs(motion_data.pitch) > threshold:
                # Calculate swipe based on tilt
                # This sends continuous position updates
                center = 500
                scale = 10  # sensitivity
                
                x = int(center + motion_data.roll * scale)
                y = int(center + motion_data.pitch * scale)
                
                # Clamp to valid range
                x = max(0, min(1000, x))
                y = max(0, min(1000, y))
                
                # Send touch action
                service.touch_action(x, y, 'move')
    
    # Touch pad handlers
    
    def _on_tap(self, instance, coord):
        """Handle tap - primary action."""
        service = self._get_service()
        if service:
            service.select()
    
    def _on_double_tap(self, instance, coord):
        """Handle double tap."""
        service = self._get_service()
        if service:
            # Could be mapped to a secondary action
            service.select()
    
    def _on_swipe(self, instance, direction, velocity, start_coord, end_coord):
        """Handle swipe gesture."""
        service = self._get_service()
        if service:
            # Send the actual swipe to Apple TV
            duration = int(200 / max(velocity / 1000, 0.5))  # Faster swipe = shorter duration
            duration = max(50, min(500, duration))
            
            service.swipe(
                start_coord[0], start_coord[1],
                end_coord[0], end_coord[1],
                duration
            )
    
    def _on_long_press(self, instance, coord):
        """Handle long press - secondary action."""
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'tap')
    
    def _on_pad_start(self, instance, coord):
        """Handle touch start."""
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'down')

    def _on_pad_move(self, instance, coord):
        """Handle continuous touch movement."""
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'move')

    def _on_pad_end(self, instance, coord):
        """Handle touch end."""
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'up')
    
    # D-pad handlers
    
    def _on_dpad_direction(self, instance, direction):
        """Handle D-pad direction press."""
        service = self._get_service()
        if not service:
            return
        
        direction_map = {
            'up': service.up,
            'down': service.down,
            'left': service.left,
            'right': service.right,
        }
        
        action = direction_map.get(direction)
        if action:
            action()
    
    def _on_dpad_release(self, instance, direction):
        """Handle D-pad direction release."""
        # Could be used for games that need release events
        pass
    
    # Game button handlers
    
    def _on_button_press(self, instance, button_name):
        """Handle game button press."""
        service = self._get_service()
        if not service:
            return
        
        # Map buttons to Apple TV actions
        # Note: The exact mapping depends on how the game uses buttons
        button_map = {
            'A': service.select,      # Primary action
            'B': service.menu,        # Back/cancel
            'X': service.play_pause,  # Often used for secondary action
            'Y': service.home,        # Can be remapped
        }
        
        action = button_map.get(button_name)
        if action:
            action()
    
    def _on_button_release(self, instance, button_name):
        """Handle game button release."""
        # Could be used for games that need release events
        pass
    
    # System buttons
    
    def _on_menu(self, instance):
        """Handle menu button."""
        service = self._get_service()
        if service:
            service.menu()
    
    def _on_home(self, instance):
        """Handle home button."""
        service = self._get_service()
        if service:
            service.home()
    
    def _on_play_pause(self, instance):
        """Handle play/pause button."""
        service = self._get_service()
        if service:
            service.play_pause()
