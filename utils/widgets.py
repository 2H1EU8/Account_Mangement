import tkinter as tk
from tkinter import ttk, messagebox
import string
from .security import SecurityUtils  # Add this import

class PasswordEntry(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(show="•")
        self.create_context_menu()
        
    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Show/Hide", command=self.toggle_show)
        self.context_menu.add_command(label="Generate Strong Password", 
                                    command=self.generate_password)
        self.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        
    def toggle_show(self):
        current = self.cget("show")
        self.configure(show="" if current else "•")
        
    def generate_password(self):
        import random
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(chars) for _ in range(16))
        self.delete(0, tk.END)
        self.insert(0, password)

class StrengthMeter(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_styles()
        self.create_widgets()
    
    def setup_styles(self):
        self.style = ttk.Style()
        styles = {
            'Critical': '#ff0000',
            'Weak': '#ff6b6b',
            'Medium': '#ffd93d',
            'Strong': '#6bff6b',
            'Very Strong': '#00ff00'
        }
        for name, color in styles.items():
            self.style.configure(
                f'{name}.Horizontal.TProgressbar',
                background=color,
                troughcolor='#f0f0f0',
                bordercolor='#e0e0e0',
                lightcolor=color,
                darkcolor=color
            )
    
    def create_widgets(self):
        self.progress = ttk.Progressbar(
            self, length=200, mode='determinate', 
            maximum=100, style='Critical.Horizontal.TProgressbar'
        )
        self.progress.pack(side=tk.LEFT, padx=5)
        
        self.label = ttk.Label(self, text="Password Strength: 0%")
        self.label.pack(side=tk.LEFT, padx=5)
        
        self.details = ttk.Label(self, text="")
        self.details.pack(side=tk.LEFT, padx=5)
    
    def update_strength(self, score):
        self.progress['value'] = score
        self.label['text'] = f"Password Strength: {score}%"
        
        if score < 40:
            self.progress['style'] = 'Weak.Horizontal.TProgressbar'
        elif score < 70:
            self.progress['style'] = 'Medium.Horizontal.TProgressbar'
        else:
            self.progress['style'] = 'Strong.Horizontal.TProgressbar'
            
    def reset(self):
        """Reset strength meter to initial state"""
        self.progress['value'] = 0
        self.label['text'] = "Password Strength: 0%"
        self.progress['style'] = 'Weak.Horizontal.TProgressbar'

class SecureEntry(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove face verification, just make it a normal entry
        self.create_context_menu()
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy", command=lambda: self.event_generate('<<Copy>>'))
        self.context_menu.add_command(label="Paste", command=lambda: self.event_generate('<<Paste>>'))
        self.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)
