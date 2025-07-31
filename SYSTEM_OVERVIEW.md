# Slide Scanner v3 - System Overview

## Complete System Components

This repository contains a complete slide scanning system with the following essential components:

### 1. Calibration System
- **Interactive Slide Positioning** (`calibration/slide_position_calibration.py`)
  - WASD key controls for X/Y movement
  - R/F keys for Z-axis focus adjustment
  - Real-time camera preview
  - Position capture and validation

- **Auto-Focus Calibration** (`calibration/focus_calibration.py`)
  - Automatic Z-axis sweep
  - Sharpness analysis using Laplacian variance
  - Optimal focus point detection
  - Focus quality metrics

- **Coverage Planning** (`calibration/coverage_planning.py`)
  - Field of view measurement
  - Optimal grid pattern calculation
  - Overlap optimization
  - Scan efficiency analysis

- **Corner Selection** 
  - Slide corners (`calibration/select_slide_corners.py`)
  - Calibration region corners (`calibration/select_calibration_corners.py`)
  - Interactive visual selection
  - Position validation and testing

### 2. Imaging System
- **Main Imaging Script** (`sweep_and_stitch.py`)
  - Grid-based image capture
  - Auto-focus at each position
  - Sharpness quality checking
  - Progress tracking and timing

- **Hardware Interfaces** (`utils/`)
  - Camera control (`camera_interface.py`)
  - 3D printer movement (`printer_interface.py`)
  - Connection management
  - Error handling

### 3. Stitching System
- **Simple Grid Stitch** (`simple_grid_stitch.py`)
  - Basic grid placement without complex alignment
  - Reliable composite creation
  - Support for missing tiles
  - Orientation handling

### 4. Workflow Management
- **Complete Workflow** (`run_slide_scan_complete.py`)
  - Automated end-to-end process
  - Error handling and recovery
  - Progress reporting
  - Session management

- **Legacy Support** (`scan_both_regions.py`)
  - Original calibration and scanning workflow
  - Backward compatibility

## Workflow Steps

### Initial Setup (First Time)
1. **Interactive Slide Positioning** - Find slide center and test corners
2. **Auto-Focus Calibration** - Determine optimal focus settings
3. **Coverage Planning** - Calculate scan patterns and field of view
4. **Corner Selection** - Define slide and calibration regions
5. **Configuration Generation** - Create JSON files for scanning

### Regular Scanning
1. **Calibration Scan** - Capture calibration region images
2. **Slide Scan** - Capture slide region images
3. **Simple Stitch** - Create final composite
4. **Session Summary** - Generate metadata and statistics

## Key Features

### Auto-Focus
- Automatic Z-axis positioning for optimal focus
- Sharpness measurement using Laplacian variance
- Quality threshold enforcement
- Focus optimization at each scan position

### Interactive Controls
- Real-time camera preview
- Keyboard-based movement controls
- Visual feedback for positioning
- Position capture and validation

### Quality Assurance
- Sharpness checking at each position
- Progress tracking and timing
- Error handling and recovery
- Session metadata generation

### Hardware Integration
- 3D printer movement control
- Camera capture and settings
- Connection management
- Error handling and recovery

## File Structure

```
final/
├── README.md                    # Main documentation
├── QUICK_START_GUIDE.md        # Usage instructions
├── SYSTEM_OVERVIEW.md           # This file
├── run_slide_scan_complete.py  # Main workflow script
├── sweep_and_stitch.py         # Imaging script
├── simple_grid_stitch.py       # Stitching script
├── slide_scanner.py            # Legacy scanner
├── scan_both_regions.py        # Calibration + scanning
├── calibration/                # Calibration scripts
│   ├── slide_position_calibration.py
│   ├── focus_calibration.py
│   ├── coverage_planning.py
│   ├── select_slide_corners.py
│   └── select_calibration_corners.py
├── utils/                      # Hardware interfaces
│   ├── camera_interface.py
│   └── printer_interface.py
├── config/                     # Configuration files
│   ├── slide_corners.json
│   └── calibration_corners.json
├── requirements.txt            # Python dependencies
├── LICENSE                     # MIT license
├── .gitignore                 # Git ignore rules
└── setup_github.sh           # GitHub setup helper
```

## Usage Summary

### First Time Setup
```bash
python3 calibration/slide_position_calibration.py
python3 calibration/focus_calibration.py
python3 calibration/coverage_planning.py
python3 calibration/select_slide_corners.py
python3 calibration/select_calibration_corners.py
```

### Regular Scanning
```bash
python3 run_slide_scan_complete.py
```

### Individual Steps
```bash
# Calibration scan
python3 sweep_and_stitch.py --corners config/calibration_corners.json --output calibration_images/

# Slide scan
python3 sweep_and_stitch.py --corners config/slide_corners.json --output slide_images/

# Stitch composite
python3 simple_grid_stitch.py --capture_dir slide_images/
```

This system provides a complete, professional-grade slide scanning solution with calibration, auto-focus, interactive controls, and reliable stitching. 