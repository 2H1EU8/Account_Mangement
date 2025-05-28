import os
from cryptography.fernet import Fernet

class Config:
    # Database configuration
    DB_CONFIG = {
        'dbname': 'account_manager',
        'user': 'postgres',
        'password': '',
        'host': 'localhost',
        'port': '5432'
    }
    
    # Security settings
    SECRET_KEY = Fernet.generate_key()
    FINGERPRINT_TIMEOUT = 300  # seconds
    PASSWORD_EXPIRY_DAYS = 90
    MIN_PASSWORD_STRENGTH = 60
    
    # UI Configuration
    WINDOW_SIZE = "1200x800"
    THEME_COLOR = {
        'primary': '#2c3e50',
        'secondary': '#34495e',
        'accent': '#3498db',
        'warning': '#e74c3c',
        'success': '#2ecc71',
        'background': '#ecf0f1'
    }
    
    # File paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')
    
    @staticmethod
    def init():
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
