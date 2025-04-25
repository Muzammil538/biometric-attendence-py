"""
GUI Interface
PyQt5-based user interface for the attendance system
"""

import sys
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QLineEdit, QTableWidget, 
                           QTableWidgetItem, QTabWidget, QGroupBox, 
                           QFormLayout, QSpinBox, QMessageBox, QFileDialog,
                           QDateEdit, QStatusBar)
from PyQt5.QtCore import Qt, QDate


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.attendance_mode_active = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI elements"""
        self.setWindowTitle("Biometric Attendance System")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.create_attendance_tab()
        self.create_users_tab()
        self.create_reports_tab()
        self.create_settings_tab()
        
        # Add tabs to tab widget
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connection status label
        self.connection_label = QLabel("Not Connected")
        self.connection_label.setStyleSheet("color: red;")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # Status message label
        self.status_message = QLabel("")
        self.status_bar.addWidget(self.status_message)
        
        # Set central widget
        self.setCentralWidget(central_widget)
    
    def create_attendance_tab(self):
        """Create the attendance tab"""
        attendance_tab = QWidget()
        layout = QVBoxLayout(attendance_tab)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("Start Attendance Mode")
        self.btn_start.clicked.connect(self.toggle_attendance_mode)
        btn_layout.addWidget(self.btn_start)
        
        self.btn_refresh = QPushButton("Refresh List")
        self.btn_refresh.clicked.connect(self.controller.update_attendance_list)
        btn_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(btn_layout)
        
        # Attendance table
        self.attendance_table = QTableWidget(0, 3)
        self.attendance_table.setHorizontalHeaderLabels(["ID", "Name", "Time"])
        self.attendance_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.attendance_table)
        
        # Status label
        self.attendance_status = QLabel("Ready")
        layout.addWidget(self.attendance_status)
        
        self.tabs.addTab(attendance_tab, "Attendance")
    
    def create_users_tab(self):
        """Create the users management tab"""
        users_tab = QWidget()
        layout = QVBoxLayout(users_tab)
        
        # User enrollment group
        enroll_group = QGroupBox("Enroll New User")
        enroll_layout = QFormLayout()
        
        self.user_id_input = QSpinBox()
        self.user_id_input.setRange(1, 127)  # R307 usually supports up to 127 templates
        enroll_layout.addRow("User ID:", self.user_id_input)
        
        self.user_name_input = QLineEdit()
        enroll_layout.addRow("Name:", self.user_name_input)
        
        self.btn_enroll = QPushButton("Enroll Fingerprint")
        self.btn_enroll.clicked.connect(self.enroll_user)
        enroll_layout.addRow("", self.btn_enroll)
        
        enroll_group.setLayout(enroll_layout)
        layout.addWidget(enroll_group)
        
        # User list
        list_group = QGroupBox("User List")
        list_layout = QVBoxLayout()
        
        self.users_table = QTableWidget(0, 3)
        self.users_table.setHorizontalHeaderLabels(["ID", "Name", "Actions"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        list_layout.addWidget(self.users_table)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        self.tabs.addTab(users_tab, "Users")
    
    def create_reports_tab(self):
        """Create the reports tab"""
        reports_tab = QWidget()
        layout = QVBoxLayout(reports_tab)
        
        # Date range selection
        date_group = QGroupBox("Select Date Range")
        date_layout = QFormLayout()
        
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        date_layout.addRow("Start Date:", self.start_date)
        
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addRow("End Date:", self.end_date)
        
        self.btn_generate = QPushButton("Generate Report")
        self.btn_generate.clicked.connect(self.generate_report)
        date_layout.addRow("", self.btn_generate)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        self.tabs.addTab(reports_tab, "Reports")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # Database management group
        db_group = QGroupBox("Database Management")
        db_layout = QVBoxLayout()
        
        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self.backup_database)
        db_layout.addWidget(backup_btn)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Fingerprint sensor group
        sensor_group = QGroupBox("Fingerprint Sensor")
        sensor_layout = QVBoxLayout()
        
        check_btn = QPushButton("Check Sensor")
        check_btn.clicked.connect(self.controller.check_sensor)
        sensor_layout.addWidget(check_btn)
        
        clear_btn = QPushButton("Clear Sensor Database")
        clear_btn.clicked.connect(self.clear_sensor_database)
        sensor_layout.addWidget(clear_btn)
        
        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)
        
        self.tabs.addTab(settings_tab, "Settings")
    
    def update_connection_status(self, connected):
        """Update connection status display"""
        if connected:
            self.connection_label.setText("Connected")
            self.connection_label.setStyleSheet("color: green;")
        else:
            self.connection_label.setText("Not Connected")
            self.connection_label.setStyleSheet("color: red;")
    
    def update_status_message(self, message):
        """Update status message"""
        self.status_message.setText(message)
        self.attendance_status.setText(message)
    
    def show_message(self, message):
        """Show information message"""
        QMessageBox.information(self, "Information", message)
    
    def show_warning(self, message):
        """Show warning message"""
        QMessageBox.warning(self, "Warning", message)
    
    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
    
    def update_user_list(self, users):
        """Update the user list table"""
        self.users_table.setRowCount(0)
        
        for row, user in enumerate(users):
            self.users_table.insertRow(row)
            
            # ID and Name
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['name']))
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, id=user['id']: self.delete_user(id))
            self.users_table.setCellWidget(row, 2, delete_btn)
    
    def update_attendance_list(self, attendance):
        """Update the attendance list table"""
        self.attendance_table.setRowCount(0)
        
        for row, record in enumerate(attendance):
            self.attendance_table.insertRow(row)
            
            # Format time
            time_str = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
            
            # Set items
            self.attendance_table.setItem(row, 0, QTableWidgetItem(str(record['id'])))
            self.attendance_table.setItem(row, 1, QTableWidgetItem(record['name']))
            self.attendance_table.setItem(row, 2, QTableWidgetItem(time_str))
    
    def enroll_user(self):
        """Handle user enrollment"""
        user_id = self.user_id_input.value()
        name = self.user_name_input.text().strip()
        
        if not name:
            self.show_warning("Please enter a name for the user")
            return
        
        if self.controller.enroll_new_user(user_id, name):
            self.update_status_message("Place finger on sensor...")
        else:
            self.show_error("Failed to enroll user. ID may already be in use.")
    
    def delete_user(self, user_id):
        """Handle user deletion"""
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                    f"Are you sure you want to delete user ID {user_id}?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.controller.delete_user(user_id):
                self.show_message(f"User {user_id} deleted successfully")
            else:
                self.show_error("Failed to delete user")
    
    def toggle_attendance_mode(self):
        """Toggle attendance mode on/off"""
        if self.attendance_mode_active:
            # Turn off attendance mode
            self.attendance_mode_active = False
            self.btn_start.setText("Start Attendance Mode")
            self.update_status_message("Attendance mode stopped")
        else:
            # Turn on attendance mode
            self.attendance_mode_active = True
            self.btn_start.setText("Stop Attendance Mode")
            self.update_status_message("Waiting for fingerprint...")
            self.controller.start_attendance_mode()
    
    def is_attendance_mode_active(self):
        """Return if attendance mode is active"""
        return self.attendance_mode_active
    
    def generate_report(self):
        """Generate attendance report"""
        start = self.start_date.date().toString('yyyy-MM-dd')
        end = self.end_date.date().toString('yyyy-MM-dd')
        
        # Validate date range
        if self.start_date.date() > self.end_date.date():
            self.show_warning("Start date must be before end date")
            return
        
        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
                
            self.controller.export_attendance_report(start, end, file_path)
    
    def backup_database(self):
        """Backup the database file"""
        current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"attendance_backup_{current_date}.db"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Database Backup", default_filename, 
            "Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            try:
                # Simple file copy as backup
                import shutil
                shutil.copy2(self.controller.db.db_file, file_path)
                self.show_message(f"Database backed up to {file_path}")
            except Exception as e:
                self.show_error(f"Backup failed: {e}")
    
    def clear_sensor_database(self):
        """Clear fingerprint sensor database"""
        reply = QMessageBox.question(self, 'Confirm Clear Database', 
                                    "Are you sure you want to clear ALL fingerprints from the sensor?\n"
                                    "This cannot be undone!",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.controller.arduino.empty_database()
            self.show_message("Fingerprint database cleared")