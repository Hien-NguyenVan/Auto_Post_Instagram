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

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

# GitHub repository URL
GITHUB_REPO_URL = "https://github.com/Hien-NguyenVan/Auto_Post_Instagram.git"


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
        self.repo_url = GITHUB_REPO_URL

    def print_header(self):
        """Print update tool header"""
        print("=" * 60)
        print("     Instagram Automation Tool - Auto Updater")
        print("=" * 60)
        print()

    def setup_git_repo(self):
        """Automatically setup git repository if not exists"""
        try:
            # Check if .git exists
            if not os.path.exists(self.git_dir):
                print("⚙️  Chưa có Git repository, đang tự động setup...")
                print()

                # Git init
                print("   [1/3] Khởi tạo Git repository...")
                result = subprocess.run(
                    ["git", "init"],
                    cwd=self.app_dir,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(f"   ❌ Lỗi: {result.stderr}")
                    return False
                print("   ✅ Git init thành công")

            # Check if remote exists
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Add remote
                print("   [2/3] Thêm GitHub remote...")
                result = subprocess.run(
                    ["git", "remote", "add", "origin", self.repo_url],
                    cwd=self.app_dir,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(f"   ❌ Lỗi: {result.stderr}")
                    return False
                print(f"   ✅ Đã thêm remote: {self.repo_url}")
            else:
                print("   ✅ Git remote đã có sẵn")

            # Initial pull if no commits
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # No commits yet, do initial pull
                print("   [3/3] Đang tải code từ GitHub lần đầu...")
                result = subprocess.run(
                    ["git", "pull", "origin", "main"],
                    cwd=self.app_dir,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    # Try without --rebase if fails
                    result = subprocess.run(
                        ["git", "pull", "origin", "main", "--allow-unrelated-histories"],
                        cwd=self.app_dir,
                        capture_output=True,
                        text=True
                    )

                if result.returncode == 0:
                    print("   ✅ Tải code thành công")
                else:
                    print(f"   ⚠️  Warning: {result.stderr}")
                    print("   Tiếp tục với code hiện tại...")

            print()
            print("✅ Git repository đã sẵn sàng!")
            print()
            return True

        except Exception as e:
            print(f"❌ Lỗi khi setup Git: {e}")
            return False

    def check_git_repo(self):
        """Check and setup git repository if needed"""
        return self.setup_git_repo()

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

    def get_remote_version(self):
        """Get remote version from GitHub"""
        try:
            # Fetch the version.txt content from remote
            result = subprocess.run(
                ["git", "show", "origin/main:version.txt"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except Exception:
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

    def backup_user_data(self):
        """
        Backup user data folder before update.

        CRITICAL FIX: Backup to PARENT directory (outside git folder)
        to prevent git operations from deleting the backup.
        """
        data_dir = os.path.join(self.app_dir, "data")

        # IMPORTANT: Backup to PARENT folder (outside git)
        parent_dir = os.path.dirname(self.app_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_data_dir = os.path.join(parent_dir, f".InstagramTool_DATA_BACKUP_{timestamp}")

        try:
            # Backup data folder if exists
            if os.path.exists(data_dir):
                print("💾 Đang backup dữ liệu người dùng ra ngoài folder git...")
                shutil.copytree(data_dir, temp_data_dir)
                print(f"✅ Đã backup dữ liệu vào: {os.path.basename(temp_data_dir)}")
                return temp_data_dir

            return None

        except Exception as e:
            print(f"⚠️  Cảnh báo: Không thể backup data: {e}")
            return None

    def restore_user_data(self, temp_data_dir):
        """
        Restore user data folder after update.

        CRITICAL: Always clean up backup folder after restore to save disk space.
        """
        if not temp_data_dir or not os.path.exists(temp_data_dir):
            print("⚠️  Không tìm thấy backup để restore")
            return

        data_dir = os.path.join(self.app_dir, "data")

        try:
            print("♻️  Đang khôi phục dữ liệu người dùng...")

            # Remove current data dir if exists (might be from git)
            if os.path.exists(data_dir):
                try:
                    shutil.rmtree(data_dir)
                except Exception as e:
                    print(f"⚠️  Không thể xóa data cũ: {e}")

            # Restore from backup
            shutil.copytree(temp_data_dir, data_dir)
            print("✅ Đã khôi phục dữ liệu người dùng")

            # Clean up temp backup (IMPORTANT: Save disk space)
            try:
                shutil.rmtree(temp_data_dir)
                print(f"🗑️  Đã xóa backup tạm: {os.path.basename(temp_data_dir)}")
            except Exception as e:
                print(f"⚠️  Không thể xóa backup tạm (bạn có thể xóa thủ công): {temp_data_dir}")

        except Exception as e:
            print(f"❌ LỖI NGHIÊM TRỌNG: Không thể restore data!")
            print(f"   Lỗi: {e}")
            print(f"   Dữ liệu backup vẫn còn tại: {temp_data_dir}")
            print(f"   Hãy copy thủ công folder trên vào: {data_dir}")

    def cleanup_old_backups(self):
        """
        Clean up old backup folders (older than 7 days) to save disk space.

        Backups are stored in parent directory with pattern:
        .InstagramTool_DATA_BACKUP_YYYYMMDD_HHMMSS
        """
        try:
            parent_dir = os.path.dirname(self.app_dir)
            if not os.path.exists(parent_dir):
                return

            # Find all backup folders
            backup_pattern = ".InstagramTool_DATA_BACKUP_"
            now = time.time()
            seven_days_ago = now - (7 * 24 * 60 * 60)  # 7 days in seconds

            for item in os.listdir(parent_dir):
                if item.startswith(backup_pattern):
                    backup_path = os.path.join(parent_dir, item)
                    if os.path.isdir(backup_path):
                        # Check if older than 7 days
                        mtime = os.path.getmtime(backup_path)
                        if mtime < seven_days_ago:
                            try:
                                shutil.rmtree(backup_path)
                                print(f"🗑️  Đã xóa backup cũ: {item}")
                            except Exception as e:
                                # Ignore errors when deleting old backups
                                pass

        except Exception:
            # Ignore all errors in cleanup (non-critical)
            pass

    def pull_updates(self):
        """Pull latest code from GitHub"""
        temp_data_backup = None

        try:
            print("📥 Đang tải code mới từ GitHub...")

            # IMPORTANT: Backup user data BEFORE any git operations
            temp_data_backup = self.backup_user_data()

            # Step 1: Add all files to Git (including untracked)
            # This prevents "untracked working tree files would be overwritten" error
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            # Step 2: Stash any local changes (if any)
            subprocess.run(
                ["git", "stash", "--include-untracked"],
                cwd=self.app_dir,
                capture_output=True,
                text=True
            )

            # Step 3: Reset to remote branch (force update)
            result = subprocess.run(
                ["git", "reset", "--hard", "origin/main"],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"❌ Lỗi khi reset: {result.stderr}")
                # Try pull anyway
                result = subprocess.run(
                    ["git", "pull", "origin", "main", "--allow-unrelated-histories"],
                    cwd=self.app_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode != 0:
                    print(f"❌ Lỗi khi pull code: {result.stderr}")
                    # Restore data even if pull failed
                    self.restore_user_data(temp_data_backup)
                    return False

            print("✅ Đã tải code mới thành công!")

            # IMPORTANT: Restore user data AFTER successful pull
            self.restore_user_data(temp_data_backup)

            return True

        except subprocess.TimeoutExpired:
            print("❌ Timeout khi tải code")
            # Restore data even if timeout
            self.restore_user_data(temp_data_backup)
            return False
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            # Restore data even if error
            self.restore_user_data(temp_data_backup)
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

        # Step 3: Get remote version
        remote_ver = self.get_remote_version()

        # Step 4: Check if updates available
        has_updates = self.check_updates_available()

        if has_updates:
            print(f"🎯 Phiên bản mới nhất: {remote_ver}")
            print()

        if not has_updates:
            self.wait_and_exit(0)
            return

        # Step 5: Confirm update
        print()
        print(f"📦 Cập nhật từ {current_ver} → {remote_ver}")
        print()
        confirm = input("❓ Bạn có muốn cập nhật không? (Y/n): ").strip().lower()
        if confirm and confirm not in ['y', 'yes']:
            print("❌ Đã hủy cập nhật")
            self.wait_and_exit(0)
            return

        # Step 6: Backup current version
        self.backup_current_version()

        # Step 7: Pull updates
        if not self.pull_updates():
            print()
            print("❌ Cập nhật thất bại!")
            print("   Bạn có thể khôi phục từ thư mục 'backups'")
            self.wait_and_exit(1)
            return

        # Step 8: Install dependencies
        self.install_dependencies()

        # Step 9: Clean up old backups (non-critical)
        self.cleanup_old_backups()

        # Get new version after update
        new_version = self.get_current_version()

        # Success
        print()
        print("=" * 60)
        print("🎉 CẬP NHẬT THÀNH CÔNG!")
        print("=" * 60)
        print()
        print(f"✅ Đã cập nhật từ {current_ver} → {new_version}")
        print("💡 Chạy lại run_tool.bat hoặc main.py để sử dụng phiên bản mới")
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
