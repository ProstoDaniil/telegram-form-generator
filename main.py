# telegram-form-generator/main.py

import os
import sys
import json
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import time
import uuid
import re
import threading
import urllib.request
import urllib.error
import base64

APP_TITLE = "Генератор анкет → Telegram (v3.1.2beta)"
APP_VERSION = "3.1.2beta"
MAX_QUESTIONS = 300
CHAR_LIMIT = 1500

# --- Вспомогательные функции ---

def get_data_dir():
    """Определяет и создаёт папку для хранения конфигурации приложения."""
    try:
        if sys.platform == "win32":
            base = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        elif sys.platform == "darwin":
            base = str(Path.home() / "Library" / "Application Support")
        else:
            base = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        d = Path(base) / "form_gen"
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        try:
            d = Path.home() / ".form_gen"
            d.mkdir(parents=True, exist_ok=True)
            return d
        except Exception:
            return Path.cwd()

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# --- Словари-константы для тем и шрифтов ---
SITE_THEMES = {
    "dark":       {"bg":"#0B1220","text":"#E5E7EB","primary":"#7C3AED","card_border":"rgba(255,255,255,0.1)","card_bg_alpha":0.06,"shadow":"0 10px 30px rgba(0,0,0,0.35)","field_border":"#263041","field_bg":"#0f172a"},
    "light":      {"bg":"#F8FAFC","text":"#0F172A","primary":"#4F46E5","card_border":"#e5e7eb","card_bg_alpha":1,"shadow":"0 10px 30px rgba(0,0,0,0.06)","field_border":"#cbd5e1","field_bg":"#ffffff"},
    "retrowave":  {"bg":"#0D0033","text":"#F8E7FF","primary":"#FF2E88","card_border":"rgba(255,46,136,0.35)","card_bg_alpha":0.12,"shadow":"0 10px 40px rgba(255,46,136,0.25)","field_border":"#4C1D95","field_bg":"#12023F"},
    # ... (и так далее для всех тем сайта)
}
SITE_THEME_MAP = {
    "dark": "Темная", "light": "Светлая", "retrowave": "Ретровейв", "nord": "Норд",
    "dracula": "Дракула", "ocean": "Океан", "forest": "Лес", "sunset": "Закат", "minty": "Мятная",
    "midnight": "Полночь", "rose_quartz": "Розовый кварц", "coffee": "Кофе", "solarized": "Солярис",
    "gruvbox": "Gruvbox", "sandstone": "Песчаник", "cyberpunk": "Киберпанк", "tokyo_night": "Ночной Токио",
    "emerald": "Изумруд", "amethyst": "Аметист", "slate": "Сланец", "crimson": "Багровый", "latte": "Латте",
    "monokai": "Monokai", "sakura": "Сакура", "graphite": "Графит", "mandarin": "Дерзкий мандарин", "fuflick": "Весёлый фуфлик"
}
RU_THEME_MAP = {v: k for k, v in SITE_THEME_MAP.items()}
SITE_FONTS = {
    "System UI": "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif",
    "Roboto": "'Roboto', sans-serif", "Inter": "'Inter', sans-serif", "Montserrat": "'Montserrat', sans-serif",
    "Playfair Display": "'Playfair Display', serif", "Source Code Pro": "'Source Code Pro', monospace",
    "Lobster": "'Lobster', cursive", "Georgia (serif)": "Georgia, 'Times New Roman', serif",
    "Verdana (sans-serif)": "Verdana, Geneva, Tahoma, sans-serif", "Courier New (monospace)": "'Courier New', Courier, monospace",
}

def bind_paste_hotkeys(widget):
    def do_paste(event=None):
        try:
            widget.event_generate("<<Paste>>")
        except Exception:
            try:
                data = widget.clipboard_get()
                widget.insert(tk.INSERT, data)
            except Exception: pass
        return "break"
    widget.bind("<Control-v>", do_paste)
    widget.bind("<Control-V>", do_paste)
    widget.bind("<Shift-Insert>", do_paste)

