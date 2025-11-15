# 📋 CLAUDE.MD - Tài liệu Tổng quan Project

> **Mục đích:** File này dùng để Claude hiểu nhanh toàn bộ project khi bắt đầu cuộc hội thoại mới.
> **Cập nhật lần cuối:** 2025-11-15
> **Phiên bản hiện tại:** v1.5.26

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

> ⚠️ **QUY TẮC VERSION NUMBERING:**
> - Mỗi lần push git, **PHẢI tăng số version**
> - Format: `v1.5.X` → `v1.5.(X+1)` (tăng số cuối)
> - **KHÔNG dùng lại số cũ + text** (VD: ~~v1.5.20.1~~, ~~v1.5.20-hotfix~~)
> - Đúng: v1.5.20 → v1.5.21 → v1.5.22 ✅
> - Sai: v1.5.20 → v1.5.20.1 → v1.5.20.2 ❌

### v1.5.26 (2025-11-15) - Current Version
**✨ FEATURE: Thêm chế độ xem "Nhóm theo máy ảo" trong tab_post**
- Thêm toggle view mode: **Danh sách phẳng** vs **Nhóm theo máy ảo**
- **Grouped View:**
  - Videos được nhóm theo VM (TreeView với parent/child nodes)
  - Click vào VM group để expand/collapse
  - Track expanded state tự động (giữ nguyên khi reload)
  - Group "⚠️ Chưa đặt máy ảo" cho videos chưa assign VM
- **UI/UX:**
  - Toggle buttons: 📋 Danh sách phẳng | 📂 Nhóm theo máy ảo
  - Styling đặc biệt cho VM groups (accent color, bold font)
  - Global index (STT) giữ nguyên từ 1-N trong cả 2 modes
- **Bulk Operations:**
  - Hoạt động chính xác trong cả 2 modes
  - Số thứ tự (1, 2, 3...) vẫn theo thứ tự toàn cục
  - `self.displayed_posts` vẫn giữ flat order để bulk operations sử dụng
- **Lợi ích:**
  - Dễ quản lý videos theo từng máy ảo
  - Nhanh chóng xem được VM nào có bao nhiêu videos
  - Workflow linh hoạt: Chọn view mode phù hợp với task
  - Không ảnh hưởng đến existing features (sort, filter, bulk operations)

### v1.5.25 (2025-11-15)
**🔄 MAJOR CHANGE: Thay đổi hoàn toàn cơ chế TikTok API**
- Loại bỏ cơ chế TikTok cũ (yt-dlp scraping + DumplingAI API)
- Chuyển sang RapidAPI (tiktok-api23.p.rapidapi.com)
- **Tạo file mới:** `utils/tiktok_api_rapidapi.py` với đầy đủ functions
- **Tab Post:**
  - Thêm trường số lượng video cho TikTok (giống YouTube)
  - Workflow: Extract username → Get secUid → Fetch N videos với pagination (cursor)
  - Download: Gọi API lấy direct link → Download video
  - Filter isPinnedItem = true (không lấy video ghim)
- **Tab Follow:**
  - Quét TikTok theo thời gian (chỉ lấy 35 videos mới nhất)
  - Filter theo cutoff_time
  - Download và đăng bài tự động
- **Lợi ích:**
  - API ổn định hơn (không bị TikTok chặn như yt-dlp)
  - Pagination chính xác (lấy đúng số lượng video yêu cầu)
  - Download nhanh hơn (direct link từ API)
  - Hỗ trợ API key rotation
- **Breaking change:** Cần TikTok API key từ RapidAPI (tiktok-api23)
- **Deprecated files:** `utils/tiktok_api.py`, `utils/tiktok_api_new.py` (có thể xóa sau khi test)

### v1.5.24 (2025-11-14)
**🗑️ REMOVE FEATURE: Loại bỏ chức năng cắt video**
- Xóa nút "✂️ Cắt video" khỏi UI (tab_post row 1)
- Xóa toàn bộ function `split_video_dialog()` (272 dòng code)
- Lý do: Chức năng không cần thiết cho core workflow của tool
- Giảm complexity: Tool tập trung vào posting automation thay vì video editing

### v1.5.23 (2025-11-14)
**🔍 DEBUG IMPROVEMENT: Enhanced logging for video split tool**
- Cải thiện logging chi tiết để debug lỗi "ffprobe stdout is empty"
- Thêm verbose ffprobe retry khi stdout empty (không dùng `-v quiet`)
- Log stderr chi tiết khi ffprobe returncode=0 nhưng stdout empty
- Thêm detailed logging cho rename/copy file:
  - Log tên file cũ/mới khi detect ký tự đặc biệt
  - Log file path trước và sau rename/copy
  - Log exception type và message khi rename/copy fail
- Giúp user debug chính xác vấn đề khi cắt video fail

### v1.5.22 (2025-11-14)
**🐛 FIX: Cắt video đều nhau bằng -t (duration)**
- Fix video 57:32 cắt 3 phần → Part 1: 14:01, Part 2: 28:00, Part 3: 14:08 (mất 15 phút)
- Đổi từ `-to` (absolute time) sang `-t` (duration) để cắt chính xác
- Example: Video 57:32 / 3 parts → Mỗi part ~19 phút (thay vì 14-28-14)

