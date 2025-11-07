import subprocess
import sys

def clear_dcim(device,log_callback=None):
    """
    Xóa toàn bộ mọi thứ trong /sdcard/DCIM/ của thiết bị Android.
    Giữ lại thư mục gốc DCIM.
    """
    log = log_callback or (lambda msg: print(msg))
    try:
        # Chạy lệnh xóa
        adb_path = r"C:\LDPlayer\LDPlayer9\adb.exe"
        result = subprocess.run(
            [adb_path, "-s", device, "shell", "rm", "-rf", "/sdcard/DCIM/*"],
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True
        )

        # Kiểm tra kết quả
        if result.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        # log(f"❌ Lỗi khi gửi file sang máy ảo: {e}")
        return False

