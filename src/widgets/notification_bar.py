"""
Notification Bar Widget

Footer bar that displays the latest notification/log message.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, NumericProperty
from kivy.graphics import Color, Rectangle
from kivy.app import App
from kivy.clock import Clock


class NotificationBar(BoxLayout):
    """
    Footer notification bar.

    Features:
    - Shows latest log message with color coding
    - Badge showing unread count
    - Click to open log viewer popup
    """

    message = StringProperty("")
    level = StringProperty("info")
    unread_count = NumericProperty(0)

    def __init__(self, **kwargs):
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 35)
        kwargs.setdefault('padding', [10, 2])
        kwargs.setdefault('spacing', 5)
        super().__init__(**kwargs)

        # Background
        with self.canvas.before:
            Color(0.1, 0.1, 0.12, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Message label
        self.message_label = Label(
            text="",
            font_size='12sp',
            halign='left',
            valign='middle',
            text_size=(None, None),
            shorten=True,
            shorten_from='right'
        )
        self.message_label.bind(size=self._update_label_text_size)
        self.add_widget(self.message_label)

        # Logs button with badge
        self.logs_btn = Button(
            text='Logs',
            size_hint=(None, 1),
            width=60,
            font_size='11sp',
            background_color=(0.2, 0.2, 0.25, 1),
            background_normal=''
        )
        self.logs_btn.bind(on_press=self._show_logs)
        self.add_widget(self.logs_btn)

        # Bind to log service updates
        Clock.schedule_once(self._bind_log_service, 0.5)

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _update_label_text_size(self, instance, size):
        instance.text_size = (size[0], size[1])

    def _bind_log_service(self, dt):
        """Bind to the log service for updates."""
        app = App.get_running_app()
        if app and hasattr(app, 'log_service') and app.log_service:
            app.log_service.bind(
                current_message=self._on_message_changed,
                current_level=self._on_level_changed,
                unread_count=self._on_unread_changed
            )

    def _on_message_changed(self, instance, value):
        """Handle message change."""
        self.message = value
        self.message_label.text = value

    def _on_level_changed(self, instance, value):
        """Handle level change - update color."""
        self.level = value
        from ..services.log_service import LogService
        color = LogService.get_level_color(value)
        self.message_label.color = color

    def _on_unread_changed(self, instance, value):
        """Handle unread count change."""
        self.unread_count = value
        if value > 0:
            self.logs_btn.text = f'Logs ({value})'
            self.logs_btn.background_color = (0.4, 0.25, 0.25, 1)
        else:
            self.logs_btn.text = 'Logs'
            self.logs_btn.background_color = (0.2, 0.2, 0.25, 1)

    def _show_logs(self, instance):
        """Show the logs popup."""
        app = App.get_running_app()
        if not app or not hasattr(app, 'log_service'):
            return

        # Mark as read
        app.log_service.mark_read()

        # Create log content
        logs = app.log_service.get_recent(50)

        content = BoxLayout(orientation='vertical', spacing=5)

        # Scroll view for logs
        scroll = ScrollView(size_hint=(1, 1))
        log_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=2,
            padding=5
        )
        log_list.bind(minimum_height=log_list.setter('height'))

        if not logs:
            log_list.add_widget(Label(
                text='No logs yet',
                size_hint_y=None,
                height=30,
                color=(0.5, 0.5, 0.5, 1)
            ))
        else:
            from ..services.log_service import LogService
            for entry in reversed(logs):
                color = LogService.get_level_color(entry.level.value)
                label = Label(
                    text=str(entry),
                    size_hint_y=None,
                    height=25,
                    font_size='11sp',
                    halign='left',
                    valign='middle',
                    color=color
                )
                label.bind(size=lambda inst, size: setattr(inst, 'text_size', (size[0] - 10, None)))
                log_list.add_widget(label)

        scroll.add_widget(log_list)
        content.add_widget(scroll)

        # Clear button
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)

        clear_btn = Button(
            text='Clear Logs',
            background_color=(0.4, 0.25, 0.25, 1),
            background_normal=''
        )

        close_btn = Button(
            text='Close',
            background_color=(0.25, 0.25, 0.3, 1),
            background_normal=''
        )

        btn_layout.add_widget(clear_btn)
        btn_layout.add_widget(close_btn)
        content.add_widget(btn_layout)

        popup = Popup(
            title='Debug Logs',
            content=content,
            size_hint=(0.9, 0.7),
            background_color=(0.15, 0.15, 0.18, 1)
        )

        clear_btn.bind(on_press=lambda x: self._clear_and_refresh(popup, app))
        close_btn.bind(on_press=popup.dismiss)

        popup.open()

    def _clear_and_refresh(self, popup, app):
        """Clear logs and refresh the popup."""
        app.log_service.clear_logs()
        popup.dismiss()
        self._show_logs(None)
