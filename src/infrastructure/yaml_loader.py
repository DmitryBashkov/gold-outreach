"""Module for loading data from YAML files."""
import yaml
from typing import Dict, Any
from pathlib import Path


class YAMLLoader:
    """Class for loading data from YAML files."""
    
    @staticmethod
    def load_variables(file_path: str) -> Dict[str, Any]:
        """
        Loads variables from a YAML file.
        
        Args:
            file_path: Path to the YAML file with variables
            
        Returns:
            Dictionary with variables
            
        Raises:
            FileNotFoundError: If the file is not found
            yaml.YAMLError: If the file contains invalid YAML
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise ValueError(f"YAML file must contain a dictionary, got: {type(data)}")
        
        return data
    
    @staticmethod
    def load_templates(file_path: str) -> Dict[str, Dict[str, str]]:
        """
        Loads email templates from a YAML file.
        
        Args:
            file_path: Path to the YAML file with templates
            
        Returns:
            Dictionary of templates, where key is the template name and value is a dict with subject, body, recipient
            
        Raises:
            FileNotFoundError: If the file is not found
            yaml.YAMLError: If the file contains invalid YAML
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise ValueError(f"YAML file must contain a dictionary, got: {type(data)}")
        
        return data