### v1.5.21 (2025-11-14)
**🐛 CRITICAL FIX: Split video - Rename file with special chars before ffprobe**
- Fix TypeError: JSON object must be str (khi file có curly quotes `"Ghost Viper"`)
- Auto rename file gốc trước khi đọc duration và split
- Fallback copy sang temp nếu rename fail
- Thêm detailed error logging cho debug (ffprobe/ffmpeg stderr, exception type)
- Fix clean curly quotes (Unicode): `"` `"` `'` `'`

### v1.5.20 (2025-11-14)
**✨ FEATURE: Smart multi-part video splitting**
- Clean filename: Loại bỏ ký tự đặc biệt `< > : " / \ | ? *`
- Cắt thông minh theo thời lượng:
  - < 39 phút → 2 phần
  - < 58 phút → 3 phần
  - < 78 phút → 4 phần
  - ≥ 78 phút → 5 phần
- Output: `{name}-part1.mp4`, `part2.mp4`, ..., `partN.mp4`

### v1.5.19 (2025-11-14)
**✨ FEATURE: Add video split tool to tab_post**
- Thêm nút "✂️ Cắt video" kế bên nút YouTube import
- Dialog cắt video thành 2 phần (không re-encode, dùng ffmpeg -c copy)
- Standalone feature, không ảnh hưởng posting workflow
- Fix ffmpeg timeout issue (stdin hang) bằng `subprocess.DEVNULL`

### v1.5.18 (2025-11-13)
**🐛 FIX: Share button improvements**
- Thêm enabled state check trước khi click Share
- Sửa post notification wait logic (wait ít nhất 15 iterations)
- Di chuyển "No thanks" button click vào wait loop
- 3 distinct error cases với detailed logging + screenshots

### v1.5.17 (2025-11-13)
**✨ FEATURE: Retry mechanism for posting**
- Thử tối đa 2 lần (1 lần retry) khi post fail
- Cleanup giữa các retry: Xóa file VM, quit VM, xóa temp, đợi 5s
- Download lại video từ URL khi retry
- Không retry nếu user nhấn stop
- Full cleanup sau 2 lần fail: Release VM lock

### v1.5.16 (2025-11-13)
**🔄 REVERT: Remove VM reset mechanism**
- Loại bỏ VM reset trước khi mở Instagram
- Reset gây timeout, VM stuck ở status=2
- Trả về code cũ (v1.5.14)

### v1.5.15 (2025-11-13) - CANCELLED
**❌ FAILED: Add VM reset before Instagram posting**
- Thêm reset VM trước khi mở Instagram
- Gây VM timeout, không shutdown được
- Đã revert trong v1.5.16

### v1.5.14 (2025-11-13)
**🔄 BASE VERSION**
- Baseline trước khi thử VM reset mechanism

### v1.5.13 (2025-11-13)
**🐛 FIX: Table không cập nhật khi xóa video**
- Update `self.displayed_posts` sau khi xóa khỏi `self.posts`
- Sync 2 lists để UI reflect đúng data
- Giữ thứ tự sort hiện tại

### v1.5.12 (2025-11-13)
**✨ FEATURE: Add "Huỷ tất cả" button to bulk schedule and bulk assign VM**
- Thêm nút "🗑️ Huỷ tất cả" trong dialog Lên lịch hàng loạt
- Thêm nút "🗑️ Huỷ tất cả" trong dialog Đặt máy ảo hàng loạt
- Gỡ bỏ thời gian/máy ảo đã set trong phạm vi videos
- Videos trở về trạng thái "Chưa cấu hình" sau khi huỷ
- Có confirmation dialog trước khi gỡ bỏ

### v1.5.11
**🐛 CRITICAL FIX: Fix table jumping issue when toggle checkbox after sorting**
- Fix table nhảy vị trí khi toggle checkbox sau khi sort
- load_posts_to_table() giờ dùng displayed_posts thay vì posts khi auto_sort=False
- Giữ nguyên thứ tự đã sort khi thao tác (check/uncheck, edit)
- Fix user confusion: "Vừa check video ở hàng 2, nó nhảy sang hàng 5!"

### v1.5.10
**✨ UX IMPROVEMENT: Add description parameter to safe_click and safe_send_text**
- Thêm parameter `description` cho `safe_click()` và `safe_send_text()`
- Log rõ ràng hơn: "🖱️ Đang click Next button (top)..." thay vì "🖱️ Đang click element //xpath..."
- Cập nhật 15+ chỗ gọi trong utils/post.py với description dễ hiểu
- Cải thiện UX khi debug: Nhìn log biết ngay đang thao tác element nào

### v1.5.9
**⚡ OPTIMIZATION: Download on-demand - Tối ưu disk usage**
- Thay đổi flow: Download → Wait → Acquire VM → Post
- Sang: Wait → Acquire VM → Download → Post
- Chỉ download khi đã có VM sẵn sàng
- Giảm peak disk usage từ 1GB xuống 50MB (20 videos cùng queue)
- Không tốn disk khi chờ VM lock

