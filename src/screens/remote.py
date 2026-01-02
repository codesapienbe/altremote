"""
Remote Screen

Basic remote control interface for navigation and playback.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty
from kivy.app import App

from ..widgets.touch_pad import TouchPad


class RemoteButton(Button):
    """Styled button for the remote control."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0.25, 0.25, 0.28, 1)
        self.background_normal = ''
        self.size_hint_y = None
        self.height = 60


class RemoteScreen(Screen):
    """
    Basic remote control screen.
    
    Features:
    - Touch pad for navigation
    - Menu/Home buttons
    - Playback controls
    - Volume controls
    """
    
    device_name = StringProperty("Not Connected")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI components."""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Header with device name and mode switch
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        # Back button
        back_btn = Button(
            text='<',
            size_hint_x=None,
            width=50,
            background_color=(0.3, 0.3, 0.35, 1)
        )
        back_btn.bind(on_press=self._on_back)
        header.add_widget(back_btn)
        
        # Device name
        self.device_label = Label(text=self.device_name, font_size='18sp')
        self.bind(device_name=lambda inst, val: setattr(self.device_label, 'text', val))
        header.add_widget(self.device_label)
        
        # Game mode button
        game_btn = Button(
            text='Game Mode',
            size_hint_x=None,
            width=120,
            background_color=(0.4, 0.5, 0.6, 1)
        )
        game_btn.bind(on_press=self._on_game_mode)
        header.add_widget(game_btn)
        
        main_layout.add_widget(header)
        
        # Touch pad area
        touch_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.45),
            padding=10
        )
        
        self.touch_pad = TouchPad()
        self.touch_pad.bind(
            on_tap=self._on_tap,
            on_swipe=self._on_swipe,
            on_long_press=self._on_long_press
        )
        touch_container.add_widget(self.touch_pad)
        
        main_layout.add_widget(touch_container)
        
        # Navigation buttons
        nav_layout = GridLayout(
            cols=3,
            size_hint=(1, 0.15),
            spacing=5,
            padding=10
        )
        
        nav_layout.add_widget(RemoteButton(text=''))  # Empty
        nav_layout.add_widget(RemoteButton(text='UP', on_press=self._on_up))
        nav_layout.add_widget(RemoteButton(text=''))  # Empty
        nav_layout.add_widget(RemoteButton(text='LEFT', on_press=self._on_left))
        nav_layout.add_widget(RemoteButton(text='OK', on_press=self._on_select))
        nav_layout.add_widget(RemoteButton(text='RIGHT', on_press=self._on_right))
        nav_layout.add_widget(RemoteButton(text=''))  # Empty
        nav_layout.add_widget(RemoteButton(text='DOWN', on_press=self._on_down))
        nav_layout.add_widget(RemoteButton(text=''))  # Empty
        
        main_layout.add_widget(nav_layout)
        
        # System buttons (Menu, Home)
        system_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.1),
            spacing=10,
            padding=10
        )
        
        menu_btn = RemoteButton(text='Menu', size_hint_x=1)
        menu_btn.bind(on_press=self._on_menu)
        system_layout.add_widget(menu_btn)
        
        home_btn = RemoteButton(text='Home', size_hint_x=1)
        home_btn.bind(on_press=self._on_home)
        system_layout.add_widget(home_btn)
        
        main_layout.add_widget(system_layout)
        
        # Playback controls
        playback_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.1),
            spacing=10,
            padding=10
        )
        
        prev_btn = RemoteButton(text='|<<', size_hint_x=1)
        prev_btn.bind(on_press=self._on_previous)
        playback_layout.add_widget(prev_btn)
        
        play_btn = RemoteButton(text='Play/Pause', size_hint_x=1)
        play_btn.bind(on_press=self._on_play_pause)
        playback_layout.add_widget(play_btn)
        
        next_btn = RemoteButton(text='>>|', size_hint_x=1)
        next_btn.bind(on_press=self._on_next)
        playback_layout.add_widget(next_btn)
        
        main_layout.add_widget(playback_layout)
        
        # Volume controls
        volume_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.1),
            spacing=10,
            padding=10
        )
        
        vol_down = RemoteButton(text='Vol -', size_hint_x=1)
        vol_down.bind(on_press=self._on_volume_down)
        volume_layout.add_widget(vol_down)
        
        vol_up = RemoteButton(text='Vol +', size_hint_x=1)
        vol_up.bind(on_press=self._on_volume_up)
        volume_layout.add_widget(vol_up)
        
        main_layout.add_widget(volume_layout)
        
        self.add_widget(main_layout)
    
    def on_enter(self):
        """Called when the screen is displayed."""
        app = App.get_running_app()
        if app.atv_service:
            self.device_name = app.atv_service.current_device_name or "Apple TV"
    
    def _get_service(self):
        """Get the Apple TV service."""
        app = App.get_running_app()
        return app.atv_service if app else None
    
    # Navigation handlers
    
    def _on_back(self, instance):
        """Go back to home screen."""
        app = App.get_running_app()
        if app:
            app.switch_to_home()
    
    def _on_game_mode(self, instance):
        """Switch to game controller mode."""
        app = App.get_running_app()
        if app:
            app.switch_to_game()
    
    # Touch pad handlers
    
    def _on_tap(self, instance, coord):
        """Handle tap on touch pad."""
        service = self._get_service()
        if service:
            service.select()
    
    def _on_swipe(self, instance, direction, velocity, start_coord, end_coord):
        """Handle swipe on touch pad."""
        service = self._get_service()
        if not service:
            return
        
        # Map swipe direction to navigation
        direction_map = {
            'up': service.up,
            'down': service.down,
            'left': service.left,
            'right': service.right,
            'up_left': service.up,
            'up_right': service.up,
            'down_left': service.down,
            'down_right': service.down,
        }
        
        action = direction_map.get(direction)
        if action:
            action()
    
    def _on_long_press(self, instance, coord):
        """Handle long press on touch pad."""
        service = self._get_service()
        if service:
            # Long press select for context menu
            service.select()
    
    # Navigation button handlers
    
    def _on_up(self, instance):
        service = self._get_service()
        if service:
            service.up()
    
    def _on_down(self, instance):
        service = self._get_service()
        if service:
            service.down()
    
    def _on_left(self, instance):
        service = self._get_service()
        if service:
            service.left()
    
    def _on_right(self, instance):
        service = self._get_service()
        if service:
            service.right()
    
    def _on_select(self, instance):
        service = self._get_service()
        if service:
            service.select()
    
    # System button handlers
    
    def _on_menu(self, instance):
        service = self._get_service()
        if service:
            service.menu()
    
    def _on_home(self, instance):
        service = self._get_service()
        if service:
            service.home()
    
    # Playback handlers
    
    def _on_play_pause(self, instance):
        service = self._get_service()
        if service:
            service.play_pause()
    
    def _on_previous(self, instance):
        service = self._get_service()
        if service:
            service.previous()
    
    def _on_next(self, instance):
        service = self._get_service()
        if service:
            service.next()
    
    # Volume handlers
    
    def _on_volume_up(self, instance):
        service = self._get_service()
        if service:
            service.volume_up()
    
    def _on_volume_down(self, instance):
        service = self._get_service()
        if service:
            service.volume_down()
