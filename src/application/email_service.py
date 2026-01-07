"""Сервис для работы с письмами."""
from typing import Dict, Any, List, Optional
from src.domain.models import EmailTemplate
from src.domain.events import (
    VariablesLoadedEvent,
    TemplatesLoadedEvent,
    EmailGeneratedEvent,
    EmailSavedEvent,
    ErrorEvent
)
from src.application.event_bus import EventBus
from src.infrastructure.yaml_loader import YAMLLoader
from src.infrastructure.csv_loader import CSVLoader
from src.infrastructure.toml_loader import TOMLLoader
from src.infrastructure.outlook_client import OutlookClient
from src.domain.models import EmailTemplate


class EmailService:
    """Сервис для генерации и сохранения писем."""
    
    def __init__(self, event_bus: EventBus):
        """
        Инициализирует сервис.
        
        Args:
            event_bus: Event bus для публикации событий
        """
        self._event_bus = event_bus
        self._yaml_loader = YAMLLoader()
        self._csv_loader = CSVLoader()
        self._toml_loader = TOMLLoader()
        self._outlook_client = OutlookClient()
        self._variables: Dict[str, Any] = {}
        self._templates: Dict[str, Dict[str, str]] = {}
        self._email_templates: Dict[str, EmailTemplate] = {}
    
    def load_variables(self, file_path: str) -> bool:
        """
        Загружает переменные из YAML файла.
        
        Args:
            file_path: Путь к YAML файлу с переменными
            
        Returns:
            True если загрузка успешна, False в противном случае
        """
        try:
            self._variables = self._yaml_loader.load_variables(file_path)
            event = VariablesLoadedEvent(self._variables)
            self._event_bus.publish(event)
            return True
        except Exception as e:
            error_event = ErrorEvent(
                error_message=f"Ошибка загрузки переменных: {str(e)}",
                error_type="load_variables"
            )
            self._event_bus.publish(error_event)
            return False
    
    def load_templates(self, file_path: str, file_type: str = "yaml") -> bool:
        """
        Загружает шаблоны из файла (YAML или TOML).
        
        Args:
            file_path: Путь к файлу с шаблонами
            file_type: Тип файла ("yaml" или "toml")
            
        Returns:
            True если загрузка успешна, False в противном случае
        """
        try:
            if file_type.lower() == "toml":
                self._templates = self._toml_loader.load_templates(file_path)
            else:
                self._templates = self._yaml_loader.load_templates(file_path)
            
            # Конвертируем в EmailTemplate объекты
            self._email_templates = {}
            for name, data in self._templates.items():
                self._email_templates[name] = EmailTemplate(
                    name=name,
                    subject=data.get('subject', ''),
                    body=data.get('body', ''),
                    recipient=data.get('recipient')
                )
            
            event = TemplatesLoadedEvent(self._templates)
            self._event_bus.publish(event)
            return True
        except Exception as e:
            error_event = ErrorEvent(
                error_message=f"Ошибка загрузки шаблонов: {str(e)}",
                error_type="load_templates"
            )
            self._event_bus.publish(error_event)
            return False
    
    def load_variables_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Загружает переменные из CSV файла.
        
        Args:
            file_path: Путь к CSV файлу
            
        Returns:
            Список словарей с переменными (каждая строка - один набор переменных)
        """
        try:
            variables_list = self._csv_loader.load_variables(file_path)
            return variables_list
        except Exception as e:
            error_event = ErrorEvent(
                error_message=f"Ошибка загрузки переменных из CSV: {str(e)}",
                error_type="load_csv"
            )
            self._event_bus.publish(error_event)
            return []
    
    def connect_outlook(self) -> bool:
        """
        Подключается к MS Outlook.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            success = self._outlook_client.connect()
            return success
        except Exception as e:
            error_event = ErrorEvent(
                error_message=f"Ошибка подключения к Outlook: {str(e)}",
                error_type="connect_outlook"
            )
            self._event_bus.publish(error_event)
            return False
    
    def generate_and_save_emails(self) -> Dict[str, bool]:
        """
        Генерирует и сохраняет все письма на основе загруженных шаблонов и переменных.
        
        Returns:
            Словарь с результатами: ключ - имя шаблона, значение - True/False
        """
        results = {}
        
        if not self._templates:
            error_event = ErrorEvent(
                error_message="Шаблоны не загружены",
                error_type="generate_emails"
            )
            self._event_bus.publish(error_event)
            return results
        
        if not self._variables:
            error_event = ErrorEvent(
                error_message="Переменные не загружены",
                error_type="generate_emails"
            )
            self._event_bus.publish(error_event)
            return results
        
        if not self._outlook_client.is_connected():
            if not self.connect_outlook():
                return results
        
        for template_name, template_data in self._templates.items():
            try:
                # Создаем объект шаблона
                email_template = EmailTemplate(
                    name=template_name,
                    subject=template_data.get('subject', ''),
                    body=template_data.get('body', ''),
                    recipient=template_data.get('recipient')
                )
                
                # Рендерим шаблон с переменными
                rendered_template = email_template.render(self._variables)
                
                # Публикуем событие генерации письма
                generated_event = EmailGeneratedEvent(
                    template_name=template_name,
                    subject=rendered_template.subject,
                    body=rendered_template.body,
                    recipient=rendered_template.recipient
                )
                self._event_bus.publish(generated_event)
                
                # Сохраняем в Outlook
                success = self._outlook_client.create_draft(
                    subject=rendered_template.subject,
                    body=rendered_template.body,
                    recipient=rendered_template.recipient
                )
                
                results[template_name] = success
                
                # Публикуем событие сохранения
                saved_event = EmailSavedEvent(
                    template_name=template_name,
                    success=success
                )
                self._event_bus.publish(saved_event)
                
            except Exception as e:
                results[template_name] = False
                error_event = ErrorEvent(
                    error_message=f"Ошибка при обработке шаблона {template_name}: {str(e)}",
                    error_type="generate_email"
                )
                self._event_bus.publish(error_event)
                
                saved_event = EmailSavedEvent(
                    template_name=template_name,
                    success=False,
                    error_message=str(e)
                )
                self._event_bus.publish(saved_event)
        
        return results
    
    def get_variables(self) -> Dict[str, Any]:
        """Возвращает загруженные переменные."""
        return self._variables.copy()
    
    def get_templates(self) -> Dict[str, Dict[str, str]]:
        """Возвращает загруженные шаблоны."""
        return self._templates.copy()
    
    def get_email_templates(self) -> Dict[str, EmailTemplate]:
        """Возвращает загруженные шаблоны как EmailTemplate объекты."""
        return self._email_templates.copy()
    
    def disconnect_outlook(self):
        """Отключается от Outlook."""
        self._outlook_client.disconnect()
