"""Module for working with MS Outlook."""
import sys
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime


class OutlookClient:
    """Client for working with MS Outlook via COM interface."""
    
    def __init__(self):
        """Initializes the Outlook client."""
        self._outlook = None
        self._namespace = None
        self._drafts_folder = None
        self._sent_folder = None
        self._inbox_folder = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """
        Connects to MS Outlook.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            if sys.platform != 'win32':
                raise RuntimeError("MS Outlook is only available on Windows")
            
            import win32com.client
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            self._namespace = self._outlook.GetNamespace("MAPI")
            self._drafts_folder = self._namespace.GetDefaultFolder(16)  # 16 = olFolderDrafts
            self._sent_folder = self._namespace.GetDefaultFolder(5)  # 5 = olFolderSentMail
            self._inbox_folder = self._namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            self._is_connected = True
            return True
        except ImportError:
            raise ImportError(
                "To work with Outlook you must install pywin32: "
                "pip install pywin32"
            )
        except Exception as e:
            self._is_connected = False
            raise RuntimeError(f"Error connecting to Outlook: {str(e)}")
    
    def is_connected(self) -> bool:
        """Checks whether the client is connected to Outlook."""
        return self._is_connected
    
    def create_draft(
        self,
        subject: str,
        body: str,
        recipient: Optional[str] = None,
        html_body: bool = False
    ) -> Optional[str]:
        """
        Creates a draft email in Outlook.
        
        Args:
            subject: Email subject
            body: Email body
            recipient: Recipient (optional)
            html_body: Whether to use HTML format for the email body
            
        Returns:
            EntryID of the created email or None on error
            
        Raises:
            RuntimeError: If the client is not connected to Outlook
        """
        if not self._is_connected:
            raise RuntimeError("Client is not connected to Outlook. Call connect() first.")
        
        try:
            mail_item = self._outlook.CreateItem(0)  # 0 = olMailItem
            
            mail_item.Subject = subject
            
            if html_body:
                mail_item.HTMLBody = body
            else:
                mail_item.Body = body
            
            if recipient:
                mail_item.To = recipient
            
            mail_item.Save()
            entry_id = mail_item.EntryID
            return entry_id
        except Exception as e:
            raise RuntimeError(f"Error creating draft: {str(e)}")
    
    def send_email(
        self,
        subject: str,
        body: str,
        recipient: str,
        delay_seconds: float = 0.0,
        html_body: bool = False
    ) -> Optional[str]:
        """
        Sends an email via Outlook (appears as if sent manually).
        
        Args:
            subject: Email subject
            body: Email body
            recipient: Recipient
            delay_seconds: Delay before sending (to simulate manual sending)
            html_body: Whether to use HTML format
            
        Returns:
            EntryID of the sent email or None on error
        """
        if not self._is_connected:
            raise RuntimeError("Client is not connected to Outlook. Call connect() first.")
        
        try:
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            
            mail_item = self._outlook.CreateItem(0)
            mail_item.Subject = subject
            
            if html_body:
                mail_item.HTMLBody = body
            else:
                mail_item.Body = body
            
            mail_item.To = recipient
            mail_item.Send()
            
            # Get EntryID from the sent items folder
            time.sleep(0.5)  # Small delay for saving
            entry_id = None
            try:
                sent_items = self._sent_folder.Items
                if sent_items.Count > 0:
                    last_item = sent_items.GetLast()
                    if last_item and last_item.Subject == subject:
                        entry_id = last_item.EntryID
            except:
                pass
            
            return entry_id
        except Exception as e:
            raise RuntimeError(f"Error sending email: {str(e)}")
    
    def check_replies(self, conversation_id: Optional[str] = None, 
                     since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Checks for replies to emails.
        
        Args:
            conversation_id: Conversation ID for filtering (optional)
            since_date: Date for filtering (optional)
            
        Returns:
            List of dicts with reply information
        """
        if not self._is_connected:
            raise RuntimeError("Client is not connected to Outlook.")
        
        replies = []
        try:
            items = self._inbox_folder.Items
            items.Sort("[ReceivedTime]", True)  # Sort by received date
            
            for item in items:
                if item.Class == 43:  # 43 = olMail
                    if since_date and item.ReceivedTime < since_date:
                        continue
                    
                    if conversation_id and hasattr(item, 'ConversationID'):
                        if item.ConversationID != conversation_id:
                            continue
                    
                    # Check whether this is a reply
                    if hasattr(item, 'PropertyAccessor'):
                        try:
                            # Get email information
                            reply_info = {
                                'entry_id': item.EntryID,
                                'subject': item.Subject,
                                'sender': item.SenderEmailAddress if hasattr(item, 'SenderEmailAddress') else '',
                                'received_time': item.ReceivedTime,
                                'conversation_id': item.ConversationID if hasattr(item, 'ConversationID') else None,
                                'body': item.Body[:200] if hasattr(item, 'Body') else ''  # First 200 characters
                            }
                            replies.append(reply_info)
                        except:
                            continue
        
        except Exception as e:
            raise RuntimeError(f"Error checking replies: {str(e)}")
        
        return replies
    
    def disconnect(self):
        """Disconnects from Outlook."""
        self._outlook = None
        self._namespace = None
        self._drafts_folder = None
        self._sent_folder = None
        self._inbox_folder = None
        self._is_connected = False
