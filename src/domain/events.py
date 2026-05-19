"""Events for event-driven architecture."""
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class Event:
    """Base class for all events."""
    timestamp: datetime
    event_type: str
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class VariablesLoadedEvent(Event):
    """Event fired when variables are loaded from YAML."""
    variables: Dict[str, Any]
    
    def __init__(self, variables: Dict[str, Any]):
        super().__init__(timestamp=datetime.now(), event_type="variables_loaded")
        self.variables = variables


@dataclass
class TemplatesLoadedEvent(Event):
    """Event fired when templates are loaded from YAML."""
    templates: Dict[str, str]
    
    def __init__(self, templates: Dict[str, str]):
        super().__init__(timestamp=datetime.now(), event_type="templates_loaded")
        self.templates = templates


@dataclass
class EmailGeneratedEvent(Event):
    """Event fired when an email is generated."""
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
    """Event fired when an email is saved to Outlook."""
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
    """Error event."""
    error_message: str
    error_type: str
    
    def __init__(self, error_message: str, error_type: str = "general"):
        super().__init__(timestamp=datetime.now(), event_type="error")
        self.error_message = error_message
        self.error_type = error_type


@dataclass
class CampaignCreatedEvent(Event):
    """Event fired when a campaign is created."""
    campaign_id: str
    campaign_name: str
    
    def __init__(self, campaign_id: str, campaign_name: str):
        super().__init__(timestamp=datetime.now(), event_type="campaign_created")
        self.campaign_id = campaign_id
        self.campaign_name = campaign_name


@dataclass
class CampaignStartedEvent(Event):
    """Event fired when a campaign is started."""
    campaign_id: str
    
    def __init__(self, campaign_id: str):
        super().__init__(timestamp=datetime.now(), event_type="campaign_started")
        self.campaign_id = campaign_id


@dataclass
class EmailSentEvent(Event):
    """Event fired when an email is sent."""
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
    """Event fired when a reply is received to an email."""
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
    """Event fired when a campaign is completed."""
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
