import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import cv2

class FaceRegistrationWindow(tk.Toplevel):
    def __init__(self, parent, username, security, on_complete):
        super().__init__(parent)
        self.username = username
        self.security = security
        self.on_complete = on_complete
        self.camera_ready = False
        self.camera = None
        self.preview_thread = None
        self.running = False
        
        self.title("Face Registration")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        self.check_camera()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def check_camera(self):
        """Check if camera is available"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Failed to open camera")
            
            ret, _ = self.camera.read()
            if not ret:
                raise Exception("Failed to capture from camera")
            
            self.camera_ready = True
            self.capture_btn.configure(state='normal')
            self.status_var.set("Camera ready - Position your face and press Space")
            self.start_preview()
            
        except Exception as e:
            self.handle_error(f"Camera error: {str(e)}\nPlease check your camera connection.")

    def start_preview(self):
        """Start camera preview thread"""
        self.running = True
        
        def preview_loop():
            while self.running and self.winfo_exists():
                try:
                    ret, frame = self.camera.read()
                    if ret:
                        # Detect face
                        has_face = self.security._detect_face(frame)[0]
                        
                        # Draw guide circle
                        height, width = frame.shape[:2]
                        center_x, center_y = width // 2, height // 2
                        cv2.circle(frame, (center_x, center_y), 
                                 min(center_x, center_y) - 50, 
                                 (0, 255, 0) if has_face else (0, 0, 255), 2)
                        
                        # Update status
                        status = "Face detected - Press SPACE to capture" if has_face else "No face detected"
                        self.after(0, lambda s=status: self.status_var.set(s))
                        
                        # Update preview using new method name
                        self.security.update_preview(self.canvas, frame)
                    time.sleep(0.03)  # ~30 FPS
                except Exception as e:
                    print(f"Preview error: {e}")
                    break
                    
        self.preview_thread = threading.Thread(target=preview_loop)
        self.preview_thread.daemon = True
        self.preview_thread.start()

    def setup_ui(self):
        # Status label with bigger font
        self.status_var = tk.StringVar(value="Checking camera...")
        self.status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            justify=tk.CENTER,
            font=('TkDefaultFont', 12, 'bold')
        )
        self.status_label.pack(pady=10)
        
        # Frame for canvas with border
        canvas_frame = ttk.Frame(self, relief='solid', borderwidth=1)
        canvas_frame.pack(pady=10, padx=10)
        
        # Canvas for preview
        self.canvas = tk.Canvas(
            canvas_frame, 
            width=640, 
            height=480,
            bg='black'  # Dark background
        )
        self.canvas.pack()
        
        # Add "No Camera" text to canvas
        self.canvas.create_text(
            320, 240,
            text="Initializing camera...",
            fill="white",
            font=('TkDefaultFont', 14)
        )
        
        # Progress section
        self.progress_var = tk.IntVar()
        self.progress = ttk.Progressbar(
            self, 
            orient="horizontal",
            length=300, 
            mode="determinate",
            variable=self.progress_var
        )
        self.progress.pack(pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        self.capture_btn = ttk.Button(
            btn_frame, 
            text="Capture (Space)", 
            command=self.start_capture,
            state='disabled'  # Initially disabled
        )
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Cancel (Esc)", 
            command=self.on_cancel
        ).pack(side=tk.LEFT, padx=5)
        
        # Bind keys
        self.bind('<space>', self.try_capture)
        self.bind('<Escape>', lambda e: self.on_cancel())
        
    def try_capture(self, event=None):
        """Handle space key or capture button press"""
        if not self.camera_ready or not self.running:
            return
            
        # Get current frame
        ret, frame = self.camera.read()
        if not ret:
            self.handle_error("Failed to capture frame")
            return
            
        # Check for face
        has_face = self.security._detect_face(frame)[0]
        if not has_face:
            messagebox.showwarning("No Face Detected", "Please position your face in the circle")
            return
            
        # Save face image
        try:
            face_path = self.security._get_user_face_path(self.username)
            cv2.imwrite(face_path, frame)
            self.finish_capture(True)
        except Exception as e:
            self.handle_error(f"Failed to save face image: {str(e)}")

    def start_capture(self):
        if not self.camera_ready:
            self.handle_error("Camera not ready")
            return
        
        self.status_var.set("Initializing camera...")
        self.progress_var.set(0)
        self.update()
        
        # Disable buttons during capture
        for child in self.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='disabled')
        
        def update_progress():
            for i in range(0, 101, 10):
                if not self.winfo_exists():
                    return
                self.progress_var.set(i)
                self.update()
                time.sleep(0.1)
        
        def capture():
            try:
                # Start progress update
                progress_thread = threading.Thread(target=update_progress)
                progress_thread.daemon = True
                progress_thread.start()
                
                # Do capture
                self.status_var.set("Capturing... Please look at the camera")
                success = self.security.capture_reference_image(self.username, self.canvas)
                
                if self.winfo_exists():
                    self.after(0, lambda: self.finish_capture(success))
                    
            except Exception as e:
                if self.winfo_exists():
                    self.after(0, lambda: self.handle_error(str(e)))
        
        # Start capture thread
        capture_thread = threading.Thread(target=capture)
        capture_thread.daemon = True
        capture_thread.start()
        
        # Add timeout
        self.after(10000, lambda: self.check_timeout(capture_thread))
    
    def check_timeout(self, thread):
        if thread.is_alive() and self.winfo_exists():
            self.handle_error("Capture timeout - Please try again")
    
    def finish_capture(self, success):
        # Re-enable buttons
        for child in self.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='normal')
                
        if success:
            self.progress_var.set(100)
            self.status_var.set("Face registered successfully!")
            self.update()
            self.after(500, lambda: (
                messagebox.showinfo("Success", "Face registered successfully!"),
                self.on_complete(True),
                self.destroy()
            ))
        else:
            self.handle_error("Failed to detect face properly")
    
    def handle_error(self, error):
        # Re-enable buttons
        for child in self.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state='normal')
        
        self.status_var.set(f"Error: {error}")
        self.update()
        messagebox.showerror("Error", f"Registration failed: {error}")
        self.on_complete(False)
        self.destroy()
        
    def on_cancel(self):
        """Clean up resources before closing"""
        self.running = False
        if self.camera is not None:
            self.camera.release()
        if self.preview_thread is not None:
            self.preview_thread.join(timeout=1.0)
        self.on_complete(False)
        self.destroy()

class LoginView(ttk.Frame):
    def __init__(self, parent, security, on_login_success):
        super().__init__(parent)
        self.security = security
        self.on_login_success = on_login_success
        self.setup_ui()
    
    def setup_ui(self):
        # Login frame
        login_frame = ttk.LabelFrame(self, text="Login")
        login_frame.pack(padx=20, pady=20)
        
        # Username field
        self.username_var = tk.StringVar()
        ttk.Label(login_frame, text="Username:").pack(pady=5)
        ttk.Entry(login_frame, textvariable=self.username_var).pack(pady=5)
        
        # Preview canvas for face detection
        self.preview_canvas = tk.Canvas(login_frame, width=640, height=480)
        self.preview_canvas.pack(pady=10)
        
        # Status label for feedback
        self.status_label = ttk.Label(login_frame, text="Enter username to begin")
        self.status_label.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(login_frame)
        btn_frame.pack(pady=10)
        
        self.login_btn = ttk.Button(btn_frame, text="Login", command=self.start_login)
        self.login_btn.pack(side=tk.LEFT, padx=5)
        
        self.register_btn = ttk.Button(btn_frame, text="Register Face", command=self.register_face)
        self.register_btn.pack(side=tk.LEFT, padx=5)
        
    def start_login(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter username")
            return
            
        if not self.security.has_registered_face(username):
            response = messagebox.askyesno(
                "Face Registration Required", 
                "You need to register your face before logging in.\nWould you like to register now?"
            )
            if response:
                self.register_face()
            return
        
        # Update status and begin face verification
        self.status_label.config(text="Starting camera...")
        self.update()
        
        # Clear canvas
        self.preview_canvas.delete("all")
        self.preview_canvas.configure(bg='black')
        self.preview_canvas.create_text(
            320, 240,
            text="Initializing camera...",
            fill="white",
            font=('TkDefaultFont', 14)
        )
        
        # Verify face using preview canvas
        if self.security.verify_user(username, self.preview_canvas, self.status_label):
            self.status_label.config(text="Face verified successfully!")
            self.update()
            self.after(1000, lambda: self.complete_login(username))
        else:
            self.preview_canvas.delete("all")
            self.preview_canvas.configure(bg='white')
            self.status_label.config(text="Face verification failed. Please try again.")
            
    def complete_login(self, username):
        self.status_label.config(text="Loading account management...")
        self.update()
        self.on_login_success(username)

    def register_face(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter username first")
            return
        
        if self.security.has_registered_face(username):
            if not messagebox.askyesno(
                "Re-register Face", 
                "Face already registered. Do you want to register again?"
            ):
                return

        def on_registration_complete(success):
            if success:
                self.status_label.config(text="Face registered. Please login.")
            else:
                self.status_label.config(text="Face registration failed. Please try again.")

        registration_window = FaceRegistrationWindow(
            self, 
            username,
            self.security,
            on_registration_complete
        )
        registration_window.focus()
