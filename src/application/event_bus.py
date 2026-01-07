"""Event Bus для event-driven архитектуры."""
from typing import Callable, Dict, List, Type
from src.domain.events import Event


class EventBus:
    """Централизованная шина событий для event-driven архитектуры."""
    
    def __init__(self):
        """Инициализирует event bus."""
        self._handlers: Dict[str, List[Callable[[Event], None]]] = {}
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]):
        """
        Подписывает обработчик на событие определенного типа.
        
        Args:
            event_type: Тип события
            handler: Функция-обработчик события
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]):
        """
        Отписывает обработчик от события.
        
        Args:
            event_type: Тип события
            handler: Функция-обработчик события
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def publish(self, event: Event):
        """
        Публикует событие, вызывая все подписанные обработчики.
        
        Args:
            event: Событие для публикации
        """
        event_type = event.event_type
        
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Логируем ошибку, но не прерываем выполнение других обработчиков
                    print(f"Ошибка в обработчике события {event_type}: {str(e)}")
    
    def clear(self):
        """Очищает все подписки."""
        self._handlers.clear()
