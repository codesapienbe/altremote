"""
Sensor Service

Provides access to device sensors (accelerometer, gyroscope) for motion controls.
Uses Plyer for cross-platform sensor access.
"""

from typing import Tuple, Optional, Callable
from dataclasses import dataclass

from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import platform


@dataclass
class MotionData:
    """Container for motion sensor data."""
    # Accelerometer (m/s²)
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 0.0
    
    # Gyroscope (rad/s)
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    
    # Derived values
    pitch: float = 0.0  # Tilt forward/backward (degrees)
    roll: float = 0.0   # Tilt left/right (degrees)
    yaw: float = 0.0    # Rotation (degrees)


class SensorService(EventDispatcher):
    """
    Service for accessing device motion sensors.
    
    Provides:
    - Accelerometer data for tilt detection
    - Gyroscope data for rotation detection
    - Calculated pitch, roll, and yaw values
    """
    
    # Properties
    is_active = BooleanProperty(False)
    has_accelerometer = BooleanProperty(False)
    has_gyroscope = BooleanProperty(False)
    
    # Update rate (times per second)
    update_rate = NumericProperty(60)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self._motion_data = MotionData()
        self._update_event = None
        self._callbacks = []
        
        # Try to initialize sensors
        self._init_sensors()
    
    def _init_sensors(self):
        """Initialize platform-specific sensors."""
        if platform == 'android':
            self._init_android_sensors()
        elif platform == 'ios':
            self._init_ios_sensors()
        else:
            # Desktop - simulate sensors for development
            self._init_simulated_sensors()
    
    def _init_android_sensors(self):
        """Initialize Android sensors using Plyer."""
        try:
            from plyer import accelerometer, gyroscope
            
            # Check accelerometer
            try:
                accelerometer.enable()
                accelerometer.disable()
                self.has_accelerometer = True
                self._accelerometer = accelerometer
            except Exception:
                self._accelerometer = None
            
            # Check gyroscope
            try:
                gyroscope.enable()
                gyroscope.disable()
                self.has_gyroscope = True
                self._gyroscope = gyroscope
            except Exception:
                self._gyroscope = None
                
        except ImportError:
            print("Plyer not available for sensor access")
            self._init_simulated_sensors()
    
    def _init_ios_sensors(self):
        """Initialize iOS sensors using Pyobjus."""
        try:
            from pyobjus import autoclass
            
            CMMotionManager = autoclass('CMMotionManager')
            self._motion_manager = CMMotionManager.alloc().init()
            
            self.has_accelerometer = self._motion_manager.accelerometerAvailable
            self.has_gyroscope = self._motion_manager.gyroAvailable
            
        except ImportError:
            print("Pyobjus not available for sensor access")
            self._init_simulated_sensors()
    
    def _init_simulated_sensors(self):
        """Initialize simulated sensors for desktop development."""
        self.has_accelerometer = True
        self.has_gyroscope = True
        self._simulated = True
        self._sim_time = 0.0
    
    def start(self):
        """Start reading sensor data."""
        if self.is_active:
            return
        
        self.is_active = True
        
        if platform == 'android':
            self._start_android_sensors()
        elif platform == 'ios':
            self._start_ios_sensors()
        
        # Schedule updates
        interval = 1.0 / self.update_rate
        self._update_event = Clock.schedule_interval(self._update, interval)
    
    def stop(self):
        """Stop reading sensor data."""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Cancel update event
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        
        if platform == 'android':
            self._stop_android_sensors()
        elif platform == 'ios':
            self._stop_ios_sensors()
    
    def _start_android_sensors(self):
        """Start Android sensors."""
        if self._accelerometer:
            self._accelerometer.enable()
        if self._gyroscope:
            self._gyroscope.enable()
    
    def _stop_android_sensors(self):
        """Stop Android sensors."""
        if self._accelerometer:
            self._accelerometer.disable()
        if self._gyroscope:
            self._gyroscope.disable()
    
    def _start_ios_sensors(self):
        """Start iOS sensors."""
        if self._motion_manager:
            interval = 1.0 / self.update_rate
            if self.has_accelerometer:
                self._motion_manager.startAccelerometerUpdatesToQueue_withHandler_(
                    None, None
                )
            if self.has_gyroscope:
                self._motion_manager.startGyroUpdatesToQueue_withHandler_(
                    None, None
                )
    
    def _stop_ios_sensors(self):
        """Stop iOS sensors."""
        if self._motion_manager:
            self._motion_manager.stopAccelerometerUpdates()
            self._motion_manager.stopGyroUpdates()
    
    def _update(self, dt):
        """Update sensor readings."""
        if platform == 'android':
            self._update_android(dt)
        elif platform == 'ios':
            self._update_ios(dt)
        else:
            self._update_simulated(dt)
        
        # Calculate derived values
        self._calculate_orientation()
        
        # Notify callbacks
        for callback in self._callbacks:
            callback(self._motion_data)
    
    def _update_android(self, dt):
        """Update from Android sensors."""
        if self._accelerometer:
            accel = self._accelerometer.acceleration
            if accel != (None, None, None):
                self._motion_data.accel_x = accel[0] or 0.0
                self._motion_data.accel_y = accel[1] or 0.0
                self._motion_data.accel_z = accel[2] or 0.0
        
        if self._gyroscope:
            gyro = self._gyroscope.rotation
            if gyro != (None, None, None):
                self._motion_data.gyro_x = gyro[0] or 0.0
                self._motion_data.gyro_y = gyro[1] or 0.0
                self._motion_data.gyro_z = gyro[2] or 0.0
    
    def _update_ios(self, dt):
        """Update from iOS sensors."""
        if self._motion_manager:
            if self.has_accelerometer:
                accel_data = self._motion_manager.accelerometerData
                if accel_data:
                    accel = accel_data.acceleration
                    self._motion_data.accel_x = accel.x * 9.81  # Convert to m/s²
                    self._motion_data.accel_y = accel.y * 9.81
                    self._motion_data.accel_z = accel.z * 9.81
            
            if self.has_gyroscope:
                gyro_data = self._motion_manager.gyroData
                if gyro_data:
                    gyro = gyro_data.rotationRate
                    self._motion_data.gyro_x = gyro.x
                    self._motion_data.gyro_y = gyro.y
                    self._motion_data.gyro_z = gyro.z
    
    def _update_simulated(self, dt):
        """Update simulated sensor data for desktop development."""
        import math
        
        self._sim_time += dt
        
        # Simulate gentle motion
        self._motion_data.accel_x = math.sin(self._sim_time) * 2.0
        self._motion_data.accel_y = math.cos(self._sim_time * 0.7) * 1.5
        self._motion_data.accel_z = -9.81 + math.sin(self._sim_time * 0.3) * 0.5
        
        self._motion_data.gyro_x = math.sin(self._sim_time * 2) * 0.1
        self._motion_data.gyro_y = math.cos(self._sim_time * 1.5) * 0.1
        self._motion_data.gyro_z = math.sin(self._sim_time * 0.5) * 0.05
    
    def _calculate_orientation(self):
        """Calculate pitch, roll, and yaw from sensor data."""
        import math
        
        ax = self._motion_data.accel_x
        ay = self._motion_data.accel_y
        az = self._motion_data.accel_z
        
        # Calculate pitch (rotation around X axis)
        if az != 0:
            self._motion_data.pitch = math.atan2(ay, az) * 180.0 / math.pi
        
        # Calculate roll (rotation around Y axis)
        gravity = math.sqrt(ax*ax + ay*ay + az*az)
        if gravity != 0:
            self._motion_data.roll = math.asin(ax / gravity) * 180.0 / math.pi
        
        # Yaw from gyroscope integration (simplified)
        # In a real app, you'd use a complementary or Kalman filter
        self._motion_data.yaw += self._motion_data.gyro_z * (1.0 / self.update_rate) * 180.0 / math.pi
    
    def register_callback(self, callback: Callable[[MotionData], None]):
        """Register a callback to receive motion data updates."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[MotionData], None]):
        """Unregister a motion data callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    @property
    def motion_data(self) -> MotionData:
        """Get the current motion data."""
        return self._motion_data
    
    @property
    def pitch(self) -> float:
        """Get the current pitch angle in degrees."""
        return self._motion_data.pitch
    
    @property
    def roll(self) -> float:
        """Get the current roll angle in degrees."""
        return self._motion_data.roll
    
    @property
    def tilt(self) -> Tuple[float, float]:
        """Get the current tilt as (pitch, roll) in degrees."""
        return (self._motion_data.pitch, self._motion_data.roll)
