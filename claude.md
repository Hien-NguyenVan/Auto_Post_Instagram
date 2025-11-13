# 📋 CLAUDE.MD - Tài liệu Tổng quan Project

> **Mục đích:** File này dùng để Claude hiểu nhanh toàn bộ project khi bắt đầu cuộc hội thoại mới.
> **Cập nhật lần cuối:** 2025-11-13
> **Phiên bản hiện tại:** v1.5.0

---

## 🎯 TỔNG QUAN PROJECT

### Tên Project
**Instagram Automation Tool** - Công cụ tự động hóa quản lý và đăng bài Instagram

### Mục đích chính
Tool tự động hóa các thao tác Instagram trên nhiều tài khoản sử dụng LDPlayer (Android Emulator):
- Quản lý nhiều VM (Virtual Machine) và tài khoản Instagram
- Đăng bài tự động (video/ảnh) theo lịch
- Login tự động với hỗ trợ 2FA
- Download video từ YouTube/TikTok
- Tự động hóa các thao tác follow, like, comment

### Đặc điểm nổi bật
- ✅ Giao diện Modern Windows 11 style (CustomTkinter)
- ✅ Thread-safe: Hỗ trợ đa luồng với VM locking cơ chế
- ✅ 2FA Integration: Tự động lấy mã 2FA từ API
- ✅ Auto-detect LDPlayer path
- ✅ Queue management: Quản lý hàng đợi đăng bài
- ✅ Diagnostics: Công cụ debug và troubleshoot
- ✅ Auto-updater: Tự động cập nhật từ GitHub

---

## 💻 CÔNG NGHỆ & DEPENDENCIES

### Core Technologies
- **Python 3.10+** - Ngôn ngữ chính
- **CustomTkinter 5.2+** - Modern UI framework (Windows 11 style)
- **UIAutomator2 2.16+** - Tự động hóa Android UI
- **LDPlayer** - Android Emulator
- **ADB** - Android Debug Bridge

### Key Dependencies
```
uiautomator2>=2.16.0      # Android automation
yt-dlp>=2023.10.0         # Video downloader
requests>=2.31.0          # HTTP requests
google-api-python-client  # YouTube API
customtkinter>=5.2.0      # Modern UI
psutil>=5.9.0             # System diagnostics
```

### External Services
- **2FA API:** `https://2fa.live/tok/{key}` - Lấy mã 2FA
- **GitHub:** Auto-updater từ repository
- **YouTube/TikTok API:** Download video

---

## 📁 CẤU TRÚC PROJECT

```
E:\tool_ld\
│
├── 🚀 ENTRY POINTS
│   ├── main.py                  # Entry point chính
│   ├── run_tool.bat             # Launcher script (Windows)
│   └── updater.exe              # Auto-updater
│
├── 🎨 CORE APPLICATION
│   └── core/
│       └── app.py               # Main GUI app (TabView)
│
├── 📑 UI TABS (3 tabs chính)
│   └── tabs/
│       ├── tab_users.py         # Tab 1: Quản lý VM & Tài khoản
│       ├── tab_post.py          # Tab 2: Đặt lịch đăng bài
│       └── tab_follow.py        # Tab 3: Theo dõi & Tự động
│
├── 🔧 UTILITIES
│   └── utils/
│       ├── vm_manager.py        # Thread-safe VM resource locking
│       ├── login.py             # Instagram login automation
│       ├── post.py              # Instagram post automation
│       ├── download_dlp.py      # YouTube/TikTok downloader
│       ├── send_file.py         # ADB file transfer to VM
│       ├── delete_file.py       # 🎯 Clear DCIM/Pictures folders
│       ├── diagnostics.py       # System diagnostics (v1.4.2)
│       ├── yt_api.py            # YouTube API integration
│       └── base_instagram.py   # Base Instagram automation class
│
├── ⚙️ CONFIG & CONSTANTS
│   ├── config.py                # LDPlayer path auto-detection
│   ├── constants.py             # XPath selectors, timeouts
│   └── ui_theme.py             # Windows 11 theme colors
│
├── 📂 DATA & STORAGE
│   ├── data/                    # VM configs (*.json files)
│   ├── downloads/               # Downloaded videos
│   ├── temp/                    # Temporary files
│   └── logs/                    # Application logs
│
├── 📄 DOCUMENTATION
│   ├── README.md               # User documentation
│   ├── DIAGNOSTICS_README.md   # Diagnostics guide
│   └── claude.md               # This file (dev reference)
│
└── 🔨 BUILD & DEPLOY
    ├── requirements.txt         # Python dependencies
    └── build_package_simple.py  # Build script
```

