"""
Slide Scanner Script (v3)
"""

import argparse
import sys
import os

# Import calibration and scanning modules
from calibration.slide_position_calibration import SlidePositionCalibrator
from calibration.focus_calibration import FocusCalibrator
from calibration.coverage_planning import CoveragePlanner
from scanning.production_scanner import ProductionScanner, QuickScanner


def run_slide_position_calibration():
    calibrator = SlidePositionCalibrator()
    calibrator.run_calibration()

def run_focus_calibration():
    calibrator = FocusCalibrator()
    calibrator.run_calibration()

def run_coverage_planning():
    planner = CoveragePlanner()
    planner.run_planning()

def run_full_calibration():
    print("\n=== Running Full Calibration Sequence ===\n")
    run_slide_position_calibration()
    run_focus_calibration()
    run_coverage_planning()
    print("\n=== Full Calibration Complete ===\n")

def run_full_scan():
    scanner = ProductionScanner()
    scanner.run_production_scan()

def run_quick_scan():
    scanner = QuickScanner()
    scanner.load_configuration()
    scanner.connect_hardware()
    scanner.setup_scan()
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"quick_scan_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    scanner.perform_quick_scan(output_dir, positions_to_scan=9)
    scanner.printer.disconnect()
    scanner.camera.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Slide Scanner v3 - Unified Control")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-command to run")

    subparsers.add_parser("slide_position", help="Run slide position calibration")
    subparsers.add_parser("focus", help="Run focus calibration")
    subparsers.add_parser("coverage", help="Run coverage planning")
    subparsers.add_parser("calibrate", help="Run full calibration sequence (all steps)")
    subparsers.add_parser("scan", help="Run full production scan")
    subparsers.add_parser("quick_scan", help="Run quick scan (test mode)")

    args = parser.parse_args()

    if args.command == "slide_position":
        run_slide_position_calibration()
    elif args.command == "focus":
        run_focus_calibration()
    elif args.command == "coverage":
        run_coverage_planning()
    elif args.command == "calibrate":
        run_full_calibration()
    elif args.command == "scan":
        run_full_scan()
    elif args.command == "quick_scan":
        run_quick_scan()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 