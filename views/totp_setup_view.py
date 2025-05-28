import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import base64
from io import BytesIO

class TOTPSetupView(tk.Toplevel):
    def __init__(self, parent, data, on_complete):
        super().__init__(parent)
        self.data = data
        self.on_complete = on_complete
        
        self.title("Set Up Two-Factor Authentication")
        self.geometry("600x800")
        self.setup_ui()
        
    def setup_ui(self):
        # Instructions
        ttk.Label(
            self,
            text="1. Scan this QR code with your authenticator app",
            font=('TkDefaultFont', 12, 'bold')
        ).pack(pady=10)
        
        # QR Code
        qr_data = base64.b64decode(self.data['qr_code'])
        img = Image.open(BytesIO(qr_data))
        photo = ImageTk.PhotoImage(img)
        
        qr_label = ttk.Label(self, image=photo)
        qr_label.image = photo  # Keep reference
        qr_label.pack(pady=20)
        
        # Manual entry section
        ttk.Label(
            self,
            text="Or manually enter this secret key:",
            font=('TkDefaultFont', 10)
        ).pack(pady=5)
        
        secret_frame = ttk.Frame(self)
        secret_frame.pack(pady=5)
        
        secret_entry = ttk.Entry(secret_frame)
        secret_entry.insert(0, self.data['secret'])
        secret_entry.config(state='readonly')
        secret_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            secret_frame,
            text="Copy",
            command=lambda: self.clipboard_clear() or self.clipboard_append(self.data['secret'])
        ).pack(side=tk.LEFT)
        
        # Verification section
        ttk.Label(
            self,
            text="2. Enter the code from your authenticator app to verify:",
            font=('TkDefaultFont', 12, 'bold')
        ).pack(pady=20)
        
        self.code_var = tk.StringVar()
        code_entry = ttk.Entry(self, textvariable=self.code_var)
        code_entry.pack(pady=5)
        
        ttk.Button(
            self,
            text="Verify Code",
            style='Primary.TButton',
            command=self.verify_code
        ).pack(pady=10)
        
        # Backup codes section
        ttk.Label(
            self,
            text="3. Save these backup codes in a secure location:",
            font=('TkDefaultFont', 12, 'bold')
        ).pack(pady=20)
        
        backup_frame = ttk.Frame(self)
        backup_frame.pack(pady=10)
        
        backup_text = tk.Text(backup_frame, height=8, width=30)
        backup_text.insert('1.0', '\n'.join(self.data['backup_codes']))
        backup_text.config(state='disabled')
        backup_text.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            backup_frame,
            text="Copy All",
            command=lambda: self.clipboard_clear() or self.clipboard_append('\n'.join(self.data['backup_codes']))
        ).pack(side=tk.LEFT)
        
    def verify_code(self):
        """Verify entered TOTP code"""
        if self.on_complete(self.code_var.get()):
            self.destroy()
