"""
Build script for creating portable Instagram Automation Tool package.

This script:
1. Builds main.exe and updater.exe using PyInstaller
2. Creates portable package structure
3. Generates README.txt
4. (Optional) Creates ZIP file for distribution

Usage: python build_package.py
"""
import os
import sys
import subprocess
import shutil
import zipfile
from datetime import datetime

# Fix console encoding for Vietnamese text
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class PackageBuilder:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.dist_dir = os.path.join(self.root_dir, "dist")
        self.build_dir = os.path.join(self.root_dir, "build")
        self.package_name = "InstagramTool_Portable"
        self.package_dir = os.path.join(self.dist_dir, self.package_name)

    def print_header(self):
        """Print build script header"""
        print("=" * 70)
        print("     Instagram Automation Tool - Package Builder")
        print("=" * 70)
        print()

    def check_pyinstaller(self):
        """Check if PyInstaller is installed"""
        try:
            import PyInstaller
            print("[OK] PyInstaller da cai dat")
            return True
        except ImportError:
            print("[FAIL] PyInstaller chua duoc cai dat!")
            print("   Cai dat: pip install pyinstaller")
            return False

    def clean_previous_builds(self):
        """Clean previous build and dist directories"""
        print("[CLEAN] Don dep build cu...")

        dirs_to_clean = [self.build_dir, self.dist_dir]

        for directory in dirs_to_clean:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                print(f"   Da xoa: {directory}")

        print("[OK] Da don dep xong")

    def build_main_exe(self):
        """Build main.exe using PyInstaller"""
        print()
        print("[BUILD] Building main.exe (GUI)...")

        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", "main",
            "--add-data", "core;core",
            "--add-data", "tabs;tabs",
            "--add-data", "utils;utils",
            "--add-data", "constants.py;.",
            "--hidden-import=PIL._tkinter_finder",
            "--hidden-import=ttkbootstrap",
            "--hidden-import=uiautomator2",
            "--hidden-import=google.oauth2",
            "main.py"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print("[FAIL] Loi khi build main.exe:")
                print(result.stderr)
                return False

            print("[OK] Build main.exe thanh cong")
            return True

        except subprocess.TimeoutExpired:
            print("[FAIL] Timeout khi build main.exe")
            return False
        except Exception as e:
            print(f"[FAIL] Loi: {e}")
            return False

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
                print("[FAIL] Loi khi build updater.exe:")
                print(result.stderr)
                return False

            print("[OK] Build updater.exe thanh cong")
            return True

        except subprocess.TimeoutExpired:
            print("[FAIL] Timeout khi build updater.exe")
            return False
        except Exception as e:
            print(f"[FAIL] Loi: {e}")
            return False

    def create_package_structure(self):
        """Create portable package directory structure"""
        print()
        print("[PACK] Tao cau truc package...")

        # Create package directory
        os.makedirs(self.package_dir, exist_ok=True)

        # Copy EXE files
        main_exe = os.path.join(self.dist_dir, "main.exe")
        updater_exe = os.path.join(self.dist_dir, "updater.exe")

        if os.path.exists(main_exe):
            shutil.copy2(main_exe, self.package_dir)
            print("   ✓ Copied main.exe")
        else:
            print("   ✗ main.exe not found!")
            return False

        if os.path.exists(updater_exe):
            shutil.copy2(updater_exe, self.package_dir)
            print("   ✓ Copied updater.exe")
        else:
            print("   ✗ updater.exe not found!")
            return False

        # Copy source code files (for git update to work)
        files_to_copy = [
            "config.py",
            "constants.py",
            "requirements.txt",
            "version.txt"
        ]

        for file in files_to_copy:
            src = os.path.join(self.root_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, self.package_dir)
                print(f"   ✓ Copied {file}")

        # Copy directories
        dirs_to_copy = ["core", "tabs", "utils"]

        for directory in dirs_to_copy:
            src_dir = os.path.join(self.root_dir, directory)
            dst_dir = os.path.join(self.package_dir, directory)

            if os.path.exists(src_dir):
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                print(f"   ✓ Copied {directory}/")

        # Create empty directories
        empty_dirs = ["data", "data/api", "data/output", "logs", "temp", "downloads", "backups"]

        for directory in empty_dirs:
            dir_path = os.path.join(self.package_dir, directory)
            os.makedirs(dir_path, exist_ok=True)

        # Create placeholder file in data/api
        api_placeholder = os.path.join(self.package_dir, "data", "api", "youtube.txt")
        with open(api_placeholder, "w", encoding="utf-8") as f:
            f.write("# Paste your YouTube API keys here, one per line\n")
            f.write("# Example:\n")
            f.write("# AIzaSy...\n")

        print("[OK] Da tao cau truc package")
        return True

    def generate_readme(self):
        """Generate README.txt with instructions"""
        print()
        print("[DOC] Tao README.txt...")

        readme_path = os.path.join(self.package_dir, "README.txt")

        readme_content = f"""
================================================================================
          INSTAGRAM AUTOMATION TOOL - PORTABLE VERSION
================================================================================

📅 Build date: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

================================================================================
🔧 YÊU CẦU HỆ THỐNG
================================================================================

[OK] Windows 10/11 (64-bit)
[OK] Python 3.10 hoac moi hon (da cai san)
[OK] LDPlayer 9 (phai cai dat truoc)
[OK] Ket noi Internet (cho update va download video)

================================================================================
[PACK] CÀI DẶT LẦN DẦU
================================================================================

1. Cai dat LDPlayer 9 (neu chua co):
   → Tai tai: https://www.ldplayer.net/

2. Cai dat Python dependencies:
   → Mo Command Prompt trong thu muc nay
   → Chay: pip install -r requirements.txt

3. Cau hinh YouTube API (tuy chon):
   → Mo file: data/api/youtube.txt
   → Paste API key cua ban (moi dong 1 key)

4. Cau hinh duong dan LDPlayer (neu can):
   → Tool se tu dong tim LDPlayer
   → Neu khong tim thay, tao file "ldplayer_path.txt"
   → Ghi duong dan LDPlayer vao (VD: C:\\LDPlayer\\LDPlayer9)

================================================================================
🚀 SỬ DỤNG
================================================================================

▶️ CHẠY TOOL:
   → Double-click vao main.exe

▶️ CẬP NHẬT TOOL:
   → Double-click vao updater.exe
   → Tool se tu dong tai code moi tu GitHub

================================================================================
📁 CẤU TRÚC THƯ MỤC
================================================================================

InstagramTool_Portable/
├── main.exe              ← Chay tool chinh
├── updater.exe           ← Cap nhat tool
├── core/                 ← Source code (core modules)
├── tabs/                 ← Source code (UI tabs)
├── utils/                ← Source code (utilities)
├── data/                 ← Du lieu nguoi dung
│   ├── api/              ← API keys
│   ├── output/           ← Video metadata
│   └── *.json            ← Cau hinh may ao
├── logs/                 ← Log files
├── temp/                 ← File tam
├── downloads/            ← Video downloads
├── backups/              ← Backup code cu (khi update)
└── README.txt            ← File nay

================================================================================
❗ LƯU Ý
================================================================================

[WARN] Khong xoa thu muc .git (can cho update)
[WARN] Khong sua file trong core/, tabs/, utils/ (se bi ghi de khi update)
[WARN] Du lieu user (data/, logs/) se khong bi mat khi update

================================================================================
🐛 XỬ LÝ LỖI
================================================================================

[FAIL] "LDPlayer not found":
   → Tao file "ldplayer_path.txt" va ghi duong dan LDPlayer

[FAIL] "Git not found" khi update:
   → Cai Git: https://git-scm.com/download/win

[FAIL] Loi Python module:
   → Chay: pip install -r requirements.txt --upgrade

================================================================================
📞 HỖ TRỢ
================================================================================

GitHub: [Paste GitHub repo URL here]
Issues: [Paste GitHub issues URL here]

================================================================================
                          © 2024 - All Rights Reserved
================================================================================
"""

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        print("[OK] Da tao README.txt")
        return True

    def create_zip(self):
        """Create ZIP file for distribution"""
        print()
        confirm = input("[?] Ban co muon tao file ZIP khong? (Y/n): ").strip().lower()

        if confirm and confirm not in ['y', 'yes']:
            print("⏭️ Bo qua tao ZIP")
            return True

        print("[PACK] Dang tao file ZIP...")

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
            print(f"[OK] Da tao ZIP: {zip_name} ({zip_size:.1f} MB)")
            return True

        except Exception as e:
            print(f"[FAIL] Loi khi tao ZIP: {e}")
            return False

    def run(self):
        """Main build process"""
        self.print_header()

        # Step 1: Check prerequisites
        if not self.check_pyinstaller():
            input("\nNhan Enter de thoat...")
            return

        # Step 2: Clean previous builds
        self.clean_previous_builds()

        # Step 3: Build main.exe
        if not self.build_main_exe():
            print("\n[FAIL] Build that bai!")
            input("\nNhan Enter de thoat...")
            return

        # Step 4: Build updater.exe
        if not self.build_updater_exe():
            print("\n[FAIL] Build that bai!")
            input("\nNhan Enter de thoat...")
            return

        # Step 5: Create package structure
        if not self.create_package_structure():
            print("\n[FAIL] Tao package that bai!")
            input("\nNhan Enter de thoat...")
            return

        # Step 6: Generate README
        self.generate_readme()

        # Step 7: Create ZIP (optional)
        self.create_zip()

        # Success
        print()
        print("=" * 70)
        print("[SUCCESS] BUILD THÀNH CÔNG!")
        print("=" * 70)
        print()
        print(f"[OK] Package da duoc tao tai: {self.package_dir}")
        print()
        print("📋 Tiep theo:")
        print("   1. Test package bang cach chay main.exe trong thu muc dist")
        print("   2. Setup Git repo (git init, git remote add origin...)")
        print("   3. Copy package sang may khac de test")
        print()

        input("Nhan Enter de thoat...")


if __name__ == "__main__":
    builder = PackageBuilder()
    builder.run()
