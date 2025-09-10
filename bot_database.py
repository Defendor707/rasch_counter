import sqlite3
import os
import threading
from datetime import datetime

class BotDatabase:
    def __init__(self, db_file=None):
        # Use persistent storage in .data directory
        if db_file is None:
            # Create .data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            db_file = os.path.join(data_dir, 'bot_data.db')
        
        self.db_file = db_file
        # Thread-local storage for connections
        self.local = threading.local()
        self.create_tables()
    
    def connect(self):
        """Create a database connection for the current thread"""
        # Check if this thread already has a connection
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            # Create a new connection for this thread
            self.local.conn = sqlite3.connect(self.db_file)
            self.local.conn.row_factory = sqlite3.Row  # This enables column access by name
        return self.local.conn
    
    def close(self):
        """Close the database connection for the current thread"""
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None
    
    def create_tables(self):
        """Create the necessary tables if they don't exist"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create users table to store user info
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            join_date TEXT,
            last_active TEXT
        )
        ''')
        
        # Create usage_stats table to track file processing
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT,
            timestamp TEXT,
            num_students INTEGER DEFAULT 0,
            num_questions INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        self.close()
    
    def add_user(self, user_id, first_name, last_name="", username=""):
        """Add a new user or update existing user"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        user_exists = cursor.fetchone()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not user_exists:
            # Add new user
            cursor.execute(
                "INSERT INTO users (user_id, first_name, last_name, username, join_date, last_active) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, first_name, last_name, username, current_time, current_time)
            )
        else:
            # Update last active time for existing user
            cursor.execute(
                "UPDATE users SET last_active = ?, first_name = ?, last_name = ?, username = ? WHERE user_id = ?",
                (current_time, first_name, last_name, username, user_id)
            )
        
        conn.commit()
        self.close()
    
    def log_file_processing(self, user_id, action_type, num_students=0, num_questions=0):
        """Log a file processing action"""
        conn = self.connect()
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "INSERT INTO usage_stats (user_id, action_type, timestamp, num_students, num_questions) VALUES (?, ?, ?, ?, ?)",
            (user_id, action_type, current_time, num_students, num_questions)
        )
        
        conn.commit()
        self.close()
    
    def get_all_users(self):
        """Get all users from the database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY last_active DESC")
        users = cursor.fetchall()
        
        self.close()
        return users
    
    def get_user_stats(self, user_id=None):
        """Get usage statistics for a specific user or all users"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if user_id:
            # Stats for specific user
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(CASE WHEN action_type = 'process_exam' THEN 1 END) as exam_count,
                    COUNT(CASE WHEN action_type = 'process_ball' THEN 1 END) as ball_count,
                    SUM(num_students) as total_students,
                    SUM(num_questions) as total_questions,
                    MAX(timestamp) as last_action
                FROM usage_stats
                WHERE user_id = ?
            """, (user_id,))
        else:
            # Stats for all users
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(CASE WHEN action_type = 'process_exam' THEN 1 END) as exam_count,
                    COUNT(CASE WHEN action_type = 'process_ball' THEN 1 END) as ball_count,
                    SUM(num_students) as total_students,
                    SUM(num_questions) as total_questions
                FROM usage_stats
            """)
        
        stats = cursor.fetchone()
        self.close()
        return dict(stats) if stats else {}
    
    def get_active_users_count(self, days=30):
        """Get count of users active in the last X days"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Calculate users active in the last X days
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as active_users 
            FROM usage_stats 
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """, (days,))
        
        result = cursor.fetchone()
        self.close()
        return result['active_users'] if result else 0
    
    def get_top_users(self, limit=10):
        """Get top users by activity"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.user_id, u.first_name, u.username, COUNT(s.id) as action_count
            FROM users u
            JOIN usage_stats s ON u.user_id = s.user_id
            GROUP BY u.user_id
            ORDER BY action_count DESC
            LIMIT ?
        """, (limit,))
        
        top_users = cursor.fetchall()
        self.close()
        return [dict(user) for user in top_users]