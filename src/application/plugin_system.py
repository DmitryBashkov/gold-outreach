"""Plugin system for extending functionality."""
import importlib
import importlib.util
import inspect
from typing import Dict, List, Type, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod
from src.application.event_bus import EventBus
from src.domain.events import Event


class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self, event_bus: EventBus):
        """
        Initializes the plugin.
        
        Args:
            event_bus: Event bus for subscribing to events
        """
        self._event_bus = event_bus
        self._name = self.__class__.__name__
        self._enabled = True
    
    @property
    def name(self) -> str:
        """Returns the plugin name."""
        return self._name
    
    @property
    def enabled(self) -> bool:
        """Checks whether the plugin is enabled."""
        return self._enabled
    
    def enable(self):
        """Enables the plugin."""
        self._enabled = True
        self.on_enable()
    
    def disable(self):
        """Disables the plugin."""
        self._enabled = False
        self.on_disable()
    
    def on_enable(self):
        """Called when the plugin is enabled. Override to customize."""
        pass
    
    def on_disable(self):
        """Called when the plugin is disabled. Override to customize."""
        pass
    
    @abstractmethod
    def initialize(self):
        """Initializes the plugin. Must be implemented in subclasses."""
        pass
    
    def handle_event(self, event: Event):
        """Handles an event. Override to process events."""
        pass


class PluginManager:
    """Manager for handling plugins."""
    
    def __init__(self, event_bus: EventBus):
        """
        Initializes the plugin manager.
        
        Args:
            event_bus: Event bus for passing to plugins
        """
        self._event_bus = event_bus
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_paths: Dict[str, Path] = {}
    
    def register_plugin(self, plugin: Plugin):
        """
        Registers a plugin.
        
        Args:
            plugin: Plugin instance
        """
        self._plugins[plugin.name] = plugin
        plugin.initialize()
        
        # Subscribe to all events for the plugin
        self._event_bus.subscribe("*", plugin.handle_event)
    
    def load_plugin_from_module(self, module_path: str, class_name: str) -> Optional[Plugin]:
        """
        Loads a plugin from a Python module.
        
        Args:
            module_path: Path to the module (e.g., 'plugins.my_plugin')
            class_name: Plugin class name
            
        Returns:
            Plugin instance or None on error
        """
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            
            if not issubclass(plugin_class, Plugin):
                raise ValueError(f"{class_name} is not a subclass of Plugin")
            
            plugin = plugin_class(self._event_bus)
            self.register_plugin(plugin)
            return plugin
        
        except Exception as e:
            print(f"Error loading plugin {module_path}.{class_name}: {str(e)}")
            return None
    
    def load_plugins_from_directory(self, directory: Path):
        """
        Loads all plugins from a directory.
        
        Args:
            directory: Path to the directory with plugins
        """
        if not directory.exists():
            return
        
        for file_path in directory.glob("*.py"):
            if file_path.name == "__init__.py":
                continue
            
            module_name = file_path.stem
            try:
                # Try to find a Plugin class in the file
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find all classes inheriting from Plugin
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, Plugin) and obj != Plugin and 
                            obj.__module__ == module.__name__):
                            plugin = obj(self._event_bus)
                            self.register_plugin(plugin)
                            break
            
            except Exception as e:
                print(f"Error loading plugin from {file_path}: {str(e)}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Returns a plugin by name."""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List[Plugin]:
        """Returns a list of all plugins."""
        return list(self._plugins.values())
    
    def unregister_plugin(self, name: str):
        """Unregisters a plugin."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.disable()
            self._event_bus.unsubscribe("*", plugin.handle_event)
            del self._plugins[name]