### v1.5.8
**🐛 CRITICAL FIX: Scheduler race condition - Fix list reference bug**
- Fix scheduler không chạy sau bulk operations (bulk_schedule, bulk_assign_vm)
- Fix race condition: scheduler.posts reference bị stale khi reassign self.posts
- Replace all `self.posts = new_list` với slice assignment `self.posts[:] = new_list`
- Fix 4 chỗ: bulk_schedule(), bulk_assign_vm(), import_channel(), delete_posts()
- Scheduler giờ luôn thấy updates, chạy deterministic 100%

### v1.5.7
**✨ MediaStore Broadcast Retry - Intelligent gallery file detection**
- Thêm retry mechanism cho MediaStore broadcast khi file chưa xuất hiện trong gallery
- Implement `_retry_mediastore_broadcast()` method với tối đa 3 lần retry
- Thêm parameter `video_filename` vào `auto_post()` để support retry broadcast
- Fail-fast behavior: Dừng ngay nếu file không xuất hiện sau 3 lần retry + screenshot
- Tăng độ tin cậy posting: Đảm bảo file có trong gallery trước khi tiếp tục
- Defensive approach thay vì optimistic: Kiểm tra chặt chẽ trước khi thao tác

### v1.5.6
**🐛 Fix device offline error by checking ADB state properly**
- Improved `wait_adb_ready()` to parse and validate device state from 'adb devices' output
- Parse device state column (device/offline/unauthorized) instead of just checking presence
- Only return success when state is "device", not when offline or unauthorized
- Log device state changes in real-time to help debug connection issues
- Prevents race condition where device appears in list but isn't ready for file operations

### v1.5.5
**🐛 Remove all hardcoded ADB paths, use config auto-detection**
- Fix critical bug: Hardcoded `adb_path = r"C:\LDPlayer\LDPlayer9\adb.exe"` fails cho users cài LDPlayer ở D:\ hoặc E:\
- Update `send_file.py` và `delete_file.py` để dùng `ADB_EXE` từ config
- Thêm fallback mechanism: `if adb_path is None: adb_path = ADB_EXE`
- Fix `[WinError 2] The system cannot find the file specified` cho all users

### v1.4.5
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

## ⚠️ KNOWN ISSUES & TODO

### 🔴 Priority: High

#### 1. **Stop video đang processing không có cơ chế clean**
**Vấn đề:**
- Khi nhấn "Dừng tất cả", video `status="processing"` (đang đăng bài) sẽ bị bỏ qua
- Không có cách nào dừng video đang processing một cách clean và ổn định
- Nếu force stop Instagram app → Có thể để lại draft, thread sẽ exception

**Impact:**
- User phải đợi video processing hoàn tất (1-3 phút) mới mở khóa table
- Không thể cancel video bị stuck
- Confusion: "Dừng tất cả" nhưng vẫn thấy "🔄 Đang đăng"

**Giải pháp đề xuất:**
- **Option 1 (Graceful):** Thêm `cancel_event` + checkpoint checks trong automation flow
- **Option 2 (Force):** Force stop Instagram app (nhanh nhưng không clean)
- **Option 3 (Nuclear):** Quit VM (chắc chắn nhưng phải reboot VM)
- **Option 4 (Hybrid):** Thử graceful → Timeout → Hỏi user chọn force/wait/cancel

**Status:** Pending - Sẽ implement sau

**File liên quan:** `tabs/tab_post.py` (stop_all_videos), `utils/post.py` (auto_post)

**Date noted:** 2025-11-13

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

### [2025-11-13] - v1.5.13 - Fix table không cập nhật khi xóa video
**File thay đổi:**
- `tabs/tab_post.py`
- `version.txt`
- `claude.md`

**Nội dung:**
- **🐛 Bug Fix:** Khi xóa video, scheduler đã xóa (JSON updated) nhưng table UI vẫn hiển thị videos đã xóa
- **Nguyên nhân:**
  - `delete_selected_videos()` gọi `load_posts_to_table()` với `auto_sort=False` (mặc định)
  - Khi `auto_sort=False`, `load_posts_to_table()` dùng `self.displayed_posts` (thứ tự cũ)
  - Nhưng `self.displayed_posts` không được update sau khi xóa → Table vẫn load từ list cũ
- **Fix:**
  - Thêm logic update `self.displayed_posts` sau khi xóa khỏi `self.posts` (line 2881-2883)
  - Đảm bảo cả 2 lists đều sync sau delete operation

**Lý do:**
- Đồng bộ `self.posts` và `self.displayed_posts` là critical để UI reflect đúng data
- Giữ được thứ tự sort hiện tại (không jump về thứ tự mặc định)

**Impact:**
- ✅ Table cập nhật đúng ngay sau khi xóa video
- ✅ Giữ nguyên thứ tự sort hiện tại
- ✅ Sync hoàn hảo giữa data và UI

**Code changes:**
- tabs/tab_post.py:2881-2883: Update displayed_posts sau khi xóa
- version.txt: v1.5.12 → v1.5.13
- claude.md: Update version và changelog

---

### [2025-11-13] - v1.5.9 - OPTIMIZATION: Download on-demand để tối ưu disk usage
**File thay đổi:**
- `tabs/tab_post.py`
- `version.txt`

