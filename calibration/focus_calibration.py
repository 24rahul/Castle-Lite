#!/usr/bin/env python3
"""
Focus Calibration for Scanner v2
Find optimal Z height for sharp imaging through automated focus sweep
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.printer_interface import PrinterInterface
from utils.camera_interface import CameraInterface
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import cv2

class FocusCalibrator:
    def __init__(self):
        self.printer = PrinterInterface()
        self.camera = CameraInterface()
        self.slide_position = None
        
    def load_slide_position(self):
        """Load slide position from previous calibration"""
        config_file = "../config/slide_position.json"
        try:
            with open(config_file, 'r') as f:
                self.slide_position = json.load(f)
            print(f"Loaded slide position: X={self.slide_position['slide_center_x']:.1f}, "
                  f"Y={self.slide_position['slide_center_y']:.1f}, "
                  f"Z={self.slide_position['slide_center_z']:.1f}")
        except FileNotFoundError:
            raise Exception("Slide position not calibrated. Run slide_position_calibration.py first.")
    
    def connect_hardware(self):
        """Connect to printer and camera"""
        print("Connecting to hardware...")
        
        if not self.printer.connect():
            raise Exception("Failed to connect to printer")
            
        if not self.camera.connect():
            raise Exception("Failed to connect to camera")
            
        print("Hardware connected successfully")
    
    def setup_positioning(self):
        """Home printer and move to slide center"""
        print("Setting up positioning...")
        self.printer.home_printer()
        
        # Move to slide center position from calibration
        self.printer.move_to_position(
            x=self.slide_position['slide_center_x'],
            y=self.slide_position['slide_center_y'],
            z=self.slide_position['slide_center_z']
        )
        print("Positioned at slide center")
    
    def automated_focus_sweep(self, z_range=5.0, z_steps=21):
        """Perform automated focus sweep around current Z position"""
        current_z = self.printer.get_position()['Z']
        
        # Create Z positions centered around current position
        z_start = current_z - z_range/2
        z_end = current_z + z_range/2
        z_positions = np.linspace(z_start, z_end, z_steps)
        
        print(f"\n=== Automated Focus Sweep ===")
        print(f"Range: Z={z_start:.1f} to Z={z_end:.1f} ({z_steps} steps)")
        print(f"Step size: {z_range/(z_steps-1):.2f}mm")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"focus_sweep_{timestamp}"
        
        # Perform focus sweep analysis
        results, best_result = self.camera.focus_sweep_analysis(
            z_positions, self.printer, output_dir
        )
        
        return results, best_result, output_dir
    
    def fine_focus_sweep(self, best_z, z_range=1.0, z_steps=21):
        """Perform fine focus sweep around best Z position"""
        print(f"\n=== Fine Focus Sweep ===")
        print(f"Centering around Z={best_z:.1f}")
        
        # Create fine Z positions around best result
        z_start = best_z - z_range/2
        z_end = best_z + z_range/2
        z_positions = np.linspace(z_start, z_end, z_steps)
        
        print(f"Fine range: Z={z_start:.1f} to Z={z_end:.1f} ({z_steps} steps)")
        print(f"Fine step size: {z_range/(z_steps-1):.3f}mm")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"fine_focus_sweep_{timestamp}"
        
        # Perform fine focus sweep
        results, best_result = self.camera.focus_sweep_analysis(
            z_positions, self.printer, output_dir
        )
        
        return results, best_result, output_dir
    
    def plot_focus_results(self, results, output_dir, title="Focus Sweep Results"):
        """Plot sharpness vs Z position"""
        z_positions = [r['z_position'] for r in results]
        sharpness_values = [r['sharpness'] for r in results]
        
        plt.figure(figsize=(10, 6))
        plt.plot(z_positions, sharpness_values, 'b-o', linewidth=2, markersize=6)
        plt.xlabel('Z Position (mm)')
        plt.ylabel('Sharpness (Laplacian Variance)')
        plt.title(title)
        plt.grid(True, alpha=0.3)
        
        # Mark best focus position
        best_idx = np.argmax(sharpness_values)
        best_z = z_positions[best_idx]
        best_sharpness = sharpness_values[best_idx]
        plt.plot(best_z, best_sharpness, 'ro', markersize=10, 
                label=f'Best Focus: Z={best_z:.2f}mm')
        plt.legend()
        
        # Save plot
        plot_filename = os.path.join(output_dir, 'focus_analysis.png')
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"Focus analysis plot saved: {plot_filename}")
    
    def save_focus_calibration(self, best_result):
        """Save focus calibration data"""
        focus_data = {
            'optimal_z_position': best_result['z_position'],
            'max_sharpness': best_result['sharpness'],
            'slide_center_x': self.slide_position['slide_center_x'],
            'slide_center_y': self.slide_position['slide_center_y'],
            'calibration_date': datetime.now().isoformat(),
            'notes': 'Focus calibrated using Laplacian variance sharpness measurement'
        }
        
        config_file = "../config/focus_calibration.json"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(focus_data, f, indent=2)
            
        print(f"\nFocus calibration saved to: {config_file}")
        print("Configuration:")
        for key, value in focus_data.items():
            print(f"  {key}: {value}")
    
    def test_focus_position(self, optimal_z):
        """Test the optimal focus position with a final capture"""
        print(f"\n=== Testing Optimal Focus Position ===")
        
        # Move to optimal focus position
        self.printer.move_to_position(z=optimal_z)
        
        # Capture test image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_dir = "calibration_images"
        os.makedirs(img_dir, exist_ok=True)
        filename = os.path.join(img_dir, f"optimal_focus_test_{timestamp}.jpg")
        frame = self.camera.capture_and_save(filename)
        
        # Calculate final sharpness
        final_sharpness = self.camera.calculate_sharpness(frame)
        
        print(f"Final focus test:")
        print(f"  Z position: {optimal_z:.2f}mm")
        print(f"  Sharpness: {final_sharpness:.1f}")
        print(f"  Test image: {filename}")
        
        return final_sharpness
    
    def manual_focus_selection(self):
        """Interactive manual focus selection at the slide center"""
        print("\n=== Manual Focus Selection ===")
        print("Use WASD keys to move X/Y, RF for Z, F to record focus, Q to quit.")
        print("W/S = Y axis (forward/back)")
        print("A/D = X axis (left/right)")
        print("R/F = Z axis (up/down)")
        print("F = record current Z as focus, Q = quit")
        step_sizes = {1: 0.1, 2: 0.5, 3: 1.0, 4: 5.0, 5: 10.0}
        current_step = 3
        while True:
            frame = self.camera.capture_frame()
            h, w = frame.shape[:2]
            cv2.line(frame, (w//2-30, h//2), (w//2+30, h//2), (0, 255, 0), 2)
            cv2.line(frame, (w//2, h//2-30), (w//2, h//2+30), (0, 255, 0), 2)
            pos = self.printer.get_position()
            cv2.putText(frame, f"X:{pos['X']:.2f} Y:{pos['Y']:.2f} Z:{pos['Z']:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, f"Step: {step_sizes[current_step]}mm", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, "WASD=move, RF=Z, 1-5=step, F=focus, Q=quit", (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
            cv2.imshow("Manual Focus Selection", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Manual focus selection cancelled.")
                cv2.destroyAllWindows()
                return None
            elif key == ord('f'):
                pos = self.printer.get_position()
                z_focus = pos['Z']
                print(f"Selected focus at Z={z_focus:.2f}mm (X={pos['X']:.2f}, Y={pos['Y']:.2f})")
                cv2.destroyAllWindows()
                # Move to the selected Z to ensure focus
                self.printer.move_to_position(z=z_focus)
                # Show a test image at the selected Z
                test_frame = self.camera.capture_frame()
                cv2.imshow("Test Image at Selected Focus", test_frame)
                print("Press any key to continue...")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return z_focus
            elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5')]:
                current_step = int(chr(key))
                print(f"Step size changed to: {step_sizes[current_step]}mm")
            elif key == ord('w'):
                self.printer.move_relative(dy=step_sizes[current_step])
            elif key == ord('s'):
                self.printer.move_relative(dy=-step_sizes[current_step])
            elif key == ord('a'):
                self.printer.move_relative(dx=-step_sizes[current_step])
            elif key == ord('d'):
                self.printer.move_relative(dx=step_sizes[current_step])
            elif key == ord('r'):
                self.printer.move_relative(dz=step_sizes[current_step])
            elif key == ord('f'):
                self.printer.move_relative(dz=-step_sizes[current_step])

    def interactive_xy_selection(self):
        """Interactive X/Y selection for focus calibration"""
        print("\n=== Manual X/Y Selection ===")
        print("Use WASD keys to move X/Y, 1-5 to change step, F to select, Q to quit.")
        step_sizes = {1: 0.1, 2: 0.5, 3: 1.0, 4: 5.0, 5: 10.0}
        current_step = 3
        while True:
            frame = self.camera.capture_frame()
            h, w = frame.shape[:2]
            cv2.line(frame, (w//2-30, h//2), (w//2+30, h//2), (0, 255, 0), 2)
            cv2.line(frame, (w//2, h//2-30), (w//2, h//2+30), (0, 255, 0), 2)
            pos = self.printer.get_position()
            cv2.putText(frame, f"X:{pos['X']:.2f} Y:{pos['Y']:.2f} Z:{pos['Z']:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, f"Step: {step_sizes[current_step]}mm", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, "WASD=move, 1-5=step, F=select, Q=quit", (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
            cv2.imshow("Manual X/Y Selection", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Manual X/Y selection cancelled.")
                cv2.destroyAllWindows()
                return None, None
            elif key == ord('f'):
                pos = self.printer.get_position()
                print(f"Selected X={pos['X']:.2f}, Y={pos['Y']:.2f}")
                cv2.destroyAllWindows()
                return pos['X'], pos['Y']
            elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5')]:
                current_step = int(chr(key))
                print(f"Step size changed to: {step_sizes[current_step]}mm")
            elif key == ord('w'):
                self.printer.move_relative(dy=step_sizes[current_step])
            elif key == ord('s'):
                self.printer.move_relative(dy=-step_sizes[current_step])
            elif key == ord('a'):
                self.printer.move_relative(dx=-step_sizes[current_step])
            elif key == ord('d'):
                self.printer.move_relative(dx=step_sizes[current_step])

    def run_calibration(self):
        """Run complete focus calibration, with three modes"""
        try:
            print("=== Focus Calibration v2 ===")
            self.load_slide_position()
            self.connect_hardware()
            self.setup_positioning()
            print("\nSelect focus calibration mode:")
            print("  [1] Full auto (automated sweep at slide center)")
            print("  [2] Auto after manual X/Y (move to X/Y, then auto sweep)")
            print("  [3] Fully manual (move X/Y/Z, pick Z)")
            mode = input("Enter 1, 2, or 3: ").strip()
            if mode == '3':
                z_focus = self.manual_focus_selection()
                if z_focus is not None:
                    best_result = {'z_position': z_focus, 'sharpness': None}
                    self.save_focus_calibration(best_result)
                    print(f"\n=== Manual Focus Calibration Complete ===\nOptimal Z position: {z_focus:.2f}mm\nNext step: Run coverage planning to determine scan pattern")
                else:
                    print("Manual focus not selected.")
                return
            elif mode == '2':
                x, y = self.interactive_xy_selection()
                if x is None or y is None:
                    print("Manual X/Y not selected.")
                    return
                self.printer.move_to_position(x=x, y=y)
                print("\nStarting automated focus sweep at selected X/Y...")
                # Use current Z as center
                z_center = self.printer.get_position()['Z']
                coarse_results, coarse_best, coarse_dir = self.automated_focus_sweep(z_range=8.0, z_steps=17)
                self.plot_focus_results(coarse_results, coarse_dir, "Coarse Focus Sweep")
                print("\nStarting fine focus sweep...")
                fine_results, fine_best, fine_dir = self.fine_focus_sweep(coarse_best['z_position'], z_range=2.0, z_steps=21)
                self.plot_focus_results(fine_results, fine_dir, "Fine Focus Sweep")
                final_sharpness = self.test_focus_position(fine_best['z_position'])
                self.save_focus_calibration(fine_best)
                print("\n=== Focus Calibration Complete (manual X/Y) ===")
                print(f"Optimal Z position: {fine_best['z_position']:.2f}mm")
                print(f"Maximum sharpness: {fine_best['sharpness']:.1f}")
                print("Next step: Run coverage planning to determine scan pattern")
                return
            # Default: full auto
            print("\nStarting coarse focus sweep at slide center...")
            coarse_results, coarse_best, coarse_dir = self.automated_focus_sweep(z_range=8.0, z_steps=17)
            self.plot_focus_results(coarse_results, coarse_dir, "Coarse Focus Sweep")
            print("\nStarting fine focus sweep...")
            fine_results, fine_best, fine_dir = self.fine_focus_sweep(coarse_best['z_position'], z_range=2.0, z_steps=21)
            self.plot_focus_results(fine_results, fine_dir, "Fine Focus Sweep")
            final_sharpness = self.test_focus_position(fine_best['z_position'])
            self.save_focus_calibration(fine_best)
            print("\n=== Focus Calibration Complete (full auto) ===")
            print(f"Optimal Z position: {fine_best['z_position']:.2f}mm")
            print(f"Maximum sharpness: {fine_best['sharpness']:.1f}")
            print("Next step: Run coverage planning to determine scan pattern")
        except Exception as e:
            print(f"Focus calibration error: {e}")
        finally:
            self.printer.disconnect()
            self.camera.disconnect()

if __name__ == "__main__":
    calibrator = FocusCalibrator()
    calibrator.run_calibration() 
 