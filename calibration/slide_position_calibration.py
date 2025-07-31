#!/usr/bin/env python3
"""
Slide Position Calibration for Scanner v2
Find the exact position of the slide relative to camera coordinates
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.printer_interface import PrinterInterface
from utils.camera_interface import CameraInterface
import cv2
import time
import json
from datetime import datetime

class SlidePositionCalibrator:
    def __init__(self):
        self.printer = PrinterInterface()
        self.camera = CameraInterface()
        self.slide_holder_height = 2.2  # mm tall slide holder plate
        
    def connect_hardware(self):
        """Connect to printer and camera"""
        print("Connecting to hardware...")
        
        if not self.printer.connect():
            raise Exception("Failed to connect to printer")
            
        if not self.camera.connect():
            raise Exception("Failed to connect to camera")
            
        print("Hardware connected successfully")
        
    def home_and_setup(self):
        """Home printer and move to safe position"""
        print("Homing printer...")
        self.printer.home_printer()
        
        # Move to a safe Z height above the slide holder
        safe_z = self.slide_holder_height + 10  # 10mm above slide holder
        self.printer.move_to_position(z=safe_z)
        print(f"Moved to safe Z height: {safe_z}mm")
        
    def interactive_positioning(self):
        """Interactive tool to position camera over slide center"""
        print("\n=== Interactive Slide Positioning ===")
        print("Use WASD keys to move camera, Q to quit, C to capture center position")
        print("W/S = Y axis (forward/back)")
        print("A/D = X axis (left/right)")  
        print("R/F = Z axis (up/down)")
        print("Numbers 1-5 = move step size (1=0.1mm, 2=0.5mm, 3=1mm, 4=5mm, 5=10mm)")
        
        step_sizes = {1: 0.1, 2: 0.5, 3: 1.0, 4: 5.0, 5: 10.0}
        current_step = 3  # Default to 1mm steps
        
        # Start at printer center (rough estimate)
        start_x, start_y = 110, 110  # Center of typical 220x220 bed
        self.printer.move_to_position(x=start_x, y=start_y)
        
        print(f"Starting position: X={start_x}, Y={start_y}")
        print(f"Current step size: {step_sizes[current_step]}mm")
        
        while True:
            # Show live camera feed
            frame = self.camera.capture_frame()
            
            # Add crosshairs and position info
            h, w = frame.shape[:2]
            cv2.line(frame, (w//2-30, h//2), (w//2+30, h//2), (0, 255, 0), 2)
            cv2.line(frame, (w//2, h//2-30), (w//2, h//2+30), (0, 255, 0), 2)
            
            pos = self.printer.get_position()
            cv2.putText(frame, f"X:{pos['X']:.1f} Y:{pos['Y']:.1f} Z:{pos['Z']:.1f}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Step: {step_sizes[current_step]}mm", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "WASD=move, RF=Z, 1-5=step, C=capture, Q=quit", 
                       (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            cv2.imshow("Slide Positioning", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Capture current position as slide center
                pos = self.printer.get_position()
                print(f"\nCaptured slide center position: X={pos['X']:.1f}, Y={pos['Y']:.1f}, Z={pos['Z']:.1f}")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_dir = "calibration_images"
                os.makedirs(img_dir, exist_ok=True)
                filename = os.path.join(img_dir, f"slide_center_{timestamp}.jpg")
                self.camera.capture_and_save(filename)
                print(f"Center image saved: {filename}")
                cv2.destroyAllWindows()
                return pos
            elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5')]:
                current_step = int(chr(key))
                print(f"Step size changed to: {step_sizes[current_step]}mm")
            elif key == ord('w'):  # Move Y forward
                self.printer.move_relative(dy=step_sizes[current_step])
            elif key == ord('s'):  # Move Y back
                self.printer.move_relative(dy=-step_sizes[current_step])
            elif key == ord('a'):  # Move X left
                self.printer.move_relative(dx=-step_sizes[current_step])
            elif key == ord('d'):  # Move X right
                self.printer.move_relative(dx=step_sizes[current_step])
            elif key == ord('r'):  # Move Z up
                self.printer.move_relative(dz=step_sizes[current_step])
            elif key == ord('f'):  # Move Z down
                self.printer.move_relative(dz=-step_sizes[current_step])
        
        cv2.destroyAllWindows()
        return None
        
    def test_corner_positions(self, center_pos):
        """Test moving to slide corners from center to verify positioning"""
        print("\n=== Testing Corner Positions ===")
        
        # Typical slide dimensions: 75mm x 25mm
        slide_width = 75.0  # mm
        slide_height = 25.0  # mm
        
        corner_offsets = [
            (-slide_width/2, -slide_height/2, "Bottom Left"),
            (slide_width/2, -slide_height/2, "Bottom Right"), 
            (slide_width/2, slide_height/2, "Top Right"),
            (-slide_width/2, slide_height/2, "Top Left"),
            (0, 0, "Center")  # Return to center
        ]
        
        for dx, dy, corner_name in corner_offsets:
            target_x = center_pos['X'] + dx
            target_y = center_pos['Y'] + dy
            
            print(f"Moving to {corner_name}: X={target_x:.1f}, Y={target_y:.1f}")
            self.printer.move_to_position(x=target_x, y=target_y)
            
            # Capture image at corner
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_dir = "calibration_images"
            os.makedirs(img_dir, exist_ok=True)
            filename = os.path.join(img_dir, f"slide_{corner_name.lower().replace(' ', '_')}_{timestamp}.jpg")
            self.camera.capture_and_save(filename)
            print(f"Corner image saved: {filename}")
            
            # Pause to see position
            time.sleep(2)
    
    def save_calibration_data(self, center_pos):
        """Save calibration data to config file"""
        calibration_data = {
            'slide_center_x': center_pos['X'],
            'slide_center_y': center_pos['Y'], 
            'slide_center_z': center_pos['Z'],
            'slide_holder_height': self.slide_holder_height,
            'slide_width': 75.0,  # Standard slide width
            'slide_height': 25.0,  # Standard slide height
            'calibration_date': datetime.now().isoformat(),
            'notes': 'Slide positioned in center of 2.2mm tall holder plate'
        }
        
        config_file = "../config/slide_position.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(calibration_data, f, indent=2)
            
        print(f"\nCalibration data saved to: {config_file}")
        print("Configuration:")
        for key, value in calibration_data.items():
            print(f"  {key}: {value}")
    
    def run_calibration(self):
        """Run complete slide position calibration"""
        try:
            print("=== Slide Position Calibration v2 ===")
            
            self.connect_hardware()
            self.home_and_setup()
            
            center_pos = self.interactive_positioning()
            if center_pos is None:
                print("Calibration cancelled")
                return
                
            self.test_corner_positions(center_pos)
            self.save_calibration_data(center_pos)
            
            print("\n=== Calibration Complete ===")
            print("Next steps:")
            print("1. Run focus calibration to find optimal Z height")
            print("2. Run coverage planning to determine scan pattern")
            
        except Exception as e:
            print(f"Calibration error: {e}")
            
        finally:
            self.printer.disconnect()
            self.camera.disconnect()

if __name__ == "__main__":
    calibrator = SlidePositionCalibrator()
    calibrator.run_calibration() 
 