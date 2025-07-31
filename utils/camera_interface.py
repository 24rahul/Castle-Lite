#!/usr/bin/env python3
"""
Camera Interface for Slide Scanner v2
Clean, reliable camera control and image capture
"""

import cv2
import numpy as np
import time
import os
from datetime import datetime

class CameraInterface:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.is_connected = False
        self.frame_width = None
        self.frame_height = None
        
    def connect(self):
        """Connect to camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                raise Exception(f"Cannot open camera {self.camera_index}")
            
            # Get camera properties
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer lag
            
            self.is_connected = True
            print(f"Camera connected: {self.frame_width}x{self.frame_height}")
            return True
            
        except Exception as e:
            print(f"Camera connection failed: {e}")
            return False
    
    def capture_frame(self):
        """Capture a single frame"""
        if not self.is_connected:
            raise Exception("Camera not connected")
        
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to capture frame")
        
        return frame
    
    def capture_and_save(self, filename, quality=95):
        """Capture frame and save to file"""
        frame = self.capture_frame()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save with high quality
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return frame
    
    def live_preview(self, window_name="Camera Preview"):
        """Show live camera preview"""
        if not self.is_connected:
            raise Exception("Camera not connected")
        
        print("Live preview started. Press 'q' to quit, 'c' to capture, 's' to save")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break
            
            # Add crosshairs for centering
            h, w = frame.shape[:2]
            cv2.line(frame, (w//2-20, h//2), (w//2+20, h//2), (0, 255, 0), 1)
            cv2.line(frame, (w//2, h//2-20), (w//2, h//2+20), (0, 255, 0), 1)
            
            # Add instructions
            cv2.putText(frame, "q=quit, c=capture, s=save", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                print("Frame captured")
            elif key == ord('s'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"capture_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Image saved as {filename}")
        
        cv2.destroyAllWindows()
    
    def calculate_sharpness(self, frame):
        """Calculate image sharpness using Laplacian variance"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def focus_sweep_analysis(self, z_positions, printer, output_dir="focus_sweep"):
        """Perform focus sweep at different Z heights and analyze sharpness"""
        if not self.is_connected:
            raise Exception("Camera not connected")
        
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        print(f"Starting focus sweep analysis at {len(z_positions)} positions...")
        
        for i, z_pos in enumerate(z_positions):
            print(f"Position {i+1}/{len(z_positions)}: Z={z_pos}")
            
            # Move to Z position
            printer.move_to_position(z=z_pos)
            time.sleep(0.5)  # Allow movement to settle
            
            # Capture frame
            frame = self.capture_frame()
            
            # Calculate sharpness
            sharpness = self.calculate_sharpness(frame)
            
            # Save image
            filename = os.path.join(output_dir, f"focus_z{z_pos:0.1f}_sharp{sharpness:0.1f}.jpg")
            cv2.imwrite(filename, frame)
            
            results.append({
                'z_position': z_pos,
                'sharpness': sharpness,
                'filename': filename
            })
            
            print(f"  Sharpness: {sharpness:0.1f}")
        
        # Find best focus position
        best_result = max(results, key=lambda x: x['sharpness'])
        print(f"\nBest focus at Z={best_result['z_position']} (sharpness: {best_result['sharpness']:0.1f})")
        
        return results, best_result
    
    def get_camera_info(self):
        """Get camera information"""
        if not self.is_connected:
            return None
        
        return {
            'width': self.frame_width,
            'height': self.frame_height,
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'format': self.cap.get(cv2.CAP_PROP_FORMAT)
        }
    
    def disconnect(self):
        """Disconnect camera"""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            self.is_connected = False
            print("Camera disconnected")

