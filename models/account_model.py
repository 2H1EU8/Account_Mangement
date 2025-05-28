from datetime import datetime, timedelta
import psycopg2
from config import Config
from utils.security import SecurityUtils

class AccountModel:
    def __init__(self):
        self.conn = psycopg2.connect(**Config.DB_CONFIG)
        self.cur = self.conn.cursor()
        self.security = SecurityUtils()

    def create_account(self, data):
        try:
            encrypted_password = self.security.encrypt_password(data['password'])
            query = """
                INSERT INTO accounts 
                (category_id, account_name, username, encrypted_password, url, 
                password_strength, next_password_change, owner_username)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING account_id
            """
            next_change = datetime.now() + timedelta(days=Config.PASSWORD_EXPIRY_DAYS)
            values = (
                data['category_id'], 
                data['account_name'],
                data['username'],
                encrypted_password,
                data['url'],
                data['password_strength'],
                next_change,
                data['owner_username']  # Ensure owner_username is included
            )
            self.cur.execute(query, values)
            account_id = self.cur.fetchone()[0]
            self.conn.commit()
            return account_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_accounts(self, owner_username):
        """Get accounts filtered by owner"""
        try:
            query = """
                SELECT 
                    a.account_id,
                    c.name as category,
                    a.account_name,
                    a.username,
                    COALESCE(to_char(a.last_password_change, 'YYYY-MM-DD HH24:MI'), 'Never'),
                    a.password_strength
                FROM accounts a 
                JOIN categories c ON a.category_id = c.category_id
                WHERE a.owner_username = %s
                ORDER BY a.account_name
            """
            self.cur.execute(query, (owner_username,))
            return self.cur.fetchall()
        except Exception as e:
            print(f"Error in get_accounts: {e}")
            return []

    def get_expiring_passwords(self, days=7):
        try:
            query = """
                SELECT * FROM accounts 
                WHERE next_password_change <= %s
                AND next_password_change >= CURRENT_TIMESTAMP
            """
            expiry_date = datetime.now() + timedelta(days=days)
            self.cur.execute(query, (expiry_date,))
            return self.cur.fetchall()
        except Exception as e:
            raise e

    def update_password(self, account_id, new_password):
        try:
            # Store old password in history
            self.cur.execute(
                "INSERT INTO password_history (account_id, encrypted_password) "
                "SELECT account_id, encrypted_password FROM accounts WHERE account_id = %s",
                (account_id,)
            )
            
            # Update with new password
            encrypted_password = self.security.encrypt_password(new_password)
            next_change = datetime.now() + timedelta(days=Config.PASSWORD_EXPIRY_DAYS)
            
            self.cur.execute("""
                UPDATE accounts 
                SET encrypted_password = %s,
                    last_password_change = CURRENT_TIMESTAMP,
                    next_password_change = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE account_id = %s
            """, (encrypted_password, next_change, account_id))
            
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_categories(self):
        try:
            self.cur.execute("SELECT category_id, name, icon FROM categories ORDER BY name")
            categories = self.cur.fetchall()
            # Return tuple of (display_text, category_id)
            return [(f"{cat[1]}", cat[0]) for cat in categories]
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

    def get_account_by_id(self, account_id):
        try:
            query = """
                SELECT 
                    c.name as category,
                    a.account_name,
                    a.username,
                    a.url,
                    a.encrypted_password,
                    a.password_strength
                FROM accounts a 
                JOIN categories c ON a.category_id = c.category_id
                WHERE a.account_id = %s
            """
            self.cur.execute(query, (account_id,))
            result = self.cur.fetchone()
            if result:
                decrypted_password = None
                try:
                    # Only decrypt if fingerprint verification succeeds
                    decrypted_password = self.security.decrypt_password(result[4])
                except:
                    pass
                    
                return {
                    'category': result[0],
                    'account_name': result[1],
                    'username': result[2],
                    'url': result[3],
                    'password': decrypted_password,
                    'password_strength': result[5]
                }
            return None
        except Exception as e:
            print(f"Error fetching account: {e}")
            return None

    def update_account(self, data):
        try:
            encrypted_password = self.security.encrypt_password(data['password'])
            query = """
                UPDATE accounts 
                SET category_id = %s,
                    account_name = %s,
                    username = %s,
                    encrypted_password = %s,
                    url = %s,
                    password_strength = %s,
                    updated_at = CURRENT_TIMESTAMP,
                    owner_username = %s
                WHERE account_id = %s
                AND owner_username = %s  -- Add owner check for security
            """
            values = (
                data['category_id'],
                data['account_name'],
                data['username'],
                encrypted_password,
                data['url'],
                data['password_strength'],
                data['owner_username'],
                data['account_id'],
                data['owner_username']
            )
            self.cur.execute(query, values)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def delete_account(self, account_id):
        try:
            self.cur.execute("DELETE FROM accounts WHERE account_id = %s", (account_id,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def __del__(self):
        self.cur.close()
        self.conn.close()
