"""Сервис для управления кампаниями рассылок."""
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.domain.models import Campaign, Email, EmailStatus, CampaignStatus
from src.domain.events import (
    CampaignCreatedEvent,
    CampaignStartedEvent,
    CampaignCompletedEvent,
    EmailSentEvent,
    EmailRepliedEvent,
    ErrorEvent
)
from src.application.event_bus import EventBus
from src.infrastructure.outlook_client import OutlookClient
from src.domain.models import EmailTemplate


class CampaignService:
    """Сервис для управления кампаниями рассылок."""
    
    def __init__(self, event_bus: EventBus, outlook_client: OutlookClient):
        """
        Инициализирует сервис кампаний.
        
        Args:
            event_bus: Event bus для публикации событий
            outlook_client: Клиент для работы с Outlook
        """
        self._event_bus = event_bus
        self._outlook_client = outlook_client
        self._campaigns: Dict[str, Campaign] = {}
        self._templates: Dict[str, EmailTemplate] = {}
    
    def create_campaign(
        self,
        name: str,
        template_name: str,
        recipients_data: List[Dict[str, Any]]
    ) -> str:
        """
        Создает новую кампанию.
        
        Args:
            name: Имя кампании
            template_name: Имя шаблона
            recipients_data: Список словарей с данными получателей (переменные для каждого письма)
            
        Returns:
            ID созданной кампании
        """
        campaign_id = str(uuid.uuid4())
        
        emails = []
        for recipient_data in recipients_data:
            email_id = str(uuid.uuid4())
            recipient = recipient_data.get('email') or recipient_data.get('recipient') or ''
            
            email = Email(
                id=email_id,
                campaign_id=campaign_id,
                recipient=recipient,
                subject="",  # Будет заполнено при рендеринге
                body="",  # Будет заполнено при рендеринге
                status=EmailStatus.DRAFT,
                variables=recipient_data
            )
            emails.append(email)
        
        campaign = Campaign(
            id=campaign_id,
            name=name,
            template_name=template_name,
            status=CampaignStatus.DRAFT,
            emails=emails,
            total_emails=len(emails)
        )
        
        self._campaigns[campaign_id] = campaign
        
        event = CampaignCreatedEvent(campaign_id, name)
        self._event_bus.publish(event)
        
        return campaign_id
    
    def set_template(self, template_name: str, template: EmailTemplate):
        """Устанавливает шаблон для использования в кампаниях."""
        self._templates[template_name] = template
    
    def start_campaign(self, campaign_id: str, send_delay: float = 2.0) -> bool:
        """
        Запускает кампанию (отправляет письма).
        
        Args:
            campaign_id: ID кампании
            send_delay: Задержка между отправками в секундах (для имитации ручной отправки)
            
        Returns:
            True если запуск успешен
        """
        if campaign_id not in self._campaigns:
            error_event = ErrorEvent(
                f"Кампания {campaign_id} не найдена",
                "campaign_not_found"
            )
            self._event_bus.publish(error_event)
            return False
        
        campaign = self._campaigns[campaign_id]
        
        if campaign.template_name not in self._templates:
            error_event = ErrorEvent(
                f"Шаблон {campaign.template_name} не найден",
                "template_not_found"
            )
            self._event_bus.publish(error_event)
            return False
        
        template = self._templates[campaign.template_name]
        campaign.status = CampaignStatus.RUNNING
        campaign.started_at = datetime.now()
        
        event = CampaignStartedEvent(campaign_id)
        self._event_bus.publish(event)
        
        # Отправляем письма
        for email in campaign.emails:
            try:
                # Рендерим шаблон с переменными получателя
                rendered = template.render(email.variables)
                email.subject = rendered.subject
                email.body = rendered.body
                # Используем recipient из переменных, если не указан в шаблоне
                if not email.recipient:
                    email.recipient = email.variables.get('email') or email.variables.get('recipient') or ''
                if rendered.recipient:
                    email.recipient = rendered.recipient
                
                # Проверяем, что получатель указан
                if not email.recipient:
                    raise ValueError(f"Получатель не указан для письма {email.id}")
                
                # Отправляем письмо
                entry_id = self._outlook_client.send_email(
                    subject=email.subject,
                    body=email.body,
                    recipient=email.recipient,
                    delay_seconds=send_delay
                )
                
                if entry_id:
                    email.outlook_entry_id = entry_id
                    email.status = EmailStatus.SENT
                    email.sent_at = datetime.now()
                    campaign.sent_emails += 1
                    
                    sent_event = EmailSentEvent(email.id, campaign_id, email.recipient)
                    self._event_bus.publish(sent_event)
            
            except Exception as e:
                email.status = EmailStatus.FAILED
                error_event = ErrorEvent(
                    f"Ошибка отправки письма {email.id}: {str(e)}",
                    "send_email_error"
                )
                self._event_bus.publish(error_event)
        
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.now()
        
        completed_event = CampaignCompletedEvent(
            campaign_id,
            campaign.total_emails,
            campaign.sent_emails,
            campaign.replied_emails,
            campaign.conversion_rate
        )
        self._event_bus.publish(completed_event)
        
        return True
    
    def check_campaign_replies(self, campaign_id: str) -> int:
        """
        Проверяет ответы на письма кампании.
        
        Args:
            campaign_id: ID кампании
            
        Returns:
            Количество новых ответов
        """
        if campaign_id not in self._campaigns:
            return 0
        
        campaign = self._campaigns[campaign_id]
        new_replies = 0
        
        # Проверяем ответы для каждого отправленного письма
        for email in campaign.emails:
            if email.status != EmailStatus.SENT or email.status == EmailStatus.REPLIED:
                continue
            
            try:
                # Проверяем ответы с момента отправки
                since_date = email.sent_at if email.sent_at else None
                replies = self._outlook_client.check_replies(
                    conversation_id=email.outlook_conversation_id,
                    since_date=since_date
                )
                
                # Ищем ответ от получателя
                for reply in replies:
                    if reply['sender'] == email.recipient:
                        email.status = EmailStatus.REPLIED
                        email.replied_at = datetime.now()
                        campaign.replied_emails += 1
                        new_replies += 1
                        
                        reply_event = EmailRepliedEvent(email.id, campaign_id, email.recipient)
                        self._event_bus.publish(reply_event)
                        break
            
            except Exception as e:
                error_event = ErrorEvent(
                    f"Ошибка проверки ответов для письма {email.id}: {str(e)}",
                    "check_replies_error"
                )
                self._event_bus.publish(error_event)
        
        return new_replies
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Возвращает кампанию по ID."""
        return self._campaigns.get(campaign_id)
    
    def get_all_campaigns(self) -> List[Campaign]:
        """Возвращает список всех кампаний."""
        return list(self._campaigns.values())
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """Приостанавливает кампанию."""
        if campaign_id in self._campaigns:
            self._campaigns[campaign_id].status = CampaignStatus.PAUSED
            return True
        return False
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """Возобновляет кампанию."""
        if campaign_id in self._campaigns:
            if self._campaigns[campaign_id].status == CampaignStatus.PAUSED:
                self._campaigns[campaign_id].status = CampaignStatus.RUNNING
                return True
        return False