**Nội dung:**
- **⚡ OPTIMIZATION:** Thay đổi flow download để tối ưu disk usage khi nhiều videos cùng queue
- **Vấn đề cũ:**
  ```
  Flow cũ: Download → Wait → Acquire VM → Post

  20 videos cùng VM, cùng time:
  ├─ 14:00: Scheduler tạo 20 threads
  ├─ 14:00-14:05: 20 threads download SONG SONG (peak 1GB disk)
  ├─ 14:05: Thread 1 acquire VM → Post (3 phút)
  ├─ 14:08: Thread 1 release → Cleanup video 1
  ├─ 14:08: Thread 2 acquire VM → Post
  └─ ...

  → 19 videos đã download nhưng chờ → Tốn ~1GB disk trong 1 giờ!
  ```

- **Flow mới (v1.5.9):**
  ```
  Flow mới: Wait → Acquire VM → Download → Post

  20 videos cùng VM, cùng time:
  ├─ 14:00: Scheduler tạo 20 threads
  ├─ 14:00: Thread 1 acquire VM ✅ → Download (2 phút) → Post (3 phút)
  ├─ 14:00: Thread 2-20 WAIT (blocking at acquire_vm)
  ├─ 14:05: Thread 1 release → Cleanup video 1
  ├─ 14:05: Thread 2 acquire VM ✅ → Download → Post
  └─ ...

  → Chỉ 1 video được download mỗi lúc → Tốn ~50MB disk!
  ```

- **Thay đổi chi tiết:**
  1. **Di chuyển download logic:** Từ trước acquire VM → sau acquire VM
  2. **Thêm biến `original_video_path`:** Backup URL gốc trước khi download
  3. **Check local file sớm:** Nếu local file, check existence ngay (không cần wait VM)
  4. **Thêm import:** `from utils.download_dlp import download_video_api, download_tiktok_direct_url`
  5. **Cleanup VM khi download fail:** Tắt VM nếu download thất bại

**Lý do:**
- **Disk optimization:** 20 videos × 50MB = 1GB → 1 video × 50MB = 50MB (giảm 95%)
- **Không lãng phí bandwidth:** Download song song 20 videos chậm hơn download tuần tự
- **Fair resource usage:** Chỉ download khi thực sự cần (có VM rồi)
- **Tránh timeout:** Thread không phải chờ lâu với video đã download sẵn

**Impact:**
- ✅ Giảm peak disk usage từ ~1GB xuống ~50MB (20 videos cùng VM)
- ✅ Không tốn disk khi chờ VM lock
- ✅ Download nhanh hơn (không chia bandwidth)
- ✅ Backward compatible: Local files vẫn hoạt động bình thường

**Testing scenario:**
```
Before v1.5.9:
- Import 20 YouTube URLs, cùng VM, cùng time 14:00
- Hit "Run All" at 14:00
- Peak disk: ~1GB (all downloaded at once)
- Duration: ~1 hour (20 × 3 min)

After v1.5.9:
- Import 20 YouTube URLs, cùng VM, cùng time 14:00
- Hit "Run All" at 14:00
- Peak disk: ~50MB (only 1 video at a time)
- Duration: ~1.6 hours (20 × (2 min download + 3 min post))
- Trade-off: +10% thời gian, nhưng -95% disk usage
```

**Code changes:**
- tabs/tab_post.py:385-400: Detect URL, backup original_video_path, check local file early
- tabs/tab_post.py:527-619: Di chuyển download logic sau acquire VM
- tabs/tab_post.py:31: Add import for download functions

---

### [2025-11-13] - v1.5.8 - CRITICAL FIX: Scheduler race condition - List reference bug
**File thay đổi:**
- `tabs/tab_post.py`
- `version.txt`

**Nội dung:**
- **🐛 CRITICAL BUG FIX:** Scheduler không chạy sau khi user dùng bulk operations
- **Vấn đề nghiêm trọng:**
  - User lên lịch 20 videos, set thời gian, nhấn "Chạy tất cả"
  - Đến giờ KHÔNG CHẠY! (non-deterministic: đôi khi chạy lần 1, đôi khi lần 3-4)
  - Phải restart app thì mới chạy được

- **Root cause: Python Reference vs Reassignment**
  ```python
  # Khởi tạo:
  self.posts = [video1, video2, ...]  # List A
  scheduler.posts = self.posts        # scheduler TRỎ vào List A

  # User dùng bulk_schedule():
  self.posts = self.displayed_posts   # ❌ TẠO List B mới!
  # → self.posts TRỎ List B
  # → scheduler.posts VẪN TRỎ List A (CŨ!)
  # → Scheduler check List A → KHÔNG THẤY videos mới!
  ```

- **Tại sao non-deterministic?**
  - Phụ thuộc user CÓ DÙNG bulk operations không
  - Phụ thuộc KHI NÀO dùng (trước hay sau loop)
  - Nếu KHÔNG dùng bulk → In-place modify → Chạy OK
  - Nếu CÓ dùng bulk → Reassign → Scheduler mất sync

