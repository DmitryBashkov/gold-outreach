"""Лаунчер для запуска приложения из Outlook плагина."""
import sys
import os
from pathlib import Path

# Добавляем путь к проекту в sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import tkinter as tk
from src.application.event_bus import EventBus
from src.application.email_service import EmailService
from src.application.campaign_service import CampaignService
from src.infrastructure.outlook_client import OutlookClient
from src.presentation.main_window import MainWindow


def create_campaign():
    """Создает кампанию."""
    run_app(action="create_campaign")


def manage_campaigns():
    """Управляет кампаниями."""
    run_app(action="manage_campaigns")


def load_templates():
    """Загружает шаблоны."""
    run_app(action="load_templates")


def show_logs():
    """Показывает логи."""
    run_app(action="show_logs")


def check_replies():
    """Проверяет ответы."""
    run_app(action="check_replies")


def run_app(action: str = None):
    """Запускает приложение с указанным действием."""
    # Создаем event bus
    event_bus = EventBus()
    
    # Создаем клиент Outlook и подключаемся
    outlook_client = OutlookClient()
    try:
        outlook_client.connect()
    except Exception as e:
        print(f"Ошибка подключения к Outlook: {e}")
        return
    
    # Создаем сервисы
    email_service = EmailService(event_bus)
    campaign_service = CampaignService(event_bus, outlook_client)
    
    # Создаем GUI
    root = tk.Tk()
    app = MainWindow(root, event_bus, email_service, campaign_service)
    
    # Выполняем действие, если указано
    if action == "create_campaign":
        app._show_create_campaign()
    elif action == "manage_campaigns":
        app._show_campaigns_list()
    elif action == "show_logs":
        app._show_logs()
    elif action == "check_replies":
        # Можно добавить автоматическую проверку всех кампаний
        pass
    
    # Запускаем приложение
    try:
        root.mainloop()
    finally:
        outlook_client.disconnect()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None
    run_app(action)
