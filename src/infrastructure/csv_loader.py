"""Модуль для загрузки переменных из CSV файлов."""
import csv
from typing import List, Dict, Any
from pathlib import Path


class CSVLoader:
    """Класс для загрузки данных из CSV файлов."""
    
    @staticmethod
    def load_variables(file_path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        Загружает переменные из CSV файла.
        Каждая строка CSV представляет один набор переменных для письма.
        
        Args:
            file_path: Путь к CSV файлу
            encoding: Кодировка файла (по умолчанию utf-8)
            
        Returns:
            Список словарей, где каждый словарь - набор переменных для одного письма
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл пустой или невалидный
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        rows = []
        try:
            with open(path, 'r', encoding=encoding, newline='') as f:
                # Определяем разделитель (пробуем запятую и точку с запятой)
                sample = f.read(1024)
                f.seek(0)
                delimiter = ',' if sample.count(',') > sample.count(';') else ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    # Убираем пробелы из ключей и значений
                    cleaned_row = {k.strip(): v.strip() if v else '' for k, v in row.items()}
                    rows.append(cleaned_row)
        
        except Exception as e:
            raise ValueError(f"Ошибка при чтении CSV файла: {str(e)}")
        
        if not rows:
            raise ValueError("CSV файл пустой или не содержит данных")
        
        return rows
    
    @staticmethod
    def validate_csv_structure(file_path: str, required_columns: List[str] = None) -> bool:
        """
        Проверяет структуру CSV файла.
        
        Args:
            file_path: Путь к CSV файлу
            required_columns: Список обязательных колонок (опционально)
            
        Returns:
            True если структура валидна
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если структура невалидна
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8', newline='') as f:
                sample = f.read(1024)
                f.seek(0)
                delimiter = ',' if sample.count(',') > sample.count(';') else ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                columns = reader.fieldnames
                
                if not columns:
                    raise ValueError("CSV файл не содержит заголовков")
                
                if required_columns:
                    missing = set(required_columns) - set(columns)
                    if missing:
                        raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(missing)}")
        
        except Exception as e:
            raise ValueError(f"Ошибка валидации CSV: {str(e)}")
        
        return True
