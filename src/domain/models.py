"""Доменные модели."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class EmailStatus(Enum):
    """Статус письма."""
    DRAFT = "draft"
    SENT = "sent"
    REPLIED = "replied"
    FAILED = "failed"


class CampaignStatus(Enum):
    """Статус кампании."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class EmailTemplate:
    """Модель шаблона письма."""
    name: str
    subject: str
    body: str
    recipient: Optional[str] = None
    
    def render(self, variables: Dict[str, Any]) -> 'EmailTemplate':
        """Подставляет переменные в шаблон."""
        rendered_subject = self._render_text(self.subject, variables)
        rendered_body = self._render_text(self.body, variables)
        rendered_recipient = self._render_text(self.recipient, variables) if self.recipient else None
        
        return EmailTemplate(
            name=self.name,
            subject=rendered_subject,
            body=rendered_body,
            recipient=rendered_recipient
        )
    
    @staticmethod
    def _render_text(text: str, variables: Dict[str, Any]) -> str:
        """Подставляет переменные в текст."""
        if not text:
            return text
        
        result = text
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        return result


@dataclass
class Email:
    """Модель письма в рассылке."""
    id: str
    campaign_id: str
    recipient: str
    subject: str
    body: str
    status: EmailStatus = EmailStatus.DRAFT
    sent_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    outlook_entry_id: Optional[str] = None
    outlook_conversation_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Campaign:
    """Модель кампании рассылки."""
    id: str
    name: str
    template_name: str
    status: CampaignStatus = CampaignStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    emails: List[Email] = field(default_factory=list)
    total_emails: int = 0
    sent_emails: int = 0
    replied_emails: int = 0
    
    @property
    def conversion_rate(self) -> float:
        """Вычисляет конверсию (процент ответов)."""
        if self.sent_emails == 0:
            return 0.0
        return (self.replied_emails / self.sent_emails) * 100
    
    @property
    def completion_rate(self) -> float:
        """Вычисляет процент выполнения."""
        if self.total_emails == 0:
            return 0.0
        return (self.sent_emails / self.total_emails) * 100
