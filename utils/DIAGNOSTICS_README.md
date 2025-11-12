# 🔍 Diagnostics Utilities - Hướng dẫn sử dụng

File `diagnostics.py` cung cấp các hàm để ghi log và check trạng thái nhằm mục đích debug.

**QUAN TRỌNG:** File này KHÔNG thay đổi logic code hiện tại, chỉ cung cấp thông tin diagnostic.

---

## 📦 Cài đặt

Đảm bảo đã cài `psutil`:

```bash
pip install psutil>=5.9.0
```

Hoặc:

```bash
pip install -r requirements.txt
```

---

## 🎯 Sử dụng

### 1. Import module

```python
from utils.diagnostics import (
    log_system_info,
    log_adb_info,
    log_vm_info,
    log_file_info,
    run_full_diagnostics,
    Timer
)
```

---

### 2. Check System Resources

**Kiểm tra RAM, CPU, Disk:**

```python
from utils.diagnostics import log_system_info, check_system_resources

# Log thông tin system
log_system_info(log_callback=lambda msg: print(msg))

# Output:
# 💻 System Info:
#    RAM: 8.5GB / 16.0GB available (46.9% used)
#    Disk: 125.3GB / 500.0GB free (74.9% used)
#    CPU: 8 cores, 35.2% usage

# Check xem resources có đủ không
is_ok, message = check_system_resources()
if not is_ok:
    print(f"⚠️ Warning: {message}")
```

---

### 3. Check ADB Status

**Kiểm tra ADB server, devices, processes:**

```python
from utils.diagnostics import log_adb_info, diagnose_adb
from config import ADB_EXE

# Log ADB info
log_adb_info(ADB_EXE, log_callback=lambda msg: print(msg))

# Output:
# 🔧 ADB Info:
#    Server running: ✅
#    Connected devices: 2 - ['emulator-5555', 'emulator-5556']
#    ADB processes: 3
#    ADB.exe exists: ✅

# Hoặc lấy dict để xử lý
info = diagnose_adb(ADB_EXE)
if not info['server_running']:
    print("❌ ADB server không chạy!")
```

---

### 4. Check VM Status

**Kiểm tra VM có đang chạy, ADB có kết nối:**

```python
from utils.diagnostics import log_vm_info, diagnose_vm
from config import LDCONSOLE_EXE, DATA_DIR, ADB_EXE

vm_name = "VM_Test"

# Log VM info
log_vm_info(vm_name, LDCONSOLE_EXE, DATA_DIR, ADB_EXE,
            log_callback=lambda msg: print(msg))

# Output:
# 📱 VM Info (VM_Test):
#    Running: ✅
#    Port: 5555
#    ADB address: emulator-5555
#    ADB connected: ✅

# Hoặc lấy dict
info = diagnose_vm(vm_name, LDCONSOLE_EXE, DATA_DIR, ADB_EXE)
if not info['adb_connected']:
    print("❌ ADB chưa kết nối với VM!")
```

---

### 5. Check File

**Kiểm tra file có tồn tại và size:**

```python
from utils.diagnostics import log_file_info, check_file_exists_and_size

file_path = "downloads/video.mp4"

# Log file info
log_file_info(file_path, log_callback=lambda msg: print(msg))

# Output:
# 📄 File Info: video.mp4
#    Exists: ✅
#    Size: 15.23 MB
#    Path: downloads/video.mp4

# Hoặc check trực tiếp
exists, size = check_file_exists_and_size(file_path)
if not exists:
    print("❌ File không tồn tại!")
elif size == 0:
    print("⚠️ File có size = 0!")
```

---

### 6. Đo thời gian operation

**Sử dụng Timer:**

```python
from utils.diagnostics import Timer

timer = Timer()

# ... do some operation ...
push_file_to_vm()

elapsed = timer.elapsed()
print(f"⏱️ Operation took {elapsed:.2f}s")

# Nếu quá lâu
if elapsed > 30:
    print("⚠️ Operation quá chậm! Có thể là vấn đề về môi trường.")
```

---

### 7. Run Full Diagnostics

**Chạy tất cả diagnostic checks cùng lúc:**

```python
from utils.diagnostics import run_full_diagnostics
from config import LDCONSOLE_EXE, ADB_EXE, DATA_DIR

vm_name = "VM_Test"

# Chạy full diagnostic report
run_full_diagnostics(
    vm_name=vm_name,
    ldconsole_exe=LDCONSOLE_EXE,
    adb_exe=ADB_EXE,
    data_dir=DATA_DIR,
    log_callback=lambda msg: print(msg)
)

# Output:
# ============================================================
# 🔍 DIAGNOSTIC REPORT
# ============================================================
# 💻 System Info:
#    RAM: 8.5GB / 16.0GB available (46.9% used)
#    ...
# 🔧 ADB Info:
#    Server running: ✅
#    ...
# 📱 VM Info (VM_Test):
#    Running: ✅
#    ...
# ============================================================
```

---

## 💡 Ví dụ sử dụng trong code hiện tại

### Ví dụ 1: Log diagnostic khi gửi file thất bại

```python
# Trong tabs/tab_post.py hoặc tabs/tab_follow.py
from utils.diagnostics import log_adb_info, log_vm_info, log_file_info

# Khi gửi file thất bại
if not success_push:
    post.log(f"❌ Gửi file thất bại")

    # Log diagnostics để debug
    post.log("🔍 Running diagnostics...")
    log_file_info(post.video_path, log_callback=lambda msg: post.log(msg))
    log_adb_info(ADB_EXE, log_callback=lambda msg: post.log(msg))
    log_vm_info(post.vm_name, LDCONSOLE_EXE, DATA_DIR, ADB_EXE,
                log_callback=lambda msg: post.log(msg))
```

### Ví dụ 2: Log timing cho từng bước

```python
from utils.diagnostics import Timer

# Đo thời gian boot VM
post.log("🚀 Bật máy ảo...")
timer = Timer()

subprocess.run([LDCONSOLE_EXE, "launch", "--name", post.vm_name], ...)

elapsed = timer.elapsed()
post.log(f"⏱️ VM boot took {elapsed:.2f}s")

if elapsed > 60:
    post.log("⚠️ VM boot quá chậm! Check system resources.")
```

### Ví dụ 3: Check resources trước khi chạy

```python
from utils.diagnostics import check_system_resources, log_system_info

# Trước khi bắt đầu post
is_ok, message = check_system_resources()
if not is_ok:
    post.log(f"⚠️ System resources warning:")
    post.log(message)
    log_system_info(log_callback=lambda msg: post.log(msg))
```

---

## 🎯 Khi nào nên dùng

### ✅ Nên dùng khi:
- Gửi file thất bại
- VM không khởi động được
- ADB connection bị timeout
- Operation chạy quá chậm
- Code fail nhưng không rõ nguyên nhân

### ❌ KHÔNG nên dùng:
- Trong mọi operation thành công (tốn performance)
- Spam logs không cần thiết

---

## 📝 Best Practices

1. **Chỉ log khi cần debug:**
   ```python
   if not success:
       # Log diagnostics
       run_full_diagnostics(...)
   ```

2. **Đo timing cho slow operations:**
   ```python
   timer = Timer()
   # ... slow operation ...
   if timer.elapsed() > EXPECTED_TIME:
       log_diagnostics()
   ```

3. **Check resources trước khi chạy batch:**
   ```python
   is_ok, msg = check_system_resources()
   if not is_ok:
       warn_user(msg)
   ```

---

## 🐛 Debug Workflow

Khi gặp lỗi:

1. **Run full diagnostics:**
   ```python
   run_full_diagnostics(vm_name, LDCONSOLE_EXE, ADB_EXE, DATA_DIR, log_callback)
   ```

2. **Check từng phần:**
   - System resources OK?
   - ADB server running?
   - VM running và connected?
   - File tồn tại và có size > 0?

3. **Đo timing:**
   - Operation nào chạy quá lâu?
   - Có timeout không?

4. **Phân tích:**
   - Nếu RAM/CPU cao → Môi trường yếu
   - Nếu ADB không running → Cần restart ADB
   - Nếu VM không connect → Check port, reboot VM
   - Nếu file không tồn tại → Check download step

---

## 📞 Support

Nếu gặp vấn đề với diagnostics, check:
- `psutil` đã cài chưa: `pip install psutil`
- Python version >= 3.10
- Log file: `logs/app.log`
