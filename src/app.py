"""
Apple TV Game Remote - Main Application

This module contains the main Kivy application class.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.utils import platform

from .screens.home import HomeScreen
from .screens.remote import RemoteScreen
from .screens.game_controller import GameControllerScreen
from .services.apple_tv_service import AppleTVService
from .services.sensor_service import SensorService
from .services.haptic_service import HapticService
from .utils.config import Config


class AppleTVRemoteApp(App):
    """Main application class for the Apple TV Game Remote."""
    
    title = 'Apple TV Remote'
    
    # Services
    atv_service = ObjectProperty(None, allownone=True)
    sensor_service = ObjectProperty(None, allownone=True)
    haptic_service = ObjectProperty(None, allownone=True)
    
    # Configuration
    config_manager = ObjectProperty(None)
    
    def build(self):
        """Build the application UI."""
        # Set window properties for mobile
        Window.clearcolor = (0.1, 0.1, 0.12, 1)
        
        if platform in ('android', 'ios'):
            Window.softinput_mode = 'below_target'
        
        # Initialize configuration
        self.config_manager = Config()
        
        # Initialize services
        self.atv_service = AppleTVService()
        self.haptic_service = HapticService()
        
        # Sensor service (only on mobile platforms)
        if platform in ('android', 'ios'):
            self.sensor_service = SensorService()
        
        # Create screen manager
        self.screen_manager = ScreenManager(transition=SlideTransition())
        
        # Add screens
        self.screen_manager.add_widget(HomeScreen(name='home'))
        self.screen_manager.add_widget(RemoteScreen(name='remote'))
        self.screen_manager.add_widget(GameControllerScreen(name='game'))
        
        return self.screen_manager
    
    def on_start(self):
        """Called when the application starts."""
        # Start device discovery
        Clock.schedule_once(lambda dt: self.start_discovery(), 1)
    
    def on_stop(self):
        """Called when the application stops."""
        # Clean up services
        if self.atv_service:
            self.atv_service.disconnect()
        
        if self.sensor_service:
            self.sensor_service.stop()
    
    def on_pause(self):
        """Called when the application is paused (Android)."""
        # Stop sensors to save battery
        if self.sensor_service:
            self.sensor_service.stop()
        return True
    
    def on_resume(self):
        """Called when the application is resumed (Android)."""
        # Restart sensors if in game mode
        if self.screen_manager.current == 'game' and self.sensor_service:
            self.sensor_service.start()
    
    def start_discovery(self):
        """Start Apple TV discovery."""
        if self.atv_service:
            self.atv_service.start_discovery()
    
    def connect_to_device(self, device):
        """Connect to a discovered Apple TV device."""
        if self.atv_service:
            self.atv_service.connect(device)
    
    def switch_to_remote(self):
        """Switch to the remote control screen."""
        self.screen_manager.current = 'remote'
    
    def switch_to_game(self):
        """Switch to the game controller screen."""
        self.screen_manager.current = 'game'
        if self.sensor_service:
            self.sensor_service.start()
    
    def switch_to_home(self):
        """Switch to the home/discovery screen."""
        self.screen_manager.current = 'home'
        if self.sensor_service:
            self.sensor_service.stop()
    
    def vibrate(self, duration=0.05):
        """Trigger haptic feedback."""
        if self.haptic_service:
            self.haptic_service.vibrate(duration)
