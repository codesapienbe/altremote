"""
Apple TV Service

Wrapper around pyatv library for Apple TV communication.
Handles discovery, pairing, connection, and remote control commands.
"""

import asyncio
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.clock import Clock

from ..utils.credentials import CredentialStorage

# pyatv imports (will be available when installed)
try:
    import pyatv
    from pyatv import scan, pair, connect
    from pyatv.const import Protocol, InputAction, DeviceState
    from pyatv.interface import AppleTV, RemoteControl
    PYATV_AVAILABLE = True
except ImportError:
    PYATV_AVAILABLE = False
    print("Warning: pyatv not installed. Apple TV features will be simulated.")


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    PAIRING = "pairing"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class DiscoveredDevice:
    """Represents a discovered Apple TV device."""
    name: str
    address: str
    identifier: str
    model: str
    config: object = None  # pyatv config object


class AppleTVService(EventDispatcher):
    """
    Service for communicating with Apple TV devices.
    
    Wraps the pyatv library to provide:
    - Device discovery
    - Pairing with PIN
    - Remote control commands
    - Touch/swipe gestures
    - Volume control
    """
    
    # Properties
    is_connected = BooleanProperty(False)
    connection_state = StringProperty(ConnectionState.DISCONNECTED.value)
    current_device_name = StringProperty("")
    discovered_devices = ListProperty([])
    error_message = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self._atv: Optional['AppleTV'] = None
        self._remote: Optional['RemoteControl'] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._discovery_task = None
        self._credentials = {}

        # Initialize persistent storage and load saved credentials
        self._credential_storage = CredentialStorage()
        for device_id in self._credential_storage.list_devices():
            self._credentials[device_id] = self._credential_storage.get(device_id)

        # Create event loop for async operations
        self._setup_event_loop()
    
    def _setup_event_loop(self):
        """Set up the asyncio event loop."""
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
    
    def _run_async(self, coro):
        """Run an async coroutine from sync code."""
        if self._loop.is_running():
            asyncio.ensure_future(coro, loop=self._loop)
        else:
            self._loop.run_until_complete(coro)
    
    # Discovery Methods
    
    def start_discovery(self, timeout: float = 5.0):
        """Start scanning for Apple TV devices on the network."""
        self.connection_state = ConnectionState.SCANNING.value
        self.discovered_devices = []
        
        if not PYATV_AVAILABLE:
            # Simulate discovery for development
            Clock.schedule_once(lambda dt: self._simulate_discovery(), 2.0)
            return
        
        self._run_async(self._discover_devices(timeout))
    
    async def _discover_devices(self, timeout: float):
        """Async device discovery."""
        try:
            atvs = await pyatv.scan(self._loop, timeout=timeout)
            
            devices = []
            for atv in atvs:
                device = DiscoveredDevice(
                    name=atv.name,
                    address=str(atv.address),
                    identifier=atv.identifier,
                    model=str(atv.device_info.model) if atv.device_info else "Unknown",
                    config=atv
                )
                devices.append(device)
            
            # Update on main thread
            Clock.schedule_once(lambda dt: self._update_devices(devices))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._handle_error(str(e)))
    
    def _simulate_discovery(self):
        """Simulate device discovery for development without real Apple TV."""
        devices = [
            DiscoveredDevice(
                name="Living Room Apple TV",
                address="192.168.1.100",
                identifier="AAAABBBB-CCCC-DDDD",
                model="Apple TV 4K"
            ),
            DiscoveredDevice(
                name="Bedroom Apple TV",
                address="192.168.1.101",
                identifier="EEEEFFFF-GGGG-HHHH",
                model="Apple TV HD"
            )
        ]
        self._update_devices(devices)
    
    def _update_devices(self, devices: List[DiscoveredDevice]):
        """Update discovered devices list."""
        self.discovered_devices = devices
        self.connection_state = ConnectionState.DISCONNECTED.value
    
    # Connection Methods
    
    def connect(self, device: DiscoveredDevice):
        """Connect to a discovered Apple TV device."""
        self.current_device_name = device.name

        if not PYATV_AVAILABLE:
            # Simulate connection
            self.connection_state = ConnectionState.CONNECTING.value
            Clock.schedule_once(lambda dt: self._simulate_connect(), 1.0)
            return

        # Check if we have stored Companion credentials
        credentials = self._credentials.get(device.identifier)
        if not credentials:
            # No credentials - need to pair first
            self._request_pairing(device)
        else:
            # Have credentials - try to connect
            self.connection_state = ConnectionState.CONNECTING.value
            self._run_async(self._connect_to_device(device, credentials))
    
    async def _connect_to_device(self, device: DiscoveredDevice, credentials=None):
        """Async connection to Apple TV."""
        try:
            config = device.config
            
            # Set credentials if available
            if credentials:
                config.set_credentials(Protocol.Companion, credentials)
            
            self._atv = await pyatv.connect(config, self._loop)
            self._remote = self._atv.remote_control
            
            Clock.schedule_once(lambda dt: self._on_connected())
            
        except pyatv.exceptions.AuthenticationError:
            # Need to pair
            Clock.schedule_once(lambda dt: self._request_pairing(device))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._handle_error(str(e)))
    
    def _simulate_connect(self):
        """Simulate successful connection."""
        self._on_connected()
    
    def _on_connected(self):
        """Handle successful connection."""
        self.is_connected = True
        self.connection_state = ConnectionState.CONNECTED.value
    
    # Pairing Methods
    
    def _request_pairing(self, device: DiscoveredDevice):
        """Request pairing with the device."""
        self.connection_state = ConnectionState.PAIRING.value
        self._run_async(self._start_pairing(device))
    
    async def _start_pairing(self, device: DiscoveredDevice):
        """Start the pairing process."""
        try:
            pairing = await pyatv.pair(device.config, Protocol.Companion, self._loop)
            await pairing.begin()
            
            # PIN will be displayed on TV - notify UI
            self._current_pairing = pairing
            self._pairing_device = device
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._handle_error(str(e)))
    
    def submit_pin(self, pin: str):
        """Submit the PIN displayed on the Apple TV."""
        if not PYATV_AVAILABLE:
            Clock.schedule_once(lambda dt: self._on_connected(), 1.0)
            return
        
        self._run_async(self._finish_pairing(pin))
    
    async def _finish_pairing(self, pin: str):
        """Complete the pairing process with the PIN."""
        try:
            self._current_pairing.pin(pin)
            await self._current_pairing.finish()
            
            # Store credentials in memory and persist to storage
            credentials = self._current_pairing.service.credentials
            self._credentials[self._pairing_device.identifier] = credentials
            self._credential_storage.store(self._pairing_device.identifier, credentials)

            # Now connect
            await self._connect_to_device(self._pairing_device, credentials)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._handle_error(str(e)))
    
    def disconnect(self):
        """Disconnect from the Apple TV."""
        if self._atv:
            self._atv.close()
            self._atv = None
            self._remote = None
        
        self.is_connected = False
        self.connection_state = ConnectionState.DISCONNECTED.value
        self.current_device_name = ""
    
    # Remote Control Methods
    
    def _send_command(self, command_name: str, **kwargs):
        """Send a remote control command."""
        if not PYATV_AVAILABLE or not self._remote:
            print(f"[Simulated] Command: {command_name} {kwargs}")
            return
        
        command = getattr(self._remote, command_name, None)
        if command:
            self._run_async(command(**kwargs))
    
    # Navigation Commands
    
    def up(self, action=None):
        """Navigate up."""
        if action:
            self._send_command('up', action=action)
        else:
            self._send_command('up')
    
    def down(self, action=None):
        """Navigate down."""
        if action:
            self._send_command('down', action=action)
        else:
            self._send_command('down')
    
    def left(self, action=None):
        """Navigate left."""
        if action:
            self._send_command('left', action=action)
        else:
            self._send_command('left')
    
    def right(self, action=None):
        """Navigate right."""
        if action:
            self._send_command('right', action=action)
        else:
            self._send_command('right')
    
    def select(self, action=None):
        """Select/confirm."""
        if action:
            self._send_command('select', action=action)
        else:
            self._send_command('select')
    
    # Button Commands
    
    def menu(self, action=None):
        """Menu button."""
        if action:
            self._send_command('menu', action=action)
        else:
            self._send_command('menu')
    
    def home(self, action=None):
        """Home button."""
        if action:
            self._send_command('home', action=action)
        else:
            self._send_command('home')
    
    def home_hold(self):
        """Long press home button (Control Center)."""
        self._send_command('home_hold')
    
    def top_menu(self):
        """Go to top menu."""
        self._send_command('top_menu')
    
    # Playback Commands
    
    def play(self):
        """Start playback."""
        self._send_command('play')
    
    def pause(self):
        """Pause playback."""
        self._send_command('pause')
    
    def play_pause(self):
        """Toggle play/pause."""
        self._send_command('play_pause')
    
    def stop(self):
        """Stop playback."""
        self._send_command('stop')
    
    def next(self):
        """Skip to next track."""
        self._send_command('next')
    
    def previous(self):
        """Go to previous track."""
        self._send_command('previous')
    
    def skip_forward(self, seconds: int = 10):
        """Skip forward."""
        self._send_command('skip_forward', time_interval=seconds)
    
    def skip_backward(self, seconds: int = 10):
        """Skip backward."""
        self._send_command('skip_backward', time_interval=seconds)
    
    # Volume Commands
    
    def volume_up(self):
        """Increase volume."""
        self._send_command('volume_up')
    
    def volume_down(self):
        """Decrease volume."""
        self._send_command('volume_down')
    
    def set_volume(self, level: float):
        """Set volume level (0.0 - 1.0)."""
        self._send_command('set_volume', level=level)
    
    # Touch/Swipe Commands (Game Controller)
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 200):
        """
        Send a swipe gesture.
        
        Coordinates are in range [0, 1000].
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration_ms: Duration in milliseconds
        """
        if not PYATV_AVAILABLE:
            print(f"[Simulated] Swipe: ({start_x},{start_y}) -> ({end_x},{end_y}) in {duration_ms}ms")
            return
        
        if self._atv and hasattr(self._atv, 'touch'):
            self._run_async(
                self._atv.touch.swipe(start_x, start_y, end_x, end_y, duration_ms)
            )
    
    def touch_action(self, x: int, y: int, action_type: str = 'tap'):
        """
        Send a touch action at specific coordinates.
        
        Coordinates are in range [0, 1000].
        
        Args:
            x: X coordinate
            y: Y coordinate
            action_type: 'tap', 'down', 'up', or 'move'
        """
        if not PYATV_AVAILABLE:
            print(f"[Simulated] Touch {action_type}: ({x},{y})")
            return
        
        if self._atv and hasattr(self._atv, 'touch'):
            # Map action type to pyatv TouchAction enum
            from pyatv.const import TouchAction
            action_map = {
                'tap': TouchAction.Click,
                'down': TouchAction.Down,
                'up': TouchAction.Up,
                'move': TouchAction.Move
            }
            action = action_map.get(action_type, TouchAction.Click)
            self._run_async(self._atv.touch.action(x, y, action))
    
    # Error Handling
    
    def _handle_error(self, message: str):
        """Handle errors."""
        self.error_message = message
        self.connection_state = ConnectionState.ERROR.value
        print(f"AppleTVService Error: {message}")
