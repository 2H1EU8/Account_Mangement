import tkinter as tk
from views.account_view import AccountView
from views.login_view import LoginView
from views.analytics_view import AnalyticsView  # Add new import
from controllers.account_controller import AccountController
from config import Config
import threading
import time
from datetime import datetime, timedelta
from tkinter import messagebox
from utils.security import SecurityUtils
import cv2

class AuthenticationDialog(tk.Toplevel):
    def __init__(self, parent, security):
        super().__init__(parent)
        self.security = security
        self.result = False
        
        self.title("Authentication Required")
        self.geometry("300x150")
        
        tk.Label(self, text="Please look at the camera for authentication").pack(pady=20)
        tk.Button(self, text="Start Authentication", command=self.authenticate).pack()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(parent)
        self.grab_set()
    
    def authenticate(self):
        if self.security.verify_image():
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Error", "Authentication failed!")

    def on_close(self):
        if not self.result:
            self.quit()
        self.destroy()

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Account Manager")
        self.geometry(Config.WINDOW_SIZE)
        
        self.security = SecurityUtils()
        
        # Show login
        self.show_login()

    def show_login(self):
        self.clear_window()
        self.login_view = LoginView(self, self.security, self.on_login_success)
        self.login_view.pack(expand=True, pady=20)
        
    def on_login_success(self, username):
        """Handle successful login"""
        self.clear_window()
        self.controller = AccountController(username, self.security)
        self.account_view = AccountView(self, self.controller)
        self.controller.set_view(self.account_view)
        self.account_view.pack(fill=tk.BOTH, expand=True)
        self.schedule_password_checks()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def schedule_password_checks(self):
        def run_scheduler():
            while True:
                now = datetime.now()
                # Check at 9 AM
                if now.hour == 9 and now.minute == 0:
                    self.controller.check_password_expiry()
                time.sleep(60)  # Check every minute
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

    def authenticate_user(self):
        if not self.security.has_reference_image():
            if messagebox.askyesno("Setup Required", 
                "No reference image found. Would you like to capture one now?"):
                return self.security.capture_reference_image()
            return False
        
        # Show authentication dialog
        auth_dialog = AuthenticationDialog(self, self.security)
        self.wait_window(auth_dialog)
        return auth_dialog.result

    def show_analytics(self):
        try:
            if hasattr(self, 'analytics_window'):
                self.analytics_window.destroy()
                
            self.analytics_window = tk.Toplevel(self)
            self.analytics_window.title("Password Analytics")
            
            # Create and store analytics view
            self.controller.view.analytics_view = AnalyticsView(
                self.analytics_window, 
                self.controller
            )
            self.controller.view.analytics_view.pack(fill=tk.BOTH, expand=True)
            
            # Configure window
            self.analytics_window.geometry("800x600")
            self.analytics_window.transient(self)
            self.analytics_window.grab_set()
            
            # Load initial data
            self.controller.refresh_analytics()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show analytics: {str(e)}")

    def reset_face_data(self):
        if messagebox.askyesno("Confirm Reset", 
            "This will remove all face recognition data. Continue?"):
            count = self.security.reset_all_face_data()
            messagebox.showinfo("Success", 
                f"Removed {count} face data files. Please restart the application.")
            self.quit()

if __name__ == "__main__":
    Config.init()
    app = Application()
    app.mainloop()