def attach_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0, bg="#0B1118", fg="#F6F9FE",
                   activebackground="#2E4470", activeforeground="#FFFFFF", borderwidth=0)
    menu.add_command(label="Вставить из буфера", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Выделить всё", command=lambda: widget.event_generate("<<SelectAll>>"))
    def show_menu(event):
        try: menu.tk_popup(event.x_root, event.y_root)
        finally: menu.grab_release()
    widget.bind("<Button-3>", show_menu)
    bind_paste_hotkeys(widget)
    return menu

def apply_ui_theme(root, theme_dict):
    style = ttk.Style(root)
    try: style.theme_use("clam")
    except tk.TclError: pass

    root.ACC_COLOR = theme_dict['ACC']
    root.ENTRY_BG_COLOR = theme_dict['ENTRY_BG']
    root.ENTRY_TXT_COLOR = theme_dict['ENTRY_TXT']
    root.SELECTION_FG_COLOR = theme_dict['SELECTION_FG']

    BG, PANEL, CARD, FG = theme_dict['BG'], theme_dict['PANEL'], theme_dict['CARD'], theme_dict['FG']
    SUB, ACC, ENTRY_BG, ENTRY_TXT = theme_dict.get('SUB', FG), theme_dict['ACC'], theme_dict['ENTRY_BG'], theme_dict['ENTRY_TXT']
    BORDER, ACC_HOVER, SELECTION_FG = theme_dict['BORDER'], theme_dict['ACC_HOVER'], theme_dict['SELECTION_FG']
    INVALID_BORDER, HOVER_PANEL, HOVER_CARD = theme_dict['INVALID_BORDER'], theme_dict.get('HOVER_PANEL', PANEL), theme_dict.get('HOVER_CARD', CARD)

    base_font = ("Segoe UI", 14)
    root.option_add("*Font", base_font)
    root.option_add("*Entry.insertBackground", ENTRY_TXT)
    root.option_add("*Text.insertBackground", ENTRY_TXT)
    root.option_add("*TEntry*selectBackground", ENTRY_BG)
    root.option_add("*Text*selectBackground", ENTRY_BG)
    root.option_add("*TEntry*selectForeground", SELECTION_FG)
    root.option_add("*Text*selectForeground", SELECTION_FG)
    
    for option in ["*Menu.background", "*Menu.foreground", "*Menu.activeBackground", "*Menu.activeForeground", "*Menu.relief", "*Menu.borderWidth"]:
        root.option_delete(option, None)

    root.option_add("*Menu.background", PANEL)
    root.option_add("*Menu.foreground", FG)
    root.option_add("*Menu.activeBackground", ACC)
    root.option_add("*Menu.activeForeground", "#FFFFFF")
    root.option_add("*Menu.relief", "flat")
    root.option_add("*Menu.borderWidth", 0)

    root.option_add("*TCombobox*Listbox.font", base_font)
    root.option_add("*TCombobox*Listbox.background", PANEL)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", ACC)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    root.option_add("*TCombobox*Listbox.borderWidth", 0)
    root.option_add("*TCombobox*Listbox.highlightThickness", 0)

    root.configure(bg=BG)
    style.configure(".", background=BG, foreground=FG, fieldbackground=ENTRY_BG)
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("Card.TFrame", background=CARD, relief="flat", borderwidth=0)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("Sub.TLabel", background=PANEL, foreground=SUB)
    style.configure("Card.TLabel", background=CARD, foreground=FG)
    
    style.configure("TLabelFrame", background=PANEL, bordercolor=BORDER, borderwidth=1, relief="solid")
    style.configure("TLabelFrame.Label", background=PANEL, foreground=FG, padding=(10, 5), font=("Segoe UI", 14, "bold"))

    style.configure("TEntry", fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=ENTRY_TXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=12, selectbackground=ENTRY_BG, selectforeground=SELECTION_FG)
    style.map("TEntry", fieldbackground=[("disabled", ENTRY_BG),("readonly", ENTRY_BG),("active", ENTRY_BG),("focus", ENTRY_BG),("!focus", ENTRY_BG)], background=[("disabled", ENTRY_BG),("readonly", ENTRY_BG),("active", ENTRY_BG),("focus", ENTRY_BG),("!focus", ENTRY_BG)], foreground=[("disabled", "#94A3B8"), ("!disabled", ENTRY_TXT)], bordercolor=[("focus", ACC), ("!focus", BORDER)], lightcolor=[("focus", ACC), ("!focus", BORDER)], darkcolor=[("focus", ACC), ("!focus", BORDER)])
    
    style.configure("Invalid.TEntry", fieldbackground=ENTRY_BG, foreground=ENTRY_TXT, padding=12, selectbackground=ENTRY_BG, selectforeground=SELECTION_FG)
    style.map("Invalid.TEntry", bordercolor=[("focus", "#FF5C5C"), ("!focus", INVALID_BORDER)], lightcolor=[("focus", "#FF5C5C"), ("!focus", INVALID_BORDER)], darkcolor=[("focus", "#FF5C5C"), ("!focus", INVALID_BORDER)])

    style.configure("TCombobox", fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=ENTRY_TXT, selectbackground=ENTRY_BG, selectforeground=ENTRY_TXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, arrowsize=16, padding=10)
    style.map("TCombobox", fieldbackground=[("disabled", ENTRY_BG),("readonly", ENTRY_BG),("active", ENTRY_BG),("focus", ENTRY_BG),("!focus", ENTRY_BG)], background=[("disabled", ENTRY_BG),("readonly", ENTRY_BG),("active", ENTRY_BG),("focus", ENTRY_BG),("!focus", ENTRY_BG)], foreground=[("disabled", "#94A3B8"), ("readonly", ENTRY_TXT), ("!disabled", ENTRY_TXT)], bordercolor=[("focus", ACC), ("!focus", BORDER)], lightcolor=[("focus", ACC), ("!focus", BORDER)], darkcolor=[("focus", ACC), ("!focus", BORDER)])
    
    style.configure("TCheckbutton", background=PANEL, foreground=FG, font=base_font)
    style.configure("Card.TCheckbutton", background=CARD, foreground=FG, font=base_font)
    style.map("TCheckbutton", foreground=[('!disabled', FG)], background=[('active', HOVER_PANEL), ('!active', PANEL)])
    style.map("Card.TCheckbutton", foreground=[('!disabled', FG)], background=[('active', HOVER_CARD), ('!active', CARD)])

    style.configure("TButton", background=ACC, foreground="#FFFFFF", padding=(14,10), borderwidth=0, font=base_font)
    style.map("TButton", background=[("active", ACC_HOVER)])
    
    style.configure("Action.TButton", background=ACC, foreground="#FFFFFF", padding=(18, 12), borderwidth=0, font=("Segoe UI", 14))
    style.map("Action.TButton", background=[("active", ACC_HOVER)])
    style.configure("Action.TCheckbutton", background=PANEL, foreground=FG, font=("Segoe UI", 14), padding=(10, 5))
    style.map("Action.TCheckbutton", background=[('active', HOVER_PANEL)])

    style.configure("TNotebook", background=BG, tabmargins=(10,8,10,0), borderwidth=0)
    style.configure("TNotebook.Tab", background=BG, foreground=FG, padding=(18,12), borderwidth=0)
    style.map("TNotebook.Tab", background=[("selected", CARD), ("!selected", BG)])
    style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=FG, bordercolor=BORDER)
    style.configure("Treeview.Heading", background=PANEL, foreground=FG)
    
    if hasattr(root, 'preview_text'):
        root.preview_text.config(bg=ENTRY_BG, fg=ENTRY_TXT, insertbackground=ENTRY_TXT, selectbackground=ENTRY_BG, selectforeground=SELECTION_FG)
    if hasattr(root, 'canvas'):
        root.canvas.config(bg=BG)

