"""Dialog window for managing campaigns."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.campaign_service import CampaignService
    from src.application.email_service import EmailService
from src.application.campaign_service import CampaignService
from src.application.email_service import EmailService
from src.domain.models import Campaign


class CampaignDialog:
    """Dialog for creating and managing campaigns."""
    
    def __init__(self, parent: tk.Tk, campaign_service: CampaignService, 
                 email_service: EmailService):
        """
        Initializes the campaign dialog.
        
        Args:
            parent: Parent window
            campaign_service: Service for working with campaigns
            email_service: Service for working with emails
        """
        self._parent = parent
        self._campaign_service = campaign_service
        self._email_service = email_service
        self._dialog = None
        self._selected_campaign_id: Optional[str] = None
    
    def show_create_campaign(self):
        """Shows the campaign creation dialog."""
        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Create campaign")
        self._dialog.geometry("600x500")
        self._dialog.transient(self._parent)
        self._dialog.grab_set()
        
        main_frame = ttk.Frame(self._dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campaign name
        ttk.Label(main_frame, text="Campaign name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        campaign_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=campaign_name_var, width=40).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        
        # Template
        ttk.Label(main_frame, text="Template:").grid(row=1, column=0, sticky=tk.W, pady=5)
        template_var = tk.StringVar()
        templates = list(self._email_service.get_templates().keys())
        template_combo = ttk.Combobox(main_frame, textvariable=template_var, 
                                     values=templates, state="readonly", width=37)
        template_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Recipients file (CSV)
        ttk.Label(main_frame, text="Recipients file (CSV):").grid(row=2, column=0, sticky=tk.W, pady=5)
        csv_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=csv_path_var, state='readonly', width=30).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        ttk.Button(main_frame, text="Browse...", 
                  command=lambda: self._select_csv_file(csv_path_var)).grid(
            row=2, column=2, pady=5
        )
        
        # Recipients preview
        ttk.Label(main_frame, text="Recipients (preview):").grid(
            row=3, column=0, columnspan=3, sticky=tk.W, pady=5
        )
        
        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(4, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        preview_tree = ttk.Treeview(preview_frame, height=10, show="headings")
        preview_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_tree.yview)
        preview_tree.configure(yscrollcommand=preview_scroll.set)
        
        preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        def load_preview():
            """Loads the recipients preview."""
            if not csv_path_var.get():
                return
            
            try:
                recipients = self._email_service.load_variables_from_csv(csv_path_var.get())
                
                # Clear the tree
                for item in preview_tree.get_children():
                    preview_tree.delete(item)
                
                # Set up columns
                if recipients:
                    columns = list(recipients[0].keys())
                    preview_tree['columns'] = columns
                    for col in columns:
                        preview_tree.heading(col, text=col)
                        preview_tree.column(col, width=100)
                    
                    # Add data
                    for recipient in recipients[:50]:  # Show first 50
                        values = [str(recipient.get(col, '')) for col in columns]
                        preview_tree.insert('', tk.END, values=values)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load preview: {str(e)}")
        
        ttk.Button(main_frame, text="Load preview", 
                  command=load_preview).grid(row=5, column=0, columnspan=3, pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        def create_campaign():
            """Creates the campaign."""
            if not campaign_name_var.get():
                messagebox.showwarning("Warning", "Enter a campaign name")
                return
            
            if not template_var.get():
                messagebox.showwarning("Warning", "Select a template")
                return
            
            if not csv_path_var.get():
                messagebox.showwarning("Warning", "Select a recipients file")
                return
            
            try:
                recipients = self._email_service.load_variables_from_csv(csv_path_var.get())
                if not recipients:
                    messagebox.showerror("Error", "File contains no recipients")
                    return
                
                campaign_id = self._campaign_service.create_campaign(
                    name=campaign_name_var.get(),
                    template_name=template_var.get(),
                    recipients_data=recipients
                )
                
                messagebox.showinfo("Success", f"Campaign created: {campaign_name_var.get()}\nID: {campaign_id}")
                self._dialog.destroy()
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create campaign: {str(e)}")
        
        ttk.Button(buttons_frame, text="Create", command=create_campaign).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=self._dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _select_csv_file(self, path_var: tk.StringVar):
        """Selects a CSV file."""
        file_path = filedialog.askopenfilename(
            title="Select CSV file with recipients",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            path_var.set(file_path)
    
    def show_campaigns_list(self):
        """Shows the list of campaigns."""
        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Manage campaigns")
        self._dialog.geometry("800x600")
        self._dialog.transient(self._parent)
        
        main_frame = ttk.Frame(self._dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campaigns table
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("ID", "Name", "Status", "Total", "Sent", "Replies", "Conversion")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load campaigns
        campaigns = self._campaign_service.get_all_campaigns()
        for campaign in campaigns:
            tree.insert('', tk.END, values=(
                campaign.id[:8] + "...",
                campaign.name,
                campaign.status.value,
                campaign.total_emails,
                campaign.sent_emails,
                campaign.replied_emails,
                f"{campaign.conversion_rate:.1f}%"
            ), tags=(campaign.id,))
        
        # Control buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        def start_campaign():
            """Starts the selected campaign."""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Select a campaign")
                return
            
            campaign_id = tree.item(selection[0])['tags'][0]
            if messagebox.askyesno("Confirmation", "Start campaign?"):
                if self._campaign_service.start_campaign(campaign_id):
                    messagebox.showinfo("Success", "Campaign started")
                    self._dialog.destroy()
                    self.show_campaigns_list()
                else:
                    messagebox.showerror("Error", "Failed to start campaign")
        
        def check_replies():
            """Checks replies for the selected campaign."""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Select a campaign")
                return
            
            campaign_id = tree.item(selection[0])['tags'][0]
            new_replies = self._campaign_service.check_campaign_replies(campaign_id)
            messagebox.showinfo("Result", f"New replies found: {new_replies}")
            self._dialog.destroy()
            self.show_campaigns_list()
        
        ttk.Button(buttons_frame, text="Start", command=start_campaign).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Check replies", command=check_replies).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Close", command=self._dialog.destroy).pack(side=tk.LEFT, padx=5)
