#!/usr/bin/env python3
"""
Simple Grid Stitch - Baseline comparison
Places images in a basic grid without any stitching or warping.
"""

import cv2
import numpy as np
import json
import os
import glob
from pathlib import Path
import argparse

def load_corners(capture_dir):
    """Load corner positions from JSON file"""
    corners_file = os.path.join(capture_dir, "corners.json")
    if not os.path.exists(corners_file):
        print(f"Error: {corners_file} not found")
        return None
    
    with open(corners_file, 'r') as f:
        corners = json.load(f)
    
    print("Loaded corner positions:")
    for corner, pos in corners.items():
        print(f"  {corner}: X={pos['X']:.2f}, Y={pos['Y']:.2f}, Z={pos['Z']:.2f}")
    
    return corners

def load_images(capture_dir):
    """Load all captured images"""
    image_files = glob.glob(os.path.join(capture_dir, "img_*.png"))
    if not image_files:
        print(f"Error: No img_*.png files found in {capture_dir}")
        return {}
    
    images = {}
    for file_path in image_files:
        filename = os.path.basename(file_path)
        # Extract coordinates from filename: img_xX_yY.png
        parts = filename.replace('.png', '').split('_')
        if len(parts) >= 3:
            try:
                x_part = parts[1]  # xX
                y_part = parts[2]  # yY
                x = int(x_part[1:])  # Remove 'x' prefix
                y = int(y_part[1:])  # Remove 'y' prefix
                img = cv2.imread(file_path)
                if img is not None:
                    images[(x, y)] = img
            except ValueError:
                continue
    
    print(f"Loaded {len(images)} images")
    return images

def simple_grid_stitch(images):
    """Place images in a simple grid without any stitching or warping"""
    if not images:
        print("No images to stitch")
        return None
    
    # Find grid dimensions
    x_coords = [x for x, y in images.keys()]
    y_coords = [y for x, y in images.keys()]
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    nx = max_x - min_x + 1
    ny = max_y - min_y + 1
    
    print(f"Grid dimensions: {nx} x {ny}")
    
    # Get image dimensions (assuming all images are the same size)
    sample_img = next(iter(images.values()))
    img_h, img_w = sample_img.shape[:2]
    print(f"Individual image size: {img_w} x {img_h}")
    
    # Create composite canvas
    composite_w = nx * img_w
    composite_h = ny * img_h
    print(f"Simple grid composite size: {composite_w} x {composite_h}")
    
    composite = np.zeros((composite_h, composite_w, 3), dtype=np.uint8)
    
    # Place images in grid
    for (x, y), img in images.items():
        # Convert to grid coordinates
        grid_x = x - min_x
        grid_y = y - min_y
        
        # Calculate position in composite
        x_start = grid_x * img_w
        y_start = grid_y * img_h
        x_end = x_start + img_w
        y_end = y_start + img_h
        
        # Place image
        composite[y_start:y_end, x_start:x_end] = img
        print(f"Placed image ({x},{y}) at grid position ({grid_x},{grid_y}) -> pixels ({x_start},{y_start})")
    
    return composite

def parse_args():
    parser = argparse.ArgumentParser(description="Simple grid stitch for slide or calibration region.")
    parser.add_argument('--capture_dir', type=str, default=None, help="Directory containing images to stitch")
    return parser.parse_args()

def main():
    args = parse_args()
    if args.capture_dir is not None:
        capture_dir = args.capture_dir
    else:
        # Find the most recent scan_session/*/slide or sweep_captures_*
        import glob
        session_dirs = sorted(glob.glob("scan_session_*/slide"))
        if session_dirs:
            capture_dir = session_dirs[-1]
        else:
            capture_dirs = sorted(glob.glob("sweep_captures_*"))
            if not capture_dirs:
                print("Error: No sweep_captures_* or scan_session_*/slide directories found")
                return
            capture_dir = capture_dirs[-1]
    print(f"Using capture directory: {capture_dir}")
    
    # Load images
    images = load_images(capture_dir)
    if not images:
        return
    
    # Load corners (for reference only - not used in simple grid)
    corners = load_corners(capture_dir)
    
    # Create simple grid composite
    print("\nCreating simple grid composite...")
    composite = simple_grid_stitch(images)
    
    if composite is not None:
        # Save result
        output_path = os.path.join(capture_dir, "simple_grid_slide.png")
        cv2.imwrite(output_path, composite)
        print(f"\nSimple grid composite saved to: {output_path}")
        
        # Show image
        cv2.imshow("Simple Grid Composite", composite)
        print("Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Failed to create composite")

if __name__ == "__main__":
    main() 