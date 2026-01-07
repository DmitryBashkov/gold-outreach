"""Модуль для загрузки данных из TOML файлов."""
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Для Python < 3.11
    except ImportError:
        tomllib = None

from typing import Dict, Any
from pathlib import Path


class TOMLLoader:
    """Класс для загрузки данных из TOML файлов."""
    
    @staticmethod
    def load_templates(file_path: str) -> Dict[str, Dict[str, str]]:
        """
        Загружает шаблоны писем из TOML файла.
        
        Args:
            file_path: Путь к TOML файлу с шаблонами
            
        Returns:
            Словарь шаблонов, где ключ - имя шаблона, значение - словарь с subject, body, recipient
            
        Raises:
            ImportError: Если библиотека для TOML не установлена
            FileNotFoundError: Если файл не найден
            ValueError: Если файл содержит невалидный TOML
        """
        if tomllib is None:
            raise ImportError(
                "Для работы с TOML необходимо установить tomli: "
                "pip install tomli (для Python < 3.11)"
            )
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        with open(path, 'rb') as f:
            data = tomllib.load(f)
        
        if not isinstance(data, dict):
            raise ValueError(f"TOML файл должен содержать словарь, получен: {type(data)}")
        
        return data
