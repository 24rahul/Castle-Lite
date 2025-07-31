#!/usr/bin/env python3
"""
Complete Slide Scan Run Sequence
Automated workflow from slide imaging to final stitched output using simple grid stitch
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
import argparse

class SlideScanRunner:
    def __init__(self):
        self.session_name = f"scan_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.calibration_dir = os.path.join(self.session_name, "calibration")
        self.slide_dir = os.path.join(self.session_name, "slide")
        
    def run_step(self, step_name, command, description):
        """Run a step with error handling and progress reporting"""
        print(f"\n{'='*60}")
        print(f"STEP: {step_name}")
        print(f"DESCRIPTION: {description}")
        print(f"COMMAND: {' '.join(command)}")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print("SUCCESS")
            if result.stdout:
                print("Output:", result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"FAILED: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
    
    def check_prerequisites(self):
        """Check that required files and directories exist"""
        print("Checking prerequisites...")
        
        required_files = [
            "../config/slide_corners.json",
            "../config/calibration_corners.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print("Missing required files:")
            for file_path in missing_files:
                print(f"  - {file_path}")
            print("\nPlease run calibration first:")
            print("  python3 scan_both_regions.py")
            return False
        
        print("All prerequisites met")
        return True
    
    def create_session_directories(self):
        """Create session directories"""
        print(f"Creating session directories...")
        os.makedirs(self.calibration_dir, exist_ok=True)
        os.makedirs(self.slide_dir, exist_ok=True)
        print(f"Session directory: {self.session_name}")
    
    def run_calibration_scan(self):
        """Run calibration region scan"""
        return self.run_step(
            "CALIBRATION SCAN",
            ["python3", "sweep_and_stitch.py", 
             "--corners", "../config/calibration_corners.json",
             "--output", self.calibration_dir],
            "Scanning calibration checkerboard region"
        )
    
    def run_slide_scan(self):
        """Run slide scan"""
        return self.run_step(
            "SLIDE SCAN", 
            ["python3", "sweep_and_stitch.py",
             "--corners", "../config/slide_corners.json", 
             "--output", self.slide_dir],
            "Scanning slide region"
        )
    
    def run_simple_stitch(self):
        """Run simple grid stitch on slide images"""
        return self.run_step(
            "SIMPLE GRID STITCH",
            ["python3", "simple_grid_stitch.py", "--capture_dir", self.slide_dir],
            "Creating simple grid composite from slide images"
        )
    
    def create_session_summary(self):
        """Create a summary of the session"""
        summary = {
            "session_name": self.session_name,
            "timestamp": datetime.now().isoformat(),
            "calibration_dir": self.calibration_dir,
            "slide_dir": self.slide_dir,
            "steps_completed": []
        }
        
        # Check what was created
        if os.path.exists(self.calibration_dir):
            calib_files = len([f for f in os.listdir(self.calibration_dir) if f.endswith('.png')])
            summary["steps_completed"].append(f"calibration_scan ({calib_files} images)")
        
        if os.path.exists(self.slide_dir):
            slide_files = len([f for f in os.listdir(self.slide_dir) if f.endswith('.png')])
            summary["steps_completed"].append(f"slide_scan ({slide_files} images)")
            
            # Check for stitched output
            stitched_file = os.path.join(self.slide_dir, "simple_grid_slide.png")
            if os.path.exists(stitched_file):
                summary["steps_completed"].append("simple_grid_stitch")
                summary["stitched_output"] = stitched_file
        
        # Save summary
        summary_file = os.path.join(self.session_name, "session_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSession summary saved: {summary_file}")
        return summary
    
    def run_complete_workflow(self):
        """Run the complete workflow"""
        print("SLIDE SCAN COMPLETE WORKFLOW")
        print(f"Session: {self.session_name}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Create directories
        self.create_session_directories()
        
        # Run calibration scan
        if not self.run_calibration_scan():
            print("Calibration scan failed")
            return False
        
        # Run slide scan  
        if not self.run_slide_scan():
            print("Slide scan failed")
            return False
        
        # Run simple stitch
        if not self.run_simple_stitch():
            print("Simple stitch failed")
            return False
        
        # Create summary
        summary = self.create_session_summary()
        
        print(f"\nWORKFLOW COMPLETE!")
        print(f"Session directory: {self.session_name}")
        print(f"Calibration images: {self.calibration_dir}")
        print(f"Slide images: {self.slide_dir}")
        
        if "stitched_output" in summary:
            print(f"Stitched output: {summary['stitched_output']}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Complete slide scan workflow")
    parser.add_argument('--skip-calibration', action='store_true', 
                       help="Skip calibration scan (use existing)")
    parser.add_argument('--skip-scan', action='store_true',
                       help="Skip slide scan (use existing images)")
    parser.add_argument('--stitch-only', action='store_true',
                       help="Only run stitching on existing images")
    
    args = parser.parse_args()
    
    runner = SlideScanRunner()
    
    if args.stitch_only:
        print("STITCHING ONLY MODE")
        return runner.run_simple_stitch()
    
    if args.skip_calibration and args.skip_scan:
        print("STITCHING ONLY MODE")
        return runner.run_simple_stitch()
    
    # Run complete workflow
    return runner.run_complete_workflow()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 