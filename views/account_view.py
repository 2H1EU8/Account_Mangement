import tkinter as tk
from tkinter import ttk, messagebox
from .base_view import BaseView
from utils.widgets import PasswordEntry, StrengthMeter, SecureEntry

class AccountView(BaseView):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent  # Store parent reference
        self.controller = controller
        self.current_account_id = None
        self.security = controller.security  # Add security reference
        self.setup_ui()
        self.setup_password_monitoring()
        self.refresh_account_list()
        
    def setup_password_monitoring(self):
        def on_password_change(*args):
            password = self.entries['password'].get()
            strength = self.controller.security.check_password_strength(password)
            self.strength_meter.update_strength(strength)
            
        self.password_var = tk.StringVar()
        self.entries['password'].configure(textvariable=self.password_var)
        self.password_var.trace('w', on_password_change)

    def setup_ui(self):
        # Add settings button to top right
        settings_frame = ttk.Frame(self)
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Add Exit button first (leftmost)
        ttk.Button(
            settings_frame,
            text="Exit",
            command=self.quit_app,
            style='Danger.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            settings_frame, 
            text="Password Analytics",
            command=lambda: self.show_analytics()
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            settings_frame, 
            text="Password Generator",
            command=lambda: self.controller.show_password_generator()
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            settings_frame, 
            text="Setup 2FA",
            command=lambda: self.controller.setup_2fa()
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            settings_frame, 
            text="Reset Face Authentication",
            command=self.reset_face_auth
        ).pack(side=tk.RIGHT, padx=5)
        
        # Left panel - Account Form
        self.form_frame = ttk.LabelFrame(self, text="Account Details")
        self.form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Get categories and separate display values from IDs
        categories = self.controller.get_categories()
        self.category_map = dict(categories)  # Store mapping of display -> id
        category_displays = list(self.category_map.keys())
        
        # Account form fields
        fields = [
            ("Category", ttk.Combobox, category_displays),
            ("Account Name", ttk.Entry, None),
            ("Username", ttk.Entry, None),  # Changed from SecureEntry
            ("Password", PasswordEntry, None),
            ("URL", ttk.Entry, None)
        ]
        
        self.entries = {}
        for i, (label, widget_class, values) in enumerate(fields):
            ttk.Label(self.form_frame, text=label).grid(row=i, column=0, padx=5, pady=5)
            try:
                widget = widget_class(self.form_frame)
                if values:
                    widget['values'] = values
                widget.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
                self.entries[label.lower()] = widget
            except Exception as e:
                print(f"Warning: Failed to create widget {label}: {e}")
                # Create a basic Entry as fallback
                widget = ttk.Entry(self.form_frame)
                widget.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
                self.entries[label.lower()] = widget
        
        # Password strength meter
        self.strength_meter = StrengthMeter(self.form_frame)
        self.strength_meter.grid(row=len(fields), column=0, columnspan=2, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.form_frame)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Save", style='Primary.TButton', 
                  command=self.handle_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", style='Danger.TButton',
                  command=self.handle_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", 
                  command=self.handle_clear).pack(side=tk.LEFT, padx=5)

        # Add copy button next to password field
        password_frame = ttk.Frame(self.form_frame)
        password_frame.grid(row=3, column=1, sticky='ew')
        
        self.entries['password'] = PasswordEntry(password_frame)
        self.entries['password'].pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            password_frame,
            text="Copy",
            command=self.copy_password
        ).pack(side=tk.RIGHT, padx=5)

        # Right panel - Account List
        list_frame = ttk.LabelFrame(self, text="Saved Accounts")
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Search bar
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Treeview
        self.tree = ttk.Treeview(
            list_frame, 
            columns=('Category', 'Name', 'Username', 'Last Changed', 'Strength'),
            show='headings'
        )
        
        # Store account IDs for selection
        self.account_ids = {}  # Dictionary to store row_id -> account_id mapping
        
        # Configure columns
        column_widths = {
            'Category': 120,
            'Name': 150,
            'Username': 150,
            'Last Changed': 150,
            'Strength': 100
        }
        
        for col, width in column_widths.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind('<Double-1>', self.on_account_select)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Add preview area for face verification
        self.preview_frame = ttk.LabelFrame(self.form_frame, text="Face Verification")
        self.preview_frame.grid(row=len(fields)+2, column=0, columnspan=2, padx=5, pady=5)
        
        self.preview_canvas = tk.Canvas(self.preview_frame, width=320, height=240, bg='black')
        self.preview_canvas.pack(pady=5)
        
        self.status_label = ttk.Label(self.preview_frame, text="")
        self.status_label.pack(pady=5)
        
        # Hide preview frame initially
        self.preview_frame.grid_remove()

    def clear_form(self):
        for entry in self.entries.values():
            if hasattr(entry, 'delete'):
                entry.delete(0, tk.END)
        self.strength_meter.reset()

    def on_search(self, *args):
        search_text = self.search_var.get().lower()
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if not search_text or any(str(v).lower().find(search_text) >= 0 for v in values):
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)

    def refresh_account_list(self):
        self.account_ids.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        accounts = self.controller.get_accounts()
        for account in accounts:
            item_id = self.tree.insert('', 'end', values=account[1:])  # Skip account_id
            self.account_ids[item_id] = account[0]  # Store account_id mapping

    def on_account_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        # Clear current form
        self.clear_form()
        
        # Get account ID and load details
        account_id = self.account_ids.get(selected[0])
        if account_id:
            self.current_account_id = account_id
            self.controller.load_account(account_id)

    def set_form_values(self, values):
        """Helper method to set form values"""
        for field, value in values.items():
            if field in self.entries:
                self.entries[field].delete(0, tk.END)
                self.entries[field].insert(0, value)

    def set_form_values(self, data):
        """Safely set form values"""
        field_mapping = {
            'category': 'category',
            'account_name': 'account name',
            'username': 'username',
            'url': 'url'
        }
        
        for api_field, form_field in field_mapping.items():
            if api_field in data and form_field in self.entries:
                value = data[api_field] or ''
                entry = self.entries[form_field]
                
                if isinstance(entry, ttk.Combobox):
                    entry.set(value)
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, value)

    def get_selected_category_id(self):
        display_value = self.entries['category'].get()
        return self.category_map.get(display_value)

    def handle_save(self):
        """Direct save without any verification"""
        try:
            password = self.entries['password'].get()
            data = {
                'category_id': self.get_selected_category_id(),
                'account_name': self.entries['account name'].get(),
                'username': self.entries['username'].get(),
                'password': password,
                'url': self.entries['url'].get(),
                'password_strength': self.controller.security.check_password_strength(password),
                'owner_username': self.controller.logged_in_user  # Add owner_username
            }
            
            if self.current_account_id:
                data['account_id'] = self.current_account_id
                self.controller.update_account(data)
            else:
                self.controller.save_account(data)  # Pass data directly to save_account
                
            self.refresh_account_list()
            messagebox.showinfo("Success", "Account saved successfully!")
            self.clear_form()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_delete(self):
        if self.current_account_id:
            self.controller.delete_account(self.current_account_id)
        
    def handle_clear(self):
        self.current_account_id = None
        self.clear_form()

    def reset_face_auth(self):
        if messagebox.askyesno("Confirm Reset", 
                             "Are you sure you want to reset face authentication?"):
            if self.controller.security.clear_reference_image():
                messagebox.showinfo("Success", 
                    "Face authentication reset. Please restart the application.")
                self.quit()

    def copy_password(self):
        """Copy decrypted password from database with face verification"""
        if not self.current_account_id:
            messagebox.showwarning("Warning", "Please select an account first")
            return
            
        # Get encrypted password from database
        account_data = self.controller.model.get_account_by_id(self.current_account_id)
        if not account_data or 'encrypted_password' not in account_data:
            messagebox.showerror("Error", "Failed to get password")
            return
        
        # Show preview frame for verification
        self.preview_frame.grid()
        self.preview_canvas.delete("all")
        self.status_label.config(text="Starting face verification...")
        self.update()
        
        try:
            if self.security.secure_copy_password(
                account_data['encrypted_password'],
                self.preview_canvas, 
                self.status_label
            ):
                messagebox.showinfo("Success", "Password copied to clipboard\nWill clear in 30 seconds")
            else:
                messagebox.showerror("Error", "Failed to copy password - Face verification required")
        finally:
            self.preview_frame.grid_remove()

    def show_analytics(self):
        """Show analytics window"""
        if hasattr(self.parent, 'show_analytics'):
            self.parent.show_analytics()

    def quit_app(self):
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?"):
            self.parent.quit()
