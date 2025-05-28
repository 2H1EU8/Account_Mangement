import tkinter as tk
from tkinter import ttk
from .base_view import BaseView

class PasswordGeneratorView(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.title("Password Generator")
        self.geometry("400x500")
        self.setup_ui()
        
    def setup_ui(self):
        # Options frame
        options_frame = ttk.LabelFrame(self, text="Generator Options")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Password length
        ttk.Label(options_frame, text="Length:").grid(row=0, column=0, padx=5, pady=5)
        self.length_var = tk.IntVar(value=16)
        ttk.Spinbox(options_frame, from_=8, to=64, 
                   textvariable=self.length_var).grid(row=0, column=1, padx=5)
        
        # Character options
        self.options = {
            'use_uppercase': tk.BooleanVar(value=True),
            'use_lowercase': tk.BooleanVar(value=True),
            'use_numbers': tk.BooleanVar(value=True),
            'use_symbols': tk.BooleanVar(value=True),
            'avoid_similar': tk.BooleanVar(value=True)
        }
        
        labels = {
            'use_uppercase': 'Uppercase (A-Z)',
            'use_lowercase': 'Lowercase (a-z)', 
            'use_numbers': 'Numbers (0-9)',
            'use_symbols': 'Symbols (!@#$...)',
            'avoid_similar': 'Avoid Similar (1/l, O/0)'
        }
        
        for i, (key, var) in enumerate(self.options.items(), 1):
            ttk.Checkbutton(
                options_frame, 
                text=labels[key],
                variable=var
            ).grid(row=i, column=0, columnspan=2, padx=5, pady=2, sticky='w')
            
        # Generated password
        result_frame = ttk.LabelFrame(self, text="Generated Password")
        result_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(
            result_frame,
            textvariable=self.password_var,
            font=('Courier', 12)
        )
        password_entry.pack(fill=tk.X, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame,
            text="Generate",
            command=self.generate_password
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Copy",
            command=self.copy_password
        ).pack(side=tk.LEFT, padx=5)
        
        # Generate initial password
        self.generate_password()
        
    def generate_password(self):
        """Generate new password with current options"""
        preferences = {
            'min_length': self.length_var.get(),
            **{k: v.get() for k, v in self.options.items()}
        }
        password = self.controller.generate_password(preferences)
        self.password_var.set(password)
        
    def copy_password(self):
        """Copy generated password to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(self.password_var.get())
        self.update()
