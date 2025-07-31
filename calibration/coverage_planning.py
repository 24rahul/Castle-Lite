#!/usr/bin/env python3
"""
Coverage Planning for Scanner v2
Determine optimal scan pattern and number of images needed for complete slide capture
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.printer_interface import PrinterInterface
from utils.camera_interface import CameraInterface
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

class CoveragePlanner:
    def __init__(self):
        self.printer = PrinterInterface()
        self.camera = CameraInterface()
        self.slide_position = None
        self.focus_data = None
        self.field_of_view = None  # Will be measured
        
    def load_calibration_data(self):
        """Load slide position and focus calibration data"""
        # Load slide position
        try:
            with open("../config/slide_position.json", 'r') as f:
                self.slide_position = json.load(f)
            print("Loaded slide position calibration")
        except FileNotFoundError:
            raise Exception("Slide position not calibrated. Run slide_position_calibration.py first.")
        
        # Load focus calibration
        try:
            with open("../config/focus_calibration.json", 'r') as f:
                self.focus_data = json.load(f)
            print("Loaded focus calibration")
        except FileNotFoundError:
            raise Exception("Focus not calibrated. Run focus_calibration.py first.")
    
    def connect_hardware(self):
        """Connect to printer and camera"""
        print("Connecting to hardware...")
        
        if not self.printer.connect():
            raise Exception("Failed to connect to printer")
            
        if not self.camera.connect():
            raise Exception("Failed to connect to camera")
            
        print("Hardware connected successfully")
    
    def setup_positioning(self):
        """Home printer and move to optimal position"""
        print("Setting up positioning...")
        self.printer.home_printer()
        
        # Move to slide center at optimal focus
        self.printer.move_to_position(
            x=self.slide_position['slide_center_x'],
            y=self.slide_position['slide_center_y'],
            z=self.focus_data['optimal_z_position']
        )
        print("Positioned at calibrated slide center and focus")
    
    def measure_field_of_view(self):
        """Measure camera field of view by imaging a known reference"""
        print("\n=== Measuring Field of View ===")
        
        # Capture reference image
        reference_frame = self.camera.capture_frame()
        
        # Get camera resolution
        camera_info = self.camera.get_camera_info()
        pixel_width = camera_info['width']
        pixel_height = camera_info['height']
        
        print(f"Camera resolution: {pixel_width} x {pixel_height} pixels")
        
        # Move camera by known distances and measure pixel displacement
        print("Moving camera to measure field of view...")
        
        # Move 5mm in X direction and capture
        move_distance = 5.0  # mm
        self.printer.move_relative(dx=move_distance)
        moved_frame = self.camera.capture_frame()
        
        # Use phase correlation to measure pixel displacement
        displacement_pixels = self.calculate_image_displacement(reference_frame, moved_frame)
        
        # Calculate pixels per mm
        pixels_per_mm_x = abs(displacement_pixels[0]) / move_distance
        
        # Move back and test Y direction
        self.printer.move_relative(dx=-move_distance)
        self.printer.move_relative(dy=move_distance)
        moved_frame_y = self.camera.capture_frame()
        
        displacement_pixels_y = self.calculate_image_displacement(reference_frame, moved_frame_y)
        pixels_per_mm_y = abs(displacement_pixels_y[1]) / move_distance
        
        # Return to original position
        self.printer.move_relative(dy=-move_distance)
        
        # Calculate field of view in mm
        fov_width_mm = pixel_width / pixels_per_mm_x
        fov_height_mm = pixel_height / pixels_per_mm_y
        
        self.field_of_view = {
            'width_mm': fov_width_mm,
            'height_mm': fov_height_mm,
            'pixels_per_mm_x': pixels_per_mm_x,
            'pixels_per_mm_y': pixels_per_mm_y,
            'pixel_width': pixel_width,
            'pixel_height': pixel_height
        }
        
        print(f"Field of view: {fov_width_mm:.1f} x {fov_height_mm:.1f} mm")
        print(f"Resolution: {pixels_per_mm_x:.1f} x {pixels_per_mm_y:.1f} pixels/mm")
        
        return self.field_of_view
    
    def calculate_image_displacement(self, img1, img2):
        """Calculate displacement between two images using phase correlation"""
        # Convert to grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Calculate phase correlation
        f1 = np.fft.fft2(gray1)
        f2 = np.fft.fft2(gray2)
        
        # Cross-correlation
        cross_correlation = f1 * np.conj(f2)
        cross_correlation /= np.abs(cross_correlation)
        
        # Inverse FFT
        correlation = np.fft.ifft2(cross_correlation)
        correlation = np.abs(correlation)
        
        # Find peak
        y, x = np.unravel_index(np.argmax(correlation), correlation.shape)
        
        # Convert to displacement (handle wrap-around)
        h, w = gray1.shape
        if x > w // 2:
            x -= w
        if y > h // 2:
            y -= h
            
        return x, y
    
    def calculate_scan_pattern(self, overlap_percent=20):
        """Calculate optimal scan pattern for complete slide coverage"""
        print(f"\n=== Calculating Scan Pattern (overlap: {overlap_percent}%) ===")
        
        slide_width = self.slide_position['slide_width']
        slide_height = self.slide_position['slide_height']
        fov_width = self.field_of_view['width_mm']
        fov_height = self.field_of_view['height_mm']
        
        print(f"Slide dimensions: {slide_width} x {slide_height} mm")
        print(f"Field of view: {fov_width:.1f} x {fov_height:.1f} mm")
        
        # Calculate step size with overlap
        overlap_factor = (100 - overlap_percent) / 100
        step_x = fov_width * overlap_factor
        step_y = fov_height * overlap_factor
        
        # Calculate number of positions needed
        positions_x = int(np.ceil(slide_width / step_x))
        positions_y = int(np.ceil(slide_height / step_y))
        
        print(f"Step size: {step_x:.1f} x {step_y:.1f} mm")
        print(f"Grid size: {positions_x} x {positions_y} positions")
        print(f"Total images: {positions_x * positions_y}")
        
        # Generate scan positions
        scan_positions = []
        center_x = self.slide_position['slide_center_x']
        center_y = self.slide_position['slide_center_y']
        
        # Calculate starting position (bottom-left of grid)
        start_x = center_x - (positions_x - 1) * step_x / 2
        start_y = center_y - (positions_y - 1) * step_y / 2
        
        for i in range(positions_y):
            for j in range(positions_x):
                x = start_x + j * step_x
                y = start_y + i * step_y
                scan_positions.append({
                    'x': x,
                    'y': y,
                    'z': self.focus_data['optimal_z_position'],
                    'grid_x': j,
                    'grid_y': i
                })
        
        scan_pattern = {
            'positions': scan_positions,
            'grid_size_x': positions_x,
            'grid_size_y': positions_y,
            'step_size_x': step_x,
            'step_size_y': step_y,
            'overlap_percent': overlap_percent,
            'total_images': len(scan_positions),
            'field_of_view': self.field_of_view,
            'slide_dimensions': {
                'width': slide_width,
                'height': slide_height
            }
        }
        
        return scan_pattern
    
    def visualize_scan_pattern(self, scan_pattern):
        """Visualize the scan pattern over the slide"""
        print("\n=== Visualizing Scan Pattern ===")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw slide
        slide_width = scan_pattern['slide_dimensions']['width']
        slide_height = scan_pattern['slide_dimensions']['height']
        center_x = self.slide_position['slide_center_x']
        center_y = self.slide_position['slide_center_y']
        
        slide_rect = patches.Rectangle(
            (center_x - slide_width/2, center_y - slide_height/2),
            slide_width, slide_height,
            linewidth=2, edgecolor='black', facecolor='lightblue', alpha=0.3,
            label='Slide'
        )
        ax.add_patch(slide_rect)
        
        # Draw field of view for each position
        fov_width = self.field_of_view['width_mm']
        fov_height = self.field_of_view['height_mm']
        
        for i, pos in enumerate(scan_pattern['positions']):
            fov_rect = patches.Rectangle(
                (pos['x'] - fov_width/2, pos['y'] - fov_height/2),
                fov_width, fov_height,
                linewidth=1, edgecolor='red', facecolor='none', alpha=0.7
            )
            ax.add_patch(fov_rect)
            
            # Add position number
            ax.text(pos['x'], pos['y'], str(i+1), 
                   ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Mark slide center
        ax.plot(center_x, center_y, 'go', markersize=10, label='Slide Center')
        
        # Set axis properties
        ax.set_xlabel('X Position (mm)')
        ax.set_ylabel('Y Position (mm)')
        ax.set_title(f'Scan Pattern: {scan_pattern["total_images"]} images '
                    f'({scan_pattern["grid_size_x"]}x{scan_pattern["grid_size_y"]} grid)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"scan_pattern_{timestamp}.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"Scan pattern visualization saved: {plot_filename}")
    
    def test_scan_pattern(self, scan_pattern, test_positions=4):
        """Test a few positions from the scan pattern"""
        print(f"\n=== Testing {test_positions} Scan Positions ===")
        
        # Select test positions (corners and center)
        total_positions = len(scan_pattern['positions'])
        if test_positions >= 4:
            test_indices = [0, scan_pattern['grid_size_x']-1, 
                          total_positions-1, total_positions-scan_pattern['grid_size_x']]
        else:
            test_indices = [0, total_positions//2, total_positions-1]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = f"scan_pattern_test_{timestamp}"
        os.makedirs(test_dir, exist_ok=True)
        
        for i, idx in enumerate(test_indices[:test_positions]):
            pos = scan_pattern['positions'][idx]
            print(f"Test {i+1}/{test_positions}: Position {idx+1} "
                  f"(X:{pos['x']:.1f}, Y:{pos['y']:.1f})")
            
            # Move to position
            self.printer.move_to_position(x=pos['x'], y=pos['y'], z=pos['z'])
            
            # Capture image
            filename = os.path.join(test_dir, f"test_pos_{idx+1:03d}.jpg")
            self.camera.capture_and_save(filename)
            print(f"  Captured: {filename}")
        
        print(f"Test images saved to: {test_dir}")
    
    def save_scan_configuration(self, scan_pattern):
        """Save scan pattern configuration"""
        config_data = {
            'scan_pattern': scan_pattern,
            'calibration_date': datetime.now().isoformat(),
            'slide_position': self.slide_position,
            'focus_data': self.focus_data,
            'notes': 'Complete scan configuration for slide scanner v2'
        }
        
        config_file = "../config/scan_configuration.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        print(f"\nScan configuration saved to: {config_file}")
        print(f"Total scan positions: {scan_pattern['total_images']}")
        print(f"Grid size: {scan_pattern['grid_size_x']} x {scan_pattern['grid_size_y']}")
        print(f"Overlap: {scan_pattern['overlap_percent']}%")
    
    def run_planning(self):
        """Run complete coverage planning"""
        try:
            print("=== Coverage Planning v2 ===")
            
            self.load_calibration_data()
            self.connect_hardware()
            self.setup_positioning()
            
            # Measure field of view
            self.measure_field_of_view()
            
            # Calculate scan pattern
            scan_pattern = self.calculate_scan_pattern(overlap_percent=25)
            
            # Visualize pattern
            self.visualize_scan_pattern(scan_pattern)
            
            # Test pattern
            self.test_scan_pattern(scan_pattern, test_positions=4)
            
            # Save configuration
            self.save_scan_configuration(scan_pattern)
            
            print("\n=== Coverage Planning Complete ===")
            print("System is now fully calibrated and ready for scanning!")
            print("Next step: Use the scanning module to perform full slide scans")
            
        except Exception as e:
            print(f"Coverage planning error: {e}")
            
        finally:
            self.printer.disconnect()
            self.camera.disconnect()

if __name__ == "__main__":
    planner = CoveragePlanner()
    planner.run_planning() 
"""
Coverage Planning for Scanner v2
Determine optimal scan pattern and number of images needed for complete slide capture
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.printer_interface import PrinterInterface
from utils.camera_interface import CameraInterface
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

