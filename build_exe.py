"""
Build script for creating ArbuzAV.exe
Run this script to create a standalone executable
"""

import os
import subprocess
import sys

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed successfully")

def build_exe():
    """Build the executable"""
    print("\n" + "="*50)
    print("Building ArbuzAV.exe...")
    print("="*50 + "\n")
    
    # PyInstaller command with spec file
    cmd = [
        "pyinstaller",
        "--clean",                # Clean build
        "ArbuzAV.spec"           # Use spec file for correct pynput support
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*50)
        print("✓ Build successful!")
        print("="*50)
        print(f"\nYour executable is located at: dist/ArbuzAV.exe")
        print("You can share this file with your friend!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("ArbuzAV EXE Builder")
    print("="*50)
    
    # Check if ArbuzAV.py exists
    if not os.path.exists("ArbuzAV.py"):
        print("✗ Error: ArbuzAV.py not found!")
        print("Make sure you're running this script in the same directory as ArbuzAV.py")
        sys.exit(1)
    
    install_pyinstaller()
    build_exe()
    
    print("\nPress Enter to exit...")
    input()
