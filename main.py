"""Точка входа приложения."""
import tkinter as tk
from pathlib import Path
from src.application.event_bus import EventBus
from src.application.email_service import EmailService
from src.application.campaign_service import CampaignService
from src.application.plugin_system import PluginManager
from src.infrastructure.outlook_client import OutlookClient
from src.presentation.main_window import MainWindow


def main():
    """Главная функция приложения."""
    # Создаем event bus
    event_bus = EventBus()
    
    # Создаем клиент Outlook и подключаемся
    outlook_client = OutlookClient()
    try:
        outlook_client.connect()
    except Exception as e:
        print(f"Предупреждение: не удалось подключиться к Outlook: {e}")
        print("Приложение будет работать в режиме без Outlook")
    
    # Создаем сервисы
    email_service = EmailService(event_bus)
    campaign_service = CampaignService(event_bus, outlook_client) if outlook_client.is_connected() else None
    
    # Загружаем плагины
    plugin_manager = PluginManager(event_bus)
    plugins_dir = Path(__file__).parent / "plugins"
    if plugins_dir.exists():
        plugin_manager.load_plugins_from_directory(plugins_dir)
    
    # Создаем GUI
    root = tk.Tk()
    app = MainWindow(root, event_bus, email_service, campaign_service)
    
    # Запускаем приложение
    try:
        root.mainloop()
    finally:
        # Отключаемся от Outlook при выходе
        if outlook_client.is_connected():
            outlook_client.disconnect()


if __name__ == "__main__":
    main()
