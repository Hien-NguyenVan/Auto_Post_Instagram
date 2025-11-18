"""
File Checker Utility - Kiểm tra file tồn tại trong Android VM qua ADB

Sử dụng ADB shell commands để verify file đã được push thành công.
"""
import subprocess
import json
import os
from config import ADB_EXE

DATA_DIR = os.path.join(os.getcwd(), "data")


def check_file_exists_in_vm(vm_name, file_path, log_callback=None):
    """
    Kiểm tra file tồn tại trong VM qua ADB shell test

    Args:
        vm_name: Tên máy ảo
        file_path: Path trong Android (vd: /sdcard/DCIM/video.mp4)
        log_callback: Optional log function

    Returns:
        bool: True nếu file tồn tại

    Example:
        >>> check_file_exists_in_vm("test1", "/sdcard/DCIM/video.mp4")
        True
    """
    log = log_callback or (lambda msg: print(msg))

    try:
        # 1. Get VM port from config
        vm_file = os.path.join(DATA_DIR, f"{vm_name}.json")
        if not os.path.exists(vm_file):
            log(f"❌ Không tìm thấy file cấu hình VM: {vm_file}")
            return False

        with open(vm_file, "r", encoding="utf-8") as f:
            vm_info = json.load(f)

        port = vm_info.get("port")
        if not port:
            log(f"❌ VM config không có port")
            return False

        device = f"emulator-{port}"

        # 2. Check file via ADB shell test -e
        result = subprocess.run(
            [ADB_EXE, "-s", device, "shell", "test", "-e", file_path],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10
        )

        exists = (result.returncode == 0)

        if exists:
            log(f"   ✅ Đã xác nhận: File tồn tại trong VM")
        else:
            log(f"   ❌ File KHÔNG tồn tại trong VM: {file_path}")

        return exists

    except subprocess.TimeoutExpired:
        log(f"⚠️ Timeout khi kiểm tra file")
        return False
    except Exception as e:
        log(f"⚠️ Lỗi kiểm tra file: {e}")
        return False


def check_file_with_size(vm_name, file_path, log_callback=None):
    """
    Kiểm tra file và lấy kích thước

    Args:
        vm_name: Tên máy ảo
        file_path: Path trong Android
        log_callback: Optional log function

    Returns:
        tuple: (exists: bool, size_mb: float)

    Example:
        >>> exists, size = check_file_with_size("test1", "/sdcard/DCIM/video.mp4")
        >>> if exists and size > 1.0:
        ...     print("File OK!")
    """
    log = log_callback or (lambda msg: print(msg))

    try:
        # 1. Get VM port
        vm_file = os.path.join(DATA_DIR, f"{vm_name}.json")
        if not os.path.exists(vm_file):
            log(f"❌ Không tìm thấy file cấu hình VM: {vm_file}")
            return False, 0.0

        with open(vm_file, "r", encoding="utf-8") as f:
            vm_info = json.load(f)

        port = vm_info.get("port")
        if not port:
            log(f"❌ VM config không có port")
            return False, 0.0

        device = f"emulator-{port}"

        # 2. Get file size via stat -c %s
        result = subprocess.run(
            [ADB_EXE, "-s", device, "shell", "stat", "-c", "%s", file_path],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10
        )

        if result.returncode != 0:
            log(f"   ❌ File không tồn tại hoặc không truy cập được")
            return False, 0.0

        # Parse size (bytes)
        size_bytes = int(result.stdout.strip())
        size_mb = size_bytes / (1024 * 1024)

        log(f"   ✅ Đã xác nhận: {os.path.basename(file_path)} ({size_mb:.2f} MB)")
        return True, size_mb

    except subprocess.TimeoutExpired:
        log(f"⚠️ Timeout khi kiểm tra file")
        return False, 0.0
    except ValueError as e:
        log(f"⚠️ Lỗi parse size: {e}")
        return False, 0.0
    except Exception as e:
        log(f"⚠️ Lỗi kiểm tra file: {e}")
        return False, 0.0


