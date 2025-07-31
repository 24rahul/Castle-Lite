# Quick Start Guide - Complete Slide Scan Workflow

## Overview
This guide covers the complete workflow from slide imaging to final stitched output using the simple grid stitch method.

## Prerequisites
Before running the complete workflow, you need:
1. **Calibration files** in `../config/`:
   - `slide_corners.json` - Slide corner positions
   - `calibration_corners.json` - Calibration region corners

2. **Hardware setup**:
   - 3D printer connected and configured
   - Camera connected and working
   - Slide properly positioned

## Complete Workflow Script

### One-Command Solution
```bash
python3 run_slide_scan_complete.py
```

This single command will:
1. Check prerequisites
2. Scan calibration region
3. Scan slide region  
4. Create simple grid composite
5. Generate session summary

### Output Structure
```
scan_session_YYYYMMDD_HHMMSS/
├── calibration/           # Calibration checkerboard images
│   ├── img_x0_y0.png
│   ├── img_x0_y1.png
│   └── ...
├── slide/                # Slide images
│   ├── img_x0_y0.png
│   ├── img_x0_y1.png
│   ├── ...
│   └── simple_grid_slide.png  # Final stitched output
└── session_summary.json  # Session metadata
```

## Individual Scripts (Manual Workflow)

If you prefer to run steps individually:

### 1. Calibration Scan
```bash
python3 sweep_and_stitch.py --corners ../config/calibration_corners.json --output calibration_images/
```

### 2. Slide Scan
```bash
python3 sweep_and_stitch.py --corners ../config/slide_corners.json --output slide_images/
```

### 3. Simple Grid Stitch
```bash
python3 simple_grid_stitch.py --capture_dir slide_images/
```

## Advanced Options

### Stitch Only (Use Existing Images)
```bash
python3 run_slide_scan_complete.py --stitch-only
```

### Skip Calibration Scan
```bash
python3 run_slide_scan_complete.py --skip-calibration
```

### Skip Slide Scan  
```bash
python3 run_slide_scan_complete.py --skip-scan
```

## Script Reference

### Core Imaging Scripts
- **`sweep_and_stitch.py`** - Main imaging script that captures grid of images
- **`simple_grid_stitch.py`** - Creates simple grid composite from captured images

### Workflow Scripts
- **`run_slide_scan_complete.py`** - Complete automated workflow
- **`scan_both_regions.py`** - Legacy script for both calibration and slide scanning

### Calibration Scripts
- **`calibration/checkerboard_calibration.py`** - Checkerboard detection and calibration
- **`calibration/align_calibration_images.py`** - Image alignment using feature matching
- **`calibration/auto_crop_checkerboard.py`** - Auto-crop checkerboard from composite

### Utility Scripts
- **`utils/camera_interface.py`** - Camera control and image capture
- **`utils/printer_interface.py`** - 3D printer movement control

## Troubleshooting

### Missing Calibration Files
If you get "Missing required files" error:
```bash
# Run the legacy calibration script first
python3 scan_both_regions.py
```

### Hardware Connection Issues
Check that:
- 3D printer is connected and responding
- Camera is connected and working
- Slide is properly positioned

### Image Quality Issues
- Clean camera lens and slide
- Ensure proper focus
- Check lighting conditions

## File Naming Convention
Images are saved as: `img_x{X}_y{Y}.png`
- X = column index (0, 1, 2, ...)
- Y = row index (0, 1, 2, ...)
- Example: `img_x3_y5.png` = image at column 3, row 5

## Output Files
- **`simple_grid_slide.png`** - Final stitched composite
- **`session_summary.json`** - Session metadata and statistics
- Individual captured images in session directories

## Performance Notes
- **Typical scan time**: 5-15 minutes depending on grid size
- **Image count**: 20-100 images depending on slide size and overlap
- **Output size**: 10-50 MB for typical slides
- **Memory usage**: ~1-2 GB during processing

## Next Steps
After successful scan:
1. Review the stitched output (`simple_grid_slide.png`)
2. Check session summary for statistics
3. Use images for analysis or further processing
4. Archive session directory for future reference 