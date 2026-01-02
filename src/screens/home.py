"""
Home Screen

Device discovery and connection screen.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.app import App


class DeviceButton(Button):
    """Button representing a discovered Apple TV device."""
    
    device = ObjectProperty(None)
    
    def __init__(self, device, **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.text = f"{device.name}\n{device.model}\n{device.address}"
        self.halign = 'center'
        self.valign = 'middle'
        self.text_size = self.size
        self.size_hint_y = None
        self.height = 100
        self.background_color = (0.2, 0.2, 0.25, 1)
        
        self.bind(size=self._update_text_size)
    
    def _update_text_size(self, *args):
        self.text_size = self.size


class HomeScreen(Screen):
    """
    Home screen for discovering and connecting to Apple TV devices.
    """
    
    status_text = StringProperty("Searching for Apple TV devices...")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI components."""
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        header = Label(
            text='Apple TV Remote',
            font_size='28sp',
            size_hint_y=None,
            height=60,
            bold=True
        )
        layout.add_widget(header)
        
        # Status label
        self.status_label = Label(
            text=self.status_text,
            font_size='16sp',
            size_hint_y=None,
            height=40
        )
        self.bind(status_text=lambda inst, val: setattr(self.status_label, 'text', val))
        layout.add_widget(self.status_label)
        
        # Device list container
        scroll = ScrollView(size_hint=(1, 1))
        self.device_list = GridLayout(
            cols=1,
            spacing=10,
            size_hint_y=None,
            padding=10
        )
        self.device_list.bind(minimum_height=self.device_list.setter('height'))
        scroll.add_widget(self.device_list)
        layout.add_widget(scroll)
        
        # Button row
        button_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=60,
            spacing=10
        )
        
        # Refresh button
        refresh_btn = Button(
            text='Refresh',
            background_color=(0.3, 0.5, 0.7, 1)
        )
        refresh_btn.bind(on_press=self._on_refresh)
        button_row.add_widget(refresh_btn)
        
        # Manual connect button
        manual_btn = Button(
            text='Manual Connect',
            background_color=(0.4, 0.4, 0.45, 1)
        )
        manual_btn.bind(on_press=self._on_manual_connect)
        button_row.add_widget(manual_btn)
        
        layout.add_widget(button_row)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """Called when the screen is displayed."""
        app = App.get_running_app()
        
        if app.atv_service:
            # Bind to service updates
            app.atv_service.bind(
                discovered_devices=self._update_device_list,
                connection_state=self._on_connection_state_change
            )
            
            # Start discovery if not connected
            if not app.atv_service.is_connected:
                app.atv_service.start_discovery()
    
    def on_leave(self):
        """Called when leaving the screen."""
        app = App.get_running_app()
        
        if app.atv_service:
            app.atv_service.unbind(
                discovered_devices=self._update_device_list,
                connection_state=self._on_connection_state_change
            )
    
    def _update_device_list(self, instance, devices):
        """Update the device list UI."""
        self.device_list.clear_widgets()
        
        if not devices:
            self.status_text = "No Apple TV devices found"
            return
        
        self.status_text = f"Found {len(devices)} device(s)"
        
        for device in devices:
            btn = DeviceButton(device)
            btn.bind(on_press=lambda inst: self._on_device_selected(inst.device))
            self.device_list.add_widget(btn)
    
    def _on_connection_state_change(self, instance, state):
        """Handle connection state changes."""
        app = App.get_running_app()
        
        if state == 'scanning':
            self.status_text = "Searching for Apple TV devices..."
        elif state == 'connecting':
            self.status_text = f"Connecting to {app.atv_service.current_device_name}..."
        elif state == 'pairing':
            self._show_pairing_dialog()
        elif state == 'connected':
            self.status_text = "Connected!"
            # Navigate to remote screen
            Clock.schedule_once(lambda dt: app.switch_to_remote(), 0.5)
        elif state == 'error':
            self.status_text = f"Error: {app.atv_service.error_message}"
    
    def _on_device_selected(self, device):
        """Handle device selection."""
        app = App.get_running_app()
        if app.atv_service:
            app.atv_service.connect(device)
    
    def _on_refresh(self, instance):
        """Handle refresh button press."""
        app = App.get_running_app()
        if app.atv_service:
            self.status_text = "Searching for Apple TV devices..."
            app.atv_service.start_discovery()
    
    def _on_manual_connect(self, instance):
        """Show manual connection dialog."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        content.add_widget(Label(text='Enter Apple TV IP address:'))
        
        ip_input = TextInput(
            hint_text='192.168.1.100',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        content.add_widget(ip_input)
        
        button_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        cancel_btn = Button(text='Cancel')
        connect_btn = Button(text='Connect', background_color=(0.3, 0.5, 0.7, 1))
        
        button_row.add_widget(cancel_btn)
        button_row.add_widget(connect_btn)
        content.add_widget(button_row)
        
        popup = Popup(
            title='Manual Connect',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        
        cancel_btn.bind(on_press=popup.dismiss)
        connect_btn.bind(on_press=lambda inst: self._manual_connect(ip_input.text, popup))
        
        popup.open()
    
    def _manual_connect(self, ip_address, popup):
        """Attempt manual connection."""
        if not ip_address:
            return
        
        popup.dismiss()
        
        # Create a device object for manual connection
        from services.apple_tv_service import DiscoveredDevice
        device = DiscoveredDevice(
            name=f"Apple TV ({ip_address})",
            address=ip_address,
            identifier=ip_address,
            model="Unknown"
        )
        
        app = App.get_running_app()
        if app.atv_service:
            app.atv_service.connect(device)
    
    def _show_pairing_dialog(self):
        """Show PIN entry dialog for pairing."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        content.add_widget(Label(
            text='Enter the PIN shown on your Apple TV:',
            size_hint_y=None,
            height=40
        ))
        
        pin_input = TextInput(
            hint_text='0000',
            multiline=False,
            size_hint_y=None,
            height=50,
            font_size='24sp',
            halign='center',
            input_filter='int'
        )
        # Limit to 4 characters
        def limit_chars(instance, value):
            if len(value) > 4:
                instance.text = value[:4]
        pin_input.bind(text=limit_chars)
        content.add_widget(pin_input)
        
        button_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        cancel_btn = Button(text='Cancel')
        submit_btn = Button(text='Submit', background_color=(0.3, 0.5, 0.7, 1))
        
        button_row.add_widget(cancel_btn)
        button_row.add_widget(submit_btn)
        content.add_widget(button_row)
        
        popup = Popup(
            title='Enter Pairing PIN',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        
        def on_cancel(inst):
            popup.dismiss()
            app = App.get_running_app()
            if app.atv_service:
                app.atv_service.disconnect()
        
        def on_submit(inst):
            pin = pin_input.text
            if len(pin) == 4:
                popup.dismiss()
                app = App.get_running_app()
                if app.atv_service:
                    app.atv_service.submit_pin(pin)
        
        cancel_btn.bind(on_press=on_cancel)
        submit_btn.bind(on_press=on_submit)
        
        popup.open()
