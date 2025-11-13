"""
Screenshot utility for capturing Android emulator screen via ADB.

Used for debugging automation failures and detecting UI changes.
"""
import os
import time
import subprocess
import logging

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = "D:/temp"


def take_screenshot(device: str, adb_path: str, vm_name: str = None) -> str:
    """
    Chụp màn hình emulator và lưu về PC.

    Args:
        device: Device name (e.g., "emulator-5554")
        adb_path: Đường dẫn adb.exe
        vm_name: Tên máy ảo (để đặt tên file)

    Returns:
        str: Đường dẫn file ảnh đã lưu, hoặc None nếu thất bại
    """
    try:
        # Tạo tên file với timestamp
        port = device.split('-')[-1]
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        if vm_name:
            filename = f"{vm_name}-{port}-{timestamp}.png"
        else:
            filename = f"{port}-{timestamp}.png"

        save_path = os.path.join(SCREENSHOT_DIR, filename)
        remote_path = "/storage/emulated/0/screen.png"

        # Tạo thư mục nếu chưa có
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        # 1. Chụp màn hình trên emulator
        logger.info(f"Taking screenshot on {device}...")
        result = subprocess.run(
            [adb_path, "-s", device, "shell", "screencap", "-p", remote_path],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10
        )

        if result.returncode != 0:
            logger.error(f"Failed to capture screen: {result.stderr}")
            return None

        # Đợi file được ghi xong
        time.sleep(0.5)

        # 2. Pull file về PC
        logger.info(f"Pulling screenshot to {save_path}...")
        result = subprocess.run(
            [adb_path, "-s", device, "pull", remote_path, save_path],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10
        )

        if result.returncode != 0:
            logger.error(f"Failed to pull screenshot: {result.stderr}")
            return None

        # 3. Xóa file tạm trên emulator
        subprocess.run(
            [adb_path, "-s", device, "shell", "rm", "-f", remote_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5
        )

        logger.info(f"Screenshot saved: {save_path}")
        return save_path

    except subprocess.TimeoutExpired:
        logger.error("Screenshot timeout")
        return None
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return None
