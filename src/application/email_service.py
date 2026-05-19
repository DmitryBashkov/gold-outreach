"""Service for working with emails."""
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
    """Service for generating and saving emails."""
    
    def __init__(self, event_bus: EventBus):
        """
        Initializes the service.
        
        Args:
            event_bus: Event bus for publishing events
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
        Loads variables from a YAML file.
        
        Args:
            file_path: Path to the YAML file with variables
            
        Returns:
            True if loading was successful, False otherwise
        """
        try:
            self._variables = self._yaml_loader.load_variables(file_path)
            event = VariablesLoadedEvent(self._variables)
            self._event_bus.publish(event)
            return True
        except Exception as e:
            error_event = ErrorEvent(
                error_message=f"Error loading variables: {str(e)}",
                error_type="load_variables"
            )
            self._event_bus.publish(error_event)
            return False
    
    def load_templates(self, file_path: str, file_type: str = "yaml") -> bool:
        """
        Loads templates from a file (YAML or TOML).
        
        Args:
            file_path: Path to the templates file
            file_type: File type ("yaml" or "toml")
            
        Returns:
            True if loading was successful, False otherwise
        """
        try:
            if file_type.lower() == "toml":
                self._templates = self._toml_loader.load_templates(file_path)
            else:
                self._templates = self._yaml_loader.load_templates(file_path)
            
            # Convert to EmailTemplate objects
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
                error_message=f"Error loading templates: {str(e)}",
                error_type="load_templates"
            )
            self._event_bus.publish(error_event)
            return False
    
    def load_variables_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Loads variables from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of dicts with variables (each row is one set of variables)
        """
        try:
            variables_list = self._csv_loader.load_variables(file_path)
            return variables_list
        except Exception as e:
            error_event = ErrorEvent(
                error_message=f"Error loading variables from CSV: {str(e)}",
                error_type="load_csv"
            )
            self._event_bus.publish(error_event)
            return []
    
    def connect_outlook(self) -> bool:
        """
        Connects to MS Outlook.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            success = self._outlook_client.connect()
            return success
        except Exception as e:
            error_event = ErrorEvent(
                error_message=f"Error connecting to Outlook: {str(e)}",
                error_type="connect_outlook"
            )
            self._event_bus.publish(error_event)
            return False
    
    def generate_and_save_emails(self) -> Dict[str, bool]:
        """
        Generates and saves all emails based on loaded templates and variables.
        
        Returns:
            Dict with results: key is template name, value is True/False
        """
        results = {}
        
        if not self._templates:
            error_event = ErrorEvent(
                error_message="Templates not loaded",
                error_type="generate_emails"
            )
            self._event_bus.publish(error_event)
            return results
        
        if not self._variables:
            error_event = ErrorEvent(
                error_message="Variables not loaded",
                error_type="generate_emails"
            )
            self._event_bus.publish(error_event)
            return results
        
        if not self._outlook_client.is_connected():
            if not self.connect_outlook():
                return results
        
        for template_name, template_data in self._templates.items():
            try:
                # Create template object
                email_template = EmailTemplate(
                    name=template_name,
                    subject=template_data.get('subject', ''),
                    body=template_data.get('body', ''),
                    recipient=template_data.get('recipient')
                )
                
                # Render template with variables
                rendered_template = email_template.render(self._variables)
                
                # Publish email generation event
                generated_event = EmailGeneratedEvent(
                    template_name=template_name,
                    subject=rendered_template.subject,
                    body=rendered_template.body,
                    recipient=rendered_template.recipient
                )
                self._event_bus.publish(generated_event)
                
                # Save to Outlook
                success = self._outlook_client.create_draft(
                    subject=rendered_template.subject,
                    body=rendered_template.body,
                    recipient=rendered_template.recipient
                )
                
                results[template_name] = success
                
                # Publish save event
                saved_event = EmailSavedEvent(
                    template_name=template_name,
                    success=success
                )
                self._event_bus.publish(saved_event)
                
            except Exception as e:
                results[template_name] = False
                error_event = ErrorEvent(
                    error_message=f"Error processing template {template_name}: {str(e)}",
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
        """Returns the loaded variables."""
        return self._variables.copy()
    
    def get_templates(self) -> Dict[str, Dict[str, str]]:
        """Returns the loaded templates."""
        return self._templates.copy()
    
    def get_email_templates(self) -> Dict[str, EmailTemplate]:
        """Returns the loaded templates as EmailTemplate objects."""
        return self._email_templates.copy()
    
    def disconnect_outlook(self):
        """Disconnects from Outlook."""
        self._outlook_client.disconnect()
