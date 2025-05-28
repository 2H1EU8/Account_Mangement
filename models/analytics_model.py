from datetime import datetime
import psycopg2
from config import Config

class AnalyticsModel:
    def __init__(self):
        self.conn = psycopg2.connect(**Config.DB_CONFIG)
        self.cur = self.conn.cursor()

    def calculate_analytics(self, owner_username):
        """Calculate password analytics for user"""
        try:
            query = """
                WITH stats AS (
                    SELECT 
                        COUNT(*) as total,
                        COALESCE(AVG(NULLIF(password_strength, 0)), 0) as avg_strength,
                        COUNT(CASE WHEN password_strength < 40 THEN 1 END) as weak,
                        COUNT(CASE WHEN password_strength BETWEEN 40 AND 70 THEN 1 END) as medium,
                        COUNT(CASE WHEN password_strength > 70 THEN 1 END) as strong
                    FROM accounts
                    WHERE owner_username = %s
                )
                INSERT INTO password_analytics 
                (owner_username, total_accounts, avg_strength, 
                 weak_passwords, medium_passwords, strong_passwords)
                SELECT %s, total, avg_strength, weak, medium, strong
                FROM stats
                RETURNING *;
            """
            self.cur.execute(query, (owner_username, owner_username))
            result = self.cur.fetchone()
            self.conn.commit()
            
            if not result:
                # Return default values if no data
                return (None, owner_username, 0, 0.0, 0, 0, 0)
            return result
            
        except Exception as e:
            self.conn.rollback()
            print(f"Analytics calculation error: {e}")
            return None

    def get_historical_analytics(self, owner_username, limit=30):
        """Get historical analytics data"""
        query = """
            SELECT analyzed_at, avg_strength 
            FROM password_analytics
            WHERE owner_username = %s
            ORDER BY analyzed_at DESC
            LIMIT %s
        """
        self.cur.execute(query, (owner_username, limit))
        return self.cur.fetchall()

    def __del__(self):
        self.cur.close()
        self.conn.close()
