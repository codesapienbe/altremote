"""
Configuration Management

Handles app configuration and settings persistence.
"""

import os
import json
from typing import Any, Dict, Optional

from kivy.utils import platform


class Config:
    """
    Configuration manager for app settings.
    
    Handles:
    - Loading/saving configuration
    - Default values
    - Platform-specific paths
    """
    
    DEFAULT_CONFIG = {
        'motion_sensitivity': 1.0,
        'haptic_enabled': True,
        'auto_connect': True,
        'last_device_id': None,
        'theme': 'dark',
        'button_layout': 'default',
        'swipe_sensitivity': 1.0,
        'motion_enabled_by_default': True,
    }
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_path = self._get_config_path()
        self._load()
    
    def _get_config_path(self) -> str:
        """Get the platform-specific config file path."""
        if platform == 'android':
            from android.storage import app_storage_path
            base_path = app_storage_path()
        elif platform == 'ios':
            base_path = os.path.expanduser('~/Documents')
        else:
            # Desktop
            base_path = os.path.expanduser('~/.appletv-remote')
        
        # Ensure directory exists
        os.makedirs(base_path, exist_ok=True)
        
        return os.path.join(base_path, 'config.json')
    
    def _load(self):
        """Load configuration from file."""
        self._config = self.DEFAULT_CONFIG.copy()
        
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r') as f:
                    saved_config = json.load(f)
                    self._config.update(saved_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self._config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self._config[key] = value
        self.save()
    
    def reset(self):
        """Reset configuration to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        self.save()
    
    # Convenience properties
    
    @property
    def motion_sensitivity(self) -> float:
        return self.get('motion_sensitivity', 1.0)
    
    @motion_sensitivity.setter
    def motion_sensitivity(self, value: float):
        self.set('motion_sensitivity', value)
    
    @property
    def haptic_enabled(self) -> bool:
        return self.get('haptic_enabled', True)
    
    @haptic_enabled.setter
    def haptic_enabled(self, value: bool):
        self.set('haptic_enabled', value)
    
    @property
    def auto_connect(self) -> bool:
        return self.get('auto_connect', True)
    
    @auto_connect.setter
    def auto_connect(self, value: bool):
        self.set('auto_connect', value)
    
    @property
    def last_device_id(self) -> Optional[str]:
        return self.get('last_device_id')
    
    @last_device_id.setter
    def last_device_id(self, value: Optional[str]):
        self.set('last_device_id', value)
