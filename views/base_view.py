import tkinter as tk
from tkinter import ttk
from config import Config

class BaseView(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
    
    def configure_styles(self):
        self.style.configure(
            'Primary.TButton',
            background=Config.THEME_COLOR['primary'],
            foreground='white',
            padding=5
        )
        self.style.configure(
            'Custom.TEntry',
            fieldbackground='white',
            padding=5
        )
        self.style.configure(
            'Danger.TButton',
            background=Config.THEME_COLOR['warning'],
            foreground='white',
            padding=5
        )
