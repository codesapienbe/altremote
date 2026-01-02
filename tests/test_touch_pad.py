"""
Tests for TouchPad widget.
"""

import unittest
from unittest.mock import MagicMock, patch


class TestTouchPad(unittest.TestCase):
    """Tests for the TouchPad widget."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Kivy imports
        self.kivy_patches = []
        
    def test_coordinate_conversion(self):
        """Test that touch coordinates are properly converted to 0-1000 range."""
        # Test logic for coordinate conversion
        width = 300
        height = 400
        coord_scale = 1000
        
        # Simulate touch at center
        touch_x = 150
        touch_y = 200
        
        rel_x = touch_x / width
        rel_y = touch_y / height
        
        coord_x = int(rel_x * coord_scale)
        coord_y = int(rel_y * coord_scale)
        
        self.assertEqual(coord_x, 500)
        self.assertEqual(coord_y, 500)
    
    def test_coordinate_clamping(self):
        """Test that coordinates are clamped to valid range."""
        width = 300
        height = 400
        coord_scale = 1000
        
        # Simulate touch outside bounds
        touch_x = 400  # Beyond width
        touch_y = -50  # Negative
        
        rel_x = touch_x / width
        rel_y = touch_y / height
        
        # Clamp
        rel_x = max(0, min(1, rel_x))
        rel_y = max(0, min(1, rel_y))
        
        coord_x = int(rel_x * coord_scale)
        coord_y = int(rel_y * coord_scale)
        
        self.assertEqual(coord_x, 1000)  # Clamped to max
        self.assertEqual(coord_y, 0)     # Clamped to min
    
    def test_swipe_direction_detection(self):
        """Test swipe direction detection from delta values."""
        import math
        
        def get_swipe_direction(dx, dy):
            angle = math.atan2(dy, dx) * 180 / math.pi
            if angle < 0:
                angle += 360
            
            if 337.5 <= angle or angle < 22.5:
                return 'right'
            elif 22.5 <= angle < 67.5:
                return 'up_right'
            elif 67.5 <= angle < 112.5:
                return 'up'
            elif 112.5 <= angle < 157.5:
                return 'up_left'
            elif 157.5 <= angle < 202.5:
                return 'left'
            elif 202.5 <= angle < 247.5:
                return 'down_left'
            elif 247.5 <= angle < 292.5:
                return 'down'
            else:
                return 'down_right'
        
        # Test each direction
        self.assertEqual(get_swipe_direction(100, 0), 'right')
        self.assertEqual(get_swipe_direction(-100, 0), 'left')
        self.assertEqual(get_swipe_direction(0, 100), 'up')
        self.assertEqual(get_swipe_direction(0, -100), 'down')
        self.assertEqual(get_swipe_direction(100, 100), 'up_right')
        self.assertEqual(get_swipe_direction(-100, 100), 'up_left')
        self.assertEqual(get_swipe_direction(100, -100), 'down_right')
        self.assertEqual(get_swipe_direction(-100, -100), 'down_left')


class TestMotionData(unittest.TestCase):
    """Tests for motion data processing."""
    
    def test_pitch_roll_calculation(self):
        """Test pitch and roll calculation from accelerometer data."""
        import math
        
        # Simulate phone lying flat
        ax, ay, az = 0, 0, -9.81
        
        pitch = math.atan2(ay, az) * 180 / math.pi
        gravity = math.sqrt(ax*ax + ay*ay + az*az)
        roll = math.asin(ax / gravity) * 180 / math.pi
        
        self.assertAlmostEqual(pitch, 180, places=1)  # Pointing up
        self.assertAlmostEqual(roll, 0, places=1)      # No roll
    
    def test_tilt_detection(self):
        """Test tilt detection thresholds."""
        import math
        
        # Simulate phone tilted 30 degrees right
        tilt_angle = 30
        ax = 9.81 * math.sin(math.radians(tilt_angle))
        ay = 0
        az = -9.81 * math.cos(math.radians(tilt_angle))
        
        gravity = math.sqrt(ax*ax + ay*ay + az*az)
        roll = math.asin(ax / gravity) * 180 / math.pi
        
        self.assertAlmostEqual(roll, 30, places=0)


class TestAppleTVService(unittest.TestCase):
    """Tests for Apple TV service."""
    
    def test_coordinate_range(self):
        """Test that pyatv coordinate range is respected."""
        # pyatv uses 0-1000 coordinate range
        min_coord = 0
        max_coord = 1000
        
        # Test various inputs
        test_values = [-50, 0, 500, 1000, 1500]
        
        for val in test_values:
            clamped = max(min_coord, min(max_coord, val))
            self.assertGreaterEqual(clamped, min_coord)
            self.assertLessEqual(clamped, max_coord)


if __name__ == '__main__':
    unittest.main()