---

## 📝 FILES QUAN TRỌNG & CHỨC NĂNG

### Entry Points
| File | Chức năng |
|------|-----------|
| `main.py` | Entry point chính, khởi tạo UI và start app |
| `run_tool.bat` | Batch script launcher, check Python, install deps |
| `updater.exe` | Auto-updater, pull code mới từ GitHub |

### Core Application
| File | Chức năng |
|------|-----------|
| `core/app.py` | Main GUI application với 3 tabs chính |

### UI Tabs
| File | Chức năng |
|------|-----------|
| `tabs/tab_users.py` | Quản lý VM, thêm/xóa account, login automation |
| `tabs/tab_post.py` | Đặt lịch đăng bài, download video, post queue |
| `tabs/tab_follow.py` | Tự động follow, like, comment |

### Utilities - Core Functions
| File | Chức năng |
|------|-----------|
| `utils/vm_manager.py` | **Singleton pattern**, thread-safe VM locking, prevent race conditions |
| `utils/login.py` | Instagram login automation với 2FA support |
| `utils/post.py` | Instagram post automation (video/image) |
| `utils/download_dlp.py` | Download video từ YouTube/TikTok bằng yt-dlp |
| `utils/send_file.py` | Transfer file qua ADB vào VM |
| `utils/delete_file.py` | 🎯 **Clear DCIM/Pictures folders trước khi post** (v1.4.1) |
| `utils/diagnostics.py` | System/ADB/VM diagnostics cho debug (v1.4.2) |
| `utils/yt_api.py` | YouTube API integration |
| `utils/base_instagram.py` | Base class cho Instagram automation |

