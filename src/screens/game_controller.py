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
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line

from ..widgets.touch_pad import TouchPad
from ..widgets.game_buttons import GameButtons, DPad


class IconButton(ButtonBehavior, Widget):
    """Button with canvas-drawn icon."""

    def __init__(self, icon_type: str = "back", size_hint=(None, None),
                 width=50, height=50, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = size_hint
        self.size = (width, height)
        self.icon_type = icon_type
        self._draw()
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.22, 0.22, 0.27, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

            # Icon color
            Color(0.7, 0.7, 0.7, 1)

            cx, cy = self.center_x, self.center_y

            if self.icon_type == "back":
                # Left chevron <
                Line(points=[cx + 6, cy + 10, cx - 6, cy, cx + 6, cy - 10], width=2)

            elif self.icon_type == "menu":
                # Three horizontal lines (hamburger menu)
                Line(points=[cx - 10, cy + 8, cx + 10, cy + 8], width=2)
                Line(points=[cx - 10, cy, cx + 10, cy], width=2)
                Line(points=[cx - 10, cy - 8, cx + 10, cy - 8], width=2)

            elif self.icon_type == "home":
                # House shape
                # Roof
                Line(points=[cx - 12, cy, cx, cy + 10, cx + 12, cy], width=2)
                # Walls
                Line(points=[cx - 10, cy, cx - 10, cy - 10, cx + 10, cy - 10, cx + 10, cy], width=2)
                # Door
                Line(points=[cx - 3, cy - 10, cx - 3, cy - 3, cx + 3, cy - 3, cx + 3, cy - 10], width=1.5)

            elif self.icon_type == "gamepad":
                # Controller shape
                RoundedRectangle(pos=(cx - 14, cy - 6), size=(28, 14), radius=[4])
                # D-pad (left)
                Line(points=[cx - 9, cy - 2, cx - 9, cy + 2], width=1.5)
                Line(points=[cx - 11, cy, cx - 7, cy], width=1.5)
                # Buttons (right) - small circles
                Color(0.7, 0.7, 0.7, 1)
                Line(circle=(cx + 8, cy + 1, 2), width=1.2)
                Line(circle=(cx + 11, cy - 1, 2), width=1.2)

    def on_press(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

    def on_release(self):
        self.canvas.before.clear()
        self._draw()


class GameControllerScreen(Screen):
    """
    Game controller screen with gamepad-style layout.

    Layout (landscape-style on portrait screen):
    ┌─────────────────────────────────────────────────────┐
    │  [<]           [Gamepad] Game Mode        [Motion]  │
    ├─────────────────────────────────────────────────────┤
    │              [MENU]            [HOME]               │
    │                                                     │
    │   ┌───────┐                              Y          │
    │   │   ↑   │     ┌──────────────────┐   X   A        │
    │ ┌─┼───────┼─┐   │                  │      B         │
    │ │←│       │→│   │    TOUCH PAD     │                │
    │ └─┼───────┼─┘   │                  │                │
    │   │   ↓   │     └──────────────────┘                │
    │   └───────┘                                         │
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
            height=50,
            padding=[5, 0],
            spacing=10
        )

        # Back button (icon only)
        back_btn = IconButton(
            icon_type='back',
            width=45,
            height=45
        )
        back_btn.bind(on_release=self._on_back)
        header.add_widget(back_btn)

        header.add_widget(Widget())  # Spacer

        # Game Mode with icon and text
        game_mode_box = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=150,
            spacing=5
        )
        game_icon = IconButton(
            icon_type='gamepad',
            width=40,
            height=35
        )
        game_mode_box.add_widget(game_icon)
        game_mode_box.add_widget(Label(
            text='Game Mode',
            font_size='15sp',
            bold=True,
            size_hint=(None, 1),
            width=100
        ))
        header.add_widget(game_mode_box)

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

        # === System Buttons Row (Menu/Home icons) ===
        system_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=50,
            padding=[20, 0],
            spacing=30
        )
        system_row.add_widget(Widget())  # Left spacer

        # Menu button (icon only)
        menu_btn = IconButton(
            icon_type='menu',
            width=60,
            height=45
        )
        menu_btn.bind(on_release=self._on_menu)
        system_row.add_widget(menu_btn)

        # Home button (icon only)
        home_btn = IconButton(
            icon_type='home',
            width=60,
            height=45
        )
        home_btn.bind(on_release=self._on_home)
        system_row.add_widget(home_btn)

        system_row.add_widget(Widget())  # Right spacer
        main_layout.add_widget(system_row)

        # === Main Controls Area ===
        controls_area = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[5, 5],
            spacing=5
        )

        # --- Left: D-Pad (2x larger = 360x360) ---
        left_container = FloatLayout(size_hint=(0.35, 1))

        # Center the D-pad vertically in its container
        self.dpad = DPad(
            size_hint=(None, None),
            size=(360, 360),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.dpad.bind(
            on_direction=self._on_dpad_direction,
            on_direction_release=self._on_dpad_release
        )
        left_container.add_widget(self.dpad)
        controls_area.add_widget(left_container)

        # --- Center: Touch Pad ---
        center_container = FloatLayout(size_hint=(0.35, 1))

        # Touch pad with background
        self.touchpad_wrapper = RelativeLayout(
            size_hint=(0.95, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
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
        right_container = FloatLayout(size_hint=(0.30, 1))

        self.game_buttons = GameButtons(
            size_hint=(None, None),
            size=(170, 170),
            button_size=55,
            spacing=5,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
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
