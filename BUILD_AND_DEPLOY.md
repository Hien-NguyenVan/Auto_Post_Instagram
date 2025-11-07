# 📦 Hướng Dẫn Build và Deploy Instagram Automation Tool

## 🎯 Tổng quan

Dự án này được thiết kế để build thành **portable package** có thể chạy trên bất kỳ máy Windows nào (có Python 3.10+ và LDPlayer).

**2 file EXE chính:**
- **main.exe** - Chạy tool Instagram automation
- **updater.exe** - Auto-update code từ GitHub

---

## 📋 Yêu Cầu Trước Khi Build

### Trên máy development:

```bash
# 1. Python 3.10+ đã cài
python --version

# 2. Cài PyInstaller
pip install pyinstaller

# 3. Cài tất cả dependencies
pip install -r requirements.txt
```

---

## 🔨 BƯỚC 1: Build Portable Package

### Chạy build script:

```bash
python build_package.py
```

Script sẽ:
1. ✅ Kiểm tra PyInstaller đã cài chưa
2. ✅ Clean build cũ
3. ✅ Build `main.exe` (GUI mode)
4. ✅ Build `updater.exe` (Console mode)
5. ✅ Tạo cấu trúc folder portable
6. ✅ Copy files cần thiết
7. ✅ Generate README.txt
8. ✅ (Optional) Tạo ZIP file

### Kết quả:

```
dist/
└── InstagramTool_Portable/
    ├── main.exe              ← Chạy tool chính
    ├── updater.exe           ← Update từ GitHub
    ├── config.py
    ├── constants.py
    ├── requirements.txt
    ├── version.txt
    ├── core/
    ├── tabs/
    ├── utils/
    ├── data/
    │   └── api/
    │       └── youtube.txt   ← API placeholder
    ├── logs/
    ├── temp/
    ├── downloads/
    ├── backups/
    └── README.txt
```

---

## 🌐 BƯỚC 2: Setup GitHub Repository

### 2.1. Tạo GitHub repo mới (nếu chưa có):

1. Truy cập https://github.com/new
2. Tạo repo tên: `instagram-automation-tool` (hoặc tên khác)
3. Chọn **Private** nếu không muốn public

### 2.2. Setup Git local (trong thư mục tool):

```bash
# Khởi tạo git repo
git init

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/instagram-automation-tool.git

# Add files
git add .

# Commit
git commit -m "Initial commit - Instagram Automation Tool v1.0"

# Push lần đầu
git push -u origin main
```

**Lưu ý:** Tạo file `.gitignore` đã có sẵn để tránh commit data/logs/temp

---

## 📤 BƯỚC 3: Distribute Package

### Option 1: Trực tiếp copy folder

Copy toàn bộ folder `dist/InstagramTool_Portable/` sang máy đích.

### Option 2: Qua ZIP file

```bash
# Build script có option tạo ZIP
# Hoặc tạo manual:
cd dist
7z a InstagramTool_v1.0.zip InstagramTool_Portable/
```

Upload ZIP lên:
- Google Drive / Dropbox (share link)
- GitHub Releases
- File hosting khác

---

## 🚀 BƯỚC 4: Cài Đặt Trên Máy Đích

### 4.1. Giải nén package (nếu dùng ZIP)

### 4.2. Cài dependencies:

```bash
cd InstagramTool_Portable
pip install -r requirements.txt
```

### 4.3. Setup Git cho auto-update:

```bash
# Khởi tạo git
git init

# Add remote (replace với repo của bạn)
git remote add origin https://github.com/YOUR_USERNAME/instagram-automation-tool.git

# Pull code
git pull origin main
```

### 4.4. Cấu hình LDPlayer path (nếu cần):

Nếu tool không tự detect được LDPlayer:

```txt
# Tạo file: ldplayer_path.txt
# Nội dung:
C:\LDPlayer\LDPlayer9
```

### 4.5. Chạy tool:

```bash
# Double-click main.exe
# Hoặc:
main.exe
```

---

## 🔄 BƯỚC 5: Update Code

### Khi bạn sửa code:

```bash
# 1. Commit changes
git add .
git commit -m "Fix bug / Add feature"

# 2. Push lên GitHub
git push origin main
```

### User update trên máy đích:

```bash
# Chỉ cần chạy:
updater.exe

# Hoặc manual:
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 🛠️ Troubleshooting

### ❌ PyInstaller build lỗi "Module not found"

```bash
# Thêm hidden-import vào build_package.py:
"--hidden-import=MODULE_NAME"
```

### ❌ main.exe crash khi chạy

```bash
# Test bằng console mode để xem lỗi:
python main.py

# Check logs:
logs/app.log
```

### ❌ updater.exe báo "Git not found"

Cài Git:
- https://git-scm.com/download/win
- Chọn "Add to PATH" khi cài

### ❌ LDPlayer not found

Tạo file `ldplayer_path.txt` với đường dẫn LDPlayer.

---

## 📝 Version Management

### Bump version:

```bash
# Edit version.txt
echo "v1.1.0" > version.txt

# Commit
git add version.txt
git commit -m "Bump version to v1.1.0"
git push
```

### Create GitHub Release (Optional):

1. Vào GitHub repo → Releases → New Release
2. Tag: `v1.1.0`
3. Upload ZIP file
4. Write release notes

---

## 🎉 Done!

Bạn đã có:
- ✅ Tool chạy portable (main.exe)
- ✅ Auto-updater (updater.exe)
- ✅ GitHub repo để distribute updates
- ✅ Hướng dẫn đầy đủ cho user

**Next steps:**
1. Test package trên máy khác (không có Python/dependencies)
2. Document các features trong README.txt
3. Setup GitHub Releases cho version management
4. (Optional) Tạo website/landing page

---

## 📞 Support

Nếu có vấn đề, tạo issue trên GitHub:
- https://github.com/YOUR_USERNAME/instagram-automation-tool/issues
