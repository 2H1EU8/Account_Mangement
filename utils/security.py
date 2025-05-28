import os
import cv2
import numpy as np
from cryptography.fernet import Fernet
import subprocess
import getpass
from config import Config
import threading
import tkinter as tk

# Handle PIL import with fallback
try:
    from PIL import Image, ImageTk
except ImportError:
    print("Installing Pillow package...")
    os.system('pip install Pillow')
    from PIL import Image, ImageTk

# Try to import pyperclip, fallback to xclip if not available
try:
    import pyperclip
except ImportError:
    class ClipboardFallback:
        @staticmethod
        def copy(text):
            with open('/tmp/clipboard.txt', 'w') as f:
                f.write(text)
            subprocess.run(['xclip', '-selection', 'clipboard', '/tmp/clipboard.txt'])
            
        @staticmethod
        def paste():
            try:
                return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o']).decode()
            except:
                return ''
    pyperclip = ClipboardFallback

class SecurityUtils:
    def __init__(self):
        self.fernet = Fernet(Config.SECRET_KEY)
        self._ensure_data_directory()
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.current_user = None
        self.face_threshold = 0.5
        self.preview_size = (640, 480)  # Standard webcam size
        self.logged_in_user = None  # Add this to track current logged in user
        self.sensitive_operations = {'login', 'copy_password'}  # Only login and copy need verification
        self.reference_image = None  # Initialize reference_image
        
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        self.data_dir = os.path.join(Config.BASE_DIR, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def _get_user_face_path(self, username):
        return os.path.join(self.data_dir, f'face_{username}.jpg')
        
    def has_registered_face(self, username):
        return os.path.exists(self._get_user_face_path(username))
        
    def _load_reference_image(self):
        """Load reference image for authentication"""
        ref_path = os.path.join(self.data_dir, 'reference.jpg')
        if os.path.exists(ref_path):
            return cv2.imread(ref_path)
        return None
        
    def _detect_face(self, frame):
        """Detect face in frame using OpenCV"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        return len(faces) > 0, faces
    
    def capture_reference_image(self, username, canvas=None):
        """Capture and save reference image for user"""
        face_path = self._get_user_face_path(username)
        cap = cv2.VideoCapture(0)
        
        try:
            # Set capture resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.preview_size[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.preview_size[1])
            
            # Configure canvas if provided
            if canvas:
                canvas.configure(width=self.preview_size[0], height=self.preview_size[1])
                canvas.update()
                
            success = False
            running = True
            
            while running:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                display_frame = frame.copy()
                has_face, faces = self._detect_face(frame)
                
                # Draw guide overlay
                height, width = frame.shape[:2]
                center_x, center_y = width // 2, height // 2
                cv2.circle(display_frame, (center_x, center_y), 
                          min(center_x, center_y) - 50, (0, 255, 0), 2)
                
                # Draw face rectangle and status text
                if has_face:
                    for (x, y, w, h) in faces:
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(display_frame, "Press SPACE to capture", (10, height - 20),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(display_frame, "No face detected", (10, height - 20),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Update canvas if provided
                if canvas:
                    try:
                        self._update_preview(canvas, display_frame)
                        canvas.update()
                    except Exception as e:
                        print(f"Canvas update error: {e}")
                        running = False
                        break

                # Handle key events
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' ') and has_face:  # SPACE
                    cv2.imwrite(face_path, frame)
                    success = True
                    running = False
                elif key == 27:  # ESC
                    running = False
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
        return success
        
    def verify_image(self, canvas=None, status_label=None):
        """Verify face with continuous preview"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return False
            
        # Set capture resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.preview_size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.preview_size[1])
        
        if canvas:
            canvas.configure(width=self.preview_size[0], height=self.preview_size[1])
            
        max_attempts = 3
        attempts = 0
        
        try:
            while attempts < max_attempts:
                ret, frame = cap.read()
                if not ret:
                    break

                display_frame = frame.copy()
                has_face, faces = self._detect_face(frame)
                
                # Draw guide overlay
                height, width = frame.shape[:2]
                center_x, center_y = width // 2, height // 2
                cv2.circle(display_frame, (center_x, center_y), 
                          min(center_x, center_y) - 50, 
                          (0, 255, 0) if has_face else (0, 0, 255), 2)
                
                if has_face:
                    for (x, y, w, h) in faces:
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        
                # Update UI with preview
                if canvas:
                    try:
                        self._update_preview(canvas, display_frame)
                        canvas.update()
                    except Exception as e:
                        print(f"Preview update error: {e}")
                
                # Update status
                if status_label:
                    if has_face:
                        status_label.config(text=f"Face detected! Verifying... ({max_attempts - attempts} attempts left)")
                    else:
                        status_label.config(text="Position your face in the circle")

                if has_face:
                    # Compare with reference
                    try:
                        result = cv2.matchTemplate(
                            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                            cv2.cvtColor(self.reference_image, cv2.COLOR_BGR2GRAY),
                            cv2.TM_CCOEFF_NORMED
                        )
                        similarity = np.max(result)
                        
                        if similarity > self.face_threshold:
                            return True
                            
                        attempts += 1
                    except Exception as e:
                        print(f"Face comparison error: {e}")
                        attempts += 1
                        
                cv2.waitKey(100)  # Add small delay
                
        finally:
            cap.release()
            cv2.destroy_all_windows()
            
        return False

    def encrypt_password(self, password: str) -> str:
        return self.fernet.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted: str) -> str:
        if self.verify_image():
            return self.fernet.decrypt(encrypted.encode()).decode()
        raise PermissionError("Authentication required")
    
    def check_password_strength(self, password: str) -> int:
        score = 0
        if len(password) >= 8: score += 20
        if any(c.isupper() for c in password): score += 20
        if any(c.islower() for c in password): score += 20
        if any(c.isdigit() for c in password): score += 20
        if any(not c.isalnum() for c in password): score += 20
        return score

    def has_reference_image(self):
        """Check if reference image exists"""
        ref_path = os.path.join(self.data_dir, 'reference.jpg')
        return os.path.exists(ref_path) and self.reference_image is not None

    def verify_auth(self):
        """Main authentication method"""
        if not self.has_reference_image():
            return self._verify_system_password()
        return self.verify_image()
    
    def _verify_system_password(self):
        """Fallback authentication"""
        try:
            password = getpass.getpass("Enter system password for verification: ")
            cmd = ['sudo', '-k', '-S', 'true']
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(input=f"{password}\n".encode())
            return process.returncode == 0
        except Exception as e:
            print(f"Password verification failed: {e}")
            return False

    def clear_reference_image(self):
        """Clear stored reference image"""
        ref_path = os.path.join(self.data_dir, 'reference.jpg')
        if os.path.exists(ref_path):
            os.remove(ref_path)
        self.reference_image = None
        return True
    
    def update_preview(self, canvas, frame):
        """Update canvas with current webcam frame"""
        if frame is not None:
            try:
                # Convert frame to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Get canvas dimensions, use frame dimensions as fallback
                canvas_width = canvas.winfo_width() or frame.shape[1]
                canvas_height = canvas.winfo_height() or frame.shape[0]
                
                # Configure canvas size if not set
                if canvas_width <= 1 or canvas_height <= 1:
                    canvas_width = frame.shape[1]
                    canvas_height = frame.shape[0]
                    canvas.configure(width=canvas_width, height=canvas_height)
                
                # Calculate scaling factor (ensure positive values)
                scale = min(
                    canvas_width/max(1, frame.shape[1]), 
                    canvas_height/max(1, frame.shape[0])
                )
                
                # Resize frame
                new_width = max(1, int(frame.shape[1] * scale))
                new_height = max(1, int(frame.shape[0] * scale))
                resized = cv2.resize(rgb_frame, (new_width, new_height))
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(Image.fromarray(resized))
                
                # Clear previous image
                canvas.delete("all")
                
                # Update canvas
                canvas.create_image(
                    canvas_width/2, canvas_height/2,
                    image=photo, anchor=tk.CENTER
                )
                canvas.image = photo  # Keep reference!
                
            except Exception as e:
                print(f"Preview update error: {e}")

    def verify_user(self, username, canvas=None, status_label=None, operation='default'):
        """Verify user face only for sensitive operations"""
        # Skip verification for non-sensitive operations
        if operation not in self.sensitive_operations:
            return True
            
        try:
            # Load reference image first
            face_path = self._get_user_face_path(username)
            self.reference_image = cv2.imread(face_path)
            if self.reference_image is None:
                raise Exception("Failed to load reference image")

            # Configure camera and canvas
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                if status_label:
                    status_label.config(text="Failed to open camera")
                return False
                
            # Set capture resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.preview_size[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.preview_size[1])
            
            if canvas:
                canvas.configure(width=self.preview_size[0], height=self.preview_size[1])
                canvas.update()
            
            max_attempts = 3
            attempts = 0
            
            while attempts < max_attempts:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Update preview
                if canvas:
                    display_frame = frame.copy()
                    has_face = self._detect_face(frame)[0]
                    
                    # Draw guide overlay
                    height, width = frame.shape[:2]
                    center_x, center_y = width // 2, height // 2
                    cv2.circle(display_frame, (center_x, center_y), 
                             min(center_x, center_y) - 50, 
                             (0, 255, 0) if has_face else (0, 0, 255), 2)
                    
                    self.update_preview(canvas, display_frame)
                    canvas.update()
                    
                    if status_label:
                        status_label.config(text=f"Verifying... ({max_attempts - attempts} attempts left)")
                
                if self._detect_face(frame)[0]:
                    # Compare with reference using grayscale
                    try:
                        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        ref_gray = cv2.cvtColor(self.reference_image, cv2.COLOR_BGR2GRAY)
                        
                        result = cv2.matchTemplate(frame_gray, ref_gray, cv2.TM_CCOEFF_NORMED)
                        similarity = np.max(result)
                        
                        if similarity > self.face_threshold:
                            if operation == 'login':
                                self.logged_in_user = username
                            return True
                    except Exception as e:
                        print(f"Face comparison warning: {e}")
                        
                attempts += 1
                cv2.waitKey(100)
                
        except Exception as e:
            print(f"Verification error: {e}")
            if status_label:
                status_label.config(text=f"Verification error: {str(e)}")
            return False
            
        finally:
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()
            
        return False

    def reset_all_face_data(self):
        """Remove all face data files"""
        import glob
        face_files = glob.glob(os.path.join(self.data_dir, 'face_*.jpg'))
        for f in face_files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"Error removing {f}: {e}")
        return len(face_files)
    
    def secure_copy_password(self, password, canvas=None, status_label=None):
        """Verify face before copying password"""
        if not self.logged_in_user:
            return False
            
        try:
            if self.verify_user(self.logged_in_user, canvas, status_label, operation='copy_password'):
                pyperclip.copy(password)
                threading.Timer(30.0, lambda: pyperclip.copy('')).start()
                return True
            return False
        except Exception as e:
            print(f"Secure copy error: {e}")
            return False
            
    def logout_user(self):
        """Clear current user session"""
        self.logged_in_user = None
        self.reference_image = None
