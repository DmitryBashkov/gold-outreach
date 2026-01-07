"""Модуль для загрузки данных из YAML файлов."""
import yaml
from typing import Dict, Any
from pathlib import Path


class YAMLLoader:
    """Класс для загрузки данных из YAML файлов."""
    
    @staticmethod
    def load_variables(file_path: str) -> Dict[str, Any]:
        """
        Загружает переменные из YAML файла.
        
        Args:
            file_path: Путь к YAML файлу с переменными
            
        Returns:
            Словарь с переменными
            
        Raises:
            FileNotFoundError: Если файл не найден
            yaml.YAMLError: Если файл содержит невалидный YAML
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise ValueError(f"YAML файл должен содержать словарь, получен: {type(data)}")
        
        return data
    
    @staticmethod
    def load_templates(file_path: str) -> Dict[str, Dict[str, str]]:
        """
        Загружает шаблоны писем из YAML файла.
        
        Args:
            file_path: Путь к YAML файлу с шаблонами
            
        Returns:
            Словарь шаблонов, где ключ - имя шаблона, значение - словарь с subject, body, recipient
            
        Raises:
            FileNotFoundError: Если файл не найден
            yaml.YAMLError: Если файл содержит невалидный YAML
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise ValueError(f"YAML файл должен содержать словарь, получен: {type(data)}")
        
        return data
