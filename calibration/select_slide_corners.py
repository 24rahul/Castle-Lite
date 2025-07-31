import sys
import os
import cv2
import time
import json
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.printer_interface import PrinterInterface
from utils.camera_interface import CameraInterface

CORNER_NAMES = [
    "bottom_left",
    "bottom_right",
    "top_right",
    "top_left"
]

SAVE_PATH = "../config/slide_corners.json"

class SlideCornerSelector:
    def __init__(self):
        self.printer = PrinterInterface()
        self.camera = CameraInterface()
        self.corners = {}
        self.step_sizes = {1: 0.1, 2: 0.5, 3: 1.0, 4: 5.0, 5: 10.0}
        self.current_step = 3  # Default to 1mm steps

    def connect_hardware(self):
        print("Connecting to hardware...")
        if not self.printer.connect():
            raise Exception("Failed to connect to printer")
        if not self.camera.connect():
            raise Exception("Failed to connect to camera")
        print("Hardware connected successfully")

    def home_and_setup(self):
        print("Homing stage...")
        self.printer.home_printer()
        print("Homing complete")

    def select_corners(self):
        print("\n=== Slide Corner Selection ===")
        print("You will be prompted to move the camera to each slide corner.")
        print("Use WASD keys to move camera, Q to quit, C to capture corner position")
        print("W/S = Y axis (forward/back)")
        print("A/D = X axis (left/right)")
        print("R/F = Z axis (up/down)")
        print("Numbers 1-5 = move step size (1=0.1mm, 2=0.5mm, 3=1mm, 4=5mm, 5=10mm)")

        for corner in CORNER_NAMES:
            print(f"\nMove to the {corner.replace('_', ' ').title()} of the slide and press 'C' to capture.")
            while True:
                frame = self.camera.capture_frame()
                h, w = frame.shape[:2]
                # Draw crosshairs
                cv2.line(frame, (w//2-30, h//2), (w//2+30, h//2), (0, 255, 0), 2)
                cv2.line(frame, (w//2, h//2-30), (w//2, h//2+30), (0, 255, 0), 2)
                pos = self.printer.get_position()
                cv2.putText(frame, f"X:{pos['X']:.1f} Y:{pos['Y']:.1f} Z:{pos['Z']:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Step: {self.step_sizes[self.current_step]}mm", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Corner: {corner.replace('_', ' ').title()}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, "WASD=move, RF=Z, 1-5=step, C=capture, Q=quit", (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.imshow("Slide Corner Selection", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Corner selection cancelled.")
                    cv2.destroyAllWindows()
                    return False
                elif key == ord('c'):
                    pos = self.printer.get_position()
                    self.corners[corner] = dict(pos)
                    print(f"Captured {corner.replace('_', ' ')}: X={pos['X']:.2f}, Y={pos['Y']:.2f}, Z={pos['Z']:.2f}")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    img_dir = "calibration_images"
                    os.makedirs(img_dir, exist_ok=True)
                    filename = os.path.join(img_dir, f"slide_{corner}_{timestamp}.jpg")
                    self.camera.capture_and_save(filename)
                    print(f"Corner image saved: {filename}")
                    cv2.destroyAllWindows()
                    break
                elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5')]:
                    self.current_step = int(chr(key))
                    print(f"Step size changed to: {self.step_sizes[self.current_step]}mm")
                elif key == ord('w'):
                    self.printer.move_relative(dy=self.step_sizes[self.current_step])
                elif key == ord('s'):
                    self.printer.move_relative(dy=-self.step_sizes[self.current_step])
                elif key == ord('a'):
                    self.printer.move_relative(dx=-self.step_sizes[self.current_step])
                elif key == ord('d'):
                    self.printer.move_relative(dx=self.step_sizes[self.current_step])
                elif key == ord('r'):
                    self.printer.move_relative(dz=self.step_sizes[self.current_step])
                elif key == ord('f'):
                    self.printer.move_relative(dz=-self.step_sizes[self.current_step])
        return True

    def save_corners(self):
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, 'w') as f:
            json.dump(self.corners, f, indent=2)
        print(f"\nCorner positions saved to: {SAVE_PATH}")
        for corner, pos in self.corners.items():
            print(f"  {corner}: X={pos['X']:.2f}, Y={pos['Y']:.2f}, Z={pos['Z']:.2f}")

    def run(self):
        try:
            self.connect_hardware()
            self.home_and_setup()
            if self.select_corners():
                self.save_corners()
                print("\n=== Slide corner selection complete ===")
            else:
                print("Corner selection not completed.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.printer.disconnect()
            self.camera.disconnect()

if __name__ == "__main__":
    selector = SlideCornerSelector()
    selector.run() 