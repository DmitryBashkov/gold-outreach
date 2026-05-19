"""Main application window."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional
from src.application.event_bus import EventBus
from src.application.email_service import EmailService
from src.application.campaign_service import CampaignService
from src.presentation.campaign_dialog import CampaignDialog
from src.presentation.log_dialog import LogDialog
from src.domain.events import (
    VariablesLoadedEvent,
    TemplatesLoadedEvent,
    EmailGeneratedEvent,
    EmailSavedEvent,
    ErrorEvent,
    CampaignCreatedEvent,
    CampaignStartedEvent,
    EmailSentEvent,
    EmailRepliedEvent
)


class MainWindow:
    """Main application window with tkinter GUI."""
    
    def __init__(self, root: tk.Tk, event_bus: EventBus, email_service: EmailService,
                 campaign_service: Optional[CampaignService] = None):
        """
        Initializes the main window.
        
        Args:
            root: Root tkinter widget
            event_bus: Event bus for subscribing to events
            email_service: Service for working with emails
            campaign_service: Service for working with campaigns (optional)
        """
        self._root = root
        self._event_bus = event_bus
        self._email_service = email_service
        self._campaign_service = campaign_service
        
        self._variables_file_path: Optional[str] = None
        self._templates_file_path: Optional[str] = None
        
        # Initialize dialogs
        self._campaign_dialog = CampaignDialog(root, campaign_service, email_service) if campaign_service else None
        self._log_dialog = LogDialog(root)
        
        self._setup_ui()
        self._subscribe_to_events()
    
    def _setup_ui(self):
        """Sets up the user interface."""
        self._root.title("Outlook Email Generator")
        self._root.geometry("800x600")
        self._root.resizable(True, True)
        
        # Main container
        main_frame = ttk.Frame(self._root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File selection section
        files_frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        files_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        files_frame.columnconfigure(1, weight=1)
        
        # Variables file
        ttk.Label(files_frame, text="Variables file:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self._variables_path_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self._variables_path_var, state='readonly').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(files_frame, text="Browse...", command=self._select_variables_file).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # Templates file
        ttk.Label(files_frame, text="Templates file:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self._templates_path_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self._templates_path_var, state='readonly').grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(files_frame, text="Browse...", command=self._select_templates_file).grid(
            row=1, column=2, padx=5, pady=5
        )
        
        # Information section
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        self._info_text = scrolledtext.ScrolledText(info_frame, height=15, wrap=tk.WORD)
        self._info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self._info_text.config(state=tk.DISABLED)
        
        # Buttons section
        buttons_frame = ttk.Frame(main_frame, padding="10")
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(
            buttons_frame,
            text="Load files",
            command=self._load_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Connect to Outlook",
            command=self._connect_outlook
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Generate emails",
            command=self._generate_emails
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Clear",
            command=self._clear_info
        ).pack(side=tk.LEFT, padx=5)
        
        # Campaign buttons (if available)
        if self._campaign_service:
            ttk.Button(
                buttons_frame,
                text="Create campaign",
                command=self._show_create_campaign
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                buttons_frame,
                text="Manage campaigns",
                command=self._show_campaigns_list
            ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Logs",
            command=self._show_logs
        ).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self._status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self._status_var, relief=tk.SUNKEN)
        status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
    
    def _subscribe_to_events(self):
        """Subscribes to events."""
        self._event_bus.subscribe("variables_loaded", self._on_variables_loaded)
        self._event_bus.subscribe("templates_loaded", self._on_templates_loaded)
        self._event_bus.subscribe("email_generated", self._on_email_generated)
        self._event_bus.subscribe("email_saved", self._on_email_saved)
        self._event_bus.subscribe("error", self._on_error)
        
        # Subscribe to campaign events
        if self._campaign_service:
            self._event_bus.subscribe("campaign_created", self._on_campaign_created)
            self._event_bus.subscribe("campaign_started", self._on_campaign_started)
            self._event_bus.subscribe("email_sent", self._on_email_sent)
            self._event_bus.subscribe("email_replied", self._on_email_replied)
    
    def _select_variables_file(self):
        """Selects the variables file."""
        file_path = filedialog.askopenfilename(
            title="Select variables file",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if file_path:
            self._variables_file_path = file_path
            self._variables_path_var.set(file_path)
    
    def _select_templates_file(self):
        """Selects the templates file."""
        file_path = filedialog.askopenfilename(
            title="Select templates file",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if file_path:
            self._templates_file_path = file_path
            self._templates_path_var.set(file_path)
    
    def _load_files(self):
        """Loads the selected files."""
        if not self._variables_file_path:
            messagebox.showwarning("Warning", "Select a variables file")
            return
        
        if not self._templates_file_path:
            messagebox.showwarning("Warning", "Select a templates file")
            return
        
        self._add_info("Loading files...")
        self._status_var.set("Loading files...")
        
        # Load variables
        if self._email_service.load_variables(self._variables_file_path):
            self._add_info("✓ Variables file loaded successfully")
        else:
            self._add_info("✗ Error loading variables file")
        
        # Load templates
        if self._email_service.load_templates(self._templates_file_path):
            self._add_info("✓ Templates file loaded successfully")
        else:
            self._add_info("✗ Error loading templates file")
        
        self._status_var.set("Files loaded")
    
    def _connect_outlook(self):
        """Connects to Outlook."""
        self._add_info("Connecting to Outlook...")
        self._status_var.set("Connecting to Outlook...")
        
        if self._email_service.connect_outlook():
            self._add_info("✓ Connected to Outlook successfully")
            self._status_var.set("Connected to Outlook")
        else:
            self._add_info("✗ Error connecting to Outlook")
            self._status_var.set("Connection error")
    
    def _generate_emails(self):
        """Generates and saves emails."""
        self._add_info("Starting email generation...")
        self._status_var.set("Generating emails...")
        
        results = self._email_service.generate_and_save_emails()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        self._add_info(f"\nResults: {success_count}/{total_count} emails created successfully")
        self._status_var.set(f"Created {success_count}/{total_count} emails")
        
        if success_count == total_count and total_count > 0:
            messagebox.showinfo("Success", f"All emails ({total_count}) successfully saved to Outlook drafts")
        elif success_count > 0:
            messagebox.showwarning(
                "Partial success",
                f"Created {success_count} of {total_count} emails. Check the log for details."
            )
        elif total_count > 0:
            messagebox.showerror("Error", "Failed to create any emails. Check the log.")
    
    def _clear_info(self):
        """Clears the information panel."""
        self._info_text.config(state=tk.NORMAL)
        self._info_text.delete(1.0, tk.END)
        self._info_text.config(state=tk.DISABLED)
        self._status_var.set("Ready")
    
    def _add_info(self, message: str):
        """Adds a message to the information panel."""
        self._info_text.config(state=tk.NORMAL)
        self._info_text.insert(tk.END, message + "\n")
        self._info_text.see(tk.END)
        self._info_text.config(state=tk.DISABLED)
    
    def _on_variables_loaded(self, event: VariablesLoadedEvent):
        """Handler for the variables loaded event."""
        var_count = len(event.variables)
        self._add_info(f"Variables loaded: {var_count}")
    
    def _on_templates_loaded(self, event: TemplatesLoadedEvent):
        """Handler for the templates loaded event."""
        template_count = len(event.templates)
        self._add_info(f"Templates loaded: {template_count}")
        for template_name in event.templates.keys():
            self._add_info(f"  - {template_name}")
    
    def _on_email_generated(self, event: EmailGeneratedEvent):
        """Handler for the email generated event."""
        self._add_info(f"Email generated: {event.template_name}")
        self._add_info(f"  Subject: {event.subject}")
    
    def _on_email_saved(self, event: EmailSavedEvent):
        """Handler for the email saved event."""
        if event.success:
            self._add_info(f"✓ Email '{event.template_name}' saved to drafts")
        else:
            self._add_info(f"✗ Error saving email '{event.template_name}'")
            if event.error_message:
                self._add_info(f"  Error: {event.error_message}")
    
    def _on_error(self, event: ErrorEvent):
        """Handler for the error event."""
        message = f"✗ ERROR [{event.error_type}]: {event.error_message}"
        self._add_info(message)
        self._log_dialog.add_log(message, "ERROR")
    
    def _show_create_campaign(self):
        """Shows the campaign creation dialog."""
        if self._campaign_dialog:
            self._campaign_dialog.show_create_campaign()
    
    def _show_campaigns_list(self):
        """Shows the campaigns list."""
        if self._campaign_dialog:
            self._campaign_dialog.show_campaigns_list()
    
    def _show_logs(self):
        """Shows the logs dialog."""
        self._log_dialog.show()
    
    def _on_campaign_created(self, event: CampaignCreatedEvent):
        """Handler for the campaign created event."""
        message = f"Campaign created: {event.campaign_name} (ID: {event.campaign_id})"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
    
    def _on_campaign_started(self, event: CampaignStartedEvent):
        """Handler for the campaign started event."""
        message = f"Campaign started: {event.campaign_id}"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
    
    def _on_email_sent(self, event: EmailSentEvent):
        """Handler for the email sent event."""
        message = f"Email sent to: {event.recipient} (Campaign: {event.campaign_id})"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
    
    def _on_email_replied(self, event: EmailRepliedEvent):
        """Handler for the email replied event."""
        message = f"Reply received from: {event.recipient} (Campaign: {event.campaign_id})"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
