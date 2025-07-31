import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import cv2
import numpy as np
from utils.camera_interface import CameraInterface
from utils.printer_interface import PrinterInterface
import time
import json

# User-adjustable parameters
START_X_OFFSET = 0  # mm offset from slide_center_x (set to 0 for center)
START_Y_OFFSET = 0  # mm offset from slide_center_y (set to 0 for center)
COARSE_STEP = 1     # mm step size for scanning (set to 1 for high resolution)
SLIDE_LENGTH = 75   # mm (standard slide length)
SLIDE_WIDTH = 25    # mm (standard slide width)
X_MAX_DIST = SLIDE_LENGTH    # max distance from center for X scan (full slide length)
Y_MAX_DIST = SLIDE_WIDTH     # max distance from center for Y scan (full slide width)

def percent_black(thresh):
    return np.mean(thresh == 0) * 100

def find_border_black_edge(printer, cam, axis, center, fixed, z, direction, max_distance=100, coarse_step=2, img_label=''):
    """
    Scan outward in one direction, record black edge strength at each step,
    and find the position with the strongest black edge (peak edge pixel count).
    """
    pos = center
    positions = []
    edge_strengths = []
    while abs(pos - center) <= max_distance:
        if axis == 'y':
            printer.move_to_position(x=fixed, y=pos, z=z)
        else:
            printer.move_to_position(x=pos, y=fixed, z=z)
        time.sleep(1)
        frame = cam.capture_frame()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Threshold to isolate black/dark regions (tune threshold as needed)
        _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
        # Edge detection on thresholded image
        edges = cv2.Canny(thresh, 50, 150)
        edge_strength = np.sum(edges) / 255  # Number of edge pixels
        positions.append(pos)
        edge_strengths.append(edge_strength)
        # Save images for inspection
        cv2.imwrite(f"border_detection_test/{img_label}_{axis}_{pos:.2f}.jpg", frame)
        cv2.imwrite(f"border_detection_test/{img_label}_{axis}_{pos:.2f}_thresh.jpg", thresh)
        cv2.imwrite(f"border_detection_test/{img_label}_{axis}_{pos:.2f}_edges.jpg", edges)
        print(f"{axis.upper()}={pos:.2f}: black edge strength={edge_strength}")
        pos += direction * coarse_step
    # Find the peak in edge strength
    max_edge_idx = np.argmax(edge_strengths)
    border_pos = positions[max_edge_idx]
    print(f"{axis.upper()} border found at {border_pos:.2f} (max black edge strength: {edge_strengths[max_edge_idx]})")
    # Save edge strengths for inspection
    with open(f"border_detection_test/{img_label}_{axis}_edges.txt", "w") as f:
        for p, e in zip(positions, edge_strengths):
            f.write(f"{p:.2f}\t{e}\n")
    return border_pos

def main():
    cam = CameraInterface()
    printer = PrinterInterface()
    if not cam.connect():
        print("Failed to connect to camera.")
        return
    if not printer.connect():
        print("Failed to connect to printer.")
        cam.disconnect()
        return

    # Load slide position from calibration (could be anywhere on the slide)
    try:
        with open("../config/slide_position.json", 'r') as f:
            slide_pos = json.load(f)
        start_x = slide_pos['slide_center_x'] + START_X_OFFSET
        start_y = slide_pos['slide_center_y'] + START_Y_OFFSET
        z = slide_pos['slide_center_z']
        print(f"Loaded slide position from calibration: X={start_x}, Y={start_y}, Z={z}")
    except Exception as e:
        print(f"Could not load slide position: {e}")
        cam.disconnect()
        printer.disconnect()
        return

    os.makedirs("border_detection_test", exist_ok=True)

    # --- Find top (negative Y), bottom (positive Y) ---
    y_max_dist = Y_MAX_DIST  # mm (now full slide width)
    coarse_step = COARSE_STEP  # mm
    # Top: scan negative Y from start_y
    top_y = find_border_black_edge(printer, cam, 'y', start_y, start_x, z, direction=-1, max_distance=y_max_dist, coarse_step=coarse_step, img_label='vertical_top')
    # Bottom: scan positive Y from start_y
    bottom_y = find_border_black_edge(printer, cam, 'y', start_y, start_x, z, direction=1, max_distance=y_max_dist, coarse_step=coarse_step, img_label='vertical_bottom')
    if top_y is None or bottom_y is None:
        print("Could not find top/bottom edges!")
        cam.disconnect()
        printer.disconnect()
        return
    print(f"Detected top edge at Y={top_y:.2f}, bottom edge at Y={bottom_y:.2f}")

    # --- Move to vertical midpoint ---
    mid_y = (top_y + bottom_y) / 2

    # --- Find left (negative X), right (positive X) ---
    x_max_dist = X_MAX_DIST  # mm (now full slide length)
    # Left: scan negative X from start_x
    left_x = find_border_black_edge(printer, cam, 'x', start_x, mid_y, z, direction=-1, max_distance=x_max_dist, coarse_step=coarse_step, img_label='horizontal_left')
    # Right: scan positive X from start_x
    right_x = find_border_black_edge(printer, cam, 'x', start_x, mid_y, z, direction=1, max_distance=x_max_dist, coarse_step=coarse_step, img_label='horizontal_right')
    if left_x is None or right_x is None:
        print("Could not find left/right edges!")
        cam.disconnect()
        printer.disconnect()
        return
    print(f"Detected left edge at X={left_x:.2f}, right edge at X={right_x:.2f}")

    cam.disconnect()
    printer.disconnect()

    print("\nEstimated slide boundaries (printer coordinates):")
    print(f"  left_x: {left_x:.2f}")
    print(f"  right_x: {right_x:.2f}")
    print(f"  top_y: {top_y:.2f}")
    print(f"  bottom_y: {bottom_y:.2f}")
    print("Images and black edge logs saved in border_detection_test/ directory.")

if __name__ == "__main__":
    main() 