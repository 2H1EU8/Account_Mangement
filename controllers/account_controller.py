import tkinter as tk
from tkinter import ttk, messagebox
from models.account_model import AccountModel
from models.analytics_model import AnalyticsModel
from models.totp_model import TOTPModel
from utils.security import SecurityUtils
from utils.password_generator import PasswordGenerator
from datetime import datetime

class AccountController:
    def __init__(self, username, security, view=None):
        self.model = AccountModel()
        self.analytics_model = AnalyticsModel()
        self.totp_model = TOTPModel()
        self.password_generator = PasswordGenerator()
        self.current_user_id = self._get_user_id(username)
        self.security = security
        self.logged_in_user = username
        self.view = view
        
    def _get_user_id(self, username):
        """Get or create user ID for username"""
        try:
            query = """
                INSERT INTO users (username)
                VALUES (%s)
                ON CONFLICT (username) DO UPDATE 
                SET username = EXCLUDED.username
                RETURNING user_id;
            """
            self.model.cur.execute(query, (username,))
            self.model.conn.commit()
            return self.model.cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting user_id: {e}")
            return None

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

    def show_password_generator(self):
        """Show password generator dialog"""
        from views.generator_view import PasswordGeneratorView
        generator_window = PasswordGeneratorView(self.view, self)
        generator_window.grab_set()

    def setup_2fa(self):
        """Set up 2FA for current user"""
        if not self.current_user_id:
            messagebox.showerror("Error", "User ID not found")
            return
            
        try:
            setup_data = self.totp_model.setup_2fa(
                self.current_user_id,
                self.logged_in_user
            )
            
            def verify_code(code):
                if self.totp_model.verify_totp(self.current_user_id, code):
                    messagebox.showinfo("Success", "2FA has been enabled!")
                    return True
                messagebox.showerror("Error", "Invalid code")
                return False
                
            from views.totp_setup_view import TOTPSetupView
            TOTPSetupView(self.view, setup_data, verify_code)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set up 2FA: {str(e)}")

    def verify_2fa(self, code):
        """Verify 2FA code"""
        return self.totp_model.verify_totp(self.current_user_id, code)

    def refresh_analytics(self):
        """Update analytics data"""
        try:
            stats = self.analytics_model.calculate_analytics(self.logged_in_user)
            if not stats:
                return
                
            history = self.analytics_model.get_historical_analytics(self.logged_in_user)
            
            # Update view with data
            data = {
                'total': stats[2],
                'avg_strength': round(float(stats[3]), 1),
                'weak': stats[4],
                'medium': stats[5],
                'strong': stats[6]
            }
            
            if hasattr(self.view, 'analytics_view'):
                self.view.analytics_view.update_stats(data)
                
                if history:
                    dates = [h[0] for h in history]
                    values = [float(h[1]) for h in history]
                    self.view.analytics_view.plot_history(dates, values)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh analytics: {str(e)}")

    def generate_password(self, preferences=None):
        """Generate password with given preferences"""
        if preferences is None:
            preferences = {
                'min_length': 16,
                'use_uppercase': True,
                'use_lowercase': True,
                'use_numbers': True,
                'use_symbols': True,
                'avoid_similar': True
            }
        return self.password_generator.generate_password(preferences)

    def show_analytics(self):
        """Show analytics window and load data"""
        try:
            stats = self.analytics_model.calculate_analytics(self.logged_in_user)
            if not stats:
                messagebox.showerror("Error", "No data available for analysis")
                return
                
            history = self.analytics_model.get_historical_analytics(self.logged_in_user)
            
            # Create analytics window
            analytics_window = tk.Toplevel(self.view)
            analytics_window.title("Password Analytics")
            analytics_view = AnalyticsView(analytics_window, self)
            analytics_view.pack(fill=tk.BOTH, expand=True)
            
            # Update view with data
            analytics_view.update_stats({
                'total': stats[2],
                'avg_strength': round(stats[3], 1),
                'weak': stats[4],
                'medium': stats[5],
                'strong': stats[6]
            })
            
            if history:
                dates = [h[0] for h in history]
                values = [h[1] for h in history]
                analytics_view.plot_history(dates, values)
            
            # Configure window
            analytics_window.geometry("800x600")
            analytics_window.transient(self.view)
            analytics_window.grab_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load analytics: {str(e)}")
