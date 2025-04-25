"""
Configuration Module
Contains configuration settings for the attendance system
"""

import os
import json
from pathlib import Path


class Config:
    # Default configuration
    DEFAULT_CONFIG = {
        "arduino_port": None,  # Auto-detect
        "baud_rate": 9600,
        "database_file": "attendance.db",
        "data_dir": "data",
        "log_level": "INFO",
        "attendance_timeout": 30,  # seconds between attendance marks
    }
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.settings = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            # If config file exists, load it
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                # Otherwise use defaults and save them
                self.settings = self.DEFAULT_CONFIG.copy()
                self.save_config()
                
            # Create data directory if it doesn't exist
            data_dir = self.get("data_dir")
            if data_dir and not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
        except Exception as e:
            print(f"Error loading config: {e}")
            self.settings = self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set configuration value and save"""
        self.settings[key] = value
        return self.save_config()
    
    def get_database_path(self):
        """Get full database path"""
        data_dir = self.get("data_dir", "data")
        db_file = self.get("database_file", "attendance.db")
        return os.path.join(data_dir, db_file)