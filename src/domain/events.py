"""События для event-driven архитектуры."""
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class Event:
    """Базовый класс для всех событий."""
    timestamp: datetime
    event_type: str
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class VariablesLoadedEvent(Event):
    """Событие загрузки переменных из YAML."""
    variables: Dict[str, Any]
    
    def __init__(self, variables: Dict[str, Any]):
        super().__init__(timestamp=datetime.now(), event_type="variables_loaded")
        self.variables = variables


@dataclass
class TemplatesLoadedEvent(Event):
    """Событие загрузки шаблонов из YAML."""
    templates: Dict[str, str]
    
    def __init__(self, templates: Dict[str, str]):
        super().__init__(timestamp=datetime.now(), event_type="templates_loaded")
        self.templates = templates


@dataclass
class EmailGeneratedEvent(Event):
    """Событие генерации письма."""
    template_name: str
    subject: str
    body: str
    recipient: Optional[str] = None
    
    def __init__(self, template_name: str, subject: str, body: str, recipient: Optional[str] = None):
        super().__init__(timestamp=datetime.now(), event_type="email_generated")
        self.template_name = template_name
        self.subject = subject
        self.body = body
        self.recipient = recipient


@dataclass
class EmailSavedEvent(Event):
    """Событие сохранения письма в Outlook."""
    template_name: str
    success: bool
    error_message: Optional[str] = None
    
    def __init__(self, template_name: str, success: bool, error_message: Optional[str] = None):
        super().__init__(timestamp=datetime.now(), event_type="email_saved")
        self.template_name = template_name
        self.success = success
        self.error_message = error_message


@dataclass
class ErrorEvent(Event):
    """Событие ошибки."""
    error_message: str
    error_type: str
    
    def __init__(self, error_message: str, error_type: str = "general"):
        super().__init__(timestamp=datetime.now(), event_type="error")
        self.error_message = error_message
        self.error_type = error_type


@dataclass
class CampaignCreatedEvent(Event):
    """Событие создания кампании."""
    campaign_id: str
    campaign_name: str
    
    def __init__(self, campaign_id: str, campaign_name: str):
        super().__init__(timestamp=datetime.now(), event_type="campaign_created")
        self.campaign_id = campaign_id
        self.campaign_name = campaign_name


@dataclass
class CampaignStartedEvent(Event):
    """Событие запуска кампании."""
    campaign_id: str
    
    def __init__(self, campaign_id: str):
        super().__init__(timestamp=datetime.now(), event_type="campaign_started")
        self.campaign_id = campaign_id


@dataclass
class EmailSentEvent(Event):
    """Событие отправки письма."""
    email_id: str
    campaign_id: str
    recipient: str
    
    def __init__(self, email_id: str, campaign_id: str, recipient: str):
        super().__init__(timestamp=datetime.now(), event_type="email_sent")
        self.email_id = email_id
        self.campaign_id = campaign_id
        self.recipient = recipient


@dataclass
class EmailRepliedEvent(Event):
    """Событие ответа на письмо."""
    email_id: str
    campaign_id: str
    recipient: str
    
    def __init__(self, email_id: str, campaign_id: str, recipient: str):
        super().__init__(timestamp=datetime.now(), event_type="email_replied")
        self.email_id = email_id
        self.campaign_id = campaign_id
        self.recipient = recipient


@dataclass
class CampaignCompletedEvent(Event):
    """Событие завершения кампании."""
    campaign_id: str
    total_emails: int
    sent_emails: int
    replied_emails: int
    conversion_rate: float
    
    def __init__(self, campaign_id: str, total_emails: int, sent_emails: int, 
                 replied_emails: int, conversion_rate: float):
        super().__init__(timestamp=datetime.now(), event_type="campaign_completed")
        self.campaign_id = campaign_id
        self.total_emails = total_emails
        self.sent_emails = sent_emails
        self.replied_emails = replied_emails
        self.conversion_rate = conversion_rate