- **Fix toàn diện (4 chỗ):**

  **1. bulk_schedule() - Line 1761:**
  ```python
  # Before:
  self.posts = self.displayed_posts  # ❌ Reassign

  # After:
  self.posts[:] = self.displayed_posts  # ✅ Slice assignment (in-place)
  ```

  **2. bulk_assign_vm() - Line 2016:**
  ```python
  self.posts[:] = self.displayed_posts  # ✅ In-place
  ```

  **3. import_channel() - Line 2166-2167:**
  ```python
  # Before:
  self.posts = imported_posts  # ❌ Reassign

  # After:
  self.posts.clear()                      # ✅ Clear old
  self.posts.extend(imported_posts)       # ✅ Add new (in-place)
  ```

  **4. delete_posts() - Line 2706:**
  ```python
  # Before:
  self.posts = [post for post in self.posts if ...]  # ❌ Reassign

  # After:
  self.posts[:] = [post for post in self.posts if ...]  # ✅ In-place
  ```

**Lý do:**
- **Python reference semantics:** Gán `=` tạo reference mới, không modify list cũ
- **Slice assignment `[:]`:** Modify list in-place, giữ nguyên reference
- **Scheduler thread:** Giữ reference đến `self.posts` ban đầu
- **Reassign → Scheduler mất sync** → Không thấy videos mới → Không chạy

**Impact:**
- ✅ Fix 100% issue scheduler không chạy
- ✅ Deterministic: Luôn chạy ngay lần 1
- ✅ Không cần restart app
- ✅ Thread-safe: Scheduler luôn sync với UI
- ✅ Fix cả 4 edge cases: bulk schedule, bulk assign, import, delete

**Testing:**
```
Before fix:
- Import 20 videos → Bulk schedule → Chạy tất cả → FAIL ❌
- Restart → Chạy tất cả → OK ✅ (nhưng phải restart!)

After fix:
- Import 20 videos → Bulk schedule → Chạy tất cả → OK ✅
- Không cần restart! ✅
```

**Code changes:**
- tabs/tab_post.py:1761: `self.posts[:] = ...` (bulk_schedule)
- tabs/tab_post.py:2016: `self.posts[:] = ...` (bulk_assign_vm)
- tabs/tab_post.py:2166-2167: `clear() + extend()` (import_channel)
- tabs/tab_post.py:2706: `self.posts[:] = [...]` (delete_posts)

---

### [2025-11-13] - v1.5.7 - MediaStore Broadcast Retry - Intelligent gallery file detection
**File thay đổi:**
- `utils/post.py`
- `tabs/tab_post.py`
- `tabs/tab_follow.py`
- `version.txt`

**Nội dung:**
- **✨ Feature mới:** Retry mechanism cho MediaStore broadcast khi file chưa xuất hiện trong Instagram gallery
- **Vấn đề gốc:**
  - `send_file_api()` đã broadcast MediaStore sau khi push file
  - Tuy nhiên, đôi khi file vẫn chưa xuất hiện trong Instagram gallery picker
  - Automation tiếp tục click Next → Fail vì không có file để select

- **Giải pháp:**
  1. **Thêm helper method `_retry_mediastore_broadcast()`** trong `InstagramPost` class:
     - Retry broadcast tối đa 3 lần
     - Mỗi lần broadcast: `am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/DCIM/{filename}`
     - Đợi 2 giây sau mỗi broadcast để MediaStore update
     - Log chi tiết từng lần retry

  2. **Update `auto_post()` method:**
     - Thêm parameter `video_filename` để biết filename cần broadcast
     - Import `subprocess` để chạy broadcast command

  3. **Sửa logic kiểm tra file trong gallery (dòng 237-258 post.py):**
     - **TRƯỚC:** Kiểm tra `XPATH_FIRST_BOX` → Nếu CÓ thì comment "gọi lại mediastore" (không làm gì) → Tiếp tục
     - **SAU:**
       - Kiểm tra `XPATH_FIRST_BOX` (file đầu tiên trong gallery)
       - Nếu **KHÔNG CÓ** → Retry broadcast 3 lần → Kiểm tra lại
       - Nếu vẫn **KHÔNG CÓ** → Screenshot + return False (fail fast)
       - Nếu **CÓ** → Log "✅ File đã có trong gallery" → Tiếp tục

  4. **Update callers:**
     - `tab_post.py`: Extract `video_filename = os.path.basename(post.video_path)` → Truyền vào `auto_post()`
     - `tab_follow.py`: Extract `video_filename = os.path.basename(video_path)` → Truyền vào `auto_post()`

**Behavior change:**
- **Logic CŨ (Optimistic):** Không kiểm tra file có trong gallery không → Cứ tiếp tục click Next → Fail sau
- **Logic MỚI (Defensive):** Enforce file phải có → Retry broadcast 3 lần → Fail fast nếu không có → Screenshot evidence

**Lý do:**
- **Tăng độ tin cậy:** Đảm bảo file CÓ trong gallery trước khi tiếp tục
- **Fail fast:** Biết ngay file không có, không lãng phí thời gian
- **Debug dễ hơn:** Screenshot + log chi tiết khi fail
- **Có cơ hội retry:** Broadcast 3 lần trước khi fail (tổng cộng 4 lần broadcast: 1 lần từ send_file + 3 lần retry)

