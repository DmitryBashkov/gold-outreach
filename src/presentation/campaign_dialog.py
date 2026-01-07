"""Диалоговое окно для управления кампаниями."""
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
    """Диалог для создания и управления кампаниями."""
    
    def __init__(self, parent: tk.Tk, campaign_service: CampaignService, 
                 email_service: EmailService):
        """
        Инициализирует диалог кампаний.
        
        Args:
            parent: Родительское окно
            campaign_service: Сервис для работы с кампаниями
            email_service: Сервис для работы с письмами
        """
        self._parent = parent
        self._campaign_service = campaign_service
        self._email_service = email_service
        self._dialog = None
        self._selected_campaign_id: Optional[str] = None
    
    def show_create_campaign(self):
        """Показывает диалог создания кампании."""
        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Создать кампанию")
        self._dialog.geometry("600x500")
        self._dialog.transient(self._parent)
        self._dialog.grab_set()
        
        main_frame = ttk.Frame(self._dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название кампании
        ttk.Label(main_frame, text="Название кампании:").grid(row=0, column=0, sticky=tk.W, pady=5)
        campaign_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=campaign_name_var, width=40).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        
        # Шаблон
        ttk.Label(main_frame, text="Шаблон:").grid(row=1, column=0, sticky=tk.W, pady=5)
        template_var = tk.StringVar()
        templates = list(self._email_service.get_templates().keys())
        template_combo = ttk.Combobox(main_frame, textvariable=template_var, 
                                     values=templates, state="readonly", width=37)
        template_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Файл с получателями (CSV)
        ttk.Label(main_frame, text="Файл получателей (CSV):").grid(row=2, column=0, sticky=tk.W, pady=5)
        csv_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=csv_path_var, state='readonly', width=30).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )
        ttk.Button(main_frame, text="Выбрать...", 
                  command=lambda: self._select_csv_file(csv_path_var)).grid(
            row=2, column=2, pady=5
        )
        
        # Предпросмотр получателей
        ttk.Label(main_frame, text="Получатели (предпросмотр):").grid(
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
            """Загружает предпросмотр получателей."""
            if not csv_path_var.get():
                return
            
            try:
                recipients = self._email_service.load_variables_from_csv(csv_path_var.get())
                
                # Очищаем дерево
                for item in preview_tree.get_children():
                    preview_tree.delete(item)
                
                # Настраиваем колонки
                if recipients:
                    columns = list(recipients[0].keys())
                    preview_tree['columns'] = columns
                    for col in columns:
                        preview_tree.heading(col, text=col)
                        preview_tree.column(col, width=100)
                    
                    # Добавляем данные
                    for recipient in recipients[:50]:  # Показываем первые 50
                        values = [str(recipient.get(col, '')) for col in columns]
                        preview_tree.insert('', tk.END, values=values)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить предпросмотр: {str(e)}")
        
        ttk.Button(main_frame, text="Загрузить предпросмотр", 
                  command=load_preview).grid(row=5, column=0, columnspan=3, pady=5)
        
        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        def create_campaign():
            """Создает кампанию."""
            if not campaign_name_var.get():
                messagebox.showwarning("Предупреждение", "Введите название кампании")
                return
            
            if not template_var.get():
                messagebox.showwarning("Предупреждение", "Выберите шаблон")
                return
            
            if not csv_path_var.get():
                messagebox.showwarning("Предупреждение", "Выберите файл с получателями")
                return
            
            try:
                recipients = self._email_service.load_variables_from_csv(csv_path_var.get())
                if not recipients:
                    messagebox.showerror("Ошибка", "Файл не содержит получателей")
                    return
                
                campaign_id = self._campaign_service.create_campaign(
                    name=campaign_name_var.get(),
                    template_name=template_var.get(),
                    recipients_data=recipients
                )
                
                messagebox.showinfo("Успех", f"Кампания создана: {campaign_name_var.get()}\nID: {campaign_id}")
                self._dialog.destroy()
            
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать кампанию: {str(e)}")
        
        ttk.Button(buttons_frame, text="Создать", command=create_campaign).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Отмена", command=self._dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _select_csv_file(self, path_var: tk.StringVar):
        """Выбирает CSV файл."""
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл с получателями",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
        )
        if file_path:
            path_var.set(file_path)
    
    def show_campaigns_list(self):
        """Показывает список кампаний."""
        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Управление кампаниями")
        self._dialog.geometry("800x600")
        self._dialog.transient(self._parent)
        
        main_frame = ttk.Frame(self._dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Таблица кампаний
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("ID", "Название", "Статус", "Всего", "Отправлено", "Ответов", "Конверсия")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Загружаем кампании
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
        
        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        def start_campaign():
            """Запускает выбранную кампанию."""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите кампанию")
                return
            
            campaign_id = tree.item(selection[0])['tags'][0]
            if messagebox.askyesno("Подтверждение", "Запустить кампанию?"):
                if self._campaign_service.start_campaign(campaign_id):
                    messagebox.showinfo("Успех", "Кампания запущена")
                    self._dialog.destroy()
                    self.show_campaigns_list()
                else:
                    messagebox.showerror("Ошибка", "Не удалось запустить кампанию")
        
        def check_replies():
            """Проверяет ответы для выбранной кампании."""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите кампанию")
                return
            
            campaign_id = tree.item(selection[0])['tags'][0]
            new_replies = self._campaign_service.check_campaign_replies(campaign_id)
            messagebox.showinfo("Результат", f"Найдено новых ответов: {new_replies}")
            self._dialog.destroy()
            self.show_campaigns_list()
        
        ttk.Button(buttons_frame, text="Запустить", command=start_campaign).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Проверить ответы", command=check_replies).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Закрыть", command=self._dialog.destroy).pack(side=tk.LEFT, padx=5)