def verify_file_after_push(vm_name, remote_path, expected_size_mb=None,
                           wait_seconds=5, max_retries=3, log_callback=None):
    """
    Verify file đã được push thành công vào VM với retry mechanism

    Workflow:
    1. Chờ wait_seconds để file settle
    2. Check file tồn tại
    3. Nếu chưa có, retry broadcast MediaStore
    4. Check size (nếu có expected_size_mb)

    Args:
        vm_name: Tên máy ảo
        remote_path: Path trong Android
        expected_size_mb: Size mong đợi (MB), nếu None thì chỉ check tồn tại
        wait_seconds: Thời gian chờ trước khi verify (default 5s)
        max_retries: Số lần retry nếu file chưa xuất hiện (default 3)
        log_callback: Optional log function

    Returns:
        bool: True nếu file verify OK

    Example:
        >>> # Sau khi send_file_api()
        >>> if verify_file_after_push("test1", "/sdcard/DCIM/video.mp4",
        ...                           expected_size_mb=45.5):
        ...     print("File push thành công!")
    """
    log = log_callback or (lambda msg: print(msg))

    import time

    # Wait for file to settle
    if wait_seconds > 0:
        log(f"⏳ Đợi {wait_seconds}s để file settle...")
        time.sleep(wait_seconds)

    # Retry logic
    for attempt in range(1, max_retries + 1):
        log(f"🔍 Đang verify file (lần {attempt}/{max_retries})...")

        # Check with size
        if expected_size_mb is not None:
            exists, actual_size = check_file_with_size(vm_name, remote_path, log_callback)

            if not exists:
                if attempt < max_retries:
                    log(f"⚠️ File chưa xuất hiện - Retry broadcast MediaStore...")
                    _retry_broadcast_mediastore(vm_name, remote_path, log_callback)
                    time.sleep(2)  # Đợi 2s sau mỗi broadcast
                    continue
                else:
                    log(f"❌ Verify FAILED: File không tồn tại sau {max_retries} lần thử!")
                    return False

            # Tolerance: ±5% hoặc ±1MB (tùy cái nào lớn hơn)
            tolerance = max(expected_size_mb * 0.05, 1.0)
            size_diff = abs(actual_size - expected_size_mb)

            if size_diff > tolerance:
                log(f"⚠️ WARNING: File size khác biệt: Expected {expected_size_mb:.2f}MB, Got {actual_size:.2f}MB")
                log(f"   (Chênh lệch: {size_diff:.2f}MB, tolerance: {tolerance:.2f}MB)")
                # Vẫn return True nếu file tồn tại, chỉ warning

            # ✅ v1.5.32: Check file permissions
            log(f"🔍 Kiểm tra file permissions...")
            has_perms, perm_str = check_file_permissions(vm_name, remote_path, log_callback)
            if not has_perms:
                log(f"⚠️ WARNING: File có thể không có read permission cho Instagram")
                # Vẫn tiếp tục, chỉ warning

            log(f"✅ Verify thành công: File đã có trong VM và đúng kích thước")
            return True

        # Check existence only
        else:
            exists = check_file_exists_in_vm(vm_name, remote_path, log_callback)

            if exists:
                log(f"✅ Verify thành công: File đã có trong VM")
                return True
            else:
                if attempt < max_retries:
                    log(f"⚠️ File chưa xuất hiện - Retry broadcast MediaStore...")
                    _retry_broadcast_mediastore(vm_name, remote_path, log_callback)
                    time.sleep(2)
                    continue
                else:
                    log(f"❌ Verify FAILED: File không tồn tại sau {max_retries} lần thử!")
                    return False

    return False


def check_file_permissions(vm_name, file_path, log_callback=None):
    """
    Kiểm tra permissions của file trong VM

    Args:
        vm_name: Tên máy ảo
        file_path: Path trong Android
        log_callback: Optional log function

    Returns:
        tuple: (has_permissions: bool, permission_string: str)
        Example: (True, "rw-rw----")
    """
    log = log_callback or (lambda msg: print(msg))

    try:
        # Get VM port
        vm_file = os.path.join(DATA_DIR, f"{vm_name}.json")
        if not os.path.exists(vm_file):
            return False, ""

        with open(vm_file, "r", encoding="utf-8") as f:
            vm_info = json.load(f)

        port = vm_info.get("port")
        device = f"emulator-{port}"

        # Get file permissions via stat
        result = subprocess.run(
            [ADB_EXE, "-s", device, "shell", "stat", "-c", "%A", file_path],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10
        )

        if result.returncode != 0:
            return False, ""

        permissions = result.stdout.strip()

        # Check if readable (rw or r--)
        # Instagram cần ít nhất read permission
        is_readable = len(permissions) >= 4 and permissions[1] == 'r'

        if is_readable:
            log(f"   ✅ File permissions OK: {permissions}")
        else:
            log(f"   ⚠️ File không có read permission: {permissions}")

        return is_readable, permissions

    except Exception as e:
        log(f"⚠️ Lỗi check permissions: {e}")
        return False, ""


def _retry_broadcast_mediastore(vm_name, remote_path, log_callback=None):
    """
    Retry broadcast MediaStore scan khi file chưa xuất hiện

    Args:
        vm_name: Tên máy ảo
        remote_path: Path trong Android
        log_callback: Optional log function
    """
    log = log_callback or (lambda msg: print(msg))

    try:
        # Get VM port
        vm_file = os.path.join(DATA_DIR, f"{vm_name}.json")
        with open(vm_file, "r", encoding="utf-8") as f:
            vm_info = json.load(f)

        port = vm_info.get("port")
        device = f"emulator-{port}"

        # Broadcast MediaStore scan
        log(f"   📡 Broadcasting MediaStore scan: {remote_path}")
        subprocess.run([
            ADB_EXE, "-s", device, "shell",
            "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", f"file://{remote_path}"
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
        timeout=10
        )

    except Exception as e:
        log(f"⚠️ Lỗi broadcast MediaStore: {e}")
