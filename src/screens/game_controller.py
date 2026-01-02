"""
Game Controller Screen

Full game controller interface with gamepad-style layout.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, RoundedRectangle, Rectangle

from ..widgets.touch_pad import TouchPad
from ..widgets.game_buttons import GameButtons, DPad


class GameControllerScreen(Screen):
    """
    Game controller screen with gamepad-style layout.

    Layout (landscape-style on portrait screen):
    ┌─────────────────────────────────────────────────────┐
    │  [< Back]            Game Mode         [Motion]     │
    ├─────────────────────────────────────────────────────┤
    │              [MENU]            [HOME]               │
    │                                                     │
    │   ┌─────┐                              Y            │
    │   │  ↑  │     ┌──────────────────┐   X   A          │
    │ ┌─┼─────┼─┐   │                  │      B           │
    │ │←│     │→│   │    TOUCH PAD     │                  │
    │ └─┼─────┼─┘   │                  │                  │
    │   │  ↓  │     └──────────────────┘                  │
    │   └─────┘                                           │
    │                                                     │
    │                  [PLAY / PAUSE]                     │
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
        # Main vertical layout
        main_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)

        # Dark background
        with main_layout.canvas.before:
            Color(0.1, 0.1, 0.12, 1)
            self._bg_rect = Rectangle(pos=(0, 0), size=(800, 600))
        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # === Header Bar ===
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=45,
            padding=[5, 0],
            spacing=10
        )

        back_btn = Button(
            text='< Back',
            size_hint=(None, 1),
            width=70,
            font_size='13sp',
            background_color=(0.2, 0.2, 0.25, 1),
            background_normal=''
        )
        back_btn.bind(on_press=self._on_back)
        header.add_widget(back_btn)

        header.add_widget(Widget())  # Spacer

        header.add_widget(Label(
            text='Game Mode',
            font_size='16sp',
            bold=True,
            size_hint=(None, 1),
            width=100
        ))

        header.add_widget(Widget())  # Spacer

        self.motion_btn = Button(
            text='Motion',
            size_hint=(None, 1),
            width=70,
            font_size='13sp',
            background_color=(0.2, 0.5, 0.3, 1),
            background_normal=''
        )
        self.motion_btn.bind(on_press=self._toggle_motion)
        header.add_widget(self.motion_btn)

        main_layout.add_widget(header)

        # === System Buttons Row ===
        system_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=40,
            padding=[20, 0],
            spacing=20
        )
        system_row.add_widget(Widget())  # Left spacer

        menu_btn = Button(
            text='MENU',
            size_hint=(None, 1),
            width=80,
            font_size='13sp',
            background_color=(0.22, 0.22, 0.27, 1),
            background_normal=''
        )
        menu_btn.bind(on_press=self._on_menu)
        system_row.add_widget(menu_btn)

        home_btn = Button(
            text='HOME',
            size_hint=(None, 1),
            width=80,
            font_size='13sp',
            background_color=(0.22, 0.22, 0.27, 1),
            background_normal=''
        )
        home_btn.bind(on_press=self._on_home)
        system_row.add_widget(home_btn)

        system_row.add_widget(Widget())  # Right spacer
        main_layout.add_widget(system_row)

        # === Main Controls Area ===
        controls_area = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[10, 10],
            spacing=10
        )

        # --- Left: D-Pad ---
        left_container = FloatLayout(size_hint=(0.28, 1))

        # Center the D-pad vertically in its container
        self.dpad = DPad(
            size_hint=(None, None),
            size=(180, 180),
            pos_hint={'center_x': 0.5, 'center_y': 0.55}
        )
        self.dpad.bind(
            on_direction=self._on_dpad_direction,
            on_direction_release=self._on_dpad_release
        )
        left_container.add_widget(self.dpad)
        controls_area.add_widget(left_container)

        # --- Center: Touch Pad ---
        center_container = FloatLayout(size_hint=(0.44, 1))

        # Touch pad with background
        self.touchpad_wrapper = RelativeLayout(
            size_hint=(0.95, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.55}
        )

        with self.touchpad_wrapper.canvas.before:
            Color(0.15, 0.15, 0.18, 1)
            self._touchpad_bg = RoundedRectangle(
                pos=(0, 0),
                size=(200, 150),
                radius=[12]
            )
        self.touchpad_wrapper.bind(
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
        self.touchpad_wrapper.add_widget(self.touch_pad)
        center_container.add_widget(self.touchpad_wrapper)
        controls_area.add_widget(center_container)

        # --- Right: A/B/X/Y Buttons ---
        right_container = FloatLayout(size_hint=(0.28, 1))

        self.game_buttons = GameButtons(
            size_hint=(None, None),
            size=(170, 170),
            button_size=55,
            spacing=5,
            pos_hint={'center_x': 0.5, 'center_y': 0.55}
        )
        self.game_buttons.bind(
            on_button_press=self._on_button_press,
            on_button_release=self._on_button_release
        )
        right_container.add_widget(self.game_buttons)
        controls_area.add_widget(right_container)

        main_layout.add_widget(controls_area)

        # === Bottom: Play/Pause Button ===
        bottom_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=50,
            padding=[40, 5]
        )

        play_btn = Button(
            text='PLAY / PAUSE',
            font_size='14sp',
            background_color=(0.22, 0.22, 0.27, 1),
            background_normal=''
        )
        play_btn.bind(on_press=self._on_play_pause)
        bottom_row.add_widget(play_btn)

        main_layout.add_widget(bottom_row)

        self.add_widget(main_layout)

    def _update_bg(self, instance, value):
        """Update background rectangle."""
        self._bg_rect.size = instance.size
        self._bg_rect.pos = instance.pos

    def _update_touchpad_bg(self, instance, value):
        """Update touchpad background."""
        self._touchpad_bg.pos = instance.pos
        self._touchpad_bg.size = instance.size

    def on_enter(self):
        """Called when screen is displayed."""
        app = App.get_running_app()

        if app.atv_service:
            self.device_name = app.atv_service.current_device_name or "Apple TV"

        if self.motion_enabled and app.sensor_service:
            self._motion_callback = self._on_motion_update
            app.sensor_service.register_callback(self._motion_callback)
            app.sensor_service.start()

    def on_leave(self):
        """Called when leaving screen."""
        app = App.get_running_app()

        if app.sensor_service:
            if self._motion_callback:
                app.sensor_service.unregister_callback(self._motion_callback)
                self._motion_callback = None
            app.sensor_service.stop()

    def _get_service(self):
        """Get the Apple TV service."""
        app = App.get_running_app()
        return app.atv_service if app else None

    # === Navigation ===

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
            self.motion_btn.background_color = (0.2, 0.5, 0.3, 1)
            if app.sensor_service:
                self._motion_callback = self._on_motion_update
                app.sensor_service.register_callback(self._motion_callback)
                app.sensor_service.start()
        else:
            self.motion_btn.background_color = (0.4, 0.25, 0.25, 1)
            if app.sensor_service:
                if self._motion_callback:
                    app.sensor_service.unregister_callback(self._motion_callback)
                    self._motion_callback = None
                app.sensor_service.stop()

    # === Motion Handlers ===

    def _on_motion_update(self, motion_data):
        """Handle motion sensor updates."""
        service = self._get_service()
        if service:
            threshold = 15
            if abs(motion_data.roll) > threshold or abs(motion_data.pitch) > threshold:
                center = 500
                scale = 10
                x = max(0, min(1000, int(center + motion_data.roll * scale)))
                y = max(0, min(1000, int(center + motion_data.pitch * scale)))
                service.touch_action(x, y, 'move')

    # === Touch Pad Handlers ===

    def _on_tap(self, instance, coord):
        service = self._get_service()
        if service:
            service.select()

    def _on_double_tap(self, instance, coord):
        service = self._get_service()
        if service:
            service.select()

    def _on_swipe(self, instance, direction, velocity, start_coord, end_coord):
        service = self._get_service()
        if service:
            duration = max(50, min(500, int(200 / max(velocity / 1000, 0.5))))
            service.swipe(
                start_coord[0], start_coord[1],
                end_coord[0], end_coord[1],
                duration
            )

    def _on_long_press(self, instance, coord):
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'tap')

    def _on_pad_start(self, instance, coord):
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'down')

    def _on_pad_move(self, instance, coord):
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'move')

    def _on_pad_end(self, instance, coord):
        service = self._get_service()
        if service:
            service.touch_action(coord[0], coord[1], 'up')

    # === D-Pad Handlers ===

    def _on_dpad_direction(self, instance, direction):
        service = self._get_service()
        if not service:
            return

        actions = {
            'up': service.up,
            'down': service.down,
            'left': service.left,
            'right': service.right,
        }
        action = actions.get(direction)
        if action:
            action()

    def _on_dpad_release(self, instance, direction):
        pass

    # === Game Button Handlers ===

    def _on_button_press(self, instance, button_name):
        service = self._get_service()
        if not service:
            return

        actions = {
            'A': service.select,
            'B': service.menu,
            'X': service.play_pause,
            'Y': service.home,
        }
        action = actions.get(button_name)
        if action:
            action()

    def _on_button_release(self, instance, button_name):
        pass

    # === System Buttons ===

    def _on_menu(self, instance):
        service = self._get_service()
        if service:
            service.menu()

    def _on_home(self, instance):
        service = self._get_service()
        if service:
            service.home()

    def _on_play_pause(self, instance):
        service = self._get_service()
        if service:
            service.play_pause()
