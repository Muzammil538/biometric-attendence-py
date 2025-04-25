"""
Arduino Controller
Handles serial communication with Arduino
"""

import serial
import serial.tools.list_ports
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal


class ArduinoController(QObject):
    # Signals
    message_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    
    # Command codes - must match Arduino
    CMD_ENROLL = 'E'
    CMD_VERIFY = 'V'
    CMD_DELETE = 'D'
    CMD_COUNT = 'C'
    CMD_EMPTY = 'X'
    CMD_CHECK = 'P'
    
    def __init__(self, baud_rate=9600):
        super().__init__()
        self.serial = None
        self.baud_rate = baud_rate
        self.is_connected = False
        self.running = False
        self.read_thread = None
    
    def connect(self, port=None):
        """Connect to Arduino"""
        try:
            # Auto-detect Arduino port if not specified
            if port is None:
                ports = list(serial.tools.list_ports.comports())
                for p in ports:
                    # Arduino usually has "Arduino" or "CH340" in description
                    if "Arduino" in p.description or "CH340" in p.description:
                        port = p.device
                        break
            
            if port is None:
                # If still none, try first available port
                if ports:
                    port = ports[0].device
                else:
                    self.connection_status.emit(False)
                    return False
            
            # Connect to the port
            self.serial = serial.Serial(port, self.baud_rate, timeout=1)
            time.sleep(2)  # Allow Arduino to reset
            
            # Start reading thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_serial)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            self.is_connected = True
            self.connection_status.emit(True)
            
            # Ping the Arduino to confirm connection
            self.check_sensor()
            return True
            
        except (serial.SerialException, IOError) as e:
            print(f"Error connecting to Arduino: {e}")
            self.is_connected = False
            self.connection_status.emit(False)
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.is_connected:
            self.running = False
            if self.read_thread:
                self.read_thread.join(timeout=1.0)
            
            if self.serial:
                self.serial.close()
            
            self.is_connected = False
            self.connection_status.emit(False)
    
    def _read_serial(self):
        """Read serial data in background thread"""
        while self.running:
            try:
                if self.serial and self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line:
                        self.message_received.emit(line)
            except Exception as e:
                print(f"Serial read error: {e}")
                self.is_connected = False
                self.connection_status.emit(False)
                break
            time.sleep(0.1)
    
    def _send_command(self, command, param=0):
        """Send command to Arduino"""
        if not self.is_connected:
            return False
        
        try:
            cmd_string = f"{command}{param}\n"
            self.serial.write(cmd_string.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False
    
    def enroll_fingerprint(self, finger_id):
        """Start fingerprint enrollment process"""
        return self._send_command(self.CMD_ENROLL, finger_id)
    
    def verify_fingerprint(self):
        """Start fingerprint verification process"""
        return self._send_command(self.CMD_VERIFY)
    
    def delete_fingerprint(self, finger_id):
        """Delete a fingerprint from sensor"""
        return self._send_command(self.CMD_DELETE, finger_id)
    
    def get_template_count(self):
        """Get number of stored fingerprints"""
        return self._send_command(self.CMD_COUNT)
    
    def empty_database(self):
        """Clear fingerprint database"""
        return self._send_command(self.CMD_EMPTY)
    
    def check_sensor(self):
        """Check if sensor is responding"""
        return self._send_command(self.CMD_CHECK)