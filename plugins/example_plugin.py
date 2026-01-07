"""Пример плагина для системы."""
from src.application.plugin_system import Plugin
from src.domain.events import Event, EmailSentEvent


class ExamplePlugin(Plugin):
    """Пример плагина, который логирует отправленные письма."""
    
    def initialize(self):
        """Инициализирует плагин."""
        print(f"Плагин {self._name} инициализирован")
    
    def handle_event(self, event: Event):
        """Обрабатывает события."""
        if not self._enabled:
            return
        
        # Обрабатываем только события отправки писем
        if isinstance(event, EmailSentEvent):
            print(f"[ExamplePlugin] Письмо отправлено: {event.recipient}")
    
    def on_enable(self):
        """Вызывается при включении плагина."""
        print(f"Плагин {self._name} включен")
    
    def on_disable(self):
        """Вызывается при выключении плагина."""
        print(f"Плагин {self._name} выключен")
