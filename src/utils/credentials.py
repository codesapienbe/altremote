"""
Credentials Storage

Secure storage for Apple TV pairing credentials.
"""

import os
import json
import base64
from typing import Optional, Dict

from kivy.utils import platform


class CredentialStorage:
    """
    Secure storage for Apple TV credentials.
    
    On Android: Uses app's private storage
    On iOS: Uses app's Documents directory
    On Desktop: Uses user's home directory with restricted permissions
    
    Note: For production, consider using:
    - Android Keystore
    - iOS Keychain
    - Python keyring library
    """
    
    def __init__(self):
        self._credentials: Dict[str, str] = {}
        self._storage_path = self._get_storage_path()
        self._load()
    
    def _get_storage_path(self) -> str:
        """Get the platform-specific credential storage path."""
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                base_path = app_storage_path()
            except ImportError:
                base_path = os.path.expanduser('~/.appletv-remote')
        elif platform == 'ios':
            base_path = os.path.expanduser('~/Documents')
        else:
            base_path = os.path.expanduser('~/.appletv-remote')
        
        os.makedirs(base_path, exist_ok=True)
        return os.path.join(base_path, '.credentials')
    
    def _load(self):
        """Load credentials from storage."""
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, 'r') as f:
                    data = json.load(f)
                    # Decode base64 values
                    self._credentials = {
                        k: base64.b64decode(v).decode('utf-8')
                        for k, v in data.items()
                    }
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Error loading credentials: {e}")
                self._credentials = {}
    
    def _save(self):
        """Save credentials to storage."""
        try:
            # Encode values as base64 for basic obfuscation
            data = {
                k: base64.b64encode(v.encode('utf-8')).decode('ascii')
                for k, v in self._credentials.items()
            }
            
            with open(self._storage_path, 'w') as f:
                json.dump(data, f)
            
            # Set restrictive permissions on Unix-like systems
            if platform not in ('android', 'ios', 'win'):
                os.chmod(self._storage_path, 0o600)
                
        except IOError as e:
            print(f"Error saving credentials: {e}")
    
    def store(self, device_id: str, credentials: str):
        """
        Store credentials for a device.
        
        Args:
            device_id: Unique identifier for the Apple TV
            credentials: The credential string from pyatv
        """
        self._credentials[device_id] = credentials
        self._save()
    
    def get(self, device_id: str) -> Optional[str]:
        """
        Get credentials for a device.
        
        Args:
            device_id: Unique identifier for the Apple TV
            
        Returns:
            Credential string or None if not found
        """
        return self._credentials.get(device_id)
    
    def remove(self, device_id: str):
        """
        Remove credentials for a device.
        
        Args:
            device_id: Unique identifier for the Apple TV
        """
        if device_id in self._credentials:
            del self._credentials[device_id]
            self._save()
    
    def has_credentials(self, device_id: str) -> bool:
        """Check if credentials exist for a device."""
        return device_id in self._credentials
    
    def list_devices(self) -> list:
        """Get list of device IDs with stored credentials."""
        return list(self._credentials.keys())
    
    def clear_all(self):
        """Remove all stored credentials."""
        self._credentials = {}
        self._save()