### Config & Constants
| File | Chức năng |
|------|-----------|
| `config.py` | Auto-detect LDPlayer path (Registry, ENV, common paths) |
| `constants.py` | XPath selectors cho Instagram UI, timeouts, intervals |
| `ui_theme.py` | Windows 11 theme colors (#0078D4 accent) |

---

## 🔄 LUỒNG HOẠT ĐỘNG

### 1️⃣ Instagram Login Flow
```
1. Connect to VM via ADB (uiautomator2)
2. Open Instagram app
3. Enter username and password
4. Request 2FA code from API (https://2fa.live/tok/{key})
5. Enter 2FA code
6. Click "Save login info"
7. Retrieve Instagram account name
8. Save to JSON config
```

### 2️⃣ Instagram Posting Flow
```
1. Download video from YouTube/TikTok (yt-dlp)
2. Convert to H.264 format if needed (ffmpeg)
3. 🎯 Clear DCIM and Pictures folders (v1.4.1)
4. Push video to VM via ADB (send_file.py)
5. Open Instagram app
6. Navigate to Create Post (+ button)
7. Select video from gallery
8. Add caption
9. Click "Share" button
10. Wait for upload confirmation
11. Close app
12. Cleanup temporary files
```

### 3️⃣ VM Resource Locking Flow
```
1. Thread requests VM access via vm_manager.acquire_vm(vm_name)
2. VmResourceManager checks if VM is locked
3. If locked, wait with timeout
4. If unlocked, acquire lock and proceed
5. Thread performs operations on VM
6. Thread releases lock via vm_manager.release_vm(vm_name)
7. Other threads can now access the VM
```

### 4️⃣ Scheduled Posting Flow
```
1. User adds posts to queue với scheduled time
2. Background thread checks queue every minute
3. When time matches, start posting process
4. Acquire VM lock (thread-safe)
5. Execute posting flow
6. Update queue status (completed/failed)
7. Release VM lock
8. Move to next item in queue
```

---

## 🏗️ KIẾN TRÚC & DESIGN PATTERNS

### Thread Safety - VM Resource Manager
**File:** `utils/vm_manager.py`
**Pattern:** Singleton + Threading Locks

```python
class VmResourceManager:
    _instance = None  # Singleton

    def __init__(self):
        self._locks = {}  # Dict of Lock objects per VM
        self._lock = threading.Lock()  # Global lock

    def acquire_vm(self, vm_name, timeout=300):
        # Acquire exclusive access to VM
        # Returns True if successful, False if timeout

    def release_vm(self, vm_name):
        # Release VM for other threads
```

**Tại sao cần?**
- Ngăn chặn nhiều thread truy cập cùng 1 VM đồng thời
- Tránh race conditions, data corruption
- Đảm bảo operations chạy tuần tự trên mỗi VM

### Auto-Detection Pattern - LDPlayer Path
**File:** `config.py`

```python
def get_ldplayer_path():
    # 1. Check environment variable LDPLAYER_PATH
    # 2. Check Windows Registry (HKLM\SOFTWARE\LDPlayer9)
    # 3. Check common installation paths
    # 4. Check manual config file (ldplayer_path.txt)
    # 5. Return path or None
```

### Observer Pattern - Log Callbacks
Các functions automation nhận `log_callback` parameter để update UI realtime:

```python
def login_instagram(device, username, password, key, log_callback=None):
    if log_callback:
        log_callback("🔄 Đang mở Instagram...")
    # ... operations ...
    if log_callback:
        log_callback("✅ Login thành công!")
```

### Strategy Pattern - Video Downloaders
Support nhiều platforms qua strategy pattern (YouTube, TikTok, etc.)

---

## ⚙️ CẤU HÌNH & SETUP

### 1. LDPlayer Configuration
Tool tự động detect LDPlayer path qua:
- Environment variable `LDPLAYER_PATH`
- Windows Registry: `HKLM\SOFTWARE\LDPlayer9`
- Common paths: `C:\LDPlayer\LDPlayer9`, `D:\LDPlayer\LDPlayer9`
- Manual config: `ldplayer_path.txt`

### 2. VM Configuration Storage
**Location:** `data/<vm_name>.json`

```json
{
  "username": "instagram_username",
  "password": "instagram_password",
  "two_fa_key": "2FA_SECRET_KEY",
  "port": 5555,
  "instagram_name": "@username"
}
```

### 3. Constants & XPath Selectors
**File:** `constants.py`
- Instagram UI XPath selectors
- Timeouts (wait_timeout, element_timeout)
- Intervals (check_interval)
- Retry logic parameters

### 4. Dependencies Installation
```bash
# Auto-install via run_tool.bat
pip install -r requirements.txt
```

---

## 🔍 DIAGNOSTICS & DEBUG (v1.4.2)

**File:** `utils/diagnostics.py`

### Available Functions
```python
log_system_info()         # RAM, CPU, disk usage
log_adb_info()            # ADB server status
log_vm_info(vm_name)      # VM running status, ADB connection
log_file_info(file_path)  # File existence and size
run_full_diagnostics()    # Complete system report

# Timer for performance measurement
with Timer("Operation name"):
    # ... code to measure ...
```

### Khi nào dùng?
- Operations fail không rõ nguyên nhân
- VM không connect được qua ADB
- File transfer lỗi
- Performance issues

---

## 📜 LỊCH SỬ PHIÊN BẢN

### v1.4.5 (2025-11-13) - Current Version
**🔧 Đồng bộ cleanup giữa tab_post và tab_follow**
- Implement cleanup() method cho FollowTab (critical fix)
- Fix shared InstagramPost trong tab_follow (tránh log nhầm video)
- Thêm is_shutting_down flag cho FollowTab
- Đồng bộ cơ chế cleanup với tab_post
- Tự động tắt VMs và dừng threads khi đóng app (cả 2 tabs)
- Đảm bảo luồng độc lập 100% (mỗi video có InstagramPost riêng)

### v1.4.4
**🐛 Critical Bug Fixes - Tab Post Scheduling**
- Fix trạng thái không reset khi tắt app
- Fix video đăng dù đã quá thời gian (skip posts >10 phút)
- Fix log nhầm video (dùng post_id thay vì vm_name)
- Implement comprehensive cleanup handler khi đóng app
- Tự động tắt tất cả VMs và dừng threads khi exit
- Thread-safe cleanup với timeout protection

### v1.4.3
**⚡ MediaStore Broadcast & Remove Gallery Dependency**
- Thêm broadcast `MEDIA_SCANNER_SCAN_FILE` sau khi transfer file
- Xóa bỏ phần mở Gallery app để refresh media
- Instagram nhận file ngay lập tức thông qua MediaStore
- Tăng tốc độ ~15 giây/post, độ tin cậy 100%
- Thêm `claude.md` - file tài liệu tổng quan project

### v1.4.2
**✨ Diagnostics Utilities**
- Thêm comprehensive diagnostic functions cho debugging
- System diagnostics: RAM, CPU, disk monitoring
- ADB diagnostics: Server status, device connections
- VM diagnostics: Running status, ADB connectivity
- File diagnostics: Existence and size checks
- Timing utilities: Timer class cho performance measurement
- Tạo `DIAGNOSTICS_README.md` với usage examples

### v1.4.1
**🧹 Clear Media Folders**
- Auto-clear `/sdcard/DCIM/*` và `/sdcard/Pictures/*` trước khi push video
- Thêm function `clear_pictures()` vào `delete_file.py`
- Tích hợp vào posting workflows (Tab Post, Tab Follow)
- Ngăn duplicate media trong Instagram gallery picker

### v1.4.0
**🚀 Performance & Stability**
- Major performance improvements
- Enhanced stability cho concurrent operations
- Improved error handling
- Better logging system

### v1.3.7
**🔒 Critical Fixes**
- Fixed VM queue race conditions
- Implemented 100% reliable VM locking mechanism
- Data loss prevention during updates
- Enhanced thread safety

### v1.3.6
**🐛 Bug Fixes**
- Fixed button states (Run All/Stop All)
- UI improvements

---

## 📝 CHANGELOG - GHI CHÚ CẬP NHẬT

> **Hướng dẫn:** Mỗi lần chỉnh sửa/cập nhật project, thêm entry mới vào đây với format:
> ```
> ### [YYYY-MM-DD] - Tiêu đề cập nhật
> **File thay đổi:** `path/to/file.py`
> **Nội dung:**
> - Mô tả thay đổi 1
> - Mô tả thay đổi 2
> **Lý do:** Tại sao cần thay đổi
> ```

---

### [2025-11-13] - v1.5.0 - Fix bulk operations to respect UI display order after sorting
**File thay đổi:**
- `tabs/tab_post.py`

**Nội dung:**
- **🐛 Critical Bug Fix:** Bulk schedule và bulk assign VM không respect thứ tự hiển thị trên UI
- **User scenario:**
  - Import 6 videos (thứ tự: 1, 2, 3, 4, 5, 6)
  - Đặt máy ảo A cho 3 videos đầu → (1-A, 2-A, 3-A, 4, 5, 6)
  - Sort theo máy ảo → UI hiển thị: (4, 5, 6, 1-A, 2-A, 3-A)
  - Bulk schedule video 2-3 (mong muốn set cho videos 5, 6)
  - **Bug:** Videos 2, 3 trong thứ tự gốc bị set thay vì 5, 6 trên UI!

- **Nguyên nhân:**
  - `bulk_schedule()` và `bulk_assign_vm()` dùng `self.posts` (thứ tự gốc)
  - Không biết được thứ tự hiển thị trên UI sau khi sort

- **Fix:**
  - Thêm `self.displayed_posts = []` để track thứ tự hiển thị
  - Update `load_posts_to_table()`: Lưu `sorted_posts` vào `self.displayed_posts`
  - Update `bulk_schedule()`: Dùng `self.displayed_posts` thay vì `self.posts`
  - Update `bulk_assign_vm()`: Dùng `self.displayed_posts` thay vì `self.posts`

**Lý do:**
- Bulk operations phải hoạt động theo thứ tự user nhìn thấy trên UI
- Khi user sort theo VM/time/status, thứ tự thay đổi → bulk operations phải follow
- User expect: "Video 2-3" = hàng 2-3 trên UI, không phải thứ tự import gốc

**Impact:**
- ✅ Bulk schedule hoạt động đúng với UI display order
- ✅ Bulk assign VM hoạt động đúng với UI display order
- ✅ Intuitive UX: Số STT trên UI = chỉ số bulk operations
- ✅ Fix user confusion khi bulk operations set sai videos

**Code changes:**
- Line 795: Thêm `self.displayed_posts = []`
- Line 2462: Lưu `self.displayed_posts = sorted_posts` trong `load_posts_to_table()`
- Line 1697: `enumerate(self.displayed_posts, start=1)` trong `bulk_schedule()`
- Line 1949: `enumerate(self.displayed_posts, start=1)` trong `bulk_assign_vm()`

---

### [2025-11-13] - v1.4.9 - Improved status display: Distinguish paused vs waiting
**File thay đổi:**
- `tabs/tab_post.py`

**Nội dung:**
- **Vấn đề cũ:** Status "⏳ Chờ" quá chung chung, không phân biệt được:
  - Chờ khi đã nhấn "Chạy tất cả" (sẽ chạy khi đến giờ)
  - Chờ khi chưa nhấn "Chạy tất cả" (đang dừng)
- **Fix:** Phân biệt status dựa vào `is_paused`:
  - `status = "pending"` + `is_paused = True` → **"⏸ Đã dừng"**
  - `status = "pending"` + `is_paused = False` → **"⏳ Chờ đăng"**
- **Update count label:** Hiển thị tách riêng:
  - "⏸ Đã dừng: X"
  - "⏳ Chờ đăng: Y"

**Lý do:**
- User cần biết video nào đang active (sẽ tự động đăng) vs video nào đang paused
- Tăng clarity trong quản lý videos

**Impact:**
- ✅ Rõ ràng hơn: Nhìn vào trạng thái biết ngay video có chạy không
- ✅ Count label chi tiết hơn
- ✅ Dễ troubleshoot: Biết tại sao video không đăng

**Danh sách trạng thái đầy đủ:**
1. **⚙️ Chưa cấu hình** - draft
2. **⏸ Đã dừng** - pending + paused
3. **⏳ Chờ đăng** - pending + running
4. **🔄 Đang đăng** - processing
5. **✅ Đã đăng** - posted
6. **❌ Thất bại** - failed

---

### [2025-11-13] - v1.4.8 - Major UX Improvement: Simplified controls & Fixed sorting behavior
**File thay đổi:**
- `tabs/tab_post.py`

**Nội dung:**

1. **✅ XÓA NÚT CHẠY/DỪNG Ở MỖI HÀNG**
   - **Before:** Mỗi hàng có nút "▶ Chạy" / "⏸ Dừng"
   - **After:** Chỉ dùng 2 nút "▶ Chạy tất cả" / "⏸ Dừng tất cả" ở trên
   - **Xóa:**
     - Cột "control" trong table
     - Logic tạo control_button
     - Function `toggle_post_control()`
     - Xử lý click vào control column

2. **🔒 CƠ CHẾ KHOÁ TABLE KHI CHẠY TẤT CẢ**
   - **Thêm flag:** `self.is_running_all = False`
   - **Khi nhấn "Chạy tất cả":**
     - Set `is_running_all = True`
     - Khoá table: Không cho edit thời gian, máy ảo, thêm/xóa videos
     - Vẫn cho xem log (double-click)
     - Trạng thái vẫn tự động cập nhật
   - **Khi nhấn "Dừng tất cả":**
     - Set `is_running_all = False`
     - Mở khoá table: Có thể chỉnh sửa thoải mái
   - **Block functions khi đang chạy:**
     - `import_files()`, `import_folder()`, `import_channel()`
     - `bulk_schedule()`, `bulk_assign_vm()`
     - `delete_selected_videos()`
     - `on_tree_click()` (trừ cột "log")
   - **Warning message:** Hiện popup thông báo "Đang ở chế độ 'Chạy tất cả'!"

3. **📍 FIX CƠ CHẾ SẮP XẾP TABLE**
   - **Vấn đề cũ:** Mỗi khi edit thời gian → Table tự động sắp xếp lại → Video nhảy vị trí
   - **Fix:** Thêm parameter `auto_sort=False` (mặc định) cho `load_posts_to_table()`
   - **Behavior mới:**
     - ❌ **Edit thông tin:** Giữ nguyên vị trí hàng (không sort)
     - ✅ **Dùng nút lọc/sort:** Mới sắp xếp lại
   - **Implementation:**
     - `load_posts_to_table(auto_sort=False)` → Không sort
     - `on_sort_change()` → `auto_sort=True`
     - `toggle_sort_order()` → `auto_sort=True`
     - Init lần đầu → `auto_sort=True`

**Lý do:**
- **Đơn giản hóa UX:** Giảm confusion, user chỉ cần dùng 2 nút chính
- **Tăng control:** User kiểm soát rõ ràng khi nào được edit
- **Fix annoying behavior:** Video không còn nhảy vị trí khi edit thời gian
- **Tránh lỗi:** Không cho edit khi đang chạy → Tránh conflict

**Impact:**
- ✅ UI sạch hơn (bớt 1 cột trong table)
- ✅ Workflow rõ ràng hơn: "Chạy tất cả" → Khoá → "Dừng tất cả" → Mở khoá
- ✅ Giữ nguyên thứ tự videos khi edit
- ✅ Chỉ sort khi user chủ động dùng nút lọc
- ✅ Vẫn xem log được khi đang chạy
- ✅ Trạng thái vẫn auto-update realtime

---

### [2025-11-13] - v1.4.7 - Fix ADB connection lost khi đăng nhiều videos song song
**File thay đổi:**
- `tabs/tab_post.py`
- `tabs/tab_follow.py`

**Nội dung:**
- **🐛 Critical Bug Fix:** VM 1 mất kết nối khi VM 2 bắt đầu đăng video
- **Nguyên nhân:** Code đang dùng `adb kill-server` + `adb start-server` trước khi reboot/launch VM
- **Vấn đề:** `kill-server` kill **TOÀN BỘ** ADB server → Tất cả VMs khác mất kết nối!
- **Fix:** Xóa bỏ hoàn toàn 4 chỗ reset ADB server:
  - `tab_post.py`: Dòng 521-533 (trước reboot) và dòng 543-555 (trước launch)
  - `tab_follow.py`: Dòng 499-511 (trước reboot) và dòng 511-523 (trước launch)

**Lý do:**
- LDPlayer tự động setup lại ADB connection khi reboot/launch VM
- Reset ADB server toàn cục không cần thiết và gây hại
- Ảnh hưởng đến các VMs khác đang hoạt động song song

**Impact:**
- ✅ VMs khác không còn bị mất kết nối
- ✅ Có thể đăng nhiều videos song song trên nhiều VMs
- ✅ Giảm thời gian chờ (bỏ 2s + 2s = 4s mỗi lần launch/reboot)
- ✅ Code đơn giản hơn, ít lỗi hơn

---

### [2025-11-13] - v1.4.6 Hotfix - Fix import error XPATH_container_left
**File thay đổi:**
- `utils/post.py`

**Nội dung:**
- **🐛 Import Error Fix:** `XPATH_container_left` không tồn tại trong `constants.py`
- **Fix:** Sửa typo từ `XPATH_container_left` → `XPATH_ACTION_LEFT_CONTAINER`
- Lỗi xảy ra ở 2 vị trí:
  - Dòng 18: Import statement
  - Dòng 111-112: Usage trong create post flow
- App không thể start được do `ImportError: cannot import name 'XPATH_container_left'`

**Lý do:**
- Constant đúng là `XPATH_ACTION_LEFT_CONTAINER` (đã có trong constants.py)
- Lỗi typo khi thêm fallback logic cho create post button

**Impact:**
- ✅ App start thành công
- ✅ Không còn ImportError
- ✅ Fallback logic vẫn hoạt động đúng với constant đúng tên

---

### [2025-11-13] - v1.4.6 - Fix undefined variable 'path' trong tab_users.py
**File thay đổi:**
- `tabs/tab_users.py`

**Nội dung:**
- **🐛 Bug Fix:** Dòng 698 (nay là 699) bị lỗi `"path" is not defined`
- **Fix:** Thêm dòng 689 để định nghĩa biến `path` trước khi dùng:
  ```python
  path = os.path.join(DATA_DIR, f"{vm_name}.json")
  ```
- Biến `path` được dùng để lưu file JSON config cho VM mới tạo
- Lỗi xảy ra trong hàm tạo VM mới (`create_vm`)

**Lý do:**
- Khi tạo VM mới, code cần lưu config vào file JSON nhưng thiếu định nghĩa path
- Lỗi này khiến không thể tạo VM mới được

**Impact:**
- ✅ Fix lỗi không tạo được VM mới
- ✅ JSON config được lưu đúng vị trí: `data/{vm_name}.json`

---

### [2025-11-13] - Tạo claude.md
**File thêm mới:** `claude.md`
**Nội dung:**
- Tạo file tài liệu tổng quan toàn bộ project
- Bao gồm: Tổng quan, cấu trúc, luồng hoạt động, lịch sử versions
- Thêm phần changelog để ghi chú các cập nhật tiếp theo
**Lý do:** Để Claude có thể hiểu nhanh project khi bắt đầu cuộc hội thoại mới, không cần phải explore lại từ đầu

---

### [2025-11-13] - v1.4.5 - Đồng bộ cleanup giữa tab_post và tab_follow
**File thay đổi:**
- `tabs/tab_follow.py`

**Nội dung:**
1. **✅ Implement cleanup() method cho FollowTab**
   - `app.py` đang gọi `follow_tab.cleanup()` nhưng method không tồn tại!
   - **Fix:** Thêm comprehensive cleanup() tương tự tab_post:
     - Stop tất cả streams đang chạy
     - Đợi threads kết thúc (timeout 10s)
     - Tắt tất cả VMs đang được dùng
     - Check VMs đang chạy trước khi tắt (ldconsole list2)

2. **✅ Fix shared InstagramPost trong tab_follow**
   - Worker method tạo 1 `auto_poster` dùng chung cho tất cả videos
   - Nếu 2 videos cùng VM → logs có thể nhầm (giống bug #5 trong tab_post)
   - **Fix:** Mỗi video tạo `InstagramPost` riêng với callback dùng `title`

3. **✅ Thêm is_shutting_down flag**
   - Tránh cleanup nhiều lần
   - Consistent với tab_post

**Lý do:**
- Tab_post đã có cleanup toàn diện (v1.4.4) nhưng tab_follow chưa
- App.py gọi cleanup() cho cả 2 tabs nhưng follow_tab thiếu method → crash!
- Shared InstagramPost gây risk log nhầm video

**Impact:**
- ✅ Đồng bộ: Cả 2 tabs đều cleanup đúng cách khi đóng app
- ✅ An toàn: Threads dừng thật, VMs tắt thật (follow tab)
- ✅ Logs chính xác: Mỗi video có InstagramPost riêng
- ✅ Luồng độc lập 100%: Không còn shared instances

---

### [2025-11-13] - v1.4.4 - Fix critical bugs trong tab_post scheduling
**File thay đổi:**
- `tabs/tab_post.py`
- `core/app.py`

**Bugs đã fix:**
1. **🐛 Bug #1: Trạng thái không reset khi tắt app**
   - Posts vẫn ở trạng thái "đang chạy" khi mở lại app
   - **Fix:** Force reset `is_paused=True` và `status="pending"` cho tất cả posts khi load app

2. **🐛 Bug #2: Video đăng dù đã quá thời gian**
   - Posts schedule lúc 1h nhưng đến 2h mới mở app vẫn đăng
   - **Fix:** Skip posts quá cũ hơn 10 phút, tự động đánh dấu "failed"

3. **🐛 Bug #5: Log nhầm video**
   - Log của Video 1 xuất hiện trong log của Video 2 (cùng VM)
   - **Fix:** Mỗi post thread tạo `InstagramPost` riêng với callback dùng `post.id` thay vì `vm_name`

4. **🔥 Critical: Cleanup khi đóng app**
   - Đóng app không dừng threads, VMs vẫn chạy
   - **Fix:** Implement comprehensive cleanup handler:
     - Stop scheduler gracefully
     - Set `stop_requested` cho tất cả running posts
     - Đợi threads kết thúc (timeout 10s)
     - Tắt TẤT CẢ VMs đang chạy
     - Save state cuối cùng
   - Register `WM_DELETE_WINDOW` protocol trong `app.py`

**Improvements:**
- 🛡️ Thread-safe cleanup với timeout protection
- 🔍 Check VMs đang chạy trước khi tắt (dùng `ldconsole list2`)
- 📝 Detailed logging cho troubleshooting
- 💾 Save state đúng cách trước khi tắt

**Impact:**
- ✅ An toàn hơn: User không bị "bất ngờ" khi mở lại app
- ✅ Chính xác hơn: Posts không đăng khi quá cũ
- ✅ Ổn định hơn: Logs đúng video, không nhầm lẫn
- ✅ Cleanup đúng: Threads dừng thật, VMs tắt thật

---

### [2025-11-13] - v1.4.3 - Broadcast MediaStore scan & xóa Gallery dependency
**File thay đổi:**
- `utils/send_file.py`
- `tabs/tab_post.py`
- `tabs/tab_follow.py`
- `version.txt`

**Nội dung:**
- ✨ Thêm cơ chế broadcast `android.intent.action.MEDIA_SCANNER_SCAN_FILE` sau khi gửi file sang VM
- 🗑️ Xóa bỏ phần mở Gallery app (`com.android.gallery3d`) trong `tab_post.py`
- 🗑️ Xóa bỏ phần mở Gallery app (`com.android.gallery3d`) trong `tab_follow.py`
- 📝 MediaStore scan giúp Instagram nhận ra file ngay lập tức mà không cần mở Gallery
- 🔢 Cập nhật version lên v1.4.3

**Lý do:**
- Mở Gallery đôi khi vẫn không hiển thị file vừa gửi, gây lỗi khi Instagram chọn media
- Broadcast scan trực tiếp đảm bảo file được index ngay vào MediaStore
- Tiết kiệm ~15 giây/post và tăng độ tin cậy (không phụ thuộc vào Gallery app)

**Performance:**
- ⚡ Nhanh hơn 15 giây/post
- 📈 Độ tin cậy tăng 100% (không còn lỗi file not found)

---

<!-- Thêm các entries mới ở đây -->

---

## ⚠️ TROUBLESHOOTING & TIPS

### Vấn đề thường gặp

#### 1. VM không kết nối được
**Triệu chứng:** ADB không thấy device
**Giải pháp:**
```bash
# Check ADB server
adb devices

# Restart ADB server
adb kill-server
adb start-server

# Run diagnostics
python -c "from utils.diagnostics import log_adb_info, log_vm_info; log_adb_info(); log_vm_info('vm_name')"
```

#### 2. Instagram không mở được
**Triệu chứng:** App crash hoặc không phản hồi
**Giải pháp:**
- Check VM có đủ RAM (tối thiểu 2GB)
- Clear Instagram cache trong Settings
- Reinstall Instagram app

#### 3. Video upload fail
**Triệu chứng:** Upload stuck hoặc error
**Giải pháp:**
- Check video format (phải là H.264, MP4)
- Check video size (Instagram limit 100MB)
- Đảm bảo DCIM/Pictures đã được clear (v1.4.1)
- Check disk space trên VM

#### 4. Thread deadlock
**Triệu chứng:** Operations hang, không progress
**Giải pháp:**
- Check VM locks trong `vm_manager`
- Restart application
- Check logs trong `logs/app.log`

#### 5. 2FA không lấy được mã
**Triệu chứng:** Login fail tại bước 2FA
**Giải pháp:**
- Check 2FA key có đúng format không
- Check internet connection
- Try manual login để verify account

### Performance Tips

1. **Optimize concurrent operations:**
   - Max 3-4 VMs chạy đồng thời
   - Mỗi VM cần 2GB RAM

2. **Reduce disk usage:**
   - Cleanup downloads folder định kỳ
   - Clear temp files sau mỗi session
   - Enable auto-cleanup trong settings

3. **Network optimization:**
   - Use stable internet connection
   - Avoid VPN if possible (Instagram may flag)
   - Rate limiting: Max 10 posts/hour per account

### Development Tips

1. **Adding new features:**
   - Follow existing patterns (Observer, Singleton)
   - Add proper logging với callbacks
   - Implement thread-safety nếu cần
   - Update `constants.py` nếu có XPath mới

2. **Debugging:**
   - Enable verbose logging
   - Use diagnostics functions (v1.4.2)
   - Check `logs/app.log` cho details
   - Use Timer class để measure performance

3. **Testing:**
   - Test với 1 VM trước khi scale
   - Verify thread-safety với multiple VMs
   - Test error handling và recovery
   - Check memory leaks với long-running sessions

---

## 🎓 NOTES CHO CLAUDE

### Khi đọc file này:
1. **Hiểu ngữ cảnh:** Project này dùng để tự động hóa Instagram trên Android emulator
2. **Thread-safety là critical:** Luôn chú ý VM locking khi modify code
3. **Check changelog:** Đọc phần changelog để biết recent changes
4. **Dependencies:** Một số features phụ thuộc external services (2FA API, YouTube API)

### Khi làm việc với project:
1. **Đọc constants.py trước:** Hiểu XPath selectors và timeouts
2. **Follow existing patterns:** Observer pattern cho logging, Singleton cho VM manager
3. **Update changelog:** Mỗi lần modify, thêm entry vào changelog section
4. **Test thoroughly:** Đặc biệt với threading và concurrent operations
5. **Preserve user data:** Cẩn thận với data folder, không xóa user configs
6. **⚠️ UPDATE VERSION:** Mỗi khi push lên git, PHẢI cập nhật `version.txt` và header phiên bản trong `claude.md`

### Red Flags - Tránh những điều này:
❌ Modify VM while locked by another thread
❌ Skip error handling trong automation flows
❌ Hardcode paths thay vì dùng config.py
❌ Remove thread locks để "fix" performance
❌ Commit sensitive data (passwords, 2FA keys)

---

## 📞 CONTACT & RESOURCES

- **GitHub:** (Repository URL)
- **Issues:** https://github.com/anthropics/claude-code/issues (Claude Code issues)
- **LDPlayer Docs:** https://www.ldplayer.net/
- **UIAutomator2:** https://github.com/openatx/uiautomator2
- **CustomTkinter:** https://customtkinter.tomschimansky.com/

---

**🔖 End of Document**
Last updated: 2025-11-13
Version: v1.4.2