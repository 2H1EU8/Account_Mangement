import tkinter as tk
from tkinter import ttk, messagebox
from models.account_model import AccountModel
from utils.security import SecurityUtils
from datetime import datetime

class AccountController:
    def __init__(self, username, security, view=None):
        self.model = AccountModel()
        self.security = security
        self.logged_in_user = username
        self.view = view
        
    def set_view(self, view):
        self.view = view
        
    def get_categories(self):
        try:
            return self.model.get_categories()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load categories: {str(e)}")
            return []
            
    def save_account(self, data):
        """Save new account with owner"""
        # Data already contains owner_username from view
        self.model.create_account(data)
        self.view.clear_form()
        self.view.refresh_account_list()
        
    def refresh_account_list(self):
        try:
            accounts = self.model.get_accounts(self.security.logged_in_user)
            self.view.tree.delete(*self.view.tree.get_children())
            for account in accounts:
                self.view.tree.insert('', 'end', values=(
                    account[1],  # category
                    account[2],  # account_name
                    account[3],  # username
                    account[5].strftime("%Y-%m-%d %H:%M")  # last_changed
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh accounts: {str(e)}")

    def check_password_expiry(self):
        try:
            expiring = self.model.get_expiring_passwords()
            if expiring:
                accounts = "\n".join([f"- {acc[2]}" for acc in expiring])
                messagebox.showwarning(
                    "Password Expiring",
                    f"The following accounts need password updates:\n{accounts}"
                )
        except Exception as e:
            print(f"Failed to check password expiry: {str(e)}")

    def get_accounts(self):
        """Get accounts for logged in user only"""
        return self.model.get_accounts(self.logged_in_user)

    def load_account(self, account_id):
        try:
            account = self.model.get_account_by_id(account_id)
            if account:
                self.view.clear_form()
                self.view.set_form_values(account)
                # Update strength meter using stored strength
                if 'password_strength' in account:
                    self.view.strength_meter.update_strength(account['password_strength'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load account: {str(e)}")
    
    def update_account(self, data):
        """Update account with owner"""
        # Ensure owner_username is included in update
        data['owner_username'] = self.logged_in_user
        self.model.update_account(data)
        self.view.clear_form()
        self.view.refresh_account_list()

    def delete_account(self, account_id):
        try:
            if not self.security.verify_image():
                messagebox.showerror("Error", "Authentication required!")
                return
                
            if messagebox.askyesno("Confirm Delete", 
                                 "Are you sure you want to delete this account?"):
                self.model.delete_account(account_id)
                self.view.clear_form()
                self.view.current_account_id = None
                self.view.refresh_account_list()
                messagebox.showinfo("Success", "Account deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete account: {str(e)}")