class CollapsibleFrame(ttk.LabelFrame):
    # ... (код класса CollapsibleFrame без изменений) ...
    def __init__(self, parent, text="", *args, **kwargs):
        super().__init__(parent, text="", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.parent = parent
        self.visible = tk.BooleanVar(value=True)
        self.header = ttk.Frame(self, style="Panel.TFrame")
        self.header.grid(row=0, column=0, sticky="ew")
        self.toggle_button = ttk.Label(self.header, text=f"▼ {text}", style="TLabelFrame.Label", cursor="hand2")
        self.toggle_button.pack(side="left", fill="x", expand=True)
        self.container = ttk.Frame(self, style="Panel.TFrame")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5,10))
        self.toggle_button.bind("<Button-1>", self.toggle)
        
    def toggle(self, event=None):
        if self.visible.get():
            self.container.grid_remove()
            self.toggle_button.config(text=self.toggle_button.cget("text").replace("▼", "►"))
        else:
            self.container.grid()
            self.toggle_button.config(text=self.toggle_button.cget("text").replace("►", "▼"))
        self.visible.set(not self.visible.get())

class QuestionRow:
    # ... (код класса QuestionRow без изменений) ...
    def __init__(self, master, app_ref, index, on_remove, focus_callback=None):
        self.app = app_ref
        self.master = master
        self.index = index
        self.on_remove = on_remove
        self.focus_callback = focus_callback
        self.id = str(uuid.uuid4())
        self.condition = None

        self.frame = ttk.Frame(master, padding=12, style="Card.TFrame")
        self.frame.grid_columnconfigure(1, weight=1)

        self.var_label = tk.StringVar()
        self.var_type = tk.StringVar(value="Свободный ответ")
        self.var_required = tk.BooleanVar(value=False)
        self.var_limit_chars = tk.BooleanVar(value=False)
        self.option_widgets = []

        head = ttk.Frame(self.frame, style="Card.TFrame")
        head.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.q_num_label = ttk.Label(head, text=f"Вопрос {index+1}", style="Card.TLabel", font=("Segoe UI", 14, "bold"))
        self.q_num_label.pack(side="left")
        self.conditional_info_label = ttk.Label(head, text="", style="Card.TLabel", font=("Segoe UI", 11, "italic"))
        self.conditional_info_label.pack(side="left", padx=10)
        up_btn = ttk.Button(head, text="↑", width=3, command=self.move_up)
        up_btn.pack(side="right", padx=2)
        down_btn = ttk.Button(head, text="↓", width=3, command=self.move_down)
        down_btn.pack(side="right")
        ttk.Button(head, text="Удалить", command=self.remove).pack(side="right", padx=5)

        ttk.Label(self.frame, text="Текст вопроса:", style="Card.TLabel").grid(row=1, column=0, sticky="w")
        self.entry_label = ttk.Entry(self.frame, textvariable=self.var_label)
        self.entry_label.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)
        attach_context_menu(self.entry_label)

        ttk.Label(self.frame, text="Тип:", style="Card.TLabel").grid(row=2, column=0, sticky="w")
        self.combo_type = ttk.Combobox(self.frame, textvariable=self.var_type, state="readonly", values=["Свободный ответ","Выбор варианта"], width=24)
        self.combo_type.grid(row=2, column=1, sticky="w", pady=6)
        
        self.options_frame = ttk.Frame(self.frame, style="Card.TFrame")
        self.options_frame.grid(row=2, column=2, sticky="w")
        self.chk_required = ttk.Checkbutton(self.options_frame, text="Обязательный", variable=self.var_required, style="Card.TCheckbutton")
        self.chk_limit = ttk.Checkbutton(self.options_frame, text=f"Лимит {CHAR_LIMIT} симв.", variable=self.var_limit_chars, style="Card.TCheckbutton")

        self.options_ui_container = ttk.Frame(self.frame, style="Card.TFrame")
        self.options_ui_container.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4,0))
        self.options_ui_container.grid_columnconfigure(1, weight=1)
        
        self.options_label = ttk.Label(self.options_ui_container, text="Варианты:", style="Card.TLabel")
        self.options_label.grid(row=0, column=0, sticky="nw", pady=(4,0))
        
        self.options_fields_frame = ttk.Frame(self.options_ui_container, style="Card.TFrame")
        self.options_fields_frame.grid(row=0, column=1, sticky="ew")
        
        self.add_option_btn = ttk.Button(self.options_ui_container, text="Добавить вариант", command=self.add_option_field)
        self.add_option_btn.grid(row=1, column=1, sticky="w", pady=5)
        
        self.add_dependent_btn = ttk.Button(self.options_ui_container, text="Добавить зависимый вопрос", command=self.create_dependent_question)
        self.add_dependent_btn.grid(row=2, column=1, sticky="w", pady=5)

        self.combo_type.bind("<<ComboboxSelected>>", self.on_type_change)
        self.on_type_change()

    def move_up(self):
        if self.index == 0: return
        rows = self.app.question_rows
        rows[self.index], rows[self.index - 1] = rows[self.index - 1], rows[self.index]
        self.app.reindex_questions()

    def move_down(self):
        rows = self.app.question_rows
        if self.index == len(rows) - 1: return
        rows[self.index], rows[self.index + 1] = rows[self.index + 1], rows[self.index]
        self.app.reindex_questions()

    def get_options(self):
        return [w['var'].get().strip() for w in self.option_widgets if w['var'].get().strip()]

    def add_option_field(self, text=""):
        frame = ttk.Frame(self.options_fields_frame, style="Card.TFrame")
        frame.pack(fill="x", pady=2)
        
        var = tk.StringVar(value=text)
        entry = ttk.Entry(frame, textvariable=var)
        entry.pack(side="left", fill="x", expand=True)
        attach_context_menu(entry)
        
        widget_dict = {'frame': frame, 'var': var}
        
        remove_btn = ttk.Button(frame, text="-", width=3, command=lambda w=widget_dict: self.remove_option_field(w))
        remove_btn.pack(side="left", padx=(5,0))
        
        self.option_widgets.append(widget_dict)
        if self.focus_callback:
            self.app.update_idletasks()
            self.focus_callback(frame)

    def remove_option_field(self, widget_dict):
        widget_dict['frame'].destroy()
        self.option_widgets.remove(widget_dict)

    def create_dependent_question(self):
        self.app.open_dependent_question_dialog(self)

    def on_type_change(self, event=None):
        self.chk_required.pack(side="left", padx=(10, 5))
        q_type = self.var_type.get()

        if q_type == "Выбор варианта":
            self.options_ui_container.grid()
            self.chk_limit.pack_forget()
            if not self.option_widgets:
                self.add_option_field()
        elif q_type == "Свободный ответ":
            self.options_ui_container.grid_remove()
            self.chk_limit.pack(side="left", padx=5)
            for w in self.option_widgets[:]: self.remove_option_field(w)

    def grid(self, **kwargs): self.frame.grid(**kwargs)
    def remove(self):
        if messagebox.askyesno("Удалить вопрос", "Вы уверены, что хотите удалить этот вопрос?"):
            self.frame.destroy()
            self.on_remove(self)
    def focus_label(self):
        try: self.entry_label.focus_set()
        except: pass
        if self.focus_callback: self.focus_callback(self.frame)

    def to_dict(self):
        t_map = {"Свободный ответ":1, "Выбор варианта":2}
        t = t_map.get(self.var_type.get(), 1)
        data = { "id": self.id, "label": self.var_label.get().strip(), "type": t, "required": bool(self.var_required.get()), "limit_chars": bool(self.var_limit_chars.get()) if t == 1 else False }
        if t == 2:
            data["options"] = self.get_options()
        if self.condition:
            data["condition"] = self.condition
        return data

