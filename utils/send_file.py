import os
import subprocess
import json

DATA_DIR = os.path.join(os.getcwd(), "data")


def send_file_api(local_path, vm_name, adb_path=r"C:\LDPlayer\LDPlayer9\adb.exe", log_callback=None):
    """
    Gửi file từ PC sang LDPlayer dựa vào file /data/<vm_name>.json
    - vm_name: tên máy ảo (vd: mayaotest1)
    - local_path: đường dẫn file trên PC
    - log_callback: hàm callback để ghi log (vd: self.log hoặc lambda msg: ui_queue.put(...))
    """
    # ✅ fallback cho log
    log = log_callback or (lambda msg: print(msg))
   
    try:
        # 🔹 1️⃣ Kiểm tra file tồn tại
        if not os.path.exists(local_path):
            log(f"❌ File không tồn tại: {local_path}")
            return False

        # 🔹 2️⃣ Đọc thông tin máy ảo từ /data/<vm_name>.json
        vm_file = os.path.join(DATA_DIR, f"{vm_name}.json")
        if not os.path.exists(vm_file):
            log(f"❌ Không tìm thấy file cấu hình: {vm_file}")
            return False

        with open(vm_file, "r", encoding="utf-8") as f:
            vm_info = json.load(f)

        port = vm_info.get("port")
        if not port or not str(port).isdigit():
            log(f"❌ File cấu hình máy ảo không có port hợp lệ.")
            return False

        device = f"emulator-{port}"
        log(f"🔹 Device: {device}")

        # 🔹 3️⃣ Kiểm tra kết nối ADB
        log(f"   🔍 Kiểm tra ADB connection...")
        result = subprocess.run(
            [adb_path, "devices"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if device not in result.stdout:
            log(f"❌ Device '{device}' không có trong 'adb devices'")
            log(f"   📋 Output: {result.stdout.strip()}")
            return False
        log(f"   ✅ Device '{device}' đã kết nối ADB")

        # 🔹 4️⃣ Thực hiện adb push
        filename = os.path.basename(local_path)
        remote_path = f"/sdcard/DCIM/{filename}"
        log(f"🚀 Đang gửi file {filename} sang {device} ...")

        push = subprocess.run(
            [adb_path, "-s", device, "push", local_path, remote_path],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if push.returncode == 0:
            log(f"✅ Gửi file thành công → {remote_path}")

            # 🔹 5️⃣ Quét lại MediaStore để Gallery/Instagram nhận ra file ngay
            log(f"🔁 Đang refresh MediaStore...")
            try:
                subprocess.run([
                    adb_path, "-s", device, "shell",
                    "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                    "-d", f"file://{remote_path}"
                ],
                text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
                )
                log(f"✅ Đã refresh MediaStore — Instagram sẽ thấy video ngay")
            except Exception as e:
                log(f"⚠️ Lỗi khi refresh MediaStore: {e}")

            return True
        else:
            log(f"❌ Gửi file thất bại (returncode: {push.returncode})")
            if push.stderr:
                log(f"   📋 Error: {push.stderr.strip()}")
            if push.stdout:
                log(f"   📋 Output: {push.stdout.strip()}")
            return False

    except Exception as e:
        log(f"❌ Lỗi khi gửi file sang máy ảo: {e}")
        return False
