"""
Build script for creating portable Instagram Automation Tool package (Simple version).

This script:
1. Builds updater.exe using PyInstaller
2. Creates portable package structure with Python scripts
3. Includes batch launcher (run_tool.bat)
4. Generates README.txt

Usage: python build_package_simple.py
"""
import os
import sys
import subprocess
import shutil
import zipfile
from datetime import datetime

# Fix console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class SimplePackageBuilder:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.dist_dir = os.path.join(self.root_dir, "dist")
        self.build_dir = os.path.join(self.root_dir, "build")
        self.package_name = "InstagramTool_Portable"
        self.package_dir = os.path.join(self.dist_dir, self.package_name)

    def print_header(self):
        """Print build script header"""
        print("=" * 70)
        print("     Instagram Automation Tool - Simple Package Builder")
        print("=" * 70)
        print()

    def check_pyinstaller(self):
        """Check if PyInstaller is installed"""
        try:
            import PyInstaller
            print("[OK] PyInstaller installed")
            return True
        except ImportError:
            print("[FAIL] PyInstaller not installed!")
            print("   Install: pip install pyinstaller")
            return False

    def clean_previous_builds(self):
        """Clean previous build and dist directories"""
        print("[CLEAN] Cleaning previous builds...")

        dirs_to_clean = [self.build_dir, self.dist_dir]

        for directory in dirs_to_clean:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                print(f"   Removed: {directory}")

        print("[OK] Cleanup complete")

    def build_updater_exe(self):
        """Build updater.exe using PyInstaller"""
        print()
        print("[BUILD] Building updater.exe (Console)...")

        cmd = [
            "pyinstaller",
            "--onefile",
            "--console",
            "--name", "updater",
            "updater.py"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=180
            )

            if result.returncode != 0:
                print("[FAIL] Error building updater.exe:")
                print(result.stderr)
                return False

            print("[OK] Build updater.exe successful")
            return True

        except subprocess.TimeoutExpired:
            print("[FAIL] Timeout building updater.exe")
            return False
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            return False

    def create_package_structure(self):
        """Create portable package directory structure"""
        print()
        print("[PACK] Creating package structure...")

        # Create package directory
        os.makedirs(self.package_dir, exist_ok=True)

        # Copy updater.exe
        updater_exe = os.path.join(self.dist_dir, "updater.exe")
        if os.path.exists(updater_exe):
            shutil.copy2(updater_exe, self.package_dir)
            print("   [OK] Copied updater.exe")
        else:
            print("   [WARN] updater.exe not found!")

        # Copy source code files
        files_to_copy = [
            "main.py",
            "config.py",
            "constants.py",
            "requirements.txt",
            "version.txt",
            "run_tool.bat"
        ]

        for file in files_to_copy:
            src = os.path.join(self.root_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, self.package_dir)
                print(f"   [OK] Copied {file}")

        # Copy directories
        dirs_to_copy = ["core", "tabs", "utils"]

        for directory in dirs_to_copy:
            src_dir = os.path.join(self.root_dir, directory)
            dst_dir = os.path.join(self.package_dir, directory)

            if os.path.exists(src_dir):
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                print(f"   [OK] Copied {directory}/")

        # Create empty directories
        empty_dirs = ["data", "data/api", "data/output", "logs", "temp", "downloads", "backups"]

        for directory in empty_dirs:
            dir_path = os.path.join(self.package_dir, directory)
            os.makedirs(dir_path, exist_ok=True)

        # Create placeholder file in data/api
        api_placeholder = os.path.join(self.package_dir, "data", "api", "apis.json")
        import json
        api_template = {
            "youtube": [],
            "tiktok": []
        }
        with open(api_placeholder, "w", encoding="utf-8") as f:
            json.dump(api_template, f, ensure_ascii=False, indent=2)

        print("[OK] Package structure created")
        return True

    def generate_readme(self):
        """Generate README.txt with instructions"""
        print()
        print("[DOC] Creating README.txt...")

        readme_path = os.path.join(self.package_dir, "README.txt")

        readme_content = f"""
================================================================================
          INSTAGRAM AUTOMATION TOOL - PORTABLE VERSION
================================================================================

Build date: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

================================================================================
SYSTEM REQUIREMENTS
================================================================================

[OK] Windows 10/11 (64-bit)
[OK] Python 3.10 or newer (must be installed)
[OK] LDPlayer 9 (must be installed)
[OK] Internet connection (for updates and video downloads)

================================================================================
FIRST TIME SETUP
================================================================================

1. Install Python 3.10 or newer (if not already installed):
   Download from: https://www.python.org/downloads/
   IMPORTANT: Check "Add Python to PATH" during installation!

2. Install LDPlayer 9 (if not already installed):
   Download from: https://www.ldplayer.net/

3. Install Python dependencies:
   Option A: Double-click run_tool.bat (will auto-install)
   Option B: Manual install:
      - Open Command Prompt in this folder
      - Run: pip install -r requirements.txt

4. Configure API Keys (optional):
   - Use the "🔑 Quản lý API" button in the application
   - Or manually edit: data/api/apis.json
   - Add YouTube and TikTok API keys as needed

5. Configure LDPlayer path (if needed):
   - Tool will auto-detect LDPlayer
   - If not found, create file "ldplayer_path.txt"
   - Write LDPlayer path (e.g., C:\\LDPlayer\\LDPlayer9)

================================================================================
HOW TO USE
================================================================================

RUN TOOL:
   Double-click: run_tool.bat

   The batch file will:
   - Check Python installation
   - Auto-install missing packages
   - Launch the GUI application

UPDATE TOOL:
   Double-click: updater.exe

   The updater will:
   - Download latest code from GitHub
   - Backup old version
   - Install new dependencies

================================================================================
FOLDER STRUCTURE
================================================================================

InstagramTool_Portable/
├── run_tool.bat          <- Run main tool
├── updater.exe           <- Update tool
├── main.py               <- Main application script
├── config.py             <- Configuration
├── constants.py          <- Constants
├── requirements.txt      <- Python dependencies
├── core/                 <- Source code (core modules)
├── tabs/                 <- Source code (UI tabs)
├── utils/                <- Source code (utilities)
├── data/                 <- User data
│   ├── api/              <- API keys
│   ├── output/           <- Video metadata
│   └── *.json            <- VM configurations
├── logs/                 <- Log files
├── temp/                 <- Temporary files
├── downloads/            <- Video downloads
├── backups/              <- Old code backups (when updating)
└── README.txt            <- This file

================================================================================
NOTES
================================================================================

[WARN] Do not delete .git folder (needed for updates)
[WARN] Do not modify files in core/, tabs/, utils/ (will be overwritten on update)
[WARN] User data (data/, logs/) will NOT be lost when updating

================================================================================
TROUBLESHOOTING
================================================================================

[FAIL] "Python is not installed or not in PATH":
   - Install Python from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation
   - Restart Command Prompt after installation

[FAIL] "LDPlayer not found":
   - Create file "ldplayer_path.txt" and write LDPlayer path

[FAIL] "Git not found" when updating:
   - Install Git: https://git-scm.com/download/win
   - Check "Add to PATH" option during installation

[FAIL] Python module errors:
   - Run: pip install -r requirements.txt --upgrade

[FAIL] Tool crashes or errors:
   - Check logs/app.log for details
   - Try running: python main.py (from Command Prompt)

================================================================================
SUPPORT
================================================================================

GitHub: [Paste GitHub repo URL here]
Issues: [Paste GitHub issues URL here]

================================================================================
                          (c) 2024 - All Rights Reserved
================================================================================
"""

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        print("[OK] README.txt created")
        return True

    def create_zip(self):
        """Create ZIP file for distribution"""
        print()
        confirm = input("[?] Create ZIP file? (Y/n): ").strip().lower()

        if confirm and confirm not in ['y', 'yes']:
            print("Skipping ZIP creation")
            return True

        print("[PACK] Creating ZIP file...")

        zip_name = f"{self.package_name}_{datetime.now().strftime('%Y%m%d')}.zip"
        zip_path = os.path.join(self.dist_dir, zip_name)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.package_dir):
                    # Skip __pycache__ and .pyc files
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    files = [f for f in files if not f.endswith('.pyc')]

                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.dist_dir)
                        zipf.write(file_path, arcname)

            zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
            print(f"[OK] Created ZIP: {zip_name} ({zip_size:.1f} MB)")
            return True

        except Exception as e:
            print(f"[FAIL] Error creating ZIP: {e}")
            return False

    def run(self):
        """Main build process"""
        self.print_header()

        # Step 1: Check prerequisites
        if not self.check_pyinstaller():
            input("\nPress Enter to exit...")
            return

        # Step 2: Clean previous builds
        self.clean_previous_builds()

        # Step 3: Build updater.exe
        if not self.build_updater_exe():
            print("\n[FAIL] Build failed!")
            input("\nPress Enter to exit...")
            return

        # Step 4: Create package structure
        if not self.create_package_structure():
            print("\n[FAIL] Package creation failed!")
            input("\nPress Enter to exit...")
            return

        # Step 5: Generate README
        self.generate_readme()

        # Step 6: Create ZIP (optional)
        self.create_zip()

        # Success
        print()
        print("=" * 70)
        print("[SUCCESS] BUILD COMPLETE!")
        print("=" * 70)
        print()
        print(f"[OK] Package created at: {self.package_dir}")
        print()
        print("Next steps:")
        print("   1. Test package by running run_tool.bat")
        print("   2. Setup Git repo (git init, git remote add origin...)")
        print("   3. Copy package to another machine for testing")
        print()

        input("Press Enter to exit...")


if __name__ == "__main__":
    builder = SimplePackageBuilder()
    builder.run()
