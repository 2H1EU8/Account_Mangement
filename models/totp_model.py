import pyotp
import qrcode
import base64
from io import BytesIO
import psycopg2
from config import Config
from utils.security import SecurityUtils

class TOTPModel:
    def __init__(self):
        self.conn = psycopg2.connect(**Config.DB_CONFIG)
        self.cur = self.conn.cursor()
        self.security = SecurityUtils()

    def setup_2fa(self, user_id, username):
        """Set up 2FA for user"""
        try:
            # Generate TOTP secret
            secret = pyotp.random_base32()
            
            # Generate backup codes
            backup_codes = [pyotp.random_base32()[:8] for _ in range(8)]
            encrypted_codes = [self.security.encrypt_password(code) for code in backup_codes]
            
            # Save to database
            query = """
                INSERT INTO totp_settings (user_id, secret_key, backup_codes, enabled)
                VALUES (%s, %s, %s, true)
                ON CONFLICT (user_id) DO UPDATE
                SET secret_key = EXCLUDED.secret_key,
                    backup_codes = EXCLUDED.backup_codes,
                    enabled = EXCLUDED.enabled
            """
            self.cur.execute(query, (user_id, secret, encrypted_codes))
            self.conn.commit()
            
            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(username, issuer_name="Account Manager")
            
            img = qrcode.make(provisioning_uri)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                'secret': secret,
                'backup_codes': backup_codes,
                'qr_code': qr_base64
            }
            
        except Exception as e:
            self.conn.rollback()
            raise e

    def verify_totp(self, user_id, code):
        """Verify TOTP code"""
        try:
            # Get secret from database
            query = "SELECT secret_key, backup_codes FROM totp_settings WHERE user_id = %s"
            self.cur.execute(query, (user_id,))
            result = self.cur.fetchone()
            
            if not result:
                return False
                
            secret, backup_codes = result
            
            # Check if it's a backup code
            for encrypted_code in backup_codes:
                try:
                    if self.security.decrypt_password(encrypted_code) == code:
                        # Remove used backup code
                        backup_codes.remove(encrypted_code)
                        self.cur.execute(
                            "UPDATE totp_settings SET backup_codes = %s WHERE user_id = %s",
                            (backup_codes, user_id)
                        )
                        self.conn.commit()
                        return True
                except:
                    continue
            
            # Verify TOTP
            totp = pyotp.TOTP(secret)
            return totp.verify(code)
            
        except Exception as e:
            print(f"TOTP verification error: {e}")
            return False

    def __del__(self):
        self.cur.close()
        self.conn.close()
