import os
import subprocess
import shutil
import sys

def main():
    print("=== Compiling Dota 2 AI Bot Dashboard to Standalone .exe ===")
    
    # 1. Install pyinstaller if not present
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("PyInstaller not found. Installing via pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("PyInstaller installed successfully!")
        except Exception as e:
            print(f"Error installing PyInstaller: {e}")
            return

    # 2. Run PyInstaller to compile dashboard.py
    src_file = r"C:\бот\dashboard.py"
    dist_dir = r"C:\бот"
    
    if not os.path.exists(src_file):
        print(f"Error: {src_file} not found.")
        return

    print("Compiling dashboard.py...")
    import customtkinter
    customtkinter_path = os.path.dirname(customtkinter.__file__)
    print(f"CustomTkinter path found: {customtkinter_path}")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        f"--add-data={customtkinter_path}{os.pathsep}customtkinter",
        f"--distpath={dist_dir}",
        "--workpath=C:\\бот\\build",
        "--specpath=C:\\бот",
        "--name=DotaBotDashboard",
        src_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n=== Compilation Succeeded! ===")
        print(f"Your executable is ready at: C:\\бот\\DotaBotDashboard.exe")
        
        # Cleanup temporary build files
        print("Cleaning up build artifacts...")
        if os.path.exists("C:\\бот\\build"):
            shutil.rmtree("C:\\бот\\build")
        if os.path.exists("C:\\бот\\DotaBotDashboard.spec"):
            os.remove("C:\\бот\\DotaBotDashboard.spec")
        print("Cleanup done!")
        
    except Exception as e:
        print(f"Error during compilation: {e}")

if __name__ == "__main__":
    main()
