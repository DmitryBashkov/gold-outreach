"""Система плагинов для расширения функциональности."""
import importlib
import importlib.util
import inspect
from typing import Dict, List, Type, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod
from src.application.event_bus import EventBus
from src.domain.events import Event


class Plugin(ABC):
    """Базовый класс для всех плагинов."""
    
    def __init__(self, event_bus: EventBus):
        """
        Инициализирует плагин.
        
        Args:
            event_bus: Event bus для подписки на события
        """
        self._event_bus = event_bus
        self._name = self.__class__.__name__
        self._enabled = True
    
    @property
    def name(self) -> str:
        """Возвращает имя плагина."""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Проверяет, включен ли плагин."""
        return self._enabled
    
    def enable(self):
        """Включает плагин."""
        self._enabled = True
        self.on_enable()
    
    def disable(self):
        """Выключает плагин."""
        self._enabled = False
        self.on_disable()
    
    def on_enable(self):
        """Вызывается при включении плагина. Переопределите для кастомизации."""
        pass
    
    def on_disable(self):
        """Вызывается при выключении плагина. Переопределите для кастомизации."""
        pass
    
    @abstractmethod
    def initialize(self):
        """Инициализирует плагин. Должен быть реализован в подклассах."""
        pass
    
    def handle_event(self, event: Event):
        """Обрабатывает событие. Переопределите для обработки событий."""
        pass


class PluginManager:
    """Менеджер для управления плагинами."""
    
    def __init__(self, event_bus: EventBus):
        """
        Инициализирует менеджер плагинов.
        
        Args:
            event_bus: Event bus для передачи плагинам
        """
        self._event_bus = event_bus
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_paths: Dict[str, Path] = {}
    
    def register_plugin(self, plugin: Plugin):
        """
        Регистрирует плагин.
        
        Args:
            plugin: Экземпляр плагина
        """
        self._plugins[plugin.name] = plugin
        plugin.initialize()
        
        # Подписываемся на все события для плагина
        self._event_bus.subscribe("*", plugin.handle_event)
    
    def load_plugin_from_module(self, module_path: str, class_name: str) -> Optional[Plugin]:
        """
        Загружает плагин из модуля Python.
        
        Args:
            module_path: Путь к модулю (например, 'plugins.my_plugin')
            class_name: Имя класса плагина
            
        Returns:
            Экземпляр плагина или None при ошибке
        """
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            
            if not issubclass(plugin_class, Plugin):
                raise ValueError(f"{class_name} не является подклассом Plugin")
            
            plugin = plugin_class(self._event_bus)
            self.register_plugin(plugin)
            return plugin
        
        except Exception as e:
            print(f"Ошибка загрузки плагина {module_path}.{class_name}: {str(e)}")
            return None
    
    def load_plugins_from_directory(self, directory: Path):
        """
        Загружает все плагины из директории.
        
        Args:
            directory: Путь к директории с плагинами
        """
        if not directory.exists():
            return
        
        for file_path in directory.glob("*.py"):
            if file_path.name == "__init__.py":
                continue
            
            module_name = file_path.stem
            try:
                # Пытаемся найти класс Plugin в файле
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Ищем все классы, наследующиеся от Plugin
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, Plugin) and obj != Plugin and 
                            obj.__module__ == module.__name__):
                            plugin = obj(self._event_bus)
                            self.register_plugin(plugin)
                            break
            
            except Exception as e:
                print(f"Ошибка загрузки плагина из {file_path}: {str(e)}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Возвращает плагин по имени."""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List[Plugin]:
        """Возвращает список всех плагинов."""
        return list(self._plugins.values())
    
    def unregister_plugin(self, name: str):
        """Отменяет регистрацию плагина."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.disable()
            self._event_bus.unsubscribe("*", plugin.handle_event)
            del self._plugins[name]
