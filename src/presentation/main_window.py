"""Главное окно приложения."""
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
    """Главное окно приложения с GUI на tkinter."""
    
    def __init__(self, root: tk.Tk, event_bus: EventBus, email_service: EmailService,
                 campaign_service: Optional[CampaignService] = None):
        """
        Инициализирует главное окно.
        
        Args:
            root: Корневой виджет tkinter
            event_bus: Event bus для подписки на события
            email_service: Сервис для работы с письмами
            campaign_service: Сервис для работы с кампаниями (опционально)
        """
        self._root = root
        self._event_bus = event_bus
        self._email_service = email_service
        self._campaign_service = campaign_service
        
        self._variables_file_path: Optional[str] = None
        self._templates_file_path: Optional[str] = None
        
        # Инициализируем диалоги
        self._campaign_dialog = CampaignDialog(root, campaign_service, email_service) if campaign_service else None
        self._log_dialog = LogDialog(root)
        
        self._setup_ui()
        self._subscribe_to_events()
    
    def _setup_ui(self):
        """Настраивает интерфейс пользователя."""
        self._root.title("Генератор писем Outlook")
        self._root.geometry("800x600")
        self._root.resizable(True, True)
        
        # Главный контейнер
        main_frame = ttk.Frame(self._root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Секция выбора файлов
        files_frame = ttk.LabelFrame(main_frame, text="Файлы", padding="10")
        files_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        files_frame.columnconfigure(1, weight=1)
        
        # Файл с переменными
        ttk.Label(files_frame, text="Файл переменных:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self._variables_path_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self._variables_path_var, state='readonly').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(files_frame, text="Выбрать...", command=self._select_variables_file).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # Файл с шаблонами
        ttk.Label(files_frame, text="Файл шаблонов:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self._templates_path_var = tk.StringVar()
        ttk.Entry(files_frame, textvariable=self._templates_path_var, state='readonly').grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(files_frame, text="Выбрать...", command=self._select_templates_file).grid(
            row=1, column=2, padx=5, pady=5
        )
        
        # Секция информации
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        self._info_text = scrolledtext.ScrolledText(info_frame, height=15, wrap=tk.WORD)
        self._info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self._info_text.config(state=tk.DISABLED)
        
        # Секция кнопок
        buttons_frame = ttk.Frame(main_frame, padding="10")
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(
            buttons_frame,
            text="Загрузить файлы",
            command=self._load_files
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Подключиться к Outlook",
            command=self._connect_outlook
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Создать письма",
            command=self._generate_emails
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Очистить",
            command=self._clear_info
        ).pack(side=tk.LEFT, padx=5)
        
        # Кнопки для кампаний (если доступны)
        if self._campaign_service:
            ttk.Button(
                buttons_frame,
                text="Создать кампанию",
                command=self._show_create_campaign
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                buttons_frame,
                text="Управление кампаниями",
                command=self._show_campaigns_list
            ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Логи",
            command=self._show_logs
        ).pack(side=tk.LEFT, padx=5)
        
        # Статусная строка
        self._status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(main_frame, textvariable=self._status_var, relief=tk.SUNKEN)
        status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
    
    def _subscribe_to_events(self):
        """Подписывается на события."""
        self._event_bus.subscribe("variables_loaded", self._on_variables_loaded)
        self._event_bus.subscribe("templates_loaded", self._on_templates_loaded)
        self._event_bus.subscribe("email_generated", self._on_email_generated)
        self._event_bus.subscribe("email_saved", self._on_email_saved)
        self._event_bus.subscribe("error", self._on_error)
        
        # Подписки на события кампаний
        if self._campaign_service:
            self._event_bus.subscribe("campaign_created", self._on_campaign_created)
            self._event_bus.subscribe("campaign_started", self._on_campaign_started)
            self._event_bus.subscribe("email_sent", self._on_email_sent)
            self._event_bus.subscribe("email_replied", self._on_email_replied)
    
    def _select_variables_file(self):
        """Выбирает файл с переменными."""
        file_path = filedialog.askopenfilename(
            title="Выберите файл с переменными",
            filetypes=[("YAML файлы", "*.yaml *.yml"), ("Все файлы", "*.*")]
        )
        if file_path:
            self._variables_file_path = file_path
            self._variables_path_var.set(file_path)
    
    def _select_templates_file(self):
        """Выбирает файл с шаблонами."""
        file_path = filedialog.askopenfilename(
            title="Выберите файл с шаблонами",
            filetypes=[("YAML файлы", "*.yaml *.yml"), ("Все файлы", "*.*")]
        )
        if file_path:
            self._templates_file_path = file_path
            self._templates_path_var.set(file_path)
    
    def _load_files(self):
        """Загружает выбранные файлы."""
        if not self._variables_file_path:
            messagebox.showwarning("Предупреждение", "Выберите файл с переменными")
            return
        
        if not self._templates_file_path:
            messagebox.showwarning("Предупреждение", "Выберите файл с шаблонами")
            return
        
        self._add_info("Загрузка файлов...")
        self._status_var.set("Загрузка файлов...")
        
        # Загружаем переменные
        if self._email_service.load_variables(self._variables_file_path):
            self._add_info("✓ Файл переменных загружен успешно")
        else:
            self._add_info("✗ Ошибка загрузки файла переменных")
        
        # Загружаем шаблоны
        if self._email_service.load_templates(self._templates_file_path):
            self._add_info("✓ Файл шаблонов загружен успешно")
        else:
            self._add_info("✗ Ошибка загрузки файла шаблонов")
        
        self._status_var.set("Файлы загружены")
    
    def _connect_outlook(self):
        """Подключается к Outlook."""
        self._add_info("Подключение к Outlook...")
        self._status_var.set("Подключение к Outlook...")
        
        if self._email_service.connect_outlook():
            self._add_info("✓ Подключение к Outlook успешно")
            self._status_var.set("Подключено к Outlook")
        else:
            self._add_info("✗ Ошибка подключения к Outlook")
            self._status_var.set("Ошибка подключения")
    
    def _generate_emails(self):
        """Генерирует и сохраняет письма."""
        self._add_info("Начало генерации писем...")
        self._status_var.set("Генерация писем...")
        
        results = self._email_service.generate_and_save_emails()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        self._add_info(f"\nРезультаты: {success_count}/{total_count} писем создано успешно")
        self._status_var.set(f"Создано {success_count}/{total_count} писем")
        
        if success_count == total_count and total_count > 0:
            messagebox.showinfo("Успех", f"Все письма ({total_count}) успешно созданы в черновиках Outlook")
        elif success_count > 0:
            messagebox.showwarning(
                "Частичный успех",
                f"Создано {success_count} из {total_count} писем. Проверьте лог для деталей."
            )
        elif total_count > 0:
            messagebox.showerror("Ошибка", "Не удалось создать ни одного письма. Проверьте лог.")
    
    def _clear_info(self):
        """Очищает информационное поле."""
        self._info_text.config(state=tk.NORMAL)
        self._info_text.delete(1.0, tk.END)
        self._info_text.config(state=tk.DISABLED)
        self._status_var.set("Готов к работе")
    
    def _add_info(self, message: str):
        """Добавляет сообщение в информационное поле."""
        self._info_text.config(state=tk.NORMAL)
        self._info_text.insert(tk.END, message + "\n")
        self._info_text.see(tk.END)
        self._info_text.config(state=tk.DISABLED)
    
    def _on_variables_loaded(self, event: VariablesLoadedEvent):
        """Обработчик события загрузки переменных."""
        var_count = len(event.variables)
        self._add_info(f"Загружено переменных: {var_count}")
    
    def _on_templates_loaded(self, event: TemplatesLoadedEvent):
        """Обработчик события загрузки шаблонов."""
        template_count = len(event.templates)
        self._add_info(f"Загружено шаблонов: {template_count}")
        for template_name in event.templates.keys():
            self._add_info(f"  - {template_name}")
    
    def _on_email_generated(self, event: EmailGeneratedEvent):
        """Обработчик события генерации письма."""
        self._add_info(f"Сгенерировано письмо: {event.template_name}")
        self._add_info(f"  Тема: {event.subject}")
    
    def _on_email_saved(self, event: EmailSavedEvent):
        """Обработчик события сохранения письма."""
        if event.success:
            self._add_info(f"✓ Письмо '{event.template_name}' сохранено в черновики")
        else:
            self._add_info(f"✗ Ошибка сохранения письма '{event.template_name}'")
            if event.error_message:
                self._add_info(f"  Ошибка: {event.error_message}")
    
    def _on_error(self, event: ErrorEvent):
        """Обработчик события ошибки."""
        message = f"✗ ОШИБКА [{event.error_type}]: {event.error_message}"
        self._add_info(message)
        self._log_dialog.add_log(message, "ERROR")
    
    def _show_create_campaign(self):
        """Показывает диалог создания кампании."""
        if self._campaign_dialog:
            self._campaign_dialog.show_create_campaign()
    
    def _show_campaigns_list(self):
        """Показывает список кампаний."""
        if self._campaign_dialog:
            self._campaign_dialog.show_campaigns_list()
    
    def _show_logs(self):
        """Показывает диалог логов."""
        self._log_dialog.show()
    
    def _on_campaign_created(self, event: CampaignCreatedEvent):
        """Обработчик события создания кампании."""
        message = f"Создана кампания: {event.campaign_name} (ID: {event.campaign_id})"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
    
    def _on_campaign_started(self, event: CampaignStartedEvent):
        """Обработчик события запуска кампании."""
        message = f"Запущена кампания: {event.campaign_id}"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
    
    def _on_email_sent(self, event: EmailSentEvent):
        """Обработчик события отправки письма."""
        message = f"Отправлено письмо: {event.recipient} (Кампания: {event.campaign_id})"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
    
    def _on_email_replied(self, event: EmailRepliedEvent):
        """Обработчик события ответа на письмо."""
        message = f"Получен ответ от: {event.recipient} (Кампания: {event.campaign_id})"
        self._add_info(message)
        self._log_dialog.add_log(message, "INFO")
