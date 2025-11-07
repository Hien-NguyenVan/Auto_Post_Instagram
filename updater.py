"""
Auto-updater script for Instagram Automation Tool.

This script pulls the latest code from GitHub repository.
Usage: Run update.exe to update the tool to the latest version.
"""
import os
import sys
import subprocess
import shutil
from datetime import datetime
import time


class Updater:
    def __init__(self):
        # Get app directory
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))

        self.git_dir = os.path.join(self.app_dir, ".git")
        self.backup_dir = os.path.join(self.app_dir, "backups")
        self.version_file = os.path.join(self.app_dir, "version.txt")

    def print_header(self):
        """Print update tool header"""
        print("=" * 60)
        print("     Instagram Automation Tool - Auto Updater")
        print("=" * 60)
        print()

    def check_git_repo(self):
        """Check if current directory is a git repository"""
        if not os.path.exists(self.git_dir):
            print("❌ Lỗi: Không tìm thấy Git repository!")
            print("   Vui lòng clone project từ GitHub trước.")
            print()
            print("   Hướng dẫn:")
            print("   1. Mở Command Prompt")
            print("   2. cd đến thư mục chứa tool")
            print("   3. Chạy: git init")
            print("   4. Chạy: git remote add origin <URL_GITHUB_REPO>")
            print("   5. Chạy: git pull origin main")
            return False
        return True

    def check_git_installed(self):
        """Check if git command is available"""
        try:
            subprocess.run(
                ["git", "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ Lỗi: Git chưa được cài đặt!")
            print("   Tải Git tại: https://git-scm.com/download/win")
            return False

    def get_current_version(self):
        """Get current version from version.txt"""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                pass
        return "unknown"

    def backup_current_version(self):
        """Create backup of current version"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)

            print(f"📦 Đang backup phiên bản hiện tại...")

            # Create backup directory
            os.makedirs(self.backup_dir, exist_ok=True)

            # Files/folders to backup (exclude data, logs, temp, backups)
            items_to_backup = [
                "core", "tabs", "utils",
                "main.py", "config.py", "constants.py",
                "requirements.txt", "version.txt"
            ]

            os.makedirs(backup_path, exist_ok=True)

            for item in items_to_backup:
                src = os.path.join(self.app_dir, item)
                if os.path.exists(src):
                    dst = os.path.join(backup_path, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)

            print(f"✅ Đã backup vào: {backup_name}")
            return True

        except Exception as e:
            print(f"⚠️ Không thể tạo backup: {e}")
            print("   Tiếp tục update...")
            return False

    def fetch_updates(self):
        """Fetch updates from remote"""
        try:
            print("🔍 Kiểm tra cập nhật...")
            result = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"❌ Lỗi khi fetch: {result.stderr}")
                return False

            return True

        except subprocess.TimeoutExpired:
            print("❌ Timeout khi kết nối tới GitHub")
            return False
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return False

    def check_updates_available(self):
        """Check if updates are available"""
        try:
            # Get local commit hash
            local_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )
            local_hash = local_result.stdout.strip()

            # Get remote commit hash
            remote_result = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )
            remote_hash = remote_result.stdout.strip()

            if local_hash == remote_hash:
                print("✅ Bạn đang sử dụng phiên bản mới nhất!")
                return False
            else:
                print("🆕 Có phiên bản mới!")
                return True

        except Exception as e:
            print(f"⚠️ Không thể kiểm tra version: {e}")
            # Proceed with update anyway
            return True

    def pull_updates(self):
        """Pull latest code from GitHub"""
        try:
            print("📥 Đang tải code mới từ GitHub...")

            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"❌ Lỗi khi pull code: {result.stderr}")
                return False

            print("✅ Đã tải code mới thành công!")
            return True

        except subprocess.TimeoutExpired:
            print("❌ Timeout khi tải code")
            return False
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return False

    def install_dependencies(self):
        """Install/update Python dependencies"""
        req_file = os.path.join(self.app_dir, "requirements.txt")

        if not os.path.exists(req_file):
            print("⚠️ Không tìm thấy requirements.txt - Bỏ qua cài dependencies")
            return True

        try:
            print("📦 Đang cài đặt/cập nhật dependencies...")

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_file, "--upgrade"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print(f"⚠️ Cảnh báo khi cài dependencies:")
                print(result.stderr)
                print("   Bạn có thể cài thủ công: pip install -r requirements.txt")
            else:
                print("✅ Đã cập nhật dependencies")

            return True

        except Exception as e:
            print(f"⚠️ Không thể cài dependencies: {e}")
            print("   Vui lòng chạy thủ công: pip install -r requirements.txt")
            return True

    def run(self):
        """Main update process"""
        self.print_header()

        # Step 1: Check prerequisites
        if not self.check_git_installed():
            self.wait_and_exit(1)
            return

        if not self.check_git_repo():
            self.wait_and_exit(1)
            return

        # Show current version
        current_ver = self.get_current_version()
        print(f"📌 Phiên bản hiện tại: {current_ver}")
        print()

        # Step 2: Fetch updates
        if not self.fetch_updates():
            self.wait_and_exit(1)
            return

        # Step 3: Check if updates available
        if not self.check_updates_available():
            self.wait_and_exit(0)
            return

        # Step 4: Confirm update
        print()
        confirm = input("❓ Bạn có muốn cập nhật không? (Y/n): ").strip().lower()
        if confirm and confirm not in ['y', 'yes']:
            print("❌ Đã hủy cập nhật")
            self.wait_and_exit(0)
            return

        # Step 5: Backup current version
        self.backup_current_version()

        # Step 6: Pull updates
        if not self.pull_updates():
            print()
            print("❌ Cập nhật thất bại!")
            print("   Bạn có thể khôi phục từ thư mục 'backups'")
            self.wait_and_exit(1)
            return

        # Step 7: Install dependencies
        self.install_dependencies()

        # Success
        print()
        print("=" * 60)
        print("🎉 CẬP NHẬT THÀNH CÔNG!")
        print("=" * 60)
        print()
        print("✅ Tool đã được cập nhật lên phiên bản mới nhất")
        print("💡 Chạy lại main.exe để sử dụng phiên bản mới")
        print()

        self.wait_and_exit(0)

    def wait_and_exit(self, code):
        """Wait for user input before exit"""
        print()
        input("Nhấn Enter để đóng...")
        sys.exit(code)


if __name__ == "__main__":
    updater = Updater()
    updater.run()