**Impact:**
- ✅ Tăng độ tin cậy posting: File phải có trước khi post
- ✅ Giảm fail rate do file chưa xuất hiện trong gallery
- ✅ Fail fast với screenshot evidence
- ✅ Log chi tiết: Biết file xuất hiện sau lần retry thứ mấy
- ✅ Backward compatible: `video_filename` là optional parameter

**Code changes:**
- `utils/post.py`:
  - Line 7: Add `import subprocess`
  - Line 43-82: Add `_retry_mediastore_broadcast()` method
  - Line 64: Add `video_filename` parameter to `auto_post()`
  - Line 237-258: Implement file check + retry logic
- `tabs/tab_post.py`:
  - Line 666: Extract video_filename
  - Line 671: Pass video_filename to auto_post()
- `tabs/tab_follow.py`:
  - Line 707: Extract video_filename
  - Line 714: Pass video_filename to auto_post()

---

### [2025-11-13] - v1.5.6 - Fix device offline error by checking ADB state properly
**File thay đổi:**
- `utils/vm_manager.py`
- `core/app.py`
- `version.txt`

**Nội dung:**
- **🐛 Bug Fix:** Device xuất hiện trong `adb devices` nhưng state là "offline" hoặc "unauthorized" → File operations fail
- **Vấn đề:**
  - `wait_adb_ready()` chỉ check device có trong output hay không
  - Không parse state column (device/offline/unauthorized)
  - Race condition: Device vừa boot xong, trong list nhưng state="offline"

- **Fix:**
  - Parse `adb devices` output để lấy state column
  - Chỉ return True khi state = "device"
  - Log device state changes realtime
  - Prevent race condition khi device chưa ready

**Lý do:**
- Device "offline" không thể thực hiện file operations
- Cần đợi device chuyển sang state "device" mới tiếp tục

**Impact:**
- ✅ Fix device offline errors
- ✅ Prevent race conditions
- ✅ Clear logging của device state

---

### [2025-11-13] - v1.5.5 - Remove all hardcoded ADB paths, use config auto-detection
**File thay đổi:**
- `utils/send_file.py`
- `utils/delete_file.py`
- `tabs/tab_post.py`

