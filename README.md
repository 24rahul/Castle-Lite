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

### 2. Configuration Files
Create these files in `config/`:

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

### Complete Workflow
```bash
python3 run_slide_scan_complete.py
```

### Stitch Only (Use Existing Images)
```bash
python3 run_slide_scan_complete.py --stitch-only
```

### Individual Steps
```bash
# 1. Scan calibration region
python3 sweep_and_stitch.py --corners config/calibration_corners.json --output calibration_images/

# 2. Scan slide region
python3 sweep_and_stitch.py --corners config/slide_corners.json --output slide_images/

# 3. Create composite
python3 simple_grid_stitch.py --capture_dir slide_images/
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