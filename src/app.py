"""
Apple TV Game Remote - Main Application

This module contains the main Kivy application class.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.uix.boxlayout import BoxLayout
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
from .services.log_service import LogService
from .widgets.notification_bar import NotificationBar
from .utils.config import Config


class AppleTVRemoteApp(App):
    """Main application class for the Apple TV Game Remote."""

    title = 'Apple TV Remote'

    # Services
    atv_service = ObjectProperty(None, allownone=True)
    sensor_service = ObjectProperty(None, allownone=True)
    haptic_service = ObjectProperty(None, allownone=True)
    log_service = ObjectProperty(None, allownone=True)

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

        # Initialize log service first
        self.log_service = LogService()

        # Initialize services with error handling
        try:
            self.atv_service = AppleTVService()
            self.atv_service.set_log_service(self.log_service)
        except Exception as e:
            self.log_service.error(f"Failed to initialize ATV service: {e}")
            self.atv_service = None

        try:
            self.haptic_service = HapticService()
        except Exception as e:
            self.log_service.error(f"Failed to initialize haptic service: {e}")
            self.haptic_service = None

        # Sensor service (only on mobile platforms)
        if platform in ('android', 'ios'):
            try:
                self.sensor_service = SensorService()
            except Exception as e:
                self.log_service.error(f"Failed to initialize sensor service: {e}")
                self.sensor_service = None

        # Root layout with screen manager and notification bar
        root = BoxLayout(orientation='vertical')

        # Create screen manager
        self.screen_manager = ScreenManager(transition=SlideTransition())

        # Add screens
        self.screen_manager.add_widget(HomeScreen(name='home'))
        self.screen_manager.add_widget(RemoteScreen(name='remote'))
        self.screen_manager.add_widget(GameControllerScreen(name='game'))

        root.add_widget(self.screen_manager)

        # Add notification bar at the bottom
        self.notification_bar = NotificationBar()
        root.add_widget(self.notification_bar)

        self.log_service.info("App initialized successfully")

        return root

    def on_start(self):
        """Called when the application starts."""
        # Start device discovery
        Clock.schedule_once(lambda dt: self.start_discovery(), 1)

    def on_stop(self):
        """Called when the application stops."""
        # Clean up services
        if self.atv_service:
            try:
                self.atv_service.shutdown()
            except Exception as e:
                print(f"Error disconnecting: {e}")

        if self.sensor_service:
            try:
                self.sensor_service.stop()
            except Exception as e:
                print(f"Error stopping sensors: {e}")

    def on_pause(self):
        """Called when the application is paused (Android)."""
        # Stop sensors to save battery
        if self.sensor_service:
            try:
                self.sensor_service.stop()
            except Exception:
                pass
        return True

    def on_resume(self):
        """Called when the application is resumed (Android)."""
        # Restart sensors if in game mode
        if self.screen_manager.current == 'game' and self.sensor_service:
            try:
                self.sensor_service.start()
            except Exception as e:
                self.log_service.error(f"Failed to resume sensors: {e}")

    def start_discovery(self):
        """Start Apple TV discovery."""
        if self.atv_service:
            try:
                self.log_service.info("Scanning for Apple TV devices...")
                self.atv_service.start_discovery()
            except Exception as e:
                self.log_service.error(f"Discovery failed: {e}")

    def connect_to_device(self, device):
        """Connect to a discovered Apple TV device."""
        if self.atv_service:
            try:
                self.log_service.info(f"Connecting to {device.name}...")
                self.atv_service.connect(device)
            except Exception as e:
                self.log_service.error(f"Connection failed: {e}")

    def switch_to_remote(self):
        """Switch to the remote control screen."""
        self.screen_manager.current = 'remote'
        self.log_service.debug("Switched to remote mode")

    def switch_to_game(self):
        """Switch to the game controller screen."""
        self.screen_manager.current = 'game'
        if self.sensor_service:
            try:
                self.sensor_service.start()
            except Exception as e:
                self.log_service.warning(f"Could not start motion sensors: {e}")
        self.log_service.debug("Switched to game mode")

    def switch_to_home(self):
        """Switch to the home/discovery screen."""
        self.screen_manager.current = 'home'
        if self.sensor_service:
            try:
                self.sensor_service.stop()
            except Exception:
                pass
        self.log_service.debug("Switched to home screen")

    def vibrate(self, duration=0.05):
        """Trigger haptic feedback."""
        if self.haptic_service:
            try:
                self.haptic_service.vibrate(duration)
            except Exception:
                pass
