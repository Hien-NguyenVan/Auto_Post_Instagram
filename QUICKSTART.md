# ⚡ Quick Start Guide - Instagram Automation Tool

## 🎯 Mục đích: Build portable package trong 5 phút

---

## 🚀 BƯỚC 1: Cài Đặt Dependencies (3 phút)

```bash
# Cài PyInstaller
pip install pyinstaller

# Cài tất cả dependencies
pip install -r requirements.txt
```

---

## ✅ BƯỚC 2: Test Config (1 phút)

```bash
# Chạy test script
python test_config.py
```

**Kết quả mong đợi:**
```
✅ config.py imported successfully
✅ LDPlayer detected at: C:\LDPlayer\LDPlayer9
✅ ldconsole.exe found
✅ adb.exe found
✅ All directories created
✅ All dependencies installed

🎉 All tests passed! Ready to build package.
```

**Nếu có lỗi:** Xem phần [Troubleshooting](#troubleshooting) bên dưới.

---

## 🔨 BƯỚC 3: Build Package (1 phút)

```bash
# Chạy build script
python build_package.py
```

**Quá trình build:**
```
🔨 Building main.exe (GUI)...        [~30s]
🔨 Building updater.exe (Console)... [~15s]
📦 Tạo cấu trúc package...
📝 Tạo README.txt...
📦 Tạo ZIP file? (optional)

🎉 BUILD THÀNH CÔNG!
```

**Output:** `dist/InstagramTool_Portable/`

---

## 🎉 XONG! Package đã sẵn sàng

```
dist/InstagramTool_Portable/
├── main.exe        ← Chạy tool
├── updater.exe     ← Update code
├── README.txt      ← Hướng dẫn cho user
└── ...
```

---

## 📤 BƯỚC 4: Distribute

### Option A: Copy trực tiếp
```bash
# Copy folder sang máy khác
xcopy /E /I dist\InstagramTool_Portable E:\USB\InstagramTool
```

### Option B: Upload lên Drive
1. Zip folder (nếu build script chưa tạo)
2. Upload lên Google Drive / Dropbox
3. Share link với users

---

## 🌐 BƯỚC 5: Setup GitHub (cho auto-update)

### Lần đầu (trên máy dev):

```bash
# 1. Tạo repo trên GitHub: https://github.com/new
#    Tên: instagram-automation-tool
#    Visibility: Private (hoặc Public)

# 2. Init git local
git init
git remote add origin https://github.com/YOUR_USERNAME/instagram-automation-tool.git

# 3. Push code
git add .
git commit -m "Initial commit - Instagram Tool v1.0"
git push -u origin main
```

### Trên máy user (để enable auto-update):

```bash
cd InstagramTool_Portable

# Init git
git init
git remote add origin https://github.com/YOUR_USERNAME/instagram-automation-tool.git
git pull origin main

# Giờ updater.exe sẽ hoạt động!
```

---

## 🎯 Workflow Hàng Ngày

### Developer (bạn):
```bash
# 1. Sửa code
code tabs/tab_post.py

# 2. Test
python main.py

# 3. Push
git add .
git commit -m "Add new feature"
git push
```

### User:
```bash
# Chỉ cần double-click:
updater.exe

# Hoặc:
main.exe  # Tool sẽ thông báo nếu có update mới (optional)
```

---

## 🐛 Troubleshooting

### ❌ Test fails: "LDPlayer NOT detected"

**Fix 1:** Tạo file `ldplayer_path.txt`:
```bash
echo C:\LDPlayer\LDPlayer9 > ldplayer_path.txt
```

**Fix 2:** Set environment variable:
```bash
setx LDPLAYER_PATH "C:\LDPlayer\LDPlayer9"
```

**Fix 3:** Install LDPlayer:
- https://www.ldplayer.net/

---

### ❌ Build fails: "PyInstaller not found"

```bash
pip install pyinstaller
```

---

### ❌ Build fails: "Module not found"

```bash
# Cài đầy đủ dependencies
pip install -r requirements.txt

# Nếu vẫn lỗi, thêm vào build_package.py:
"--hidden-import=MODULE_NAME"
```

---

### ❌ main.exe crashes khi chạy

**Debug:**
```bash
# Chạy bằng Python để xem lỗi
python main.py

# Xem log
type logs\app.log
```

---

### ❌ updater.exe báo "Git not found"

**Cài Git:**
- https://git-scm.com/download/win
- ✅ Check option "Add to PATH"

---

## 📋 Checklist Trước Khi Distribute

- [ ] ✅ `python test_config.py` PASS
- [ ] ✅ `python build_package.py` SUCCESS
- [ ] ✅ Test `main.exe` trên máy dev
- [ ] ✅ Setup GitHub repo
- [ ] ✅ Push code lên GitHub
- [ ] ✅ Test `updater.exe` trên máy dev
- [ ] ✅ Tạo ZIP / Copy package
- [ ] ✅ Test trên máy khác (nếu có)
- [ ] ✅ Document GitHub repo URL trong README.txt

---

## 🎁 Bonus: One-Liner Commands

```bash
# Full build pipeline
pip install pyinstaller && python test_config.py && python build_package.py

# Quick rebuild (nếu đã có dependencies)
python build_package.py

# Test + Build + Push
python test_config.py && python build_package.py && git add . && git commit -m "Build v1.0" && git push
```

---

## 📚 Tài Liệu Đầy Đủ

- **BUILD_AND_DEPLOY.md** - Chi tiết về build & deployment
- **README.txt** (trong package) - Hướng dẫn cho end-user
- **config.py** - Source code với comments đầy đủ

---

## 🎯 Next Steps

1. ✅ Build package
2. ✅ Test trên máy dev
3. ✅ Setup GitHub
4. 🚀 Distribute cho users
5. 📝 Thu thập feedback
6. 🔄 Update và improve

---

**🎊 Happy Building!**

Có vấn đề gì, check BUILD_AND_DEPLOY.md hoặc create issue trên GitHub.