class App(tk.Tk):
    # ... (код класса App без изменений) ...
    APP_THEMES = {
        "Deep Space (Default)": {"BG":"#0A0F14", "PANEL":"#0E151D", "CARD":"#131C29", "FG":"#F6F9FE", "ACC":"#6D8BFF", "ACC_HOVER":"#8CA3FF", "ENTRY_BG":"#1F2E44", "ENTRY_TXT":"#FFFFFF", "BORDER":"#2B3E57", "SELECTION_FG":"#FFD700", "INVALID_BORDER":"#EF4444"},
        "Arctic Light":         {"BG":"#F8FAFC", "PANEL":"#FFFFFF", "CARD":"#F1F5F9", "FG":"#0F172A", "ACC":"#4F46E5", "ACC_HOVER":"#6A64F8", "ENTRY_BG":"#FFFFFF", "ENTRY_TXT":"#0F172A", "BORDER":"#CBD5E1", "SELECTION_FG":"#0F172A", "INVALID_BORDER":"#EF4444"},
        "Slate":                {"BG":"#334155", "PANEL":"#475569", "CARD":"#525F75", "FG":"#F1F5F9", "ACC":"#60A5FA", "ACC_HOVER":"#7BC0FF", "ENTRY_BG":"#1E293B", "ENTRY_TXT":"#F1F5F9", "BORDER":"#64748B", "SELECTION_FG":"#F1F5F9", "INVALID_BORDER":"#F87171"},
        "Rose Pine":            {"BG":"#191724", "PANEL":"#1f1d2e", "CARD":"#26233a", "FG":"#e0def4", "ACC":"#eb6f92", "ACC_HOVER":"#F588A9", "ENTRY_BG":"#2a273f", "ENTRY_TXT":"#e0def4", "BORDER":"#403d52", "SELECTION_FG":"#f6c177", "INVALID_BORDER":"#eb6f92"},
        "Solarized Dark":       {"BG":"#002b36", "PANEL":"#073642", "CARD":"#08404f", "FG":"#839496", "ACC":"#268bd2", "ACC_HOVER":"#3A9CE3", "ENTRY_BG":"#00252e", "ENTRY_TXT":"#839496", "BORDER":"#094F61", "SELECTION_FG":"#b58900", "INVALID_BORDER":"#dc322f"},
        "Nord":                 {"BG":"#2E3440", "PANEL":"#3B4252", "CARD":"#434C5E", "FG":"#D8DEE9", "ACC":"#88C0D0", "ACC_HOVER":"#99D1E1", "ENTRY_BG":"#4C566A", "ENTRY_TXT":"#ECEFF4", "BORDER":"#4C566A", "SELECTION_FG":"#EBCB8B", "INVALID_BORDER":"#BF616A"},
        "Gruvbox Dark":         {"BG":"#282828", "PANEL":"#3c3836", "CARD":"#504945", "FG":"#ebdbb2", "ACC":"#fabd2f", "ACC_HOVER":"#FBC955", "ENTRY_BG":"#504945", "ENTRY_TXT":"#ebdbb2", "BORDER":"#665c54", "SELECTION_FG":"#282828", "INVALID_BORDER":"#fb4934"},
        "Dracula":              {"BG":"#282a36", "PANEL":"#343746", "CARD":"#44475a", "FG":"#f8f8f2", "ACC":"#bd93f9", "ACC_HOVER":"#CA9FFB", "ENTRY_BG":"#44475a", "ENTRY_TXT":"#f8f8f2", "BORDER":"#6272a4", "SELECTION_FG":"#f1fa8c", "INVALID_BORDER":"#ff5555"},
        "Monokai Pro":          {"BG":"#222222", "PANEL":"#2D2A2E", "CARD":"#3c383e", "FG":"#FCFCFA", "ACC":"#FF6188", "ACC_HOVER":"#FF7CA0", "ENTRY_BG":"#403E41", "ENTRY_TXT":"#FCFCFA", "BORDER":"#5B595C", "SELECTION_FG":"#FFD866", "INVALID_BORDER":"#FF6188"},
        "City Lights":          {"BG":"#ecf0f1", "PANEL":"#ffffff", "CARD":"#f5f7fa", "FG":"#2c3e50", "ACC":"#3498db", "ACC_HOVER":"#5DADE2", "ENTRY_BG":"#ffffff", "ENTRY_TXT":"#2c3e50", "BORDER":"#bdc3c7", "SELECTION_FG":"#34495e", "INVALID_BORDER":"#e74c3c"}
    }
    
    APPS_SCRIPT_CODE = """
// ==================== КОНФИГУРАЦИЯ ====================
const SHEET_NAME = "Ответы"; // Точное имя листа в вашей таблице

// ===============================================================
// НОВЫЙ УПРОЩЕННЫЙ КОД (только для записи в таблицу)
// ===============================================================

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    // Обработка тестового запроса от кнопки "Проверить"
    if (data.action === 'verify') {
      return ContentService.createTextOutput(JSON.stringify({ "result": "success", "message": "Connection to Google Script is OK." })).setMimeType(ContentService.MimeType.JSON);
    }

    // Обработка реальных данных из формы
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    if (!sheet) throw new Error("Лист '" + SHEET_NAME + "' не найден.");
    
    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    const newRow = new Array(headers.length).fill('');

    const headerMap = {};
    headers.forEach((header, i) => { headerMap[header] = i; });

    if (data.answers && Array.isArray(data.answers)) {
      data.answers.forEach(item => {
        if (headerMap.hasOwnProperty(item.label)) {
          newRow[headerMap[item.label]] = item.answer;
        }
      });
    }

    if (headerMap.hasOwnProperty("Дата ответа")) {
      newRow[headerMap["Дата ответа"]] = new Date();
    }

    sheet.appendRow(newRow);
    
    return ContentService.createTextOutput(JSON.stringify({ "result": "success" })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    Logger.log(error); // Для отладки в Google Script
    return ContentService.createTextOutput(JSON.stringify({ "result": "error", "message": error.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}
"""
    
    def __init__(self):
        super().__init__()
        
        self.config_file = get_data_dir() / "app_config.json"
        
        self.var_app_theme = tk.StringVar(value="Deep Space (Default)")
        self.change_theme()
        
        self.title(APP_TITLE)
        
        self.menubar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Новый", command=lambda: self.new_project(), accelerator="Ctrl+N")
        self.file_menu.add_command(label="Открыть…", command=lambda: self.open_project(), accelerator="Ctrl+O")
        self.file_menu.add_command(label="Сохранить", command=lambda: self.save_project(), accelerator="Ctrl+S")
        self.file_menu.add_command(label="Сохранить как…", command=lambda: self.save_project_as())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Выход", command=lambda: self.on_close())
        self.menubar.add_cascade(label="Файл", menu=self.file_menu)
        
        view_menu = tk.Menu(self.menubar, tearoff=0)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        for theme_name in self.APP_THEMES:
            theme_menu.add_radiobutton(label=theme_name, variable=self.var_app_theme, command=self.change_theme)
        view_menu.add_cascade(label="Тема", menu=theme_menu)
        self.menubar.add_cascade(label="Вид", menu=view_menu)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="О программе", command=lambda: self.show_about())
        self.menubar.add_cascade(label="Справка", menu=self.help_menu)

        self.config(menu=self.menubar)

        self.container = tk.Frame(self, bg="#0A0F14", bd=0, highlightthickness=0)
        self.container.pack(fill="both", expand=True)

        self.tabs = ttk.Notebook(self.container)
        self.tabs.pack(fill="both", expand=True, padx=5, pady=(0,5))

        self.builder_tab = ttk.Frame(self.tabs, style="Panel.TFrame")
        self.preview_tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=14)
        self.tabs.add(self.builder_tab, text="Конструктор")
        self.tabs.add(self.preview_tab, text="Предпросмотр")

        self.question_rows = []
        self.var_numbering = tk.BooleanVar(value=True)
        self.var_view_mode = tk.StringVar(value="standard")
        self.var_site_theme = tk.StringVar(value="Темная")
        self.var_site_font = tk.StringVar(value="System UI")
        self.var_submit_text = tk.StringVar(value="Отправить")
        self.var_success_message = tk.StringVar(value="Ответ успешно отправлен. Спасибо!")
        self.var_password_enabled = tk.BooleanVar(value=False)
        self.var_password = tk.StringVar(value="")
        self.var_limit_one_submission = tk.BooleanVar(value=False)
        self.var_one_submission_message = tk.StringVar(value="Спасибо! Ваш ответ был получен. Отправка повторных анкет не допускается.")
        
        self.var_telegram_enabled = tk.BooleanVar(value=True)
        self.var_gsheets_enabled = tk.BooleanVar(value=False)
        self.var_gsheets_url = tk.StringVar()
        self.var_tg_separator = tk.StringVar(value="— — —")

        self.current_file = None
        self.dirty = False

        self.build_builder()
        self.build_preview()

        self.bind_all("<Control-n>", lambda e: self.new_project())
        self.bind_all("<Control-o>", lambda e: self.open_project())
        self.bind_all("<Control-s>", lambda e: self.save_project())
        self.bind_all("<F5>", lambda e: self.refresh_preview())
        
        self.after(50, self.show_welcome_message_if_needed)
        self.after(120, lambda: self.focus_first_entry())

        self.update_idletasks()
        w, h = 1300, 920
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = max(0, (sw - w)//2), max(0, (sh - h)//3)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.protocol("WM_DELETE_WINDOW", lambda: self.on_close())

    def change_theme(self):
        theme_name = self.var_app_theme.get()
        theme_dict = self.APP_THEMES.get(theme_name)
        if not theme_dict:
            theme_name = list(self.APP_THEMES.keys())[0]
            theme_dict = self.APP_THEMES[theme_name]
            self.var_app_theme.set(theme_name)
        
        apply_ui_theme(self, theme_dict)
        
    def set_dirty_status(self, is_dirty):
        self.dirty = is_dirty
        base_title = APP_TITLE
        if self.current_file:
            base_title = f"{Path(self.current_file).name} - {APP_TITLE}"
        
        current_title = self.title()
        has_asterisk = current_title.startswith("*")
        
        if is_dirty and not has_asterisk:
            self.title(f"*{base_title}")
        elif not is_dirty and has_asterisk:
             self.title(current_title[1:])

    def on_close(self):
        if self.dirty and not messagebox.askyesno("Выход", "Есть несохранённые изменения. Вы уверены, что хотите выйти?"):
            return
        self.destroy()

    def show_about(self):
        about_win = tk.Toplevel(self)
        about_win.title("О программе")
        about_win.transient(self)
        about_win.grab_set()
        about_win.resizable(False, False)
        
        self.update_idletasks()
        parent_x, parent_y = self.winfo_x(), self.winfo_y()
        parent_w, parent_h = self.winfo_width(), self.winfo_height()
        win_w, win_h = 560, 260
        x = parent_x + (parent_w // 2) - (win_w // 2)
        y = parent_y + (parent_h // 2) - (win_h // 2)
        about_win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        main_frame = ttk.Frame(about_win, style="Panel.TFrame", padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=APP_TITLE, style="Sub.TLabel", font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))
        ttk.Label(main_frame, text=f"Версия: {APP_VERSION}", style="Sub.TLabel", font=("Segoe UI", 12)).pack(pady=(0, 15))
        ttk.Label(main_frame, text="Для некоммерческого индивидуального использования.", style="Sub.TLabel", wraplength=500, font=("Segoe UI", 12)).pack(pady=2)
        
        creator_frame = ttk.Frame(main_frame, style="Panel.TFrame")
        creator_frame.pack(pady=2)
        ttk.Label(creator_frame, text="Создатель:", style="Sub.TLabel", font=("Segoe UI", 12)).pack(side="left")
        link = ttk.Label(creator_frame, text="@DV_Lub97", style="Sub.TLabel", foreground=self.ACC_COLOR, cursor="hand2", font=("Segoe UI", 12))
        link.pack(side="left", padx=5)
        link.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://t.me/DV_Lub97"))
        ttk.Label(creator_frame, text="(готов к коммерческому сотрудничеству)", style="Sub.TLabel", font=("Segoe UI", 12)).pack(side="left")

        ttk.Label(main_frame, text="Программа написана в основном с помощью ИИ.", style="Sub.TLabel", wraplength=500, font=("Segoe UI", 10, "italic")).pack(pady=(10,0))
        
        ok_btn = ttk.Button(main_frame, text="OK", command=about_win.destroy)
        ok_btn.pack(pady=(20, 0))
        ok_btn.focus_set()

    def update_view_mode_description(self, event=None):
        selected_mode = self.var_view_mode.get()
        description = self.view_mode_descriptions.get(selected_mode, "Стандартный вид с карточками для вопросов.")
        self.var_view_mode_desc.set(description)

    def build_builder(self):
        self.canvas = tk.Canvas(self.builder_tab, bd=0, highlightthickness=0, bg=self.APP_THEMES[self.var_app_theme.get()]['BG'])
        scroll = ttk.Scrollbar(self.builder_tab, orient="vertical", command=self.canvas.yview)
        scrollable_frame = ttk.Frame(self.canvas, style="Panel.TFrame")

        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)

        self.canvas_window = self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)

        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", on_canvas_configure)

        def _on_mousewheel(event):
            widget = self.winfo_containing(event.x_root, event.y_root)
            parent = widget
            is_in_canvas = False
            while parent is not None:
                if parent == self.canvas:
                    is_in_canvas = True
                    break
                parent = parent.master

            if is_in_canvas:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.bind_all("<MouseWheel>", _on_mousewheel)

        main_content = ttk.Frame(scrollable_frame, style="Panel.TFrame", padding=14)
        main_content.pack(fill="both", expand=True)
        main_content.columnconfigure(0, weight=1)

        top_panel = ttk.Frame(main_content, style="Panel.TFrame")
        self.content_frame = ttk.Frame(main_content, style="Panel.TFrame")
        bottom_panel = ttk.Frame(main_content, style="Panel.TFrame")
        
        top_panel.pack(fill="x", expand=True)
        self.content_frame.pack(fill="x", expand=True, pady=10)
        bottom_panel.pack(fill="x", expand=True)
        
        self.var_bot = tk.StringVar()
        self.var_chat = tk.StringVar()
        self.var_title = tk.StringVar()
        self.var_tg_verify_status = tk.StringVar()
        self.var_gs_verify_status = tk.StringVar()

        def on_change(*_):
            self.set_dirty_status(True)

        for v in (self.var_bot, self.var_chat, self.var_title, self.var_site_theme,
                  self.var_numbering, self.var_view_mode, self.var_site_font, 
                  self.var_submit_text, self.var_success_message, self.var_telegram_enabled, 
                  self.var_gsheets_enabled, self.var_gsheets_url, self.var_password_enabled, 
                  self.var_password, self.var_limit_one_submission, self.var_one_submission_message,
                  self.var_tg_separator):
            v.trace_add("write", on_change)

        tg_lf = CollapsibleFrame(top_panel, text="1. Интеграция с Telegram")
        tg_lf.pack(fill="x", expand=True, pady=5)
        tg_lf_inner = tg_lf.container
        tg_lf_inner.grid_columnconfigure(1, weight=1)
        ttk.Checkbutton(tg_lf_inner, text="Включить отправку в Telegram", variable=self.var_telegram_enabled, command=self.toggle_tg_fields).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5))
        ttk.Label(tg_lf_inner, text="Токен бота:", style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        self.e_bot = ttk.Entry(tg_lf_inner, textvariable=self.var_bot); self.e_bot.grid(row=1, column=1, sticky="ew", padx=10, pady=2); attach_context_menu(self.e_bot)
        ttk.Label(tg_lf_inner, text="Chat ID:", style="Sub.TLabel").grid(row=2, column=0, sticky="w", pady=2)
        self.e_chat = ttk.Entry(tg_lf_inner, textvariable=self.var_chat); self.e_chat.grid(row=2, column=1, sticky="ew", padx=10, pady=2); attach_context_menu(self.e_chat)
        
        ttk.Label(tg_lf_inner, text="Разделитель:", style="Sub.TLabel").grid(row=3, column=0, sticky="w", pady=2)
        self.separator_combo = ttk.Combobox(tg_lf_inner, textvariable=self.var_tg_separator, state="readonly", 
                                       values=["— — —", "• • •", "==========", "----------", "********", "· · · · ·", "─ ─ ─ ─ ─", "> > > > >", "~ ~ ~ ~ ~"])
        self.separator_combo.grid(row=3, column=1, sticky="w", padx=10, pady=2)

        tg_actions_frame = ttk.Frame(tg_lf_inner, style="Panel.TFrame"); tg_actions_frame.grid(row=4, column=1, sticky="e", pady=(5, 0))
        self.tg_verify_btn = ttk.Button(tg_actions_frame, text="Проверить", command=lambda: self.start_verification_thread('telegram')); self.tg_verify_btn.pack(side="left")
        ttk.Label(tg_actions_frame, textvariable=self.var_tg_verify_status, style="Sub.TLabel", font=("Segoe UI", 10)).pack(side="left", padx=10)
        
        gsheets_lf = CollapsibleFrame(top_panel, text="2. Интеграция с Google Таблицами")
        gsheets_lf.pack(fill="x", expand=True, pady=5)
        gsheets_lf_inner = gsheets_lf.container
        gsheets_lf_inner.grid_columnconfigure(1, weight=1)
        ttk.Checkbutton(gsheets_lf_inner, text="Включить отправку в Google Таблицы", variable=self.var_gsheets_enabled, command=self.toggle_gs_fields).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5))
        ttk.Label(gsheets_lf_inner, text="URL веб-приложения:", style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=2)
        self.e_gsheets_url = ttk.Entry(gsheets_lf_inner, textvariable=self.var_gsheets_url); self.e_gsheets_url.grid(row=1, column=1, sticky="ew", padx=10, pady=2); attach_context_menu(self.e_gsheets_url)
        gs_actions_frame = ttk.Frame(gsheets_lf_inner, style="Panel.TFrame"); gs_actions_frame.grid(row=2, column=1, sticky="e", pady=(5, 0))
        
        self.copy_script_btn = ttk.Button(gs_actions_frame, text="Копировать скрипт для Таблиц", command=self.copy_apps_script)
        self.copy_script_btn.pack(side="left", padx=(0,10))
        self.copy_headers_btn = ttk.Button(gs_actions_frame, text="Копировать заголовки", command=self.copy_headers_for_sheets)
        self.copy_headers_btn.pack(side="left", padx=10)
        self.gs_verify_btn = ttk.Button(gs_actions_frame, text="Проверить", command=lambda: self.start_verification_thread('gsheets')); self.gs_verify_btn.pack(side="left")
        ttk.Label(gs_actions_frame, textvariable=self.var_gs_verify_status, style="Sub.TLabel", font=("Segoe UI", 10)).pack(side="left", padx=10)
        
        appearance_lf = CollapsibleFrame(top_panel, text="3. Внешний вид и доступ")
        appearance_lf.pack(fill="x", expand=True, pady=5)
        app_lf_inner = appearance_lf.container
        app_lf_inner.grid_columnconfigure(1, weight=1)
        ttk.Label(app_lf_inner, text="Заголовок сайта:", style="Sub.TLabel").grid(row=0, column=0, sticky="w", pady=2)
        e_title = ttk.Entry(app_lf_inner, textvariable=self.var_title); e_title.grid(row=0, column=1, sticky="ew", padx=10, pady=2); attach_context_menu(e_title)
        app_lf_inner_mid = ttk.Frame(app_lf_inner, style="Panel.TFrame"); app_lf_inner_mid.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8,0))
        ttk.Label(app_lf_inner_mid, text="Тема:", style="Sub.TLabel").pack(side="left")
        self.combo_theme = ttk.Combobox(app_lf_inner_mid, state="readonly", values=list(RU_THEME_MAP.keys()), textvariable=self.var_site_theme, width=18); self.combo_theme.pack(side="left", padx=(10, 20))
        ttk.Label(app_lf_inner_mid, text="Шрифт:", style="Sub.TLabel").pack(side="left")
        self.combo_font = ttk.Combobox(app_lf_inner_mid, state="readonly", values=list(SITE_FONTS.keys()), textvariable=self.var_site_font, width=18); self.combo_font.pack(side="left", padx=(10, 20))
        ttk.Checkbutton(app_lf_inner_mid, text="Нумерация вопросов", variable=self.var_numbering).pack(side="left", padx=(10,0))
        app_lf_inner_bottom = ttk.Frame(app_lf_inner, style="Panel.TFrame"); app_lf_inner_bottom.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8,0))
        ttk.Label(app_lf_inner_bottom, text="Режим отображения:", style="Sub.TLabel").pack(side="left", anchor='n', pady=4)
        view_mode_frame = ttk.Frame(app_lf_inner_bottom, style="Panel.TFrame"); view_mode_frame.pack(side="left", padx=10)
        self.view_mode_descriptions = { "standard": "Стандартный вид.", "compact": "Уменьшенные отступы.", "contrast": "Более контрастные карточки.", "dividers": "Разделительные линии.", "floating": "'Парящие' карточки.", "outlined": "Поля с контуром.", "minimal": "Максимально упрощенный.", "neumorphic": "Мягкий 'вдавленный'.", "brutalist": "Резкие границы.", }
        self.var_view_mode_desc = tk.StringVar(value=self.view_mode_descriptions["standard"])
        self.combo_view = ttk.Combobox(view_mode_frame, state="readonly", values=list(self.view_mode_descriptions.keys()), textvariable=self.var_view_mode, width=12); self.combo_view.pack(side="top", fill="x"); self.combo_view.bind("<<ComboboxSelected>>", self.update_view_mode_description)
        ttk.Label(view_mode_frame, textvariable=self.var_view_mode_desc, style="Sub.TLabel", wraplength=400, font=("Segoe UI", 11)).pack(side="top", fill="x", pady=(4,0))
        texts_frame = ttk.Frame(app_lf_inner_bottom, style="Panel.TFrame"); texts_frame.pack(side="left", padx=(20, 10), anchor='n')
        ttk.Label(texts_frame, text="Текст кнопки отправки:", style="Sub.TLabel").pack(side="top", anchor='w')
        e_submit = ttk.Entry(texts_frame, textvariable=self.var_submit_text, width=30); e_submit.pack(side="top", anchor='w', pady=(0, 5)); attach_context_menu(e_submit)
        ttk.Label(texts_frame, text="Текст успешной отправки:", style="Sub.TLabel").pack(side="top", anchor='w')
        e_success = ttk.Entry(texts_frame, textvariable=self.var_success_message, width=30); e_success.pack(side="top", anchor='w'); attach_context_menu(e_success)
        
        security_lf = ttk.LabelFrame(app_lf_inner, text="Безопасность и ограничения")
        security_lf.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        sec_lf_inner = ttk.Frame(security_lf, style="Panel.TFrame"); sec_lf_inner.pack(fill="x", expand=True, padx=10, pady=10)
        self.chk_password = ttk.Checkbutton(sec_lf_inner, text="Установить пароль на сайт", variable=self.var_password_enabled, command=self.toggle_password_field); self.chk_password.pack(anchor="w")
        self.e_password = ttk.Entry(sec_lf_inner, textvariable=self.var_password, show="*", width=25); self.e_password.pack(anchor="w", pady=(2, 8), padx=(20,0)); attach_context_menu(self.e_password)
        self.chk_limit_submission = ttk.Checkbutton(sec_lf_inner, text="Ограничить одной отправкой (по браузеру)", variable=self.var_limit_one_submission, command=self.toggle_one_submission_message_field); self.chk_limit_submission.pack(anchor="w", pady=(8,0))
        self.e_one_submission_message = ttk.Entry(sec_lf_inner, textvariable=self.var_one_submission_message, width=50); self.e_one_submission_message.pack(anchor="w", pady=2, padx=(20,0)); attach_context_menu(self.e_one_submission_message)

        self.e_bot.bind("<FocusOut>", self.check_token_validity); self.e_chat.bind("<FocusOut>", self.check_chat_id_validity)
        self.toggle_tg_fields(); self.toggle_gs_fields(); self.toggle_password_field(); self.toggle_one_submission_message_field()

        actions_lf = ttk.LabelFrame(bottom_panel, text="4. Действия с анкетой"); actions_lf.pack(fill="x", expand=True, pady=5)
        act_lf_inner = ttk.Frame(actions_lf, style="Panel.TFrame"); act_lf_inner.pack(fill="x", expand=True, padx=10, pady=10)
        ttk.Button(act_lf_inner, text="Добавить вопрос", command=self.add_question, style="Action.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(act_lf_inner, text="Очистить всё", command=self.new_project, style="Action.TButton").pack(side="left", padx=6)
        self.lbl_counter = ttk.Label(act_lf_inner, text="Вопросов: 0", style="Sub.TLabel"); self.lbl_counter.pack(side="right", padx=12)

        proj = ttk.Frame(bottom_panel, style="Panel.TFrame"); proj.pack(fill="x", pady=(5,0))
        ttk.Button(proj, text="Сгенерировать и сохранить HTML-файл", command=self.generate_single_index).pack(side="right")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # ... (остальные методы класса App, они остаются без изменений) ...
    
if __name__ == "__main__":
    app = App()
    app.mainloop()