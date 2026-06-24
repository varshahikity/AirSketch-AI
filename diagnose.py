"""
AirSketch AI - Diagnostic Tool
This script diagnoses issues with the MediaPipe installation
and provides clean, actionable instructions to fix them.
"""

import sys
import os
import traceback

def run_diagnostics():
    print("=" * 60)
    print("AIRSKETCH AI - SYSTEM DIAGNOSTIC")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Current Directory: {os.getcwd()}")
    print("-" * 60)

    # 1. Check for shadowing files in the current directory
    local_files = os.listdir('.')
    shadowing_files = [f for f in local_files if f.startswith('mediapipe') and f != 'diagnose.py']
    if shadowing_files:
        print(f"[WARNING] Found potential shadowing files/folders in the current directory: {shadowing_files}")
        print("Please delete or rename these files/folders, as they block the real library!")
        print("-" * 60)

    # 2. Try importing mediapipe
    try:
        import mediapipe as mp
        print("[SUCCESS] Successfully imported 'mediapipe' module.")
        
        # Print where it is loaded from
        mp_file = getattr(mp, '__file__', 'Unknown')
        print(f"Loaded from: {mp_file}")
        
        # Check package directory contents if possible
        if mp_file != 'Unknown':
            mp_dir = os.path.dirname(mp_file)
            print(f"Package directory: {mp_dir}")
            solutions_dir = os.path.join(mp_dir, 'solutions')
            if os.path.exists(solutions_dir):
                print(f"[INFO] 'solutions' folder exists at: {solutions_dir}")
                print(f"Contents of 'solutions': {os.listdir(solutions_dir)}")
            else:
                print(f"[ERROR] 'solutions' folder does NOT exist inside the package directory!")
                print("This confirms your MediaPipe installation is corrupted (missing subfolders).")

        print(f"Module attributes: {dir(mp)}")
        
    except ImportError as e:
        print(f"[ERROR] Failed to import 'mediapipe' entirely: {e}")
        print("This means the library is not installed in this Python environment.")
        print("-" * 60)
        return

    print("-" * 60)
    
    # 3. Try importing solutions submodules
    try:
        import mediapipe.solutions.hands as mp_hands
        print("[SUCCESS] Successfully imported 'mediapipe.solutions.hands'.")
    except Exception as e:
        print("[ERROR] Failed to import 'mediapipe.solutions.hands'.")
        print("Detailed traceback:")
        traceback.print_exc()

    print("=" * 60)
    print("RECOMMENDED ACTION:")
    print("=" * 60)
    
    # Give exact reinstall command
    mp_dir_path = os.path.dirname(mp.__file__) if 'mp' in locals() and hasattr(mp, '__file__') else None
    if mp_dir_path:
        print(f"1. Close all programs and delete the folder:")
        print(f"   {mp_dir_path}")
        print("\n2. Then, run this command to reinstall it cleanly:")
    else:
        print("Run this command to install the library cleanly:")
        
    print("   py -3.12 -m pip install --upgrade --force-reinstall --disable-pip-version-check --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org mediapipe")
    print("=" * 60)

if __name__ == "__main__":
    run_diagnostics()
    input("\nPress Enter to exit...")
