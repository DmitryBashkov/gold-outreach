"""Application entry point."""
import tkinter as tk
from pathlib import Path
from src.application.event_bus import EventBus
from src.application.email_service import EmailService
from src.application.campaign_service import CampaignService
from src.application.plugin_system import PluginManager
from src.infrastructure.outlook_client import OutlookClient
from src.presentation.main_window import MainWindow


def main():
    """Main application function."""
    # Create event bus
    event_bus = EventBus()
    
    # Create Outlook client and connect
    outlook_client = OutlookClient()
    try:
        outlook_client.connect()
    except Exception as e:
        print(f"Warning: failed to connect to Outlook: {e}")
        print("The application will run without Outlook")
    
    # Create services
    email_service = EmailService(event_bus)
    campaign_service = CampaignService(event_bus, outlook_client) if outlook_client.is_connected() else None
    
    # Load plugins
    plugin_manager = PluginManager(event_bus)
    plugins_dir = Path(__file__).parent / "plugins"
    if plugins_dir.exists():
        plugin_manager.load_plugins_from_directory(plugins_dir)
    
    # Create GUI
    root = tk.Tk()
    app = MainWindow(root, event_bus, email_service, campaign_service)
    
    # Start the application
    try:
        root.mainloop()
    finally:
        # Disconnect from Outlook on exit
        if outlook_client.is_connected():
            outlook_client.disconnect()


if __name__ == "__main__":
    main()
