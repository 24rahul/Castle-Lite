import sys
import os
import cv2
import numpy as np
import json
import time
from datetime import datetime
import argparse
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from utils.printer_interface import PrinterInterface
from utils.camera_interface import CameraInterface

# Parameters
GRID_STEP_X = 1.0  # mm
GRID_STEP_Y = 1.0  # mm
CORNER_PATH = "../config/slide_corners.json"
CAPTURE_DIR = f"sweep_captures_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
STITCHED_PATH = os.path.join(CAPTURE_DIR, "stitched_slide.png")
SHARPNESS_THRESHOLD = 30.0  # Laplacian variance threshold (tune as needed)
LOCAL_SWEEP_RANGE = 1.0     # mm (±0.5mm)
LOCAL_SWEEP_STEP = 0.1      # mm

# Helper: Bilinear interpolation for grid points in a quadrilateral (with Z)
def quad_interp(corners, nx, ny):
    bl = np.array([corners['bottom_left']['X'], corners['bottom_left']['Y'], corners['bottom_left']['Z']])
    br = np.array([corners['bottom_right']['X'], corners['bottom_right']['Y'], corners['bottom_right']['Z']])
    tr = np.array([corners['top_right']['X'], corners['top_right']['Y'], corners['top_right']['Z']])
    tl = np.array([corners['top_left']['X'], corners['top_left']['Y'], corners['top_left']['Z']])
    grid = np.zeros((ny, nx, 3))
    for iy in range(ny):
        fy = iy / (ny - 1) if ny > 1 else 0
        left = bl * (1 - fy) + tl * fy
        right = br * (1 - fy) + tr * fy
        for ix in range(nx):
            fx = ix / (nx - 1) if nx > 1 else 0
            grid[iy, ix] = left * (1 - fx) + right * fx
    return grid

def calculate_sharpness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def local_z_autofocus(printer, camera, x, y, z_center):
    z_positions = np.arange(z_center - LOCAL_SWEEP_RANGE/2, z_center + LOCAL_SWEEP_RANGE/2 + LOCAL_SWEEP_STEP/2, LOCAL_SWEEP_STEP)
    best_sharpness = -1
    best_z = z_center
    best_frame = None
    for z in z_positions:
        printer.move_to_position(x=x, y=y, z=z)
        time.sleep(0.2)
        frame = camera.capture_frame()
        sharpness = calculate_sharpness(frame)
        print(f"    Z={z:.2f}: sharpness={sharpness:.1f}")
        if sharpness > best_sharpness:
            best_sharpness = sharpness
            best_z = z
            best_frame = frame.copy()
    return best_z, best_frame, best_sharpness

def parse_args():
    parser = argparse.ArgumentParser(description="Sweep and stitch slide or calibration region.")
    parser.add_argument('--corners', type=str, default="../config/slide_corners.json", help="Path to corners JSON file")
    parser.add_argument('--output', type=str, default=None, help="Output directory for captures")
    return parser.parse_args()