class CoveragePlanner:
    def __init__(self):
        self.printer = PrinterInterface()
        self.camera = CameraInterface()
        self.slide_position = None
        self.focus_data = None
        self.field_of_view = None  # Will be measured
        
    def load_calibration_data(self):
        """Load slide position and focus calibration data"""
        # Load slide position
        try:
            with open("../config/slide_position.json", 'r') as f:
                self.slide_position = json.load(f)
            print("Loaded slide position calibration")
        except FileNotFoundError:
            raise Exception("Slide position not calibrated. Run slide_position_calibration.py first.")
        
        # Load focus calibration
        try:
            with open("../config/focus_calibration.json", 'r') as f:
                self.focus_data = json.load(f)
            print("Loaded focus calibration")
        except FileNotFoundError:
            raise Exception("Focus not calibrated. Run focus_calibration.py first.")
    
    def connect_hardware(self):
        """Connect to printer and camera"""
        print("Connecting to hardware...")
        
        if not self.printer.connect():
            raise Exception("Failed to connect to printer")
            
        if not self.camera.connect():
            raise Exception("Failed to connect to camera")
            
        print("Hardware connected successfully")
    
    def setup_positioning(self):
        """Home printer and move to optimal position"""
        print("Setting up positioning...")
        self.printer.home_printer()
        
        # Move to slide center at optimal focus
        self.printer.move_to_position(
            x=self.slide_position['slide_center_x'],
            y=self.slide_position['slide_center_y'],
            z=self.focus_data['optimal_z_position']
        )
        print("Positioned at calibrated slide center and focus")
    
    def measure_field_of_view(self):
        """Measure camera field of view by imaging a known reference"""
        print("\n=== Measuring Field of View ===")
        
        # Capture reference image
        reference_frame = self.camera.capture_frame()
        
        # Get camera resolution
        camera_info = self.camera.get_camera_info()
        pixel_width = camera_info['width']
        pixel_height = camera_info['height']
        
        print(f"Camera resolution: {pixel_width} x {pixel_height} pixels")
        
        # Move camera by known distances and measure pixel displacement
        print("Moving camera to measure field of view...")
        
        # Move 5mm in X direction and capture
        move_distance = 5.0  # mm
        self.printer.move_relative(dx=move_distance)
        moved_frame = self.camera.capture_frame()
        
        # Use phase correlation to measure pixel displacement
        displacement_pixels = self.calculate_image_displacement(reference_frame, moved_frame)
        
        # Calculate pixels per mm
        pixels_per_mm_x = abs(displacement_pixels[0]) / move_distance
        
        # Move back and test Y direction
        self.printer.move_relative(dx=-move_distance)
        self.printer.move_relative(dy=move_distance)
        moved_frame_y = self.camera.capture_frame()
        
        displacement_pixels_y = self.calculate_image_displacement(reference_frame, moved_frame_y)
        pixels_per_mm_y = abs(displacement_pixels_y[1]) / move_distance
        
        # Return to original position
        self.printer.move_relative(dy=-move_distance)
        
        # Calculate field of view in mm
        fov_width_mm = pixel_width / pixels_per_mm_x
        fov_height_mm = pixel_height / pixels_per_mm_y
        
        self.field_of_view = {
            'width_mm': fov_width_mm,
            'height_mm': fov_height_mm,
            'pixels_per_mm_x': pixels_per_mm_x,
            'pixels_per_mm_y': pixels_per_mm_y,
            'pixel_width': pixel_width,
            'pixel_height': pixel_height
        }
        
        print(f"Field of view: {fov_width_mm:.1f} x {fov_height_mm:.1f} mm")
        print(f"Resolution: {pixels_per_mm_x:.1f} x {pixels_per_mm_y:.1f} pixels/mm")
        
        return self.field_of_view
    
    def calculate_image_displacement(self, img1, img2):
        """Calculate displacement between two images using phase correlation"""
        # Convert to grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Calculate phase correlation
        f1 = np.fft.fft2(gray1)
        f2 = np.fft.fft2(gray2)
        
        # Cross-correlation
        cross_correlation = f1 * np.conj(f2)
        cross_correlation /= np.abs(cross_correlation)
        
        # Inverse FFT
        correlation = np.fft.ifft2(cross_correlation)
        correlation = np.abs(correlation)
        
        # Find peak
        y, x = np.unravel_index(np.argmax(correlation), correlation.shape)
        
        # Convert to displacement (handle wrap-around)
        h, w = gray1.shape
        if x > w // 2:
            x -= w
        if y > h // 2:
            y -= h
            
        return x, y
    
    def calculate_scan_pattern(self, overlap_percent=20):
        """Calculate optimal scan pattern for complete slide coverage"""
        print(f"\n=== Calculating Scan Pattern (overlap: {overlap_percent}%) ===")
        
        slide_width = self.slide_position['slide_width']
        slide_height = self.slide_position['slide_height']
        fov_width = self.field_of_view['width_mm']
        fov_height = self.field_of_view['height_mm']
        
        print(f"Slide dimensions: {slide_width} x {slide_height} mm")
        print(f"Field of view: {fov_width:.1f} x {fov_height:.1f} mm")
        
        # Calculate step size with overlap
        overlap_factor = (100 - overlap_percent) / 100
        step_x = fov_width * overlap_factor
        step_y = fov_height * overlap_factor
        
        # Calculate number of positions needed
        positions_x = int(np.ceil(slide_width / step_x))
        positions_y = int(np.ceil(slide_height / step_y))
        
        print(f"Step size: {step_x:.1f} x {step_y:.1f} mm")
        print(f"Grid size: {positions_x} x {positions_y} positions")
        print(f"Total images: {positions_x * positions_y}")
        
        # Generate scan positions
        scan_positions = []
        center_x = self.slide_position['slide_center_x']
        center_y = self.slide_position['slide_center_y']
        
        # Calculate starting position (bottom-left of grid)
        start_x = center_x - (positions_x - 1) * step_x / 2
        start_y = center_y - (positions_y - 1) * step_y / 2
        
        for i in range(positions_y):
            for j in range(positions_x):
                x = start_x + j * step_x
                y = start_y + i * step_y
                scan_positions.append({
                    'x': x,
                    'y': y,
                    'z': self.focus_data['optimal_z_position'],
                    'grid_x': j,
                    'grid_y': i
                })
        
        scan_pattern = {
            'positions': scan_positions,
            'grid_size_x': positions_x,
            'grid_size_y': positions_y,
            'step_size_x': step_x,
            'step_size_y': step_y,
            'overlap_percent': overlap_percent,
            'total_images': len(scan_positions),
            'field_of_view': self.field_of_view,
            'slide_dimensions': {
                'width': slide_width,
                'height': slide_height
            }
        }
        
        return scan_pattern
    
    def visualize_scan_pattern(self, scan_pattern):
        """Visualize the scan pattern over the slide"""
        print("\n=== Visualizing Scan Pattern ===")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw slide
        slide_width = scan_pattern['slide_dimensions']['width']
        slide_height = scan_pattern['slide_dimensions']['height']
        center_x = self.slide_position['slide_center_x']
        center_y = self.slide_position['slide_center_y']
        
        slide_rect = patches.Rectangle(
            (center_x - slide_width/2, center_y - slide_height/2),
            slide_width, slide_height,
            linewidth=2, edgecolor='black', facecolor='lightblue', alpha=0.3,
            label='Slide'
        )
        ax.add_patch(slide_rect)
        
        # Draw field of view for each position
        fov_width = self.field_of_view['width_mm']
        fov_height = self.field_of_view['height_mm']
        
        for i, pos in enumerate(scan_pattern['positions']):
            fov_rect = patches.Rectangle(
                (pos['x'] - fov_width/2, pos['y'] - fov_height/2),
                fov_width, fov_height,
                linewidth=1, edgecolor='red', facecolor='none', alpha=0.7
            )
            ax.add_patch(fov_rect)
            
            # Add position number
            ax.text(pos['x'], pos['y'], str(i+1), 
                   ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Mark slide center
        ax.plot(center_x, center_y, 'go', markersize=10, label='Slide Center')
        
        # Set axis properties
        ax.set_xlabel('X Position (mm)')
        ax.set_ylabel('Y Position (mm)')
        ax.set_title(f'Scan Pattern: {scan_pattern["total_images"]} images '
                    f'({scan_pattern["grid_size_x"]}x{scan_pattern["grid_size_y"]} grid)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"scan_pattern_{timestamp}.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"Scan pattern visualization saved: {plot_filename}")
    
    def test_scan_pattern(self, scan_pattern, test_positions=4):
        """Test a few positions from the scan pattern"""
        print(f"\n=== Testing {test_positions} Scan Positions ===")
        
        # Select test positions (corners and center)
        total_positions = len(scan_pattern['positions'])
        if test_positions >= 4:
            test_indices = [0, scan_pattern['grid_size_x']-1, 
                          total_positions-1, total_positions-scan_pattern['grid_size_x']]
        else:
            test_indices = [0, total_positions//2, total_positions-1]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = f"scan_pattern_test_{timestamp}"
        os.makedirs(test_dir, exist_ok=True)
        
        for i, idx in enumerate(test_indices[:test_positions]):
            pos = scan_pattern['positions'][idx]
            print(f"Test {i+1}/{test_positions}: Position {idx+1} "
                  f"(X:{pos['x']:.1f}, Y:{pos['y']:.1f})")
            
            # Move to position
            self.printer.move_to_position(x=pos['x'], y=pos['y'], z=pos['z'])
            
            # Capture image
            filename = os.path.join(test_dir, f"test_pos_{idx+1:03d}.jpg")
            self.camera.capture_and_save(filename)
            print(f"  Captured: {filename}")
        
        print(f"Test images saved to: {test_dir}")
    
    def save_scan_configuration(self, scan_pattern):
        """Save scan pattern configuration"""
        config_data = {
            'scan_pattern': scan_pattern,
            'calibration_date': datetime.now().isoformat(),
            'slide_position': self.slide_position,
            'focus_data': self.focus_data,
            'notes': 'Complete scan configuration for slide scanner v2'
        }
        
        config_file = "../config/scan_configuration.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        print(f"\nScan configuration saved to: {config_file}")
        print(f"Total scan positions: {scan_pattern['total_images']}")
        print(f"Grid size: {scan_pattern['grid_size_x']} x {scan_pattern['grid_size_y']}")
        print(f"Overlap: {scan_pattern['overlap_percent']}%")
    
    def run_planning(self):
        """Run complete coverage planning"""
        try:
            print("=== Coverage Planning v2 ===")
            
            self.load_calibration_data()
            self.connect_hardware()
            self.setup_positioning()
            
            # Measure field of view
            self.measure_field_of_view()
            
            # Calculate scan pattern
            scan_pattern = self.calculate_scan_pattern(overlap_percent=25)
            
            # Visualize pattern
            self.visualize_scan_pattern(scan_pattern)
            
            # Test pattern
            self.test_scan_pattern(scan_pattern, test_positions=4)
            
            # Save configuration
            self.save_scan_configuration(scan_pattern)
            
            print("\n=== Coverage Planning Complete ===")
            print("System is now fully calibrated and ready for scanning!")
            print("Next step: Use the scanning module to perform full slide scans")
            
        except Exception as e:
            print(f"Coverage planning error: {e}")
            
        finally:
            self.printer.disconnect()
            self.camera.disconnect()

if __name__ == "__main__":
    planner = CoveragePlanner()
    planner.run_planning() 
 