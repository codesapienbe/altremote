"""
Haptic Feedback Service

Provides vibration/haptic feedback for touch interactions.
"""

from kivy.utils import platform


class HapticService:
    """
    Service for providing haptic feedback.
    
    Supports:
    - Simple vibration
    - Pattern vibration
    - Intensity control (where supported)
    """
    
    def __init__(self):
        self._available = False
        self._init_haptics()
    
    def _init_haptics(self):
        """Initialize platform-specific haptic feedback."""
        if platform == 'android':
            self._init_android_haptics()
        elif platform == 'ios':
            self._init_ios_haptics()
        else:
            # Desktop - haptics not available
            self._available = False
    
    def _init_android_haptics(self):
        """Initialize Android haptic feedback using Plyer."""
        try:
            from plyer import vibrator
            self._vibrator = vibrator
            self._available = True
        except ImportError:
            self._available = False
    
    def _init_ios_haptics(self):
        """Initialize iOS haptic feedback."""
        try:
            from pyobjus import autoclass
            
            UIImpactFeedbackGenerator = autoclass('UIImpactFeedbackGenerator')
            self._impact_generator = UIImpactFeedbackGenerator.alloc().initWithStyle_(1)  # Medium
            self._impact_generator.prepare()
            self._available = True
        except ImportError:
            self._available = False
    
    @property
    def is_available(self) -> bool:
        """Check if haptic feedback is available."""
        return self._available
    
    def vibrate(self, duration: float = 0.05):
        """
        Trigger a simple vibration.
        
        Args:
            duration: Vibration duration in seconds
        """
        if not self._available:
            return
        
        if platform == 'android':
            # Convert to milliseconds
            self._vibrator.vibrate(time=duration)
        elif platform == 'ios':
            self._impact_generator.impactOccurred()
    
    def vibrate_pattern(self, pattern: list):
        """
        Trigger a pattern vibration.
        
        Args:
            pattern: List of (duration, pause) tuples in seconds
                    e.g., [(0.1, 0.1), (0.1, 0.1)] for two short buzzes
        """
        if not self._available:
            return
        
        if platform == 'android':
            # Convert pattern to Android format (alternating wait/vibrate times)
            android_pattern = []
            for duration, pause in pattern:
                android_pattern.extend([int(pause * 1000), int(duration * 1000)])
            self._vibrator.pattern(pattern=android_pattern, repeat=False)
    
    def tap_feedback(self):
        """Light haptic feedback for button taps."""
        self.vibrate(0.02)
    
    def button_press_feedback(self):
        """Medium haptic feedback for button presses."""
        self.vibrate(0.05)
    
    def swipe_feedback(self):
        """Light haptic feedback for swipe gestures."""
        self.vibrate(0.01)
    
    def error_feedback(self):
        """Strong haptic feedback for errors."""
        self.vibrate_pattern([(0.1, 0.05), (0.1, 0.0)])
    
    def success_feedback(self):
        """Success haptic feedback pattern."""
        self.vibrate_pattern([(0.05, 0.05), (0.1, 0.0)])
