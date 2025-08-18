import os
import sys
import json
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import time
import uuid  # Для уникальных ID вопросов
import re
import threading
import urllib.request
import urllib.error
import base64
import ssl # Импортируем ssl для обхода проверки сертификатов

APP_TITLE = "Генератор анкет (v1.0)"
APP_VERSION = "1.0"
MAX_QUESTIONS = 300
CHAR_LIMIT = 1500

def get_data_dir():
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

SITE_THEMES = {
    "dark":       {"bg":"#0B1220","text":"#E5E7EB","primary":"#7C3AED","card_border":"rgba(255,255,255,0.1)","card_bg_alpha":0.06,"shadow":"0 10px 30px rgba(0,0,0,0.35)","field_border":"#263041","field_bg":"#0f172a"},
    "light":      {"bg":"#F8FAFC","text":"#0F172A","primary":"#4F46E5","card_border":"#e5e7eb","card_bg_alpha":1,"shadow":"0 10px 30px rgba(0,0,0,0.06)","field_border":"#cbd5e1","field_bg":"#ffffff"},
    "retrowave":  {"bg":"#0D0033","text":"#F8E7FF","primary":"#FF2E88","card_border":"rgba(255,46,136,0.35)","card_bg_alpha":0.12,"shadow":"0 10px 40px rgba(255,46,136,0.25)","field_border":"#4C1D95","field_bg":"#12023F"},
    "nord":       {"bg":"#0B1220","text":"#E5EEF5","primary":"#88C0D0","card_border":"rgba(136,192,208,0.25)","card_bg_alpha":0.08,"shadow":"0 10px 30px rgba(0,0,0,0.35)","field_border":"#2E4057","field_bg":"#0f172a"},
    "dracula":    {"bg":"#1E1F29","text":"#F8F8F2","primary":"#BD93F9","card_border":"rgba(189,147,249,0.25)","card_bg_alpha":0.08,"shadow":"0 10px 30px rgba(0,0,0,0.35)","field_border":"#3B3F51","field_bg":"#2B2D3A"},
    "ocean":      {"bg":"#071A2C","text":"#E6F0FF","primary":"#3BA3FF","card_border":"rgba(59,163,255,0.25)","card_bg_alpha":0.08,"shadow":"0 10px 30px rgba(0,0,0,0.35)","field_border":"#254563","field_bg":"#0f172a"},
    "forest":     {"bg":"#0C1611","text":"#E6FFEF","primary":"#22C55E","card_border":"rgba(34,197,94,0.25)","card_bg_alpha":0.08,"shadow":"0 10px 30px rgba(0,0,0,0.35)","field_border":"#214C34","field_bg":"#0f172a"},
    "sunset":     {"bg":"#0f0c29","text":"#e0e0e0","primary":"#ff8c00","card_border":"rgba(255, 140, 0, 0.25)","card_bg_alpha":0.08,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#4a2f2c","field_bg":"#1a1532"},
    "minty":      {"bg":"#f0fdf4","text":"#14532d","primary":"#10b981","card_border":"#a7f3d0","card_bg_alpha":1,"shadow":"0 8px 25px rgba(0,0,0,0.05)","field_border":"#d1fae5","field_bg":"#ffffff"},
    "midnight":   {"bg":"#020617","text":"#e2e8f0","primary":"#06b6d4","card_border":"rgba(6, 182, 212, 0.2)","card_bg_alpha":0.06,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#1e293b","field_bg":"#0f172a"},
    "rose_quartz":{"bg":"#fdf2f8","text":"#831843","primary":"#db2777","card_border":"#fbcfe8","card_bg_alpha":1,"shadow":"0 8px 25px rgba(0,0,0,0.05)","field_border":"#fce7f3","field_bg":"#ffffff"},
    "coffee":     {"bg":"#211715","text":"#ded1c1","primary":"#c4a381","card_border":"rgba(196, 163, 129, 0.2)","card_bg_alpha":0.09,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#43302b","field_bg":"#2d211e"},
    "solarized":  {"bg":"#002b36","text":"#839496","primary":"#268bd2","card_border":"rgba(38, 139, 210, 0.25)","card_bg_alpha":0.06,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#073642","field_bg":"#00252e"},
    "gruvbox":    {"bg":"#282828","text":"#ebdbb2","primary":"#fabd2f","card_border":"rgba(250, 189, 47, 0.2)","card_bg_alpha":0.05,"shadow":"0 10px 30px rgba(0,0,0,0.45)","field_border":"#504945","field_bg":"#3c3836"},
    "sandstone":  {"bg":"#F1E9DA","text":"#57524A","primary":"#B5651D","card_border":"#D4C2A7","card_bg_alpha":1,"shadow":"0 8px 25px rgba(0,0,0,0.07)","field_border":"#E0D5C1","field_bg":"#ffffff"},
    "cyberpunk":  {"bg":"#000000","text":"#00ff00","primary":"#ff00ff","card_border":"rgba(255, 0, 255, 0.3)","card_bg_alpha":0.08,"shadow":"0 0 20px rgba(255, 0, 255, 0.4)","field_border":"#330033","field_bg":"#100010"},
    "tokyo_night":{"bg":"#1a1b26","text":"#a9b1d6","primary":"#7aa2f7","card_border":"rgba(122, 162, 247, 0.2)","card_bg_alpha":0.07,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#414868","field_bg":"#24283b"},
    "emerald":    {"bg":"#062029","text":"#d1fae5","primary":"#34d399","card_border":"rgba(52, 211, 153, 0.25)","card_bg_alpha":0.08,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#044e3a","field_bg":"#052e31"},
    "amethyst":   {"bg":"#2a004f","text":"#f3e8ff","primary":"#c084fc","card_border":"rgba(192, 132, 252, 0.3)","card_bg_alpha":0.1,"shadow":"0 10px 30px rgba(0,0,0,0.45)","field_border":"#5b21b6","field_bg":"#3b0764"},
    "slate":      {"bg":"#f8fafc","text":"#0f172a","primary":"#475569","card_border":"#e2e8f0","card_bg_alpha":1,"shadow":"0 8px 25px rgba(0,0,0,0.06)","field_border":"#cbd5e1","field_bg":"#ffffff"},
    "crimson":    {"bg":"#310000","text":"#fee2e2","primary":"#f87171","card_border":"rgba(248, 113, 113, 0.25)","card_bg_alpha":0.09,"shadow":"0 10px 30px rgba(0,0,0,0.5)","field_border":"#7f1d1d","field_bg":"#450a0a"},
    "latte":      {"bg":"#eff1f5","text":"#4c4f69","primary":"#1e66f5","card_border":"#ccd0da","card_bg_alpha":1,"shadow":"0 8px 25px rgba(0,0,0,0.07)","field_border":"#bcc0cc","field_bg":"#ffffff"},
    "monokai":    {"bg":"#272822","text":"#f8f8f2","primary":"#a6e22e","card_border":"rgba(166, 226, 46, 0.2)","card_bg_alpha":0.05,"shadow":"0 10px 30px rgba(0,0,0,0.45)","field_border":"#75715e","field_bg":"#3d3e36"},
    "sakura":     {"bg":"#fef4f4","text":"#594949","primary":"#fe5d9f","card_border":"#fde2e2","card_bg_alpha":1,"shadow":"0 8px 25px rgba(0,0,0,0.06)","field_border":"#ffe4e4","field_bg":"#ffffff"},
    "graphite":   {"bg":"#1a1a1a","text":"#f0f0f0","primary":"#4c5fdc","card_border":"rgba(255,255,255,0.1)","card_bg_alpha":0.05,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#333333","field_bg":"#222222"},
    "mandarin":   {"bg":"#291a0d","text":"#ffe8d6","primary":"#f7941d","card_border":"rgba(247,148,29,0.2)","card_bg_alpha":0.09,"shadow":"0 10px 30px rgba(0,0,0,0.4)","field_border":"#5c3a0e","field_bg":"#3d280e"},
    "fuflick":    {"bg":"#f5f3ff","text":"#3c3166","primary":"#7c3aed","card_border":"#e4d9ff","card_bg_alpha":1,"shadow":"0 8px 25px rgba(0,0,0,0.06)","field_border":"#eaddff","field_bg":"#ffffff"},
}
SITE_THEME_MAP = {
    "dark": "Темная", "light": "Светлая", "retrowave": "Ретровейв", "nord": "Норд",
    "dracula": "Дракула", "ocean": "Океан", "forest": "Лес", "sunset": "Закат",
    "minty": "Мятная", "midnight": "Полночь", "rose_quartz": "Розовый кварц",
    "coffee": "Кофе", "solarized": "Солярис", "gruvbox": "Gruvbox",
    "sandstone": "Песчаник", "cyberpunk": "Киберпанк", "tokyo_night": "Ночной Токио",
    "emerald": "Изумруд", "amethyst": "Аметист", "slate": "Сланец",
    "crimson": "Багровый", "latte": "Латте", "monokai": "Monokai",
    "sakura": "Сакура", "graphite": "Графит", "mandarin": "Дерзкий мандарин",
    "fuflick": "Весёлый фуфлик"
}
RU_THEME_MAP = {v: k for k, v in SITE_THEME_MAP.items()}
SITE_FONTS = {
    "System UI": "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif",
    "Roboto": "'Roboto', sans-serif",
    "Inter": "'Inter', sans-serif",
    "Montserrat": "'Montserrat', sans-serif",
    "Playfair Display": "'Playfair Display', serif",
    "Source Code Pro": "'Source Code Pro', monospace",
    "Lobster": "'Lobster', cursive",
    "Georgia (serif)": "Georgia, 'Times New Roman', serif",
    "Verdana (sans-serif)": "Verdana, Geneva, Tahoma, sans-serif",
    "Courier New (monospace)": "'Courier New', Courier, monospace",
}

def bind_paste_hotkeys(widget):
    def do_paste(event=None):
        try:
            widget.event_generate("<<Paste>>")
        except Exception:
            try:
                data = widget.clipboard_get()
                widget.insert(tk.INSERT, data)
            except Exception:
                pass
        return "break"
    widget.bind("<Control-v>", do_paste)
    widget.bind("<Control-V>", do_paste)
    widget.bind("<Shift-Insert>", do_paste)

def attach_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0, bg="#0B1118", fg="#F6F9FE",
                   activebackground="#2E4470", activeforeground="#FFFFFF",
                   borderwidth=0)
    menu.add_command(label="Вставить из буфера", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Выделить всё", command=lambda: widget.event_generate("<<SelectAll>>"))
    def show_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    widget.bind("<Button-3>", show_menu)
    bind_paste_hotkeys(widget)
    return menu

def apply_ui_theme(root, theme_dict):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.ACC_COLOR = theme_dict['ACC']
    root.ENTRY_BG_COLOR = theme_dict['ENTRY_BG']
    root.ENTRY_TXT_COLOR = theme_dict['ENTRY_TXT']
    root.SELECTION_FG_COLOR = theme_dict['SELECTION_FG']

    BG = theme_dict['BG']
    PANEL = theme_dict['PANEL']
    CARD = theme_dict['CARD']
    FG = theme_dict['FG']
    SUB = theme_dict.get('SUB', FG)
    ACC = theme_dict['ACC']
    ENTRY_BG = theme_dict['ENTRY_BG']
    ENTRY_TXT = theme_dict['ENTRY_TXT']
    BORDER = theme_dict['BORDER']
    ACC_HOVER = theme_dict['ACC_HOVER']
    SELECTION_FG = theme_dict['SELECTION_FG']
    INVALID_BORDER = theme_dict['INVALID_BORDER']
    HOVER_PANEL = theme_dict.get('HOVER_PANEL', PANEL)
    HOVER_CARD = theme_dict.get('HOVER_CARD', CARD)

    base_font = ("Segoe UI", 14)
    root.option_add("*Font", base_font)
    root.option_add("*Entry.insertBackground", ENTRY_TXT)
    root.option_add("*Text.insertBackground", ENTRY_TXT)
    root.option_add("*TEntry*selectBackground", ENTRY_BG)
    root.option_add("*Text*selectBackground", ENTRY_BG)
    root.option_add("*TEntry*selectForeground", SELECTION_FG)
    root.option_add("*Text*selectForeground", SELECTION_FG)
    
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
        
        security_lf = ttk.LabelFrame(app_lf_inner, text="Безопасность и ограничения") # ИСПРАВЛЕНИЕ: Убран style
        security_lf.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        sec_lf_inner = ttk.Frame(security_lf, style="Panel.TFrame"); sec_lf_inner.pack(fill="x", expand=True, padx=10, pady=10)
        self.chk_password = ttk.Checkbutton(sec_lf_inner, text="Установить пароль на сайт", variable=self.var_password_enabled, command=self.toggle_password_field); self.chk_password.pack(anchor="w")
        self.e_password = ttk.Entry(sec_lf_inner, textvariable=self.var_password, show="*", width=25); self.e_password.pack(anchor="w", pady=(2, 8), padx=(20,0)); attach_context_menu(self.e_password)
        self.chk_limit_submission = ttk.Checkbutton(sec_lf_inner, text="Ограничить одной отправкой (по браузеру)", variable=self.var_limit_one_submission, command=self.toggle_one_submission_message_field); self.chk_limit_submission.pack(anchor="w", pady=(8,0))
        self.e_one_submission_message = ttk.Entry(sec_lf_inner, textvariable=self.var_one_submission_message, width=50); self.e_one_submission_message.pack(anchor="w", pady=2, padx=(20,0)); attach_context_menu(self.e_one_submission_message)

        self.e_bot.bind("<FocusOut>", self.check_token_validity); self.e_chat.bind("<FocusOut>", self.check_chat_id_validity)
        self.toggle_tg_fields(); self.toggle_gs_fields(); self.toggle_password_field(); self.toggle_one_submission_message_field()

        actions_lf = ttk.LabelFrame(bottom_panel, text="4. Действия с анкетой") # ИСПРАВЛЕНИЕ: Убран style
        actions_lf.pack(fill="x", expand=True, pady=5)
        act_lf_inner = ttk.Frame(actions_lf, style="Panel.TFrame"); act_lf_inner.pack(fill="x", expand=True, padx=10, pady=10)
        ttk.Button(act_lf_inner, text="Добавить вопрос", command=self.add_question, style="Action.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(act_lf_inner, text="Очистить всё", command=self.new_project, style="Action.TButton").pack(side="left", padx=6)
        self.lbl_counter = ttk.Label(act_lf_inner, text="Вопросов: 0", style="Sub.TLabel"); self.lbl_counter.pack(side="right", padx=12)

        proj = ttk.Frame(bottom_panel, style="Panel.TFrame"); proj.pack(fill="x", pady=(5,0))
        ttk.Button(proj, text="Сгенерировать и сохранить HTML-файл", command=self.generate_single_index).pack(side="right")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def verify_connection(self, integration_type):
        if integration_type == 'gsheets':
            url = self.var_gsheets_url.get().strip()
            if not url.startswith("https://script.google.com/macros/s/"):
                self.after(0, self.show_verification_result, False, "URL веб-приложения Apps Script имеет неверный формат.")
                self.after(0, self.reset_verification_ui, integration_type)
                return
            
            payload = { 'action': 'verify' }
            data = json.dumps(payload).encode('utf-8')
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        else: # Telegram
            token = self.var_bot.get().strip()
            chat_id = self.var_chat.get().strip()
            if not re.match(r"^\d+:[A-Za-z0-9_-]{35}$", token) or not re.match(r"^-?\d+$|^@[\w_]+$", chat_id):
                self.after(0, self.show_verification_result, False, "Неверный формат токена или chat_id.")
                self.after(0, self.reset_verification_ui, integration_type)
                return
            api_url = f"https://api.telegram.org/bot{token}/sendMessage"
            test_message = "✅ Тестовое сообщение от Генератора анкет.\nПодключение к Telegram API успешно!"
            payload = { 'chat_id': chat_id, 'text': test_message }
            data = json.dumps(payload).encode('utf-8')
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(api_url, data=data, headers=headers, method='POST')
        
        context = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(req, context=context, timeout=10) as response:
                response_body = response.read().decode('utf-8')
                json_response = json.loads(response_body)
                
                if json_response.get('ok') or json_response.get('result') == 'success':
                    success_msg = "Подключение к Google Script успешно!" if integration_type == 'gsheets' else "Тестовое сообщение отправлено в Telegram!"
                    self.after(0, self.show_verification_result, True, success_msg)
                else:
                    error_desc = json_response.get('description', json_response.get('message', 'Неизвестная ошибка'))
                    self.after(0, self.show_verification_result, False, f"Ошибка API: {error_desc}")
        
        except urllib.error.HTTPError as e:
            error_details = e.read().decode()
            try: error_desc = json.loads(error_details).get('description', 'Нет деталей')
            except json.JSONDecodeError: error_desc = "Не удалось прочитать ответ сервера."
            self.after(0, self.show_verification_result, False, f"Ошибка HTTP {e.code}: {error_desc}")
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLCertVerificationError):
                self.after(0, self.show_verification_result, False, f"Ошибка сертификата SSL: {e.reason}.\nЭто проблема окружения, а не кода. Попробуйте снова.")
            else:
                self.after(0, self.show_verification_result, False, f"Ошибка сети: {e.reason}. Проверьте подключение к интернету.")
        except Exception as e:
             self.after(0, self.show_verification_result, False, f"Произошла непредвиденная ошибка: {e}")
        finally:
            self.after(0, self.reset_verification_ui, integration_type)
            
    def build_preview(self):
        container = ttk.Frame(self.preview_tab, style="Panel.TFrame")
        container.pack(fill="both", expand=True)
        bar = ttk.Frame(container, style="Panel.TFrame")
        bar.pack(fill="x", pady=(0,10))
        ttk.Button(bar, text="Обновить предпросмотр (F5)", command=self.refresh_preview).pack(side="left")
        ttk.Button(bar, text="Открыть в браузере", command=self.open_in_browser).pack(side="left", padx=10)
        self.preview_text = tk.Text(container, wrap="word", bg=self.ENTRY_BG_COLOR, fg=self.ENTRY_TXT_COLOR, insertbackground=self.ENTRY_TXT_COLOR, relief="solid", borderwidth=1, font=("Consolas", 11), selectbackground=self.ENTRY_BG_COLOR, selectforeground=self.SELECTION_FG_COLOR)
        self.preview_text.pack(fill="both", expand=True)
        attach_context_menu(self.preview_text)
        self.preview_text.insert("1.0", "Нажмите «Обновить предпросмотр», чтобы увидеть здесь HTML-код страницы.")
    
    def copy_apps_script(self):
        self.clipboard_clear()
        self.clipboard_append(self.APPS_SCRIPT_CODE)
        messagebox.showinfo("Скопировано", "Код Google Apps Script скопирован в буфер обмена.")
        
    def copy_headers_for_sheets(self):
        questions = self.get_all_questions()
        if not questions:
            messagebox.showinfo("Нет вопросов", "Сначала добавьте вопросы в анкету.")
            return
        
        headers = ["Дата ответа"] + [q.var_label.get().strip() for q in questions]
        clipboard_text = "\t".join(headers)
        
        self.clipboard_clear()
        self.clipboard_append(clipboard_text)
        messagebox.showinfo("Скопировано", "Заголовки для Google Таблицы скопированы в буфер обмена.\n\nВставьте их в первую строку вашей таблицы (в ячейку A1).")

    def toggle_gs_fields(self):
        state = "normal" if self.var_gsheets_enabled.get() else "disabled"
        if hasattr(self, 'e_gsheets_url'):
            for widget in [self.e_gsheets_url, self.gs_verify_btn, self.copy_headers_btn, self.copy_script_btn]:
                widget.config(state=state)
            
    def toggle_tg_fields(self):
        state = "normal" if self.var_telegram_enabled.get() else "disabled"
        if hasattr(self, 'e_bot'):
            self.e_bot.config(state=state)
            self.e_chat.config(state=state)
            self.tg_verify_btn.config(state=state)
            self.separator_combo.config(state=state)
            
    def toggle_password_field(self):
        state = "normal" if self.var_password_enabled.get() else "disabled"
        if hasattr(self, 'e_password'):
            self.e_password.config(state=state)
            
    def toggle_one_submission_message_field(self):
        state = "normal" if self.var_limit_one_submission.get() else "disabled"
        if hasattr(self, 'e_one_submission_message'):
            self.e_one_submission_message.config(state=state)

    def check_token_validity(self, event=None):
        token = self.var_bot.get().strip()
        if token and not re.match(r"^\d+:[A-Za-z0-9_-]{35}$", token):
            self.e_bot.configure(style="Invalid.TEntry")
        else:
            self.e_bot.configure(style="TEntry")

    def check_chat_id_validity(self, event=None):
        chat_id = self.var_chat.get().strip()
        if chat_id and not re.match(r"^-?\d+$|^@[\w_]+$", chat_id):
            self.e_chat.configure(style="Invalid.TEntry")
        else:
            self.e_chat.configure(style="TEntry")
    
    def start_verification_thread(self, integration_type):
        if integration_type == 'telegram':
            self.tg_verify_btn.config(state="disabled")
            self.var_tg_verify_status.set("Проверка...")
        elif integration_type == 'gsheets':
            self.gs_verify_btn.config(state="disabled")
            self.var_gs_verify_status.set("Проверка...")
            
        thread = threading.Thread(target=self.verify_connection, args=(integration_type,), daemon=True)
        thread.start()

    def show_verification_result(self, success, message):
        if success:
            messagebox.showinfo("Проверка успешна", message)
        else:
            messagebox.showerror("Ошибка проверки", message)

    def reset_verification_ui(self, integration_type):
        if integration_type == 'telegram':
            self.var_tg_verify_status.set("")
            self.tg_verify_btn.config(state="normal")
        elif integration_type == 'gsheets':
            self.var_gs_verify_status.set("")
            self.gs_verify_btn.config(state="normal")
        
    def focus_first_entry(self):
        try:
            lf1 = self.canvas.winfo_children()[0].winfo_children()[0].winfo_children()[0]
            inner_frame = lf1.container
            first_entry = inner_frame.winfo_children()[1]
            if isinstance(first_entry, ttk.Entry): first_entry.focus_set()
        except Exception:
            pass

    def get_all_questions(self):
        return self.question_rows
    
    def get_question_row_by_id(self, id):
        for q in self.question_rows:
            if q.id == id:
                return q
        return None

    def update_conditional_info_labels(self):
        self.update_idletasks()
        all_questions = self.get_all_questions()
        for q_row in all_questions:
            if q_row.condition:
                parent_id = q_row.condition.get("parent_id")
                parent_row = self.get_question_row_by_id(parent_id)
                if parent_row:
                    parent_label = parent_row.var_label.get().strip()
                    if len(parent_label) > 20: parent_label = parent_label[:18] + "..."
                    
                    trigger_values = q_row.condition.get("trigger_values", [])
                    triggers_text = ", ".join(trigger_values)
                    if len(triggers_text) > 30:
                        triggers_text = triggers_text[:28] + "..."
                    
                    info_text = f"(Зависит от: «{parent_label}» = {triggers_text})"
                    q_row.conditional_info_label.config(text=info_text)
                else:
                    q_row.condition = None
                    q_row.conditional_info_label.config(text="")
            else:
                q_row.conditional_info_label.config(text="")

    def open_dependent_question_dialog(self, parent_question_row):
        parent_options = parent_question_row.get_options()
        if not parent_options:
            messagebox.showwarning("Нет вариантов", "Сначала добавьте варианты ответа в родительский вопрос.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Создать зависимый вопрос")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text=f"Показывать новый вопрос, когда ответ на", wraplength=400).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(main_frame, text=f"«{parent_question_row.var_label.get()}»", font=("Segoe UI", 12, "bold"), wraplength=400).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0,10))

        ttk.Label(main_frame, text="равен одному из:").grid(row=2, column=0, sticky="nw", pady=5)
        
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=1, sticky="w")
        
        trigger_vars = {}
        for option in parent_options:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(options_frame, text=option, variable=var)
            chk.pack(anchor="w")
            trigger_vars[option] = var

        ttk.Label(main_frame, text="Текст нового вопроса:").grid(row=3, column=0, sticky="w")
        var_new_q_label = tk.StringVar()
        entry_new_q = ttk.Entry(main_frame, textvariable=var_new_q_label, width=32)
        entry_new_q.grid(row=3, column=1, sticky="ew", pady=5)
        entry_new_q.focus_set()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(15,0))
        
        def on_create():
            new_label = var_new_q_label.get().strip()
            trigger_values = [opt for opt, var in trigger_vars.items() if var.get()]

            if not new_label or not trigger_values:
                messagebox.showerror("Ошибка", "Заполните текст вопроса и выберите хотя бы один вариант-триггер.", parent=dialog)
                return
            
            condition_data = {"parent_id": parent_question_row.id, "trigger_values": trigger_values}
            
            parent_index = parent_question_row.index
            self.add_question({"label": new_label, "condition": condition_data}, insert_after_index=parent_index)
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Создать", command=on_create).pack(side="right")
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side="right", padx=10)

    def add_question(self, data=None, insert_after_index=None):
        new_index = len(self.question_rows)
        if insert_after_index is not None:
            new_index = insert_after_index + 1

        row = QuestionRow(self.content_frame, self, new_index, self.remove_question, focus_callback=self.smooth_scroll_to)
        
        if insert_after_index is not None:
            self.question_rows.insert(new_index, row)
            self.reindex_questions() 
        else:
            row.grid(row=new_index, column=0, sticky="ew", pady=10)
            self.question_rows.append(row)
        
        if data:
            self.apply_question_data(row, data)

        if insert_after_index is None:
            self.update_counts_label()
        
        self.after(50, row.focus_label)
        self.set_dirty_status(True)

    def reindex_questions(self):
        for i, row in enumerate(self.question_rows):
            row.index = i
            row.q_num_label.config(text=f"Вопрос {i+1}")
            row.frame.grid(row=i, column=0, sticky="ew", pady=10)
        self.update_counts_label()
        self.update_conditional_info_labels()
        self.set_dirty_status(True)

    def remove_question(self, row):
        self.question_rows.remove(row)
        self.reindex_questions()
        
    def gather_config(self):
        bot = self.var_bot.get().strip()
        chat = self.var_chat.get().strip()
        title = self.var_title.get().strip()
        submit_text = self.var_submit_text.get().strip() or "Отправить"
        success_message = self.var_success_message.get().strip() or "Ответ успешно отправлен. Спасибо!"
        one_submission_message = self.var_one_submission_message.get().strip() or "Спасибо! Ваш ответ был получен."
        tg_separator = self.var_tg_separator.get()

        tg_enabled = self.var_telegram_enabled.get()
        gs_enabled = self.var_gsheets_enabled.get()
        gs_url = self.var_gsheets_url.get().strip()
        
        if not tg_enabled and not gs_enabled:
            raise ValueError("Необходимо включить хотя бы один способ отправки: Telegram или Google Таблицы.")
        
        if tg_enabled:
            if not bot or not chat: raise ValueError("Для отправки в Telegram укажите токен бота и chat_id.")
            if not re.match(r"^\d+:[A-Za-z0-9_-]{35}$", bot):
                self.check_token_validity()
                raise ValueError("Неверный формат токена бота.")
            if not re.match(r"^-?\d+$|^@[\w_]+$", chat):
                self.check_chat_id_validity()
                raise ValueError("Неверный формат chat_id.")
        
        if gs_enabled:
            if not gs_url.startswith("https://script.google.com/macros/s/"):
                raise ValueError("URL веб-приложения Apps Script имеет неверный формат.")
        
        if not title: raise ValueError("Укажите заголовок сайта.")

        password_enabled = self.var_password_enabled.get()
        password = self.var_password.get()
        if password_enabled and not password:
            raise ValueError("Пароль включен, но поле пароля пустое.")
            
        ru_theme_name = self.var_site_theme.get()
        en_theme_key = RU_THEME_MAP.get(ru_theme_name, "dark")

        cfg = {
            "bot_token": bot, "chat_id": chat, "title": title, 
            "submit_text": submit_text, "success_message": success_message,
            "site_theme": en_theme_key, "site_font": self.var_site_font.get(), 
            "numbering": bool(self.var_numbering.get()), "view_mode": self.var_view_mode.get(), 
            "telegram_enabled": tg_enabled, "gsheets_enabled": gs_enabled, "gsheets_url": gs_url, 
            "password_enabled": password_enabled, "password": password,
            "limit_one_submission": self.var_limit_one_submission.get(),
            "one_submission_message": one_submission_message,
            "tg_separator": tg_separator
        }
        
        questions = []
        for r in self.question_rows:
            d = r.to_dict()
            if not d["label"]: raise ValueError("У вопроса отсутствует текст.")
            if d["type"] == 2 and not d.get("options"): raise ValueError(f"У вопроса «{d['label']}» нет вариантов.")
            questions.append(d)
        
        if not questions: raise ValueError("Добавьте хотя бы один вопрос.")
        
        cfg.update({"mode": "single", "questions": questions})
        return cfg

    def apply_question_data(self, q_row, data):
        q_row.id = data.get("id", str(uuid.uuid4()))
        t = data.get("type", 1)
        q_row.var_label.set(data.get("label", ""))
        q_row.var_required.set(bool(data.get("required", False)))
        q_row.var_limit_chars.set(bool(data.get("limit_chars", False)))
        
        condition = data.get("condition")
        if condition and "trigger_value" in condition and "trigger_values" not in condition:
            condition["trigger_values"] = [condition.pop("trigger_value")]
        q_row.condition = condition


        for w in q_row.option_widgets[:]: q_row.remove_option_field(w)
        
        if t == 2:
            q_row.var_type.set("Выбор варианта")
            for option_text in data.get("options", []):
                q_row.add_option_field(option_text)
        else:
            q_row.var_type.set("Свободный ответ")

    def apply_config(self, cfg):
        self.var_bot.set(cfg.get("bot_token",""))
        self.var_chat.set(cfg.get("chat_id",""))
        self.var_title.set(cfg.get("title",""))
        self.var_submit_text.set(cfg.get("submit_text", "Отправить"))
        self.var_success_message.set(cfg.get("success_message", "Ответ успешно отправлен. Спасибо!"))
        
        en_theme_key = cfg.get("site_theme", "dark")
        ru_theme_name = SITE_THEME_MAP.get(en_theme_key, "Темная")
        self.var_site_theme.set(ru_theme_name)
        
        self.var_site_font.set(cfg.get("site_font", "System UI") if cfg.get("site_font") in SITE_FONTS else "System UI")
        self.var_numbering.set(bool(cfg.get("numbering", True)))
        self.var_view_mode.set(cfg.get("view_mode","standard"))
        self.var_telegram_enabled.set(cfg.get("telegram_enabled", True))
        self.var_gsheets_enabled.set(cfg.get("gsheets_enabled", False))
        self.var_gsheets_url.set(cfg.get("gsheets_url", ""))
        self.var_password_enabled.set(cfg.get("password_enabled", False))
        self.var_password.set(cfg.get("password", ""))
        self.var_limit_one_submission.set(cfg.get("limit_one_submission", False))
        self.var_one_submission_message.set(cfg.get("one_submission_message", "Спасибо! Ваш ответ был получен. Отправка повторных анкет не допускается."))
        self.var_tg_separator.set(cfg.get("tg_separator", "— — —"))
        self.update_view_mode_description()
        
        for w in self.content_frame.winfo_children(): w.destroy()
        self.question_rows = []
        
        questions_data = cfg.get("questions", [])
        if cfg.get("mode") == "blocks":
            questions_data = [q for b in cfg.get("blocks", []) for q in b.get("questions", [])]

        for q_data in questions_data:
            self.add_question(q_data)
        
        self.check_token_validity(); self.check_chat_id_validity()
        self.toggle_tg_fields(); self.toggle_gs_fields(); self.toggle_password_field(); self.toggle_one_submission_message_field()
        self.update_idletasks(); self.update_conditional_info_labels(); self.update_counts_label()
        self.set_dirty_status(False)

    def new_project(self, confirm=True):
        if confirm and self.dirty and not messagebox.askyesno("Новый проект", "Очистить текущий несохранённый проект?"): return
        self.var_bot.set(""); self.var_chat.set(""); self.var_title.set("")
        self.var_submit_text.set("Отправить")
        self.var_success_message.set("Ответ успешно отправлен. Спасибо!")
        self.var_site_theme.set("Темная"); self.var_numbering.set(True); self.var_view_mode.set("standard"); self.var_site_font.set("System UI")
        self.var_telegram_enabled.set(True)
        self.var_gsheets_enabled.set(False); self.var_gsheets_url.set("")
        self.var_password_enabled.set(False); self.var_password.set("")
        self.var_limit_one_submission.set(False)
        self.var_one_submission_message.set("Спасибо! Ваш ответ был получен. Отправка повторных анкет не допускается.")
        self.var_tg_separator.set("— — —")
        self.update_view_mode_description()
        
        for w in self.content_frame.winfo_children(): w.destroy()
        self.question_rows, self.current_file = [], None
        self.update_counts_label(); self.set_dirty_status(False)
        self.check_token_validity(); self.check_chat_id_validity()
        self.toggle_tg_fields(); self.toggle_gs_fields(); self.toggle_password_field(); self.toggle_one_submission_message_field()

    def open_project(self):
        if self.dirty and not messagebox.askyesno("Открыть", "Есть несохранённые изменения. Продолжить без сохранения?"): return
        path = filedialog.askopenfilename(filetypes=[("JSON анкеты", "*.json")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f: self.apply_config(json.load(f))
            self.current_file = path; self.set_dirty_status(False)
        except Exception as e: messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def save_project(self):
        if not self.current_file: return self.save_project_as()
        try:
            cfg = self.gather_config()
            with open(self.current_file, "w", encoding="utf-8") as f: json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.set_dirty_status(False); messagebox.showinfo("OK", "Проект сохранён.")
        except Exception as e: messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def save_project_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON анкеты","*.json")])
        if not path: return
        try:
            cfg = self.gather_config()
            with open(path, "w", encoding="utf-8") as f: json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.current_file = path; self.set_dirty_status(False); messagebox.showinfo("OK", "Проект сохранён как новый файл.")
        except Exception as e: messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def update_counts_label(self):
        total = len(self.question_rows)
        self.lbl_counter.config(text=f"Вопросов: {total}")

    def smooth_scroll_to(self, widget):
        self.after(50, lambda: self.canvas.yview_moveto(1.0))

    def resolve_site_theme(self, cfg):
        return SITE_THEMES.get(cfg.get("site_theme", "dark"), SITE_THEMES["dark"])

    def show_welcome_message_if_needed(self):
        show = True
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if config.get("show_welcome_message") is False:
                        show = False
        except Exception:
            pass 

        if show:
            self.create_welcome_dialog()
        else:
            self.new_project(confirm=False)

    def create_welcome_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Добро пожаловать!")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        main_frame = ttk.Frame(dialog, style="Panel.TFrame", padding=25)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Спасибо за пользование программой!", style="Sub.TLabel", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
        
        text_frame = ttk.Frame(main_frame, style="Panel.TFrame")
        text_frame.pack(pady=5)
        ttk.Label(text_frame, text="Она создана для портфолио, связь со мной в Telegram:", style="Sub.TLabel").pack(side="left")
        link = ttk.Label(text_frame, text="@DV_Lub97", style="Sub.TLabel", foreground=self.ACC_COLOR, cursor="hand2")
        link.pack(side="left", padx=5)
        link.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://t.me/DV_Lub97"))

        ttk.Label(main_frame, text="Обновление и поддержка — по мере моих сил.\nБуду благодарен за финансовую поддержку проекта.", style="Sub.TLabel", justify="center").pack(pady=5)
        
        var_dont_show = tk.BooleanVar()
        
        def on_close():
            if var_dont_show.get():
                try:
                    with open(self.config_file, 'w') as f:
                        json.dump({"show_welcome_message": False}, f)
                except Exception as e:
                    print(f"Не удалось сохранить настройки: {e}")
            dialog.destroy()
            self.new_project(confirm=False)

        bottom_frame = ttk.Frame(main_frame, style="Panel.TFrame")
        bottom_frame.pack(pady=(15,0), fill='x')
        
        ttk.Checkbutton(bottom_frame, text="Больше не показывать", variable=var_dont_show, style="Action.TCheckbutton").pack(side="left", expand=True)
        ttk.Button(bottom_frame, text="Закрыть", command=on_close).pack(side="right", expand=True)
        
        dialog.update_idletasks()
        parent_x, parent_y = self.winfo_x(), self.winfo_y()
        parent_w, parent_h = self.winfo_width(), self.winfo_height()
        win_w, win_h = dialog.winfo_width(), dialog.winfo_height()
        x = parent_x + (parent_w // 2) - (win_w // 2)
        y = parent_y + (parent_h // 2) - (win_h // 2)
        dialog.geometry(f"+{x}+{y}")

    def build_html(self, cfg):
        t = self.resolve_site_theme(cfg)
        title = cfg["title"]; numbering = bool(cfg.get("numbering", True)); view_mode = cfg.get("view_mode","standard")
        submit_text = cfg["submit_text"]
        
        password_enabled = cfg.get("password_enabled", False)
        password_html = ""
        password_css = ""
        password_js_vars = f"const PWD_ENABLED = {str(password_enabled).lower()};"
        
        main_container_initial_display = "flex"
        pass_prompt_initial_display = "none"

        if password_enabled:
            main_container_initial_display = "none"
            pass_prompt_initial_display = "flex"
            password = cfg.get("password", "")
            hashed_password = 'p' + base64.b64encode(password.encode('utf-8')).decode('utf-8')
            password_js_vars += f'const PWD_HASH = "{hashed_password}";'

            password_html = f"""<div id="pass_prompt">
  <div class="container">
      <div class="card">
        <h1>Требуется пароль</h1>
        <p class="helper">Для доступа к анкете введите пароль.</p>
        <input type="password" id="password_input" placeholder="Пароль" style="margin-top:10px; margin-bottom:10px;">
        <button class="btn" id="password_btn" type="button">Войти</button>
        <div id="pass_error" class="error" style="display:none; margin-top:14px;"></div>
      </div>
  </div>
</div>"""
        
        password_css = f"""
#main_container {{ 
    display: {main_container_initial_display};
    justify-content: center;
    width: 100%;
    min-height: 100vh;
    align-items: flex-start;
}}
#pass_prompt {{
    display: {pass_prompt_initial_display};
    justify-content: center;
    align-items: center;
    width: 100%;
    min-height: 100vh;
}}
#pass_prompt .card {{ max-width: 420px; width: 100%; }}
"""

        font_name = cfg.get("site_font", "System UI")
        font_family = SITE_FONTS.get(font_name, SITE_FONTS["System UI"])
        font_imports = ""
        font_map = { "Roboto": "Roboto:wght@400;700", "Inter": "Inter:wght@400;700;800", "Montserrat": "Montserrat:wght@400;700", "Playfair Display": "Playfair+Display:wght@400;700", "Source Code Pro": "Source+Code+Pro:wght@400;700", "Lobster": "Lobster" }
        if font_name in font_map:
            font_imports = f"""<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={font_map[font_name].replace(" ", "+")}&display=swap" rel="stylesheet">"""

        card_alpha = t['card_bg_alpha']; q_bg_alpha = 0.04; q_border_alpha = 0.08
        if view_mode == "compact": q_bg_alpha = 0.03
        elif view_mode == "contrast": q_bg_alpha = 0.07; q_border_alpha = 0.16

        css = f""":root {{ --primary: {t['primary']}; --radius: 16px; }}
* {{ box-sizing: border-box; }}
html, body {{ margin:0; height:100%; }}
body {{ font-family: {font_family}; background:{t['bg']}; color:{t['text']}; }}
.container {{ width:100%; max-width:960px; margin:0 auto; padding:28px 18px 60px; }}
{password_css}
.card {{ background: rgba(255,255,255,{card_alpha}); backdrop-filter: blur(8px); border:1px solid {t['card_border']}; border-radius: var(--radius); padding:24px; box-shadow:{t['shadow']}; }}
h1 {{ margin:0 0 6px 0; font-size:28px; line-height:1.2; }}
.helper {{ font-size:12px; opacity:.75; margin-top:6px; }}
.q {{ margin: { '10px' if view_mode in ('compact', 'minimal') else '16px' } 0 { '12px' if view_mode in ('compact', 'minimal') else '18px' }; transition: opacity .3s ease; }}
.q-card {{ position: relative; background: rgba(255,255,255,{q_bg_alpha}); border: 1px solid rgba(255,255,255,{q_border_alpha}); border-radius: 14px; padding: { '8px 10px 8px' if view_mode=='minimal' else '10px 12px 10px' if view_mode=='compact' else '14px 14px 12px' }; box-shadow: 0 8px 24px rgba(0,0,0,0.18); transition: all .18s; }}
.q-card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 28px rgba(0,0,0,0.22); border-color: rgba(255,255,255,{ 0.22 if view_mode=='contrast' else 0.16 }); background: rgba(255,255,255,{ q_bg_alpha + 0.015 }); }}
.q-head {{ display:flex; align-items:center; gap:10px; margin-bottom:{ '4px' if view_mode=='minimal' else '6px' if view_mode=='compact' else '10px' }; }}
.q-num {{ display:{'inline-flex' if numbering else 'none'}; min-width:30px; height:30px; padding:0 10px; border-radius:999px; background: color-mix(in srgb, {t['primary']} 22%, transparent); color:#fff; font-weight:800; align-items:center; justify-content:center; line-height:30px; font-size:14px; }}
.q-label {{ font-weight:800; font-size:16px; letter-spacing:.2px; }}
.q-body {{ margin-top:6px; }}
.q-divider {{ display:{'block' if view_mode=='dividers' else 'none'}; height:1px; border:0; border-top:1px dashed rgba(255,255,255,0.12); margin:14px 4px 6px; }}
input[type="text"], input[type="password"], select, textarea {{ width:100%; padding:{ '12px 14px' if view_mode=='compact' else '14px 16px' }; min-height:44px; border-radius:12px; border:1px solid {t['field_border']}; background:{t['field_bg']}; color:inherit; outline:none; font-size:16px; transition: all .18s; }}
textarea {{ height:{ '96px' if view_mode=='compact' else '120px' }; resize:vertical; }}
input[type="text"]:focus, input[type="password"]:focus, select:focus, textarea:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, {t['primary']} 30%, transparent); background: rgba(255,255,255,0.03); }}
.char-counter {{ font-size: 11px; text-align: right; opacity: 0.6; margin-top: 4px; }}
.req {{ color:var(--primary); font-weight:700; margin-left:6px; }}
.btn {{ background:var(--primary); color:#fff; border:none; padding:14px 18px; border-radius:10px; cursor:pointer; font-weight:700; font-size:16px; min-height:44px; }}
.btn:disabled {{ opacity:.6; cursor:not-allowed; }}
.success, .error {{ margin-top:14px; padding:12px 14px; border-radius:8px; font-size:14px; }}
.success {{ background:rgba(16,185,129,.15); color:#10b981; }}
.error {{ background:rgba(239,68,68,.15); color:#ef4444; }}
hr {{ border:none; border-top:1px solid {t['field_border']}; margin:18px 0; }}
.hidden {{ visibility: hidden; opacity: 0; max-height: 0; margin: 0; padding: 0; overflow: hidden; border: 0; }}
@media (max-width: 640px) {{ .container {{ padding:20px 14px 40px; }} .card {{ padding:18px; border-radius:14px; }} h1 {{ font-size:22px; }} }}
"""
        if view_mode == 'floating': css += ".card { border: none; background: transparent; box-shadow: none; padding-left: 8px; padding-right: 8px; }"
        elif view_mode == 'outlined': css += """input[type="text"], input[type="password"], select, textarea { background: transparent; border-width: 2px; } input[type="text"]:focus, input[type="password"]:focus, select:focus, textarea:focus { background: rgba(255,255,255,0.04); }"""
        elif view_mode == 'neumorphic':
            is_dark_theme = t['card_bg_alpha'] < 1
            if is_dark_theme:
                shadow_dark, shadow_light = "rgba(0,0,0,0.5)", "rgba(255,255,255,0.08)"
                inset_shadow_dark, inset_shadow_light = "rgba(0,0,0,0.6)", "rgba(255,255,255,0.07)"
            else:
                shadow_dark, shadow_light = "#a3b1c6", "#ffffff"
                inset_shadow_dark, inset_shadow_light = "#a3b1c6", "#ffffff"
            css += f"""body {{ background: {t['bg']}; color: {t['text']}; }}
            .card, .q-card, input, textarea, .btn, select {{ border-radius: 20px !important; background: {t['bg']} !important; border: none !important; }}
            .card {{ box-shadow: 9px 9px 16px {shadow_dark}, -9px -9px 16px {shadow_light}; }}
            .q-card {{ box-shadow: 5px 5px 10px {shadow_dark}, -5px -5px 10px {shadow_light}; }}
            input, textarea, select {{ box-shadow: inset 4px 4px 8px {inset_shadow_dark}, inset -4px -4px 8px {inset_shadow_light} !important; }}
            .btn {{ box-shadow: 5px 5px 10px {shadow_dark}, -5px -5px 10px {shadow_light} !important; color: var(--primary) !important; }}"""
        elif view_mode == 'brutalist': css += """body, .btn { font-family: 'Source Code Pro', monospace; } .card, .q-card, input, textarea, .btn { border-radius: 0; border: 2px solid; } .card { box-shadow: 8px 8px 0px; } .btn { background: var(--primary) !important; color: #fff; }"""

        form_id = str(uuid.uuid4())
        payload = {
            "title":title, "bot_token":cfg["bot_token"], "chat_id":cfg["chat_id"], 
            "questions": cfg.get("questions", []), 
            "telegram_enabled": cfg.get("telegram_enabled", True), 
            "gsheets_enabled": cfg.get("gsheets_enabled", False), "gsheets_url": cfg.get("gsheets_url", ""),
            "success_text": cfg.get("success_message"),
            "limit_one_submission": cfg.get("limit_one_submission", False),
            "one_submission_message": cfg.get("one_submission_message", "Спасибо! Ваш ответ был получен."),
            "form_id": form_id,
            "tg_separator": cfg.get("tg_separator", "— — —")
        }
        payload_json = json.dumps(payload, ensure_ascii=False)

        javascript_template = """
const FORM_CFG = {payload_json};
const CHAR_LIMIT = {char_limit};
const LIMIT_ONE_SUBMISSION = FORM_CFG.limit_one_submission;
const ONE_SUBMISSION_MESSAGE = FORM_CFG.one_submission_message;
const FORM_ID = FORM_CFG.form_id;
const SUBMISSION_KEY = `form_submitted_${{FORM_ID}}`;
{password_js_vars}

function checkPassword() {{
    const input = document.getElementById('password_input');
    if (!input) return;
    const inputHash = 'p' + btoa(unescape(encodeURIComponent(input.value)));
    const errorEl = document.getElementById('pass_error');

    if (inputHash === PWD_HASH) {{
        document.getElementById('pass_prompt').style.display = 'none';
        document.getElementById('main_container').style.display = 'flex';
    }} else {{
        errorEl.textContent = 'Неверный пароль.';
        errorEl.style.display = 'block';
        input.focus();
    }}
}}

function el(tag, attrs = {{}}, children = []) {{
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {{
        if (k === "class") e.className = v;
        else if (k === "for") e.htmlFor = v;
        else e.setAttribute(k, v);
    }}
    for (const c of children) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    return e;
}}

function renderQuestion(q, idx) {{
    const qWrap = el("div", {{ class: "q", "data-q-id": q.id }});
    if (q.condition && q.condition.parent_id) {{
        qWrap.classList.add("hidden");
        qWrap.dataset.conditionalParentId = q.condition.parent_id;
        qWrap.dataset.conditionalTriggerValues = JSON.stringify(q.condition.trigger_values || []);
    }}
    const card = el("div", {{ class: "q-card" }});
    const head = el("div", {{ class: "q-head" }});
    const num = el("div", {{ class: "q-num" }}, [String((idx || 0) + 1)]);
    const label = el("div", {{ class: "q-label" }}, [q.label]);
    if (q.required) label.appendChild(el("span", {{ class: "req" }}, [" *"]));
    head.appendChild(num); head.appendChild(label);
    const body = el("div", {{ class: "q-body" }});
    if (q.type === 1) {{
        const inp = el("textarea", {{ id: "q_" + q.id, name: q.id }});
        if (q.required) inp.setAttribute("required", "required");
        body.appendChild(inp);
        if (q.limit_chars) {{
            inp.setAttribute("maxlength", CHAR_LIMIT);
            const counter = el("div", {{ class: "char-counter" }}, [`0 / {char_limit}`]);
            body.appendChild(counter);
            inp.addEventListener("input", () => {{ counter.textContent = `${{inp.value.length}} / {char_limit}`; }});
        }}
    }} else if (q.type === 2) {{
        const optsWrap = el("div");
        (q.options || []).forEach((opt, oidx) => {{
            const rid = "q_" + q.id + "_opt_" + oidx;
            const r = el("input", {{ type: "radio", id: rid, name: q.id, value: opt, style: "min-height:20px; min-width:20px;" }});
            const l = el("label", {{ for: rid, style: "margin-left:6px; margin-right:14px;" }}, [opt]);
            optsWrap.appendChild(el("div", {{}}, [r, l]));
        }});
        if (q.required) optsWrap.setAttribute("data-required-radio", "1");
        body.appendChild(optsWrap);
    }}
    card.appendChild(head); card.appendChild(body);
    qWrap.appendChild(card);
    qWrap.appendChild(el("hr", {{ class: "q-divider" }}));
    return qWrap;
}}

function renderContent(parent, cfg) {{
    (cfg.questions || []).forEach((q, i) => parent.appendChild(renderQuestion(q, i)));
}}

function updateConditionalVisibility() {{
    document.querySelectorAll('[data-conditional-parent-id]').forEach(qEl => {{
        const parentId = qEl.dataset.conditionalParentId;
        const triggerValuesJSON = qEl.dataset.conditionalTriggerValues;
        if (!parentId || !triggerValuesJSON) return;

        const triggerValues = JSON.parse(triggerValuesJSON);
        const parentRadio = document.querySelector(`input[name="${{parentId}}"]:checked`);
        
        let isVisible = false;
        if (parentRadio && triggerValues.includes(parentRadio.value)) {{
            isVisible = true;
        }}

        if (isVisible) {{
            qEl.classList.remove('hidden');
        }} else {{
            if (!qEl.classList.contains('hidden')) {{
                qEl.classList.add('hidden');
                qEl.querySelectorAll('input, textarea').forEach(input => {{
                    if (input.type === 'radio' || input.type === 'checkbox') input.checked = false;
                    else input.value = '';
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }});
            }}
        }}
    }});
}}

function validateForm() {{
    for (const g of document.querySelectorAll("[data-required-radio='1']")) {{
        const parentQuestion = g.closest('.q');
        if (parentQuestion && !parentQuestion.classList.contains('hidden')) {{
             if (!g.querySelector("input[type='radio']:checked")) return false;
        }}
    }}
    return true;
}}

function escapeHtml(s) {{ return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }}

async function sendToGoogleSheets(payload) {{
    const res = await fetch(FORM_CFG.gsheets_url, {{
        method: "POST",
        mode: 'no-cors', 
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload)
    }});
}}

async function sendToTelegram(message) {{
    const url = "https://api.telegram.org/bot" + encodeURIComponent(FORM_CFG.bot_token) + "/sendMessage";
    const res = await fetch(url, {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify({{ chat_id: FORM_CFG.chat_id, text: message, parse_mode: "HTML" }}) }});
    if (!res.ok) {{
        const errorData = await res.json();
        throw new Error(`Ошибка Telegram API: ${{errorData.description || res.statusText}}`);
    }}
}}

function checkIfAlreadySubmitted() {{
    if (LIMIT_ONE_SUBMISSION && localStorage.getItem(SUBMISSION_KEY)) {{
        const form = document.getElementById("form");
        form.innerHTML = `<div class="success">${{escapeHtml(ONE_SUBMISSION_MESSAGE)}}</div>`;
        return true;
    }}
    return false;
}}


document.addEventListener("DOMContentLoaded", () => {{
    if (checkIfAlreadySubmitted()) return;
    
    if (PWD_ENABLED) {{
        document.getElementById('password_btn').addEventListener('click', checkPassword);
        document.getElementById('password_input').addEventListener('keypress', (e) => {{ if (e.key === 'Enter') {{ e.preventDefault(); checkPassword(); }} }});
    }}
    
    renderContent(document.getElementById("content"), FORM_CFG);
    const form = document.getElementById("form"), submitBtn = document.getElementById("submitBtn"), msg = document.getElementById("msg");
    form.addEventListener('change', updateConditionalVisibility);
    updateConditionalVisibility();

    form.addEventListener("submit", async (e) => {{
        e.preventDefault();
        msg.innerHTML = "";
        if (!validateForm()) {{ msg.innerHTML = '<div class="error">Заполните обязательные варианты.</div>'; return; }}
        submitBtn.disabled = true;
        
        const fd = new FormData(form);
        const visibleAnswers = [];
        
        FORM_CFG.questions.forEach(q => {{
            const parentEl = document.querySelector(`[data-q-id="${{q.id}}"]`);
            if (parentEl && !parentEl.classList.contains('hidden')) {{
                visibleAnswers.push({{ label: q.label, answer: fd.get(q.id) || "" }});
            }}
        }});

        const promises = [];
        if (FORM_CFG.gsheets_enabled) {{
            const payload = {{ "form_title": FORM_CFG.title, "answers": visibleAnswers }};
            promises.push(sendToGoogleSheets(payload));
        }}
        if (FORM_CFG.telegram_enabled) {{
            const separator = escapeHtml(FORM_CFG.tg_separator || '— — —');
            let lines = ["📝 <b>" + escapeHtml(FORM_CFG.title) + "</b>", "📅 " + new Date().toLocaleString('ru-RU')];
            if (visibleAnswers.length > 0) lines.push(separator);

            visibleAnswers.forEach((item, index) => {{
                lines.push("• <b>" + escapeHtml(item.label) + "</b>\\n" + escapeHtml(item.answer || "—"));
                if (index < visibleAnswers.length - 1) {{
                    lines.push(separator);
                }}
            }});
            promises.push(sendToTelegram(lines.join("\\n")));
        }}

        try {{
            await Promise.all(promises.map(p => p.catch(e => e)));
            const settled = await Promise.allSettled(promises);
            const failures = settled.filter(r => r.status === 'rejected');

            if (failures.length > 0) {{
                const errorMsg = failures.map(f => f.reason.message).join('<br>');
                throw new Error(errorMsg);
            }}

            msg.innerHTML = '<div class="success">' + escapeHtml(FORM_CFG.success_text) + '</div>';
            form.reset();
            if (LIMIT_ONE_SUBMISSION) {{
                localStorage.setItem(SUBMISSION_KEY, 'true');
                setTimeout(checkIfAlreadySubmitted, 100);
            }}
            document.querySelectorAll('.char-counter').forEach(c => c.textContent = `0 / {char_limit}`);
            updateConditionalVisibility();
        }} catch (err) {{
            console.error(err);
            msg.innerHTML = `<div class="error"><b>Ошибка отправки:</b><br>${{err.message}}</div>`;
        }} finally {{ 
            if (!LIMIT_ONE_SUBMISSION) {{
                submitBtn.disabled = false; 
            }}
        }}
    }});
}});
"""
        javascript_code = javascript_template.format(payload_json=payload_json, char_limit=CHAR_LIMIT, password_js_vars=password_js_vars)
        
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{font_imports}
<style>{css}</style>
</head>
<body>
{password_html}
<div id="main_container">
  <div class="container">
    <div class="card">
        <h1>{title}</h1>
        <p class="helper">Поля со звёздочкой обязательны.</p>
        <form id="form">
        <div id="content"></div>
        <button class="btn" id="submitBtn" type="submit">{submit_text}</button>
        <div id="msg"></div>
        </form>
    </div>
  </div>
</div>
<script>
{javascript_code}
</script>
</body>
</html>
"""
        return html

    def generate_single_index(self):
        try: cfg = self.gather_config()
        except Exception as e: messagebox.showerror("Ошибка", str(e)); return
        desktop = Path.home() / "Desktop"
        out_file = filedialog.asksaveasfilename(initialdir=desktop, title="Сохранить HTML", defaultextension=".html", filetypes=[("HTML-файл", "*.html")])
        if not out_file: return
        html = self.build_html(cfg)
        try:
            with open(out_file, "w", encoding="utf-8") as f: f.write(html)
            self.set_dirty_status(False)
            messagebox.showinfo("Готово", f"Файл анкеты успешно сохранён:\n{out_file}")
        except Exception as e: messagebox.showerror("Ошибка записи", f"Не удалось записать файл: {e}")

    def refresh_preview(self):
        try:
            cfg = self.gather_config()
            html = self.build_html(cfg)
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", html)
        except Exception as e: messagebox.showerror("Ошибка", str(e)); return

    def open_in_browser(self):
        try:
            cfg = self.gather_config()
            html = self.build_html(cfg)
            path = tempfile.mkstemp(suffix=".html", prefix="preview_")[1]
            with open(path, "w", encoding="utf-8") as f: f.write(html)
            webbrowser.open(f"file://{path}")
        except Exception as e: messagebox.showerror("Ошибка", str(e)); return

if __name__ == "__main__":
    app = App()
    app.mainloop()