# Test the interface
if __name__ == "__main__":
    camera = CameraInterface()
    
    try:
        if camera.connect():
            print("Testing camera interface...")
            print(f"Camera info: {camera.get_camera_info()}")
            
            # Capture test frame
            frame = camera.capture_frame()
            print(f"Captured frame: {frame.shape}")
            
            # Test sharpness calculation
            sharpness = camera.calculate_sharpness(frame)
            print(f"Frame sharpness: {sharpness:0.1f}")
            
            # Save test image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_capture_{timestamp}.jpg"
            camera.capture_and_save(filename)
            print(f"Test image saved: {filename}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        camera.disconnect() 
"""
Camera Interface for Slide Scanner v2
Clean, reliable camera control and image capture
"""

import cv2
import numpy as np
import time
import os
from datetime import datetime

class CameraInterface:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.is_connected = False
        self.frame_width = None
        self.frame_height = None
        
    def connect(self):
        """Connect to camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                raise Exception(f"Cannot open camera {self.camera_index}")
            
            # Get camera properties
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer lag
            
            self.is_connected = True
            print(f"Camera connected: {self.frame_width}x{self.frame_height}")
            return True
            
        except Exception as e:
            print(f"Camera connection failed: {e}")
            return False
    
    def capture_frame(self):
        """Capture a single frame"""
        if not self.is_connected:
            raise Exception("Camera not connected")
        
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to capture frame")
        
        return frame
    
    def capture_and_save(self, filename, quality=95):
        """Capture frame and save to file"""
        frame = self.capture_frame()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save with high quality
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return frame
    
    def live_preview(self, window_name="Camera Preview"):
        """Show live camera preview"""
        if not self.is_connected:
            raise Exception("Camera not connected")
        
        print("Live preview started. Press 'q' to quit, 'c' to capture, 's' to save")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break
            
            # Add crosshairs for centering
            h, w = frame.shape[:2]
            cv2.line(frame, (w//2-20, h//2), (w//2+20, h//2), (0, 255, 0), 1)
            cv2.line(frame, (w//2, h//2-20), (w//2, h//2+20), (0, 255, 0), 1)
            
            # Add instructions
            cv2.putText(frame, "q=quit, c=capture, s=save", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                print("Frame captured")
            elif key == ord('s'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"capture_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Image saved as {filename}")
        
        cv2.destroyAllWindows()
    
    def calculate_sharpness(self, frame):
        """Calculate image sharpness using Laplacian variance"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def focus_sweep_analysis(self, z_positions, printer, output_dir="focus_sweep"):
        """Perform focus sweep at different Z heights and analyze sharpness"""
        if not self.is_connected:
            raise Exception("Camera not connected")
        
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        print(f"Starting focus sweep analysis at {len(z_positions)} positions...")
        
        for i, z_pos in enumerate(z_positions):
            print(f"Position {i+1}/{len(z_positions)}: Z={z_pos}")
            
            # Move to Z position
            printer.move_to_position(z=z_pos)
            time.sleep(0.5)  # Allow movement to settle
            
            # Capture frame
            frame = self.capture_frame()
            
            # Calculate sharpness
            sharpness = self.calculate_sharpness(frame)
            
            # Save image
            filename = os.path.join(output_dir, f"focus_z{z_pos:0.1f}_sharp{sharpness:0.1f}.jpg")
            cv2.imwrite(filename, frame)
            
            results.append({
                'z_position': z_pos,
                'sharpness': sharpness,
                'filename': filename
            })
            
            print(f"  Sharpness: {sharpness:0.1f}")
        
        # Find best focus position
        best_result = max(results, key=lambda x: x['sharpness'])
        print(f"\nBest focus at Z={best_result['z_position']} (sharpness: {best_result['sharpness']:0.1f})")
        
        return results, best_result
    
    def get_camera_info(self):
        """Get camera information"""
        if not self.is_connected:
            return None
        
        return {
            'width': self.frame_width,
            'height': self.frame_height,
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'format': self.cap.get(cv2.CAP_PROP_FORMAT)
        }
    
    def disconnect(self):
        """Disconnect camera"""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            self.is_connected = False
            print("Camera disconnected")

# Test the interface
if __name__ == "__main__":
    camera = CameraInterface()
    
    try:
        if camera.connect():
            print("Testing camera interface...")
            print(f"Camera info: {camera.get_camera_info()}")
            
            # Capture test frame
            frame = camera.capture_frame()
            print(f"Captured frame: {frame.shape}")
            
            # Test sharpness calculation
            sharpness = camera.calculate_sharpness(frame)
            print(f"Frame sharpness: {sharpness:0.1f}")
            
            # Save test image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_capture_{timestamp}.jpg"
            camera.capture_and_save(filename)
            print(f"Test image saved: {filename}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        camera.disconnect() 
 