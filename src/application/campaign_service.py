"""Service for managing email campaigns."""
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
    """Service for managing email campaigns."""
    
    def __init__(self, event_bus: EventBus, outlook_client: OutlookClient):
        """
        Initializes the campaign service.
        
        Args:
            event_bus: Event bus for publishing events
            outlook_client: Client for working with Outlook
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
        Creates a new campaign.
        
        Args:
            name: Campaign name
            template_name: Template name
            recipients_data: List of dicts with recipient data (variables for each email)
            
        Returns:
            ID of the created campaign
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
                subject="",  # Will be filled during rendering
                body="",  # Will be filled during rendering
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
        """Sets a template for use in campaigns."""
        self._templates[template_name] = template
    
    def start_campaign(self, campaign_id: str, send_delay: float = 2.0) -> bool:
        """
        Starts a campaign (sends emails).
        
        Args:
            campaign_id: Campaign ID
            send_delay: Delay between sends in seconds (to simulate manual sending)
            
        Returns:
            True if the campaign started successfully
        """
        if campaign_id not in self._campaigns:
            error_event = ErrorEvent(
                f"Campaign {campaign_id} not found",
                "campaign_not_found"
            )
            self._event_bus.publish(error_event)
            return False
        
        campaign = self._campaigns[campaign_id]
        
        if campaign.template_name not in self._templates:
            error_event = ErrorEvent(
                f"Template {campaign.template_name} not found",
                "template_not_found"
            )
            self._event_bus.publish(error_event)
            return False
        
        template = self._templates[campaign.template_name]
        campaign.status = CampaignStatus.RUNNING
        campaign.started_at = datetime.now()
        
        event = CampaignStartedEvent(campaign_id)
        self._event_bus.publish(event)
        
        # Send emails
        for email in campaign.emails:
            try:
                # Render template with recipient variables
                rendered = template.render(email.variables)
                email.subject = rendered.subject
                email.body = rendered.body
                # Use recipient from variables if not specified in the template
                if not email.recipient:
                    email.recipient = email.variables.get('email') or email.variables.get('recipient') or ''
                if rendered.recipient:
                    email.recipient = rendered.recipient
                
                # Check that recipient is provided
                if not email.recipient:
                    raise ValueError(f"Recipient not specified for email {email.id}")
                
                # Send the email
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
                    f"Error sending email {email.id}: {str(e)}",
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
        Checks for replies to campaign emails.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Number of new replies
        """
        if campaign_id not in self._campaigns:
            return 0
        
        campaign = self._campaigns[campaign_id]
        new_replies = 0
        
        # Check replies for each sent email
        for email in campaign.emails:
            if email.status != EmailStatus.SENT or email.status == EmailStatus.REPLIED:
                continue
            
            try:
                # Check for replies since the send date
                since_date = email.sent_at if email.sent_at else None
                replies = self._outlook_client.check_replies(
                    conversation_id=email.outlook_conversation_id,
                    since_date=since_date
                )
                
                # Look for a reply from the recipient
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
                    f"Error checking replies for email {email.id}: {str(e)}",
                    "check_replies_error"
                )
                self._event_bus.publish(error_event)
        
        return new_replies
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Returns a campaign by ID."""
        return self._campaigns.get(campaign_id)
    
    def get_all_campaigns(self) -> List[Campaign]:
        """Returns a list of all campaigns."""
        return list(self._campaigns.values())
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """Pauses a campaign."""
        if campaign_id in self._campaigns:
            self._campaigns[campaign_id].status = CampaignStatus.PAUSED
            return True
        return False
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """Resumes a campaign."""
        if campaign_id in self._campaigns:
            if self._campaigns[campaign_id].status == CampaignStatus.PAUSED:
                self._campaigns[campaign_id].status = CampaignStatus.RUNNING
                return True
        return False
