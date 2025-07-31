#!/usr/bin/env python3
"""
Printer Interface for Slide Scanner v2
Clean, reliable printer communication and movement control
"""

import serial
import time
import glob
import sys

class PrinterInterface:
    def __init__(self, baudrate=115200, timeout=60):
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
        
    def find_printer_port(self):
        """Automatically detect printer port"""
        possible_ports = [
            '/dev/cu.usbserial-*',
            '/dev/tty.usbserial-*', 
            '/dev/cu.usbmodem*',
            '/dev/tty.usbmodem*'
        ]
        
        for pattern in possible_ports:
            ports = glob.glob(pattern)
            for port in ports:
                try:
                    test_connection = serial.Serial(port, self.baudrate, timeout=2)
                    test_connection.close()
                    print(f"Found printer port: {port}")
                    return port
                except:
                    continue
        return None
    
    def connect(self, port=None):
        """Connect to printer"""
        if port is None:
            port = self.find_printer_port()
            if port is None:
                raise Exception("No printer found. Check USB connection.")
        
        try:
            self.serial_connection = serial.Serial(port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for connection to stabilize
            
            # Clear any startup messages
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()
            
            print(f"Connected to printer on {port}")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_command(self, command):
        """Send G-code command and wait for response"""
        if not self.serial_connection:
            raise Exception("Printer not connected")
        
        # Send command
        full_command = command.strip() + '\n'
        self.serial_connection.write(full_command.encode())
        
        # Wait for 'ok' response
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.readline().decode().strip()
                if 'ok' in response.lower():
                    return response
                elif 'error' in response.lower():
                    raise Exception(f"Printer error: {response}")
        
        raise Exception(f"Timeout waiting for response to: {command}")
    
    def home_printer(self):
        """Home all axes"""
        print("Homing printer...")
        self.send_command("G28")  # Home all axes
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
        print("Homing complete")
    
    def move_to_position(self, x=None, y=None, z=None, feedrate=3000):
        """Move to absolute position"""
        command = f"G1 F{feedrate}"
        
        if x is not None:
            command += f" X{x}"
            self.current_position['X'] = x
        if y is not None:
            command += f" Y{y}" 
            self.current_position['Y'] = y
        if z is not None:
            command += f" Z{z}"
            self.current_position['Z'] = z
            
        self.send_command(command)
    
    def move_relative(self, dx=0, dy=0, dz=0, feedrate=3000):
        """Move relative to current position"""
        self.send_command("G91")  # Relative positioning
        command = f"G1 F{feedrate}"
        
        if dx != 0:
            command += f" X{dx}"
            self.current_position['X'] += dx
        if dy != 0:
            command += f" Y{dy}"
            self.current_position['Y'] += dy  
        if dz != 0:
            command += f" Z{dz}"
            self.current_position['Z'] += dz
            
        self.send_command(command)
        self.send_command("G90")  # Back to absolute positioning
    
    def get_position(self):
        """Get current position"""
        return self.current_position.copy()
    
    def disconnect(self):
        """Disconnect from printer"""
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            print("Disconnected from printer")

# Test the interface
if __name__ == "__main__":
    printer = PrinterInterface()
    
    try:
        if printer.connect():
            print("Testing printer interface...")
            printer.home_printer()
            print(f"Current position: {printer.get_position()}")
            
            # Small test movement
            print("Testing small movement...")
            printer.move_relative(dy=5)
            time.sleep(1)
            printer.move_relative(dy=-5)
            print("Test complete")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        printer.disconnect() 
"""
Printer Interface for Slide Scanner v2
Clean, reliable printer communication and movement control
"""

import serial
import time
import glob
import sys

class PrinterInterface:
    def __init__(self, baudrate=115200, timeout=60):
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
        
    def find_printer_port(self):
        """Automatically detect printer port"""
        possible_ports = [
            '/dev/cu.usbserial-*',
            '/dev/tty.usbserial-*', 
            '/dev/cu.usbmodem*',
            '/dev/tty.usbmodem*'
        ]
        
        for pattern in possible_ports:
            ports = glob.glob(pattern)
            for port in ports:
                try:
                    test_connection = serial.Serial(port, self.baudrate, timeout=2)
                    test_connection.close()
                    print(f"Found printer port: {port}")
                    return port
                except:
                    continue
        return None
    
    def connect(self, port=None):
        """Connect to printer"""
        if port is None:
            port = self.find_printer_port()
            if port is None:
                raise Exception("No printer found. Check USB connection.")
        
        try:
            self.serial_connection = serial.Serial(port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for connection to stabilize
            
            # Clear any startup messages
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()
            
            print(f"Connected to printer on {port}")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_command(self, command):
        """Send G-code command and wait for response"""
        if not self.serial_connection:
            raise Exception("Printer not connected")
        
        # Send command
        full_command = command.strip() + '\n'
        self.serial_connection.write(full_command.encode())
        
        # Wait for 'ok' response
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.readline().decode().strip()
                if 'ok' in response.lower():
                    return response
                elif 'error' in response.lower():
                    raise Exception(f"Printer error: {response}")
        
        raise Exception(f"Timeout waiting for response to: {command}")
    
    def home_printer(self):
        """Home all axes"""
        print("Homing printer...")
        self.send_command("G28")  # Home all axes
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
        print("Homing complete")
    
    def move_to_position(self, x=None, y=None, z=None, feedrate=3000):
        """Move to absolute position"""
        command = f"G1 F{feedrate}"
        
        if x is not None:
            command += f" X{x}"
            self.current_position['X'] = x
        if y is not None:
            command += f" Y{y}" 
            self.current_position['Y'] = y
        if z is not None:
            command += f" Z{z}"
            self.current_position['Z'] = z
            
        self.send_command(command)
    
    def move_relative(self, dx=0, dy=0, dz=0, feedrate=3000):
        """Move relative to current position"""
        self.send_command("G91")  # Relative positioning
        command = f"G1 F{feedrate}"
        
        if dx != 0:
            command += f" X{dx}"
            self.current_position['X'] += dx
        if dy != 0:
            command += f" Y{dy}"
            self.current_position['Y'] += dy  
        if dz != 0:
            command += f" Z{dz}"
            self.current_position['Z'] += dz
            
        self.send_command(command)
        self.send_command("G90")  # Back to absolute positioning
    
    def get_position(self):
        """Get current position"""
        return self.current_position.copy()
    
    def disconnect(self):
        """Disconnect from printer"""
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            print("Disconnected from printer")

# Test the interface
if __name__ == "__main__":
    printer = PrinterInterface()
    
    try:
        if printer.connect():
            print("Testing printer interface...")
            printer.home_printer()
            print(f"Current position: {printer.get_position()}")
            
            # Small test movement
            print("Testing small movement...")
            printer.move_relative(dy=5)
            time.sleep(1)
            printer.move_relative(dy=-5)
            print("Test complete")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        printer.disconnect() 
 