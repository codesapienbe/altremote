"""
Game Controller Screen

Full game controller interface with gamepad-style layout.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Rectangle

from ..widgets.touch_pad import TouchPad
from ..widgets.game_buttons import GameButtons, DPad


class GameControllerScreen(Screen):
    """
    Game controller screen with gamepad-style layout.

    Layout:
    ┌─────────────────────────────────────────────────────┐
    │  [< Back]            Game Mode         [Motion: ON] │
    ├─────────────────────────────────────────────────────┤
    │                   [Menu]  [Home]                    │
    │                                                     │
    │    D-PAD              TOUCH PAD           A/B/X/Y   │
    │    ┌───┐           ┌───────────┐            Y       │
    │    │ ↑ │           │           │         X   A      │
    │ ┌──┼───┼──┐        │           │            B       │
    │ │ ←│   │→ │        │           │                    │
    │ └──┼───┼──┘        │           │                    │
    │    │ ↓ │           └───────────┘                    │
    │    └───┘                                            │
    │                   [Play / Pause]                    │
    └─────────────────────────────────────────────────────┘
    """

    device_name = StringProperty("Not Connected")
    motion_enabled = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._motion_callback = None
        self._build_ui()

    def _build_ui(self):
        """Build the gamepad-style UI."""
        # Main container with dark background
        main_layout = FloatLayout()

        # Draw gamepad background
        with main_layout.canvas.before:
            Color(0.12, 0.12, 0.15, 1)
            self._bg_rect = Rectangle(pos=(0, 0), size=(800, 600))

        main_layout.bind(size=self._update_bg)

        # Header bar
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=50,
            pos_hint={'top': 1},
            padding=[10, 5],
            spacing=10
        )

        # Back button
        back_btn = Button(
            text='< Back',
            size_hint=(None, 1),
            width=80,
            background_color=(0.2, 0.2, 0.25, 1),
            background_normal=''
        )
        back_btn.bind(on_press=self._on_back)
        header.add_widget(back_btn)

        # Spacer
        header.add_widget(Widget())

        # Title
        header.add_widget(Label(
            text='Game Mode',
            font_size='18sp',
            bold=True,
            size_hint=(None, 1),
            width=120
        ))

        # Spacer
        header.add_widget(Widget())

        # Motion toggle
        self.motion_btn = Button(
            text='Motion',
            size_hint=(None, 1),
            width=80,
            background_color=(0.2, 0.5, 0.3, 1),
            background_normal=''
        )
        self.motion_btn.bind(on_press=self._toggle_motion)
        header.add_widget(self.motion_btn)

        main_layout.add_widget(header)

        # System buttons (Menu / Home) - center top
        system_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(160, 35),
            pos_hint={'center_x': 0.5, 'top': 0.88},
            spacing=10
        )

        menu_btn = Button(
            text='MENU',
            font_size='12sp',
            background_color=(0.25, 0.25, 0.3, 1),
            background_normal=''
        )
        menu_btn.bind(on_press=self._on_menu)
        system_layout.add_widget(menu_btn)

        home_btn = Button(
            text='HOME',
            font_size='12sp',
            background_color=(0.25, 0.25, 0.3, 1),
            background_normal=''
        )
        home_btn.bind(on_press=self._on_home)
        system_layout.add_widget(home_btn)

        main_layout.add_widget(system_layout)

        # Left side - D-Pad (positioned like left thumbstick area)
        dpad_anchor = AnchorLayout(
            anchor_x='center',
            anchor_y='center',
            size_hint=(0.3, 0.5),
            pos_hint={'x': 0.02, 'center_y': 0.45}
        )
        self.dpad = DPad(size_hint=(None, None), size=(140, 140))
        self.dpad.bind(
            on_direction=self._on_dpad_direction,
            on_direction_release=self._on_dpad_release
        )
        dpad_anchor.add_widget(self.dpad)
        main_layout.add_widget(dpad_anchor)

        # Center - Touch Pad (like PS4/PS5 touchpad)
        touchpad_container = FloatLayout(
            size_hint=(0.36, 0.45),
            pos_hint={'center_x': 0.5, 'center_y': 0.48}
        )

        # Touchpad background styling
        with touchpad_container.canvas.before:
            Color(0.18, 0.18, 0.22, 1)
            self._touchpad_bg = RoundedRectangle(
                pos=(0, 0),
                size=(200, 150),
                radius=[15]
            )

        touchpad_container.bind(
            pos=self._update_touchpad_bg,
            size=self._update_touchpad_bg
        )

        self.touch_pad = TouchPad(size_hint=(1, 1))
        self.touch_pad.bind(
            on_tap=self._on_tap,
            on_double_tap=self._on_double_tap,
            on_swipe=self._on_swipe,
            on_long_press=self._on_long_press,
            on_pad_move=self._on_pad_move,
            on_pad_start=self._on_pad_start,
            on_pad_end=self._on_pad_end
        )
        touchpad_container.add_widget(self.touch_pad)
        main_layout.add_widget(touchpad_container)

        # Right side - A/B/X/Y Buttons (positioned like right buttons)
        buttons_anchor = AnchorLayout(
            anchor_x='center',
            anchor_y='center',
            size_hint=(0.3, 0.5),
            pos_hint={'right': 0.98, 'center_y': 0.45}
        )
        self.game_buttons = GameButtons(
            size_hint=(None, None),
            size=(160, 160),
            button_size=50,
            spacing=8
        )
        self.game_buttons.bind(
            on_button_press=self._on_button_press,
            on_button_release=self._on_button_release
        )
        buttons_anchor.add_widget(self.game_buttons)
        main_layout.add_widget(buttons_anchor)

        # Bottom - Play/Pause button
        play_layout = AnchorLayout(
            anchor_x='center',
            anchor_y='center',
            size_hint=(0.4, None),
            height=45,
            pos_hint={'center_x': 0.5, 'y': 0.02}
        )

        play_btn = Button(
            text='PLAY / PAUSE',
            font_size='14sp',
            size_hint=(1, 1),
            background_color=(0.25, 0.25, 0.3, 1),
            background_normal=''
        )
        play_btn.bind(on_press=self._on_play_pause)
        play_layout.add_widget(play_btn)

        main_layout.add_widget(play_layout)

        self.add_widget(main_layout)

    def _update_bg(self, instance, value):
        """Update background rectangle size."""
        self._bg_rect.size = instance.size
        self._bg_rect.pos = instance.pos

    def _update_touchpad_bg(self, instance, value):
        """Update touchpad background."""
        self._touchpad_bg.pos = instance.pos
        self._touchpad_bg.size = instance.size

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
            self.motion_btn.text = 'Motion'
            self.motion_btn.background_color = (0.2, 0.5, 0.3, 1)
            if app.sensor_service:
                self._motion_callback = self._on_motion_update
                app.sensor_service.register_callback(self._motion_callback)
                app.sensor_service.start()
        else:
            self.motion_btn.text = 'Motion'
            self.motion_btn.background_color = (0.4, 0.25, 0.25, 1)
            if app.sensor_service:
                if self._motion_callback:
                    app.sensor_service.unregister_callback(self._motion_callback)
                    self._motion_callback = None
                app.sensor_service.stop()

    # Motion handlers

    def _on_motion_update(self, motion_data):
        """Handle motion sensor updates."""
        service = self._get_service()
        if service:
            threshold = 15  # degrees

            if abs(motion_data.roll) > threshold or abs(motion_data.pitch) > threshold:
                center = 500
                scale = 10

                x = int(center + motion_data.roll * scale)
                y = int(center + motion_data.pitch * scale)

                x = max(0, min(1000, x))
                y = max(0, min(1000, y))

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
            service.select()

    def _on_swipe(self, instance, direction, velocity, start_coord, end_coord):
        """Handle swipe gesture."""
        service = self._get_service()
        if service:
            duration = int(200 / max(velocity / 1000, 0.5))
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
        pass

    # Game button handlers

    def _on_button_press(self, instance, button_name):
        """Handle game button press."""
        service = self._get_service()
        if not service:
            return

        button_map = {
            'A': service.select,
            'B': service.menu,
            'X': service.play_pause,
            'Y': service.home,
        }

        action = button_map.get(button_name)
        if action:
            action()

    def _on_button_release(self, instance, button_name):
        """Handle game button release."""
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
