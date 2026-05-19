"""Example plugin for the plugin system."""
from src.application.plugin_system import Plugin
from src.domain.events import Event, EmailSentEvent


class ExamplePlugin(Plugin):
    """Example plugin that logs sent emails."""
    
    def initialize(self):
        """Initializes the plugin."""
        print(f"Plugin {self._name} initialized")
    
    def handle_event(self, event: Event):
        """Handles events."""
        if not self._enabled:
            return
        
        # Only handle email sent events
        if isinstance(event, EmailSentEvent):
            print(f"[ExamplePlugin] Email sent to: {event.recipient}")
    
    def on_enable(self):
        """Called when the plugin is enabled."""
        print(f"Plugin {self._name} enabled")
    
    def on_disable(self):
        """Called when the plugin is disabled."""
        print(f"Plugin {self._name} disabled")
