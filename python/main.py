"""
Biometric Attendance System - Main Controller
Main program that ties all components together
"""

import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from arduino_controller import ArduinoController
from database_manager import DatabaseManager
from gui import MainWindow


class AttendanceSystem:
    def __init__(self):
        self.arduino = ArduinoController()
        self.db = DatabaseManager()
        
        # Create GUI application
        self.app = QApplication(sys.argv)
        self.window = MainWindow(self)
        
        # Connect signals
        self.arduino.message_received.connect(self.process_arduino_message)
        self.arduino.connection_status.connect(self.window.update_connection_status)
        
        # Setup system
        self.setup()
    
    def setup(self):
        """Initialize the system"""
        # Connect to Arduino
        if not self.arduino.connect():
            self.window.show_error("Cannot connect to Arduino. Please check connections and try again.")
        
        # Initialize database
        self.db.initialize()
        
        # Update UI with user list
        self.update_user_list()
    
    def run(self):
        """Run the application"""
        self.window.show()
        return self.app.exec_()
    
    def update_user_list(self):
        """Update the UI with current user list"""
        users = self.db.get_all_users()
        self.window.update_user_list(users)
    
    def update_attendance_list(self):
        """Update the UI with current attendance records"""
        attendance = self.db.get_today_attendance()
        self.window.update_attendance_list(attendance)
    
    def process_arduino_message(self, message):
        """Process messages from Arduino"""
        if message.startswith("F:MATCH:"):
            # Fingerprint match found
            user_id = int(message.split(":")[2])
            user = self.db.get_user(user_id)
            
            if user:
                # Record attendance
                self.db.mark_attendance(user_id)
                self.window.show_message(f"Attendance marked for {user['name']}")
                self.update_attendance_list()
            else:
                self.window.show_warning(f"Fingerprint ID {user_id} not registered in database")
        
        elif message.startswith("F:ENROLLED:"):
            # Enrollment completed
            self.window.show_message("Fingerprint enrolled successfully")
            self.update_user_list()
        
        elif message.startswith("F:"):
            # Other status messages
            self.window.update_status_message(message[2:])
    
    def enroll_new_user(self, user_id, name):
        """Enroll a new user with fingerprint"""
        # First add user to database
        if self.db.add_user(user_id, name):
            # Then start fingerprint enrollment
            self.arduino.enroll_fingerprint(user_id)
            return True
        return False
    
    def delete_user(self, user_id):
        """Delete a user from system"""
        if self.db.delete_user(user_id):
            # Remove fingerprint from sensor
            self.arduino.delete_fingerprint(user_id)
            self.update_user_list()
            return True
        return False
    
    def start_attendance_mode(self):
        """Start attendance verification mode"""
        self.arduino.verify_fingerprint()
        # Set timer to request verification again after delay
        QTimer.singleShot(3000, self.continue_attendance_mode)
    
    def continue_attendance_mode(self):
        """Continue attendance mode if active"""
        if self.window.is_attendance_mode_active():
            self.arduino.verify_fingerprint()
            QTimer.singleShot(3000, self.continue_attendance_mode)
    
    def export_attendance_report(self, start_date, end_date, file_path):
        """Export attendance report to file"""
        records = self.db.get_attendance_range(start_date, end_date)
        # Export as CSV
        self.db.export_to_csv(records, file_path)
        self.window.show_message(f"Report exported to {file_path}")


if __name__ == "__main__":
    system = AttendanceSystem()
    sys.exit(system.run())