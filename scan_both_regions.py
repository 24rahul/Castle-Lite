import os
import subprocess
from datetime import datetime

PARENT_DIR = f"scan_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
CALIBRATION_SUBDIR = os.path.join(PARENT_DIR, "calibration")
SLIDE_SUBDIR = os.path.join(PARENT_DIR, "slide")

os.makedirs(CALIBRATION_SUBDIR, exist_ok=True)
os.makedirs(SLIDE_SUBDIR, exist_ok=True)

print(f"[1/2] Scanning calibration square...")
subprocess.run([
    "python3", "sweep_and_stitch.py",
    "--corners", "../config/calibration_corners.json",
    "--output", CALIBRATION_SUBDIR
], check=True)
print(f"Calibration scan complete. Images saved in: {CALIBRATION_SUBDIR}")

print(f"[2/2] Scanning slide...")
subprocess.run([
    "python3", "sweep_and_stitch.py",
    "--corners", "../config/slide_corners.json",
    "--output", SLIDE_SUBDIR
], check=True)
print(f"Slide scan complete. Images saved in: {SLIDE_SUBDIR}")

print(f"\nAll scans complete. Session folder: {PARENT_DIR}") 