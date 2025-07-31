# Slide Scanner v3 - Final Package

## Quick Start

### One-Command Complete Workflow
```bash
python3 run_slide_scan_complete.py
```

This will:
1. Check prerequisites
2. Scan calibration region
3. Scan slide region
4. Create simple grid composite
5. Generate session summary

## File Structure

```
final/
├── README.md                    # This file
├── QUICK_START_GUIDE.md        # Detailed usage guide
├── run_slide_scan_complete.py  # Main workflow script
├── sweep_and_stitch.py         # Imaging script
├── simple_grid_stitch.py       # Stitching script
├── slide_scanner.py            # Legacy slide scanner
├── scan_both_regions.py        # Calibration and slide scanning
├── calibration/                # Calibration scripts
│   ├── slide_position_calibration.py  # Interactive slide positioning
│   ├── focus_calibration.py           # Auto-focus calibration
│   ├── coverage_planning.py           # Scan pattern planning
│   ├── select_slide_corners.py        # Slide corner selection
│   └── select_calibration_corners.py  # Calibration corner selection
├── utils/                      # Hardware interfaces
│   ├── camera_interface.py     # Camera control
│   └── printer_interface.py    # 3D printer control
└── config/                     # Configuration files (create these)
    ├── slide_corners.json      # Slide corner positions
    └── calibration_corners.json # Calibration region corners
```

## Prerequisites

### 1. Hardware Setup
- 3D printer connected and configured
- Camera connected and working
- Slide properly positioned

### 2. Initial Setup (First Time Only)
For first-time setup, run the calibration sequence:

```bash
# 1. Interactive slide positioning
python3 calibration/slide_position_calibration.py

# 2. Auto-focus calibration
python3 calibration/focus_calibration.py

# 3. Coverage planning
python3 calibration/coverage_planning.py

# 4. Select slide corners
python3 calibration/select_slide_corners.py

# 5. Select calibration corners
python3 calibration/select_calibration_corners.py
```

This will create the necessary configuration files in `config/`.

### 3. Configuration Files
After calibration, these files will be created in `config/`:

**`config/slide_corners.json`**:
```json
{
  "bottom_left": {"X": 0.0, "Y": 0.0, "Z": 2.2},
  "bottom_right": {"X": 25.0, "Y": 0.0, "Z": 2.2},
  "top_right": {"X": 25.0, "Y": 75.0, "Z": 2.2},
  "top_left": {"X": 0.0, "Y": 75.0, "Z": 2.2}
}
```

**`config/calibration_corners.json`**:
```json
{
  "bottom_left": {"X": 0.0, "Y": 0.0, "Z": 2.2},
  "bottom_right": {"X": 10.0, "Y": 0.0, "Z": 2.2},
  "top_right": {"X": 10.0, "Y": 10.0, "Z": 2.2},
  "top_left": {"X": 0.0, "Y": 10.0, "Z": 2.2}
}
```

## Usage Options

### Complete Workflow (After Calibration)
```bash
python3 run_slide_scan_complete.py
```

### Initial Calibration (First Time Setup)
```bash
# Run complete calibration sequence
python3 scan_both_regions.py
```

### Individual Calibration Steps
```bash
# 1. Interactive slide positioning
python3 calibration/slide_position_calibration.py

# 2. Auto-focus calibration
python3 calibration/focus_calibration.py

# 3. Coverage planning
python3 calibration/coverage_planning.py

# 4. Select slide corners
python3 calibration/select_slide_corners.py

# 5. Select calibration corners
python3 calibration/select_calibration_corners.py
```

### Individual Scanning Steps
```bash
# 1. Scan calibration region
python3 sweep_and_stitch.py --corners config/calibration_corners.json --output calibration_images/

# 2. Scan slide region
python3 sweep_and_stitch.py --corners config/slide_corners.json --output slide_images/

# 3. Create composite
python3 simple_grid_stitch.py --capture_dir slide_images/
```

### Stitch Only (Use Existing Images)
```bash
python3 run_slide_scan_complete.py --stitch-only
```

## Output Structure

After running the complete workflow:
```
scan_session_YYYYMMDD_HHMMSS/
├── calibration/           # Calibration images
│   ├── img_x0_y0.png
│   ├── img_x0_y1.png
│   └── ...
├── slide/                # Slide images + final composite
│   ├── img_x0_y0.png
│   ├── img_x0_y1.png
│   ├── ...
│   └── simple_grid_slide.png  # Final stitched output
└── session_summary.json  # Session metadata
```

## Troubleshooting

### Missing Configuration Files
If you get "Missing required files" error:
1. Create the `config/` directory
2. Add the corner position JSON files
3. Adjust coordinates for your specific setup

### Hardware Connection Issues
- Check 3D printer connection
- Verify camera is working
- Ensure slide is properly positioned

### Image Quality Issues
- Clean camera lens and slide
- Check lighting conditions
- Verify focus settings

## Performance Notes

- **Typical scan time**: 5-15 minutes
- **Image count**: 20-100 images
- **Output size**: 10-50 MB
- **Memory usage**: ~1-2 GB

## Calibration Features

### Interactive Slide Positioning
- **File**: `calibration/slide_position_calibration.py`
- **Purpose**: Find exact slide center and test corner positions
- **Controls**: WASD keys for movement, R/F for Z-axis, C to capture position

### Auto-Focus Calibration
- **File**: `calibration/focus_calibration.py`
- **Purpose**: Automatically find optimal focus using sharpness analysis
- **Features**: Z-axis sweep with Laplacian variance measurement

### Coverage Planning
- **File**: `calibration/coverage_planning.py`
- **Purpose**: Calculate optimal scan patterns with minimal overlap
- **Features**: Field of view measurement and grid optimization

### Corner Selection
- **Files**: `calibration/select_slide_corners.py`, `calibration/select_calibration_corners.py`
- **Purpose**: Interactive corner selection for slide and calibration regions
- **Features**: Visual feedback and position validation

## Customization

### Adjust Grid Density
Modify in `sweep_and_stitch.py`:
```python
GRID_STEP_X = 1.0  # mm between images
GRID_STEP_Y = 1.0  # mm between images
```

### Change Image Quality
Modify in `sweep_and_stitch.py`:
```python
frame = camera.capture_and_save(filename, quality=95)  # JPEG quality
```

### Adjust Focus Settings
Modify in `sweep_and_stitch.py`:
```python
SHARPNESS_THRESHOLD = 30.0  # Laplacian variance threshold
LOCAL_SWEEP_RANGE = 1.0     # mm autofocus range
```

## Additional Resources

- See `QUICK_START_GUIDE.md` for detailed instructions
- Check session summary files for statistics
- Review captured images for quality assessment

## Success Indicators

- **Complete workflow**: Session directory created with images
- **Good quality**: Sharp, well-lit images in composite
- **Proper alignment**: Grid pattern visible in stitched output
- **Full coverage**: No missing regions in final composite 