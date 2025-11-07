# Hướng dẫn Update Code Thủ Công

## ✅ Đã hoàn thành tự động

Các file sau đã được tối ưu xong:
- ✅ `config.py` - File cấu hình paths (MỚI)
- ✅ `constants.py` - Constants và magic numbers (MỚI)
- ✅ `utils/base_instagram.py` - Base class chung (MỚI)
- ✅ `utils/login.py` - Đã refactor kế thừa base class
- ✅ `utils/post.py` - Đã refactor kế thừa base class
- ✅ `main.py` - Đã thêm logging setup
- ✅ `requirements.txt` - Dependencies (MỚI)
- ✅ `logs/` - Thư mục logs (MỚI)
- ✅ `.gitignore` - Git ignore file (MỚI)

---

## ⚠️ CẦN UPDATE THỦ CÔNG

### **File: `tabs/tab_users.py`**

Thực hiện các thay đổi sau:

#### 1. **Thay đổi imports (dòng 1-14)**

**TỪ:**
```python
import os
import json
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from utils.login import InstagramLogin

LDCONSOLE_PATH = r"C:\LDPlayer\LDPlayer9\ldconsole.exe"
config_dir = r"C:\LDPlayer\LDPlayer9\vms\config"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
```

**THÀNH:**
```python
import os
import json
import subprocess
import threading
import time
import logging
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from utils.login import InstagramLogin
from config import LDCONSOLE_EXE, CONFIG_DIR, ADB_EXE, DATA_DIR
from constants import (
    WAIT_SHORT, WAIT_MEDIUM, TIMEOUT_EXTENDED,
    MAX_RETRY_VM_STATUS, VM_STATUS_CHECK_INTERVAL,
    DEFAULT_VM_RESOLUTION, DEFAULT_VM_CPU, DEFAULT_VM_MEMORY,
    ADB_DEBUG_SETTING
)

os.makedirs(DATA_DIR, exist_ok=True)
```

#### 2. **Thêm logger và lock trong __init__ (dòng ~20)**

**THÊM sau dòng `super().__init__(parent)`:**
```python
self.logger = logging.getLogger(__name__)
self.vm_logs_lock = threading.Lock()  # Thread safety
```

#### 3. **Find & Replace toàn bộ file:**

| Tìm | Thay thế |
|-----|----------|
| `LDCONSOLE_PATH` | `LDCONSOLE_EXE` |
| `config_dir` | `CONFIG_DIR` |
| `r"C:\LDPlayer\LDPlayer9\adb.exe"` | `ADB_EXE` |
| `"720,1280,320"` | `DEFAULT_VM_RESOLUTION` |
| `"--cpu", "2"` | `"--cpu", DEFAULT_VM_CPU` |
| `"--memory", "2048"` | `"--memory", DEFAULT_VM_MEMORY` |
| `for _ in range(30):  # 30 * 2s` | `for _ in range(MAX_RETRY_VM_STATUS):` |
| `time.sleep(2)` (trong wait_status) | `time.sleep(VM_STATUS_CHECK_INTERVAL)` |

#### 4. **Cập nhật write_log method (dòng ~296)**

**TỪ:**
```python
def write_log(self, vm_name, message):
    timestamp = time.strftime('%H:%M:%S')
    log_entry = f"{timestamp} | {message}"

    # Lưu bộ nhớ
    self.vm_logs.setdefault(vm_name, []).append(log_entry)
```

**THÀNH:**
```python
def write_log(self, vm_name, message):
    timestamp = time.strftime('%H:%M:%S')
    log_entry = f"{timestamp} | {message}"

    # Lưu bộ nhớ (thread-safe)
    with self.vm_logs_lock:
        self.vm_logs.setdefault(vm_name, []).append(log_entry)

    # Log to file as well
    self.logger.info(f"[{vm_name}] {message}")
```

#### 5. **Cải thiện error handling**

Thay tất cả:
```python
except Exception:
    pass
```

Thành:
```python
except Exception as e:
    self.logger.error(f"Error description: {e}")
    # hoặc
    self.logger.exception("Error description")
```

---

### **File: `tabs/tab_follow.py`**

#### 1. **Thay đổi imports (dòng ~1-15)**

**THÊM vào đầu file:**
```python
import logging
from config import LDCONSOLE_EXE
from constants import (
    WAIT_SHORT, WAIT_MEDIUM, WAIT_LONG,
    TIMEOUT_DEFAULT, TIMEOUT_APP_OPEN
)
```

#### 2. **Find & Replace:**

| Tìm | Thay thế |
|-----|----------|
| `LDCONSOLE_PATH = r"C:\LDPlayer\LDPlayer9\ldconsole.exe"` | `# Imported from config` |
| `time.sleep(15)` | `time.sleep(WAIT_LONG)` |
| `time.sleep(5)` | `time.sleep(WAIT_MEDIUM)` |
| `time.sleep(2)` | `time.sleep(WAIT_SHORT)` |

#### 3. **Thêm logger trong Stream class (dòng ~269)**

**THÊM trong __init__:**
```python
self.logger = logging.getLogger(f"{__name__}.Stream")
```

#### 4. **Cải thiện error handling**

Tương tự tab_users.py, thay:
```python
except Exception as e:
    self.log(f"⚠️ Lỗi xử lý video: {e}")
```

Thành:
```python
except Exception as e:
    self.log(f"⚠️ Lỗi xử lý video: {e}")
    self.logger.exception("Error processing video")
```

---

## 🧪 Testing Sau Khi Update

1. **Kiểm tra imports:**
   ```bash
   python main.py
   ```
   → Nếu có lỗi import, kiểm tra lại các file

2. **Kiểm tra logging:**
   - Chạy app
   - Kiểm tra file `logs/app.log` được tạo
   - Kiểm tra log có đầy đủ thông tin

3. **Kiểm tra chức năng:**
   - Thử thêm máy ảo
   - Thử đăng nhập Instagram
   - Kiểm tra không có crash/error

---

## 📝 Nếu Muốn Tôi Tự Động Update

Đóng file `tabs/tab_users.py` trong IDE, sau đó bảo tôi:
```
"Hãy update tab_users.py và tab_follow.py tự động"
```

Tôi sẽ áp dụng tất cả thay đổi trên tự động.

---

## 🔧 LƯU Ý QUAN TRỌNG

### **Backward Compatibility**
- ✅ Tên class giữ nguyên (`InstagramLogin`, `InstagramPost`)
- ✅ Method signatures không đổi
- ✅ Code cũ vẫn hoạt động bình thường

### **Thay đổi LDPlayer Path (nếu cần)**
Nếu LDPlayer cài ở ổ khác, chỉ cần sửa file `config.py`:
```python
LDPLAYER_PATH = r"D:\LDPlayer\LDPlayer9"  # Thay đổi ở đây
```

### **Cài đặt dependencies mới**
```bash
pip install -r requirements.txt
```
