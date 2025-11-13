import subprocess
import sys
from config import ADB_EXE

def clear_dcim(device, adb_path=None, log_callback=None):
    """
    Xóa toàn bộ mọi thứ trong /sdcard/DCIM/ của thiết bị Android.
    Giữ lại thư mục gốc DCIM.

    Args:
        device: Device name (e.g., "emulator-5554")
        adb_path: Path to adb.exe (defaults to ADB_EXE from config)
        log_callback: Callback function for logging
    """
    log = log_callback or (lambda msg: print(msg))
    # Dùng ADB_EXE từ config nếu không truyền vào
    if adb_path is None:
        adb_path = ADB_EXE

    try:
        # Chạy lệnh xóa
        result = subprocess.run(
            [adb_path, "-s", device, "shell", "rm", "-rf", "/sdcard/DCIM/*"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # Kiểm tra kết quả
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        # log(f"❌ Lỗi khi xóa DCIM: {e}")
        return False


def clear_pictures(device, adb_path=None, log_callback=None):
    """
    Xóa toàn bộ mọi thứ trong /sdcard/Pictures/ của thiết bị Android.
    Giữ lại thư mục gốc Pictures.

    Args:
        device: Device name (e.g., "emulator-5554")
        adb_path: Path to adb.exe (defaults to ADB_EXE from config)
        log_callback: Callback function for logging
    """
    log = log_callback or (lambda msg: print(msg))
    # Dùng ADB_EXE từ config nếu không truyền vào
    if adb_path is None:
        adb_path = ADB_EXE

    try:
        # Chạy lệnh xóa
        result = subprocess.run(
            [adb_path, "-s", device, "shell", "rm", "-rf", "/sdcard/Pictures/*"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # Kiểm tra kết quả
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        # log(f"❌ Lỗi khi xóa Pictures: {e}")
        return False