**Nội dung:**
- **🐛 Critical Bug Fix:** Hardcoded `adb_path = r"C:\LDPlayer\LDPlayer9\adb.exe"` fails cho users cài LDPlayer ở D:\ hoặc E:\
- **Vấn đề:**
  ```python
  # utils/send_file.py - HARDCODED!
  def send_file_api(local_path, vm_name, adb_path=r"C:\LDPlayer\LDPlayer9\adb.exe", ...):

  # utils/delete_file.py - HARDCODED!
  adb_path = r"C:\LDPlayer\LDPlayer9\adb.exe"
  ```
  → User cài LDPlayer ở `D:\LDPlayer\` → **`[WinError 2] The system cannot find the file specified`**

- **Tại sao lại lỗi:**
  - `config.py` đã có logic **auto-detect** LDPlayer path
  - Tất cả chỗ khác dùng `ADB_EXE` từ config ✅
  - Nhưng 2 utils này vẫn hardcode `C:\` ❌
  - Khi gọi mà không truyền `adb_path` → Dùng hardcoded default → Fail

- **Log error thực tế:**
  ```
  [15:44:38] 📤 Gửi file vào máy ảo...
  [15:44:38]    🔍 Kiểm tra ADB connection...
  [15:44:38] ❌ Lỗi khi gửi file sang máy ảo: [WinError 2] The system cannot find the file specified
  ```

- **Fix:**
  1. **`utils/send_file.py`:**
     - Import `ADB_EXE` từ config
     - Đổi default parameter: `adb_path=None`
     - Fallback: `if adb_path is None: adb_path = ADB_EXE`

  2. **`utils/delete_file.py`:**
     - Import `ADB_EXE` từ config
     - Thêm `adb_path=None` parameter cho `clear_dcim()` và `clear_pictures()`
     - Fallback: `if adb_path is None: adb_path = ADB_EXE`

  3. **`tabs/tab_post.py`:**
     - Truyền `adb_path=ADB_EXE` khi gọi `send_file_api()`
     - Đảm bảo dùng config path, không dùng default

**Lý do:**
- **Flexibility:** Users cài LDPlayer ở C:\, D:\, E:\ đều hoạt động
- **Consistency:** Tất cả code đều dùng `ADB_EXE` từ config
- **Auto-detection:** `config.py` tự tìm LDPlayer path
- **No hardcode:** Không còn hardcode path nào trong utils

**Impact:**
- ✅ Fix `[WinError 2]` cho users cài LDPlayer không phải ở C:\
- ✅ Tất cả utils dùng `ADB_EXE` từ config
- ✅ Backward compatible: Không break existing code
- ✅ Linh hoạt: Có thể override `adb_path` nếu cần

**Code changes:**
- utils/send_file.py: Import ADB_EXE, đổi default parameter, add fallback
- utils/delete_file.py: Import ADB_EXE, add adb_path parameter, add fallback
- tabs/tab_post.py: Truyền `adb_path=ADB_EXE` vào send_file_api()

---

### [2025-11-13] - v1.5.4 - Add automatic screenshot on automation failure
**File thay đổi:**
- `utils/screenshot.py` (NEW)
- `utils/post.py`

**Nội dung:**
- **✨ Feature mới:** Tự động chụp màn hình Instagram khi automation thất bại
- **Use case:** Instagram thường cập nhật UI → Automation fail → Cần xem UI mới như thế nào
- **Giải pháp:**
  1. Tạo `utils/screenshot.py` với function `take_screenshot()`
  2. Thêm method `_capture_failure_screenshot()` trong InstagramPost class
  3. Gọi screenshot tại tất cả critical failure points

**Screenshot được chụp khi:**
- ❌ Feed tab không xuất hiện
- ❌ Không tìm thấy Profile tab
- ❌ Không tìm thấy Create tab sau retry
- ❌ Không tìm thấy nút Post
- ❌ Không nhập được caption
- ❌ Không tìm thấy nút OK (sau caption)
- ❌ Không tìm thấy nút Share
- ❌ Instagram từ chối đăng bài (retry button xuất hiện)

**Tính năng screenshot:**
- 📁 Lưu tại: `D:/temp/`
- 📝 Tên file: `{vm_name}-{port}-{timestamp}.png`
  - Ví dụ: `test1-5554-20251113_145530.png`
- 📸 Chụp qua ADB: `adb shell screencap -p`
- 🔍 Log đường dẫn file + lý do failure
- ⚡ Timeout 10s, không block automation flow

**Log example:**
```
[14:55:30] ❌ Feed tab không xuất hiện
[14:55:31] 📸 Screenshot đã lưu: D:/temp/test1-5554-20251113_145530.png
[14:55:31]    💡 Lý do: Feed tab không xuất hiện - Instagram có thể đã đổi giao diện
[14:55:31]    🔍 Kiểm tra ảnh để xem Instagram có đổi UI không
```

**Lý do:**
- Instagram cập nhật UI thường xuyên → Automation bị break
- Cần evidence hình ảnh để biết UI mới ra sao
- Dễ dàng update XPath selectors dựa vào screenshot
- Debug nhanh hơn: Nhìn ảnh là biết vấn đề

**Impact:**
- ✅ Tự động chụp màn hình khi fail (không cần manual)
- ✅ Evidence cho mọi failure
- ✅ Debug UI changes nhanh hơn
- ✅ Dễ dàng update selectors khi Instagram đổi UI
- ✅ Không ảnh hưởng performance (chỉ chụp khi fail)

**Code changes:**
- NEW: `utils/screenshot.py` - Screenshot utility module
- `utils/post.py`:
  - Import screenshot + ADB_EXE
  - Add `_capture_failure_screenshot()` method
  - Add screenshot calls at 8 critical failure points

---

### [2025-11-13] - v1.5.3 - Improve send_file error logging and debugging
**File thay đổi:**
- `utils/send_file.py`

**Nội dung:**
- **🐛 Bug Fix:** "Gửi file thất bại" nhưng không biết nguyên nhân cụ thể
- **User experience trước:**
  ```
  [14:44:08] 📤 Gửi file vào máy ảo...
  [14:44:08] 🔹 Device: emulator-5556
  [14:44:08] ❌ Gửi file thất bại
  ```
  → Không biết lỗi gì!

- **Vấn đề:**
  - Exception handler đã comment log: `# log(f"❌ Lỗi: {e}")` (line 87)
  - Không log ADB connection check details
  - Không log adb push stderr/stdout khi fail
  - Không biết lỗi xảy ra ở bước nào

- **Fix:**
  1. **Uncomment exception log** để catch tất cả errors
  2. **Thêm log ADB check:**
     - "🔍 Kiểm tra ADB connection..."
     - Nếu fail: Log adb devices output
     - Nếu OK: "✅ Device đã kết nối ADB"
  3. **Thêm adb push error details:**
     - Log returncode
     - Log stderr nếu có
     - Log stdout nếu có

- **User experience sau:**
  ```
  [14:44:08] 📤 Gửi file vào máy ảo...
  [14:44:08] 🔹 Device: emulator-5556
  [14:44:08]    🔍 Kiểm tra ADB connection...
  [14:44:08] ❌ Device 'emulator-5556' không có trong 'adb devices'
  [14:44:08]    📋 Output: List of devices attached
                           emulator-5554    device
  ```
  → Biết rõ: Port 5556 không connect, chỉ có 5554!

**Lý do:**
- Debug nhanh hơn: Biết ngay lỗi ở đâu (file, port, ADB, push)
- Không phải đoán: Log chi tiết stderr/stdout
- Fix được ngay: Thấy rõ ADB devices output

**Impact:**
- ✅ Exception không còn bị nuốt
- ✅ Biết device có connect ADB không
- ✅ Thấy được adb devices output
- ✅ Debug adb push errors dễ hơn
- ✅ Tiết kiệm thời gian troubleshoot

**Code changes:**
- Line 42: Add "Kiểm tra ADB connection" log
- Line 49-52: Add detailed ADB check failure log with output
- Line 61: Add capture_output=True to adb push
- Line 86-90: Add stderr/stdout logging on push failure
- Line 87: Uncomment exception log