def main():
    args = parse_args()
    CORNER_PATH = args.corners
    if args.output is not None:
        CAPTURE_DIR = args.output
    else:
        CAPTURE_DIR = f"sweep_captures_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    STITCHED_PATH = os.path.join(CAPTURE_DIR, "stitched_slide.png")
    # Load corners
    with open(CORNER_PATH, 'r') as f:
        corners = json.load(f)
    # Compute grid size
    width = np.linalg.norm(np.array([corners['bottom_right']['X'], corners['bottom_right']['Y']]) - np.array([corners['bottom_left']['X'], corners['bottom_left']['Y']]))
    height = np.linalg.norm(np.array([corners['top_left']['X'], corners['top_left']['Y']]) - np.array([corners['bottom_left']['X'], corners['bottom_left']['Y']]))
    nx = int(np.ceil(width / GRID_STEP_X)) + 1
    ny = int(np.ceil(height / GRID_STEP_Y)) + 1
    print(f"Grid: {nx} x {ny} (width={width:.2f}mm, height={height:.2f}mm)")
    grid = quad_interp(corners, nx, ny)
    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # Connect hardware
    printer = PrinterInterface()
    camera = CameraInterface()
    assert printer.connect(), "Failed to connect to printer"
    assert camera.connect(), "Failed to connect to camera"

    # Prepare for stitching
    stitched = None
    stitched_mask = None
    live_map = np.zeros((ny, nx, 3), dtype=np.uint8)
    live_map[:] = (30, 30, 30)  # dark gray for not-yet-captured

    # ORB feature matcher for adaptive stitching
    orb = cv2.ORB_create(1000)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    for iy in range(ny):
        for ix in range(nx):
            pos = grid[iy, ix]
            x, y, z = pos[0], pos[1], pos[2]
            printer.move_to_position(x=x, y=y, z=z)
            time.sleep(0.5)
            frame = camera.capture_frame()
            sharpness = calculate_sharpness(frame)
            print(f"({ix},{iy}) at X={x:.2f}, Y={y:.2f}, Z={z:.2f}: sharpness={sharpness:.1f}")
            # If sharpness is low, do local autofocus
            if sharpness < SHARPNESS_THRESHOLD:
                print(f"  Sharpness below threshold ({SHARPNESS_THRESHOLD}), running local autofocus...")
                z, frame, sharpness = local_z_autofocus(printer, camera, x, y, z)
                print(f"  Autofocus found Z={z:.2f} with sharpness={sharpness:.1f}")
            fname = os.path.join(CAPTURE_DIR, f"img_x{ix}_y{iy}.png")
            cv2.imwrite(fname, frame)
            print(f"  Saved image at ({ix},{iy})")

            # Update live progress map
            live_map[iy, ix] = (0, 255, 0)  # green for completed
            vis = cv2.resize(live_map, (nx*20, ny*20), interpolation=cv2.INTER_NEAREST)
            cv2.imshow("Live Completion Map (progress only)", vis)
            cv2.waitKey(1)

            # Stitching (feature-based, adaptive)
            if stitched is None:
                stitched = frame.copy()
                stitched_mask = np.ones(frame.shape[:2], dtype=np.uint8)*255
            else:
                # Find overlap region (naive: left or above)
                overlap = None
                if ix > 0:
                    left_img = cv2.imread(os.path.join(CAPTURE_DIR, f"img_x{ix-1}_y{iy}.png"))
                    kp1, des1 = orb.detectAndCompute(left_img, None)
                    kp2, des2 = orb.detectAndCompute(frame, None)
                    if des1 is not None and des2 is not None:
                        matches = bf.match(des1, des2)
                        if len(matches) > 10:
                            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1,1,2)
                            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1,1,2)
                            M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC,5.0)
                            if M is not None:
                                h, w = frame.shape[:2]
                                stitched = cv2.warpPerspective(frame, M, (stitched.shape[1], stitched.shape[0]), dst=stitched, borderMode=cv2.BORDER_TRANSPARENT)
                    else:
                        print(f"[WARN] No features found for stitching at ({ix},{iy}) with left neighbor.")
                elif iy > 0:
                    above_img = cv2.imread(os.path.join(CAPTURE_DIR, f"img_x{ix}_y{iy-1}.png"))
                    kp1, des1 = orb.detectAndCompute(above_img, None)
                    kp2, des2 = orb.detectAndCompute(frame, None)
                    if des1 is not None and des2 is not None:
                        matches = bf.match(des1, des2)
                        if len(matches) > 10:
                            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1,1,2)
                            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1,1,2)
                            M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC,5.0)
                            if M is not None:
                                h, w = frame.shape[:2]
                                stitched = cv2.warpPerspective(frame, M, (stitched.shape[1], stitched.shape[0]), dst=stitched, borderMode=cv2.BORDER_TRANSPARENT)
                    else:
                        print(f"[WARN] No features found for stitching at ({ix},{iy}) with above neighbor.")
    # Save final stitched image
    cv2.imwrite(STITCHED_PATH, stitched)
    print(f"Stitched image saved to {STITCHED_PATH}")
    cv2.destroyAllWindows()
    printer.disconnect()
    camera.disconnect()

if __name__ == "__main__":
    main() 