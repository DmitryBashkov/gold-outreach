"""Диалоговое окно для просмотра логов."""
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from typing import List


class LogDialog:
    """Диалог для отображения логов."""
    
    def __init__(self, parent: tk.Tk):
        """
        Инициализирует диалог логов.
        
        Args:
            parent: Родительское окно
        """
        self._parent = parent
        self._dialog = None
        self._logs: List[str] = []
    
    def show(self):
        """Показывает диалог логов."""
        if self._dialog and self._dialog.winfo_exists():
            self._dialog.lift()
            return
        
        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Логи")
        self._dialog.geometry("700x500")
        self._dialog.transient(self._parent)
        
        main_frame = ttk.Frame(self._dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Текстовое поле с логами
        log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state=tk.DISABLED)
        log_text.pack(fill=tk.BOTH, expand=True)
        
        # Загружаем существующие логи
        for log in self._logs:
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, log + "\n")
            log_text.config(state=tk.DISABLED)
        
        log_text.see(tk.END)
        
        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        def clear_logs():
            """Очищает логи."""
            self._logs.clear()
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            log_text.config(state=tk.DISABLED)
        
        ttk.Button(buttons_frame, text="Очистить", command=clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Закрыть", command=self._dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Сохраняем ссылку на текстовое поле для обновления
        self._log_text = log_text
    
    def add_log(self, message: str, level: str = "INFO"):
        """
        Добавляет запись в лог.
        
        Args:
            message: Сообщение
            level: Уровень логирования (INFO, ERROR, WARNING)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self._logs.append(log_entry)
        
        # Обновляем диалог, если он открыт
        if self._dialog and self._dialog.winfo_exists():
            self._log_text.config(state=tk.NORMAL)
            self._log_text.insert(tk.END, log_entry + "\n")
            self._log_text.see(tk.END)
            self._log_text.config(state=tk.DISABLED)
    
    def get_logs(self) -> List[str]:
        """Возвращает все логи."""
        return self._logs.copy()
