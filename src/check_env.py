import sys
import os
import platform

def check_imports():
    print("Checking environment...")
    
    # Check for Windows
    if platform.system() != "Windows":
        print("This tool is designed for Windows.")
    
    # Check PyTorch
    try:
        import torch
        print("PyTorch imported successfully.")
    except OSError as e:
        if "WinError 1114" in str(e) or "DLL load failed" in str(e):
            print("\n" + "!"*60)
            print("CRITICAL ERROR: Missing Microsoft Visual C++ Redistributable")
            print("!"*60)
            print("\nYour system is missing required DLLs to run PyTorch/TensorFlow.")
            print("Please download and install the 'Microsoft Visual C++ 2015-2022 Redistributable (x64)'.")
            print("\nDownload Link: https://aka.ms/vs/17/release/vc_redist.x64.exe")
            print("\nAfter installing, restart your computer (or just this terminal) and try again.")
            print("!"*60 + "\n")
            sys.exit(1)
        else:
            raise e
    except ImportError as e:
        print(f"ImportError: {e}")
        sys.exit(1)

    print("Environment check passed.")

if __name__ == "__main__":
    check_imports()
