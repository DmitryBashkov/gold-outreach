"""Launcher for starting the application from the Outlook plugin."""
import sys
import os
from pathlib import Path

# Add project path to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import tkinter as tk
from src.application.event_bus import EventBus
from src.application.email_service import EmailService
from src.application.campaign_service import CampaignService
from src.infrastructure.outlook_client import OutlookClient
from src.presentation.main_window import MainWindow


def create_campaign():
    """Creates a campaign."""
    run_app(action="create_campaign")


def manage_campaigns():
    """Manages campaigns."""
    run_app(action="manage_campaigns")


def load_templates():
    """Loads templates."""
    run_app(action="load_templates")


def show_logs():
    """Shows logs."""
    run_app(action="show_logs")


def check_replies():
    """Checks replies."""
    run_app(action="check_replies")


def run_app(action: str = None):
    """Starts the application with the specified action."""
    # Create event bus
    event_bus = EventBus()
    
    # Create Outlook client and connect
    outlook_client = OutlookClient()
    try:
        outlook_client.connect()
    except Exception as e:
        print(f"Error connecting to Outlook: {e}")
        return
    
    # Create services
    email_service = EmailService(event_bus)
    campaign_service = CampaignService(event_bus, outlook_client)
    
    # Create GUI
    root = tk.Tk()
    app = MainWindow(root, event_bus, email_service, campaign_service)
    
    # Execute the action if specified
    if action == "create_campaign":
        app._show_create_campaign()
    elif action == "manage_campaigns":
        app._show_campaigns_list()
    elif action == "show_logs":
        app._show_logs()
    elif action == "check_replies":
        # Can add automatic reply checking for all campaigns
        pass
    
    # Start the application
    try:
        root.mainloop()
    finally:
        outlook_client.disconnect()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None
    run_app(action)
