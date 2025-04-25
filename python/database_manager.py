"""
Database Manager
Handles user data and attendance records storage
"""

import sqlite3
import os
import csv
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_file="attendance.db"):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
    
    def initialize(self):
        """Initialize database and create tables if they don't exist"""
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(self.db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Connect to database
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row  # Return results as dictionary
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables"""
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Attendance table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, name):
        """Add a new user to the database"""
        try:
            self.cursor.execute(
                "INSERT INTO users (id, name) VALUES (?, ?)",
                (user_id, name)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # ID already exists
            return False
    
    def delete_user(self, user_id):
        """Delete a user from the database"""
        try:
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user information by ID"""
        self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return self.cursor.fetchone()
    
    def get_all_users(self):
        """Get all users"""
        self.cursor.execute("SELECT * FROM users ORDER BY id")
        return self.cursor.fetchall()
    
    def mark_attendance(self, user_id):
        """Mark attendance for a user"""
        try:
            # Check if already marked today
            today = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute(
                "SELECT COUNT(*) FROM attendance WHERE user_id = ? AND date(timestamp) = date(?)",
                (user_id, today)
            )
            
            if self.cursor.fetchone()[0] == 0:
                # Not marked today, add record
                self.cursor.execute(
                    "INSERT INTO attendance (user_id) VALUES (?)",
                    (user_id,)
                )
                self.conn.commit()
            
            return True
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def get_today_attendance(self):
        """Get attendance records for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''
            SELECT u.id, u.name, a.timestamp 
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE date(a.timestamp) = date(?)
            ORDER BY a.timestamp DESC
        ''', (today,))
        
        return self.cursor.fetchall()
    
    def get_attendance_range(self, start_date, end_date):
        """Get attendance records for a date range"""
        self.cursor.execute('''
            SELECT u.id, u.name, date(a.timestamp) as date, 
                   time(a.timestamp) as time
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE date(a.timestamp) BETWEEN ? AND ?
            ORDER BY a.timestamp
        ''', (start_date, end_date))
        
        return self.cursor.fetchall()
    
    def export_to_csv(self, records, file_path):
        """Export records to CSV file"""
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['ID', 'Name', 'Date', 'Time'])
                
                # Write data
                for record in records:
                    writer.writerow([record['id'], record['name'], 
                                    record['date'], record['time']])
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()