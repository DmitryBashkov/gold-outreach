"""Module for loading variables from CSV files."""
import csv
from typing import List, Dict, Any
from pathlib import Path


class CSVLoader:
    """Class for loading data from CSV files."""
    
    @staticmethod
    def load_variables(file_path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        Loads variables from a CSV file.
        Each CSV row represents one set of variables for an email.
        
        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default utf-8)
            
        Returns:
            List of dicts, where each dict is a set of variables for one email
            
        Raises:
            FileNotFoundError: If the file is not found
            ValueError: If the file is empty or invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        rows = []
        try:
            with open(path, 'r', encoding=encoding, newline='') as f:
                # Detect delimiter (try comma and semicolon)
                sample = f.read(1024)
                f.seek(0)
                delimiter = ',' if sample.count(',') > sample.count(';') else ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    # Strip whitespace from keys and values
                    cleaned_row = {k.strip(): v.strip() if v else '' for k, v in row.items()}
                    rows.append(cleaned_row)
        
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
        
        if not rows:
            raise ValueError("CSV file is empty or contains no data")
        
        return rows
    
    @staticmethod
    def validate_csv_structure(file_path: str, required_columns: List[str] = None) -> bool:
        """
        Validates the structure of a CSV file.
        
        Args:
            file_path: Path to the CSV file
            required_columns: List of required columns (optional)
            
        Returns:
            True if the structure is valid
            
        Raises:
            FileNotFoundError: If the file is not found
            ValueError: If the structure is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8', newline='') as f:
                sample = f.read(1024)
                f.seek(0)
                delimiter = ',' if sample.count(',') > sample.count(';') else ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                columns = reader.fieldnames
                
                if not columns:
                    raise ValueError("CSV file contains no headers")
                
                if required_columns:
                    missing = set(required_columns) - set(columns)
                    if missing:
                        raise ValueError(f"Missing required columns: {', '.join(missing)}")
        
        except Exception as e:
            raise ValueError(f"CSV validation error: {str(e)}")
        
        return True
