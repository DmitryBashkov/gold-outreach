"""Модуль для работы с MS Outlook."""
import sys
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime


class OutlookClient:
    """Клиент для работы с MS Outlook через COM интерфейс."""
    
    def __init__(self):
        """Инициализирует клиент Outlook."""
        self._outlook = None
        self._namespace = None
        self._drafts_folder = None
        self._sent_folder = None
        self._inbox_folder = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """
        Подключается к MS Outlook.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            if sys.platform != 'win32':
                raise RuntimeError("MS Outlook доступен только на Windows")
            
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
                "Для работы с Outlook необходимо установить pywin32: "
                "pip install pywin32"
            )
        except Exception as e:
            self._is_connected = False
            raise RuntimeError(f"Ошибка подключения к Outlook: {str(e)}")
    
    def is_connected(self) -> bool:
        """Проверяет, подключен ли клиент к Outlook."""
        return self._is_connected
    
    def create_draft(
        self,
        subject: str,
        body: str,
        recipient: Optional[str] = None,
        html_body: bool = False
    ) -> Optional[str]:
        """
        Создает черновик письма в Outlook.
        
        Args:
            subject: Тема письма
            body: Тело письма
            recipient: Получатель (опционально)
            html_body: Использовать ли HTML формат для тела письма
            
        Returns:
            EntryID созданного письма или None при ошибке
            
        Raises:
            RuntimeError: Если клиент не подключен к Outlook
        """
        if not self._is_connected:
            raise RuntimeError("Клиент не подключен к Outlook. Вызовите connect() сначала.")
        
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
            raise RuntimeError(f"Ошибка при создании черновика: {str(e)}")
    
    def send_email(
        self,
        subject: str,
        body: str,
        recipient: str,
        delay_seconds: float = 0.0,
        html_body: bool = False
    ) -> Optional[str]:
        """
        Отправляет письмо через Outlook (выглядит как отправленное вручную).
        
        Args:
            subject: Тема письма
            body: Тело письма
            recipient: Получатель
            delay_seconds: Задержка перед отправкой (для имитации ручной отправки)
            html_body: Использовать ли HTML формат
            
        Returns:
            EntryID отправленного письма или None при ошибке
        """
        if not self._is_connected:
            raise RuntimeError("Клиент не подключен к Outlook. Вызовите connect() сначала.")
        
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
            
            # Получаем EntryID из папки отправленных
            time.sleep(0.5)  # Небольшая задержка для сохранения
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
            raise RuntimeError(f"Ошибка при отправке письма: {str(e)}")
    
    def check_replies(self, conversation_id: Optional[str] = None, 
                     since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Проверяет ответы на письма.
        
        Args:
            conversation_id: ID беседы для фильтрации (опционально)
            since_date: Дата для фильтрации (опционально)
            
        Returns:
            Список словарей с информацией об ответах
        """
        if not self._is_connected:
            raise RuntimeError("Клиент не подключен к Outlook.")
        
        replies = []
        try:
            items = self._inbox_folder.Items
            items.Sort("[ReceivedTime]", True)  # Сортировка по дате получения
            
            for item in items:
                if item.Class == 43:  # 43 = olMail
                    if since_date and item.ReceivedTime < since_date:
                        continue
                    
                    if conversation_id and hasattr(item, 'ConversationID'):
                        if item.ConversationID != conversation_id:
                            continue
                    
                    # Проверяем, является ли это ответом
                    if hasattr(item, 'PropertyAccessor'):
                        try:
                            # Получаем информацию о письме
                            reply_info = {
                                'entry_id': item.EntryID,
                                'subject': item.Subject,
                                'sender': item.SenderEmailAddress if hasattr(item, 'SenderEmailAddress') else '',
                                'received_time': item.ReceivedTime,
                                'conversation_id': item.ConversationID if hasattr(item, 'ConversationID') else None,
                                'body': item.Body[:200] if hasattr(item, 'Body') else ''  # Первые 200 символов
                            }
                            replies.append(reply_info)
                        except:
                            continue
        
        except Exception as e:
            raise RuntimeError(f"Ошибка при проверке ответов: {str(e)}")
        
        return replies
    
    def disconnect(self):
        """Отключается от Outlook."""
        self._outlook = None
        self._namespace = None
        self._drafts_folder = None
        self._sent_folder = None
        self._inbox_folder = None
        self._is_connected = False