---

### [2025-11-13] - v1.5.2 - Add realtime logging for VM startup and ADB connection
**File thay đổi:**
- `utils/vm_manager.py`
- `tabs/tab_post.py`
- `tabs/tab_follow.py`

**Nội dung:**
- **🐛 Bug Fix:** Trong 120s chờ VM khởi động, không có log nào → User không biết đang làm gì
- **User experience trước:**
  ```
  [14:38:05] ⏳ Chờ máy ảo 'test1' khởi động hoàn toàn...
  [14:40:08] ⏱️ Timeout - Máy ảo 'test1' không khởi động được
  ```
  → 2 phút im lặng hoàn toàn!

- **Nguyên nhân:**
  - `wait_vm_ready()` và `wait_adb_ready()` chỉ log vào Python logger
  - Không log ra UI (`post.log()`)
  - User không biết VM status hiện tại, có lỗi gì không

- **Fix:**
  - Thêm parameter `log_callback=None` vào cả 2 functions
  - Log VM status changes: "Tắt" / "Đang khởi động" / "Đang chạy"
  - Log progress mỗi 15s (VM) và 10s (ADB) để user biết vẫn đang chờ
  - Log timeout cuối cùng với status cuối cùng để debug
  - Update tất cả caller để pass `post.log` hoặc `self.log`

- **User experience sau:**
  ```
  [14:38:05] ⏳ Chờ máy ảo 'test1' khởi động hoàn toàn...
  [14:38:07]    📊 VM status: Đang khởi động (sau 2s)
  [14:38:12]    📊 VM status: Đang chạy (sau 7s)
  [14:38:12] ✅ Máy ảo đã sẵn sàng (sau 7s)
  [14:38:12] ⏳ Chờ ADB kết nối...
  [14:38:14] ✅ ADB đã kết nối (sau 2s)
  ```
  → Rõ ràng từng bước!

**Lý do:**
- User cần biết VM đang ở trạng thái nào
- Debug dễ hơn: Biết VM bị stuck ở status nào (0, 1, 2)
- Tránh confusion: "App có bị đơ không?"
- UX tốt hơn: Thấy progress realtime

**Impact:**
- ✅ Thấy VM status changes realtime
- ✅ Biết khi nào timeout và status cuối là gì
- ✅ Progress updates mỗi 10-15s
- ✅ Debug dễ hơn rất nhiều
- ✅ Không còn "2 phút im lặng"

**Code changes:**
- vm_manager.py:133-212: Update `wait_vm_ready()` với log_callback
- vm_manager.py:215-281: Update `wait_adb_ready()` với log_callback
- tab_post.py:551, 559: Pass `log_callback=post.log`
- tab_follow.py:519, 540: Pass `log_callback=self.log`

---

### [2025-11-13] - v1.5.1 - Fix table order preservation after bulk operations
**File thay đổi:**
- `tabs/tab_post.py`

**Nội dung:**
- **🐛 Bug Fix:** Sau khi bulk schedule/assign VM, table nhảy về thứ tự ban đầu thay vì giữ nguyên thứ tự đã sort
- **User scenario:**
  - Import 6 videos: 1, 2, 3, 4, 5, 6
  - Set VM A cho 1-3: 1-A, 2-A, 3-A, 4, 5, 6
  - Sort theo VM → UI: 4, 5, 6, 1-A, 2-A, 3-A
  - Bulk assign VM B cho video 2-3 (tức 5, 6)
  - **Bug trước:** Gán đúng (5-B, 6-B) nhưng table nhảy về: 1-A, 2-A, 3-A, 4, 5-B, 6-B
  - **Mong muốn:** Giữ nguyên thứ tự sort: 4, 5-B, 6-B, 1-A, 2-A, 3-A

- **Nguyên nhân:**
  - Sau bulk operations, code gọi `self.load_posts_to_table()` (không tham số)
  - `auto_sort=False` (mặc định) → Load từ `self.posts` (thứ tự gốc)
  - Không giữ được thứ tự đã sort

- **Fix:**
  - Sau bulk operations: `self.posts = self.displayed_posts` (cập nhật thứ tự gốc)
  - Sau đó: `self.load_posts_to_table(auto_sort=False)` (giữ nguyên thứ tự)
  - Áp dụng cho cả `bulk_schedule()` và `bulk_assign_vm()`

**Lý do:**
- User đã chọn sort theo tiêu chí nào đó (VM/time/status/name)
- Sau khi bulk operations, phải giữ nguyên thứ tự đó
- Tránh confusion khi table tự động nhảy về thứ tự ban đầu

**Impact:**
- ✅ Giữ nguyên thứ tự sort sau bulk schedule
- ✅ Giữ nguyên thứ tự sort sau bulk assign VM
- ✅ Thứ tự gốc (`self.posts`) được cập nhật theo UI
- ✅ UX tốt hơn: Table không nhảy lung tung

**Code changes:**
- Line 1754-1756: Update `self.posts` và reload với `auto_sort=False` trong `bulk_schedule()`
- Line 2007-2009: Update `self.posts` và reload với `auto_sort=False` trong `bulk_assign_vm()`

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