import os
import json
import re
import subprocess
import threading
import time
import logging
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk  # For Treeview only
import customtkinter as ctk
from ui_theme import *

from utils.login import InstagramLogin
from config import LDCONSOLE_EXE, CONFIG_DIR, ADB_EXE, DATA_DIR
from constants import (
    WAIT_SHORT, WAIT_MEDIUM, TIMEOUT_EXTENDED,
    MAX_RETRY_VM_STATUS, VM_STATUS_CHECK_INTERVAL,
    DEFAULT_VM_RESOLUTION, DEFAULT_VM_CPU, DEFAULT_VM_MEMORY,
    DEFAULT_VM_DEVICES_NAME, DEFAULT_VM_DEVICES_MODEL,
    ADB_DEBUG_SETTING
)

os.makedirs(DATA_DIR, exist_ok=True)


class UsersTab(ctk.CTkFrame):
    """Users Tab - Modern Windows 11 Style"""

    # Danh sách tên file JSON dành riêng (không phải VM) trong thư mục data/
    RESERVED_FILENAMES = ["scheduled_posts"]  # streams và apis nằm trong subfolder nên không bị conflict

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.logger = logging.getLogger(__name__)
        self.login_handler = InstagramLogin(log_callback=self.write_log)

        # Dictionary để lưu checkbox của từng máy ảo
        self.checkboxes = {}
        self.checkbox_vars = {}
        self.vm_logs = {}
        self.vm_logs_lock = threading.Lock()  # Thread safety for vm_logs

        # ====== BẢNG TÀI KHOẢN (Treeview) ======
        # Apply CustomTkinter theme
        apply_ctk_theme()

        table_outer = ctk.CTkFrame(self, fg_color="transparent")
        table_outer.pack(fill="both", expand=True, padx=DIMENSIONS["spacing_md"], pady=(DIMENSIONS["spacing_sm"], DIMENSIONS["spacing_md"]))

        # Title
        table_title = ctk.CTkLabel(
            table_outer,
            text="📋 Danh Sách Máy Ảo & Tài Khoản",
            font=(FONTS["family"], FONTS["size_medium"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        )
        table_title.pack(anchor="w", pady=(0, DIMENSIONS["spacing_xs"]))

        table_frame = ctk.CTkFrame(table_outer, **get_frame_style("panel"))
        table_frame.pack(fill="both", expand=True)

        wrap = ctk.CTkFrame(table_frame, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        cols = ("check","stt","vm","insta","user","pass","tfa","port","status","log","toggle","login","delete")

        # Apply ttk style for Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background=COLORS["bg_secondary"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_secondary"],
            borderwidth=0,
            font=(FONTS["family"], FONTS["size_normal"])
        )
        style.configure("Treeview.Heading",
            background=COLORS["surface_3"],
            foreground=COLORS["text_primary"],
            borderwidth=1,
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"])
        )
        style.map("Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["text_on_accent"])]
        )

        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=10)

        # Configure alternating row colors (striped)
        self.tree.tag_configure("oddrow", background=COLORS["surface_2"])
        self.tree.tag_configure("evenrow", background=COLORS["bg_secondary"])

        # Header
        self.select_all_var = tk.BooleanVar(value=False)
        self.tree.heading("check", text="☐ ALL")
        self.tree.heading("stt",    text="STT")
        self.tree.heading("vm",     text="VM Name")
        self.tree.heading("insta",  text="Insta Name")
        self.tree.heading("user",   text="Username")
        self.tree.heading("pass",   text="Password")
        self.tree.heading("tfa",    text="2FA")
        self.tree.heading("port",   text="Port")
        self.tree.heading("status", text="Status")
        self.tree.heading("log",    text="Log")
        
        self.tree.heading("toggle", text="Chạy/Tắt")
        self.tree.heading("login",  text="Login")
        self.tree.heading("delete", text="Xóa")

        # Width & align (đồng bộ, không lệch)
        self.tree.column("check", width=70, anchor="center")
        self.tree.column("stt",    width=40,  anchor="center")
        self.tree.column("vm",     width=150)
        self.tree.column("insta",  width=150)
        self.tree.column("user",   width=160)
        self.tree.column("pass",   width=140)
        self.tree.column("tfa",    width=80,  anchor="center")
        self.tree.column("port",   width=80,  anchor="center")
        self.tree.column("status", width=140, anchor="center")
        self.tree.column("log",    width=70,  anchor="center")
        
        self.tree.column("toggle", width=90,  anchor="center")
        self.tree.column("login",  width=80,  anchor="center")
        self.tree.column("delete", width=70,  anchor="center")

        # Scrollbar
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Bắt click theo cột hành động
        self.tree.bind("<Button-1>", self.on_tree_click_users)

        # Thanh nút dưới bảng - Modern Windows 11 Style
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=DIMENSIONS["spacing_md"], pady=(0, DIMENSIONS["spacing_md"]))

        ctk.CTkButton(
            btn_frame,
            text="🔄 Tải danh sách",
            command=self.refresh_list,
            **get_button_style("primary"),
            width=140
        ).pack(side="left", padx=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            btn_frame,
            text="➕ Thêm máy ảo",
            command=self.add_vm,
            **get_button_style("success"),
            width=140
        ).pack(side="left", padx=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            btn_frame,
            text="📦 Cài ứng dụng",
            command=self.install_app_to_selected,
            **get_button_style("primary"),
            width=140
        ).pack(side="left", padx=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            btn_frame,
            text="📋 Copy máy ảo",
            command=self.copy_vm,
            **get_button_style("secondary"),
            width=140
        ).pack(side="left", padx=DIMENSIONS["spacing_sm"])

        self.selected_count_label = ctk.CTkLabel(
            btn_frame,
            text="Đã chọn: 0 máy ảo",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            text_color=COLORS["accent"]
        )
        self.selected_count_label.pack(side="left", padx=DIMENSIONS["spacing_lg"])

        # Nạp dữ liệu
        self.refresh_list()

    # === Helpers (UI & device id) ===
    def _ui(self, func, *args, **kwargs):
        """Chạy cập nhật UI an toàn trên main thread."""
        try:
            self.after(0, func, *args, **kwargs)
        except Exception:
            pass

    @staticmethod
    def to_device_id(port: str) -> str:
        """Chuẩn hóa device id 'emulator-<port>' từ port dạng '5554'."""
        p = (port or "").strip()
        return f"emulator-{p}" if p.isdigit() else ""

    def modify_vm_config(self, vm_id, vm_name, add_adb_debug=False, set_root_mode=False):
        """
        Modify VM config file to set device model and manufacturer.
        Optionally add ADB debug setting and enable root mode.

        Args:
            vm_id: VM ID (e.g., "0", "1", "6")
            vm_name: VM name for logging
            add_adb_debug: If True, add ADB debug setting
            set_root_mode: If True, set rootMode to true
        """
        try:
            config_path = os.path.join(CONFIG_DIR, f"leidian{vm_id}.config")

            if not os.path.exists(config_path):
                self.logger.warning(f"Config file not found: {config_path}")
                return False

            # Read config file
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace phoneModel
            if '"propertySettings.phoneModel"' in content:
                # Find and replace the phoneModel value
                content = re.sub(
                    r'"propertySettings\.phoneModel":\s*"[^"]*"',
                    f'"propertySettings.phoneModel": "{DEFAULT_VM_DEVICES_MODEL}"',
                    content
                )
                self.logger.info(f"Updated phoneModel to {DEFAULT_VM_DEVICES_MODEL}")

            # Replace phoneManufacturer
            if '"propertySettings.phoneManufacturer"' in content:
                content = re.sub(
                    r'"propertySettings\.phoneManufacturer":\s*"[^"]*"',
                    f'"propertySettings.phoneManufacturer": "{DEFAULT_VM_DEVICES_NAME}"',
                    content
                )
                self.logger.info(f"Updated phoneManufacturer to {DEFAULT_VM_DEVICES_NAME}")

            # Set root mode to true if requested
            if set_root_mode and '"basicSettings.rootMode"' in content:
                content = re.sub(
                    r'"basicSettings\.rootMode":\s*(false|true)',
                    '"basicSettings.rootMode": true',
                    content
                )
                self.logger.info("Enabled root mode (set to true)")

            # Add ADB Debug if requested and not exists
            if add_adb_debug and '"basicSettings.adbDebug"' not in content:
                # Insert after opening brace
                lines = content.splitlines(keepends=True)
                if lines and lines[0].strip() == "{":
                    lines.insert(1, "\n")
                    lines.insert(2, f"    {ADB_DEBUG_SETTING}\n")
                    content = "".join(lines)
                    self.logger.info("Added ADB Debug setting")

            # Write back
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Successfully modified config for VM {vm_name} (ID: {vm_id})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to modify config for VM {vm_name}: {e}")
            return False

    # ======= Chọn tất cả / Bỏ chọn tất cả =======
    # def toggle_select_all(self):
    #     select_state = self.select_all_var.get()
    #     for var in self.checkbox_vars.values():
    #         var.set(select_state)
    #     self.update_selected_count()

    # ======= Cập nhật số lượng đã chọn =======
    def update_selected_count(self):
        count = sum(1 for var in self.checkbox_vars.values() if var.get())
        self.selected_count_label.configure(text=f"Đã chọn: {count} máy ảo")

    # ======= Load / Refresh danh sách =======
    # Sửa lại refresh_list
    def refresh_list(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self.checkbox_vars = {}

        # Lấy tất cả VM từ LDPlayer list2
        all_vms = self.get_ld_list_full()  # [(id, name, status), ...]

        # Kiểm tra và tạo file JSON cho các VM chưa có
        for vm_id, vm_name, status in all_vms:
            # Bỏ qua nếu tên VM trùng với file JSON đặc biệt
            if vm_name in self.RESERVED_FILENAMES:
                self.logger.warning(f"VM name '{vm_name}' is reserved. Skipping JSON creation.")
                continue

            json_path = os.path.join(DATA_DIR, f"{vm_name}.json")

            # Nếu chưa có file JSON, tạo mới
            if not os.path.exists(json_path):
                self.logger.info(f"Creating new JSON file for VM: {vm_name} (ID: {vm_id})")
                new_data = {
                    "id": vm_id,
                    "vm_name": vm_name,
                    "insta_name": "",
                    "username": "",
                    "password": "",
                    "2fa": "",
                    "port": ""
                }
                try:
                    with open(json_path, "w", encoding="utf-8") as fp:
                        json.dump(new_data, fp, ensure_ascii=False, indent=2)
                except Exception as e:
                    self.logger.error(f"Failed to create JSON for {vm_name}: {e}")
                    continue

        # Hiển thị tất cả VM (bỏ qua các VM có tên reserved)
        displayed_vms = [(vm_id, vm_name, status_txt) for vm_id, vm_name, status_txt in all_vms
                         if vm_name not in self.RESERVED_FILENAMES]

        for idx, (vm_id, vm_name, status_txt) in enumerate(displayed_vms, start=1):
            json_path = os.path.join(DATA_DIR, f"{vm_name}.json")

            # Đọc thông tin từ file JSON
            try:
                with open(json_path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)

                insta = data.get("insta_name", "")
                username = data.get("username", "")
                password = data.get("password", "")
                tfa = data.get("2fa", "")
                port = str(data.get("port", ""))
            except Exception as e:
                self.logger.error(f"Failed to read JSON for {vm_name}: {e}")
                # Fallback nếu không đọc được
                insta = username = password = tfa = port = ""

            # Tạo biến checkbox cho từng VM
            self.checkbox_vars[vm_name] = tk.BooleanVar(value=False)

            # Thêm vào tree với icon checkbox và striped rows
            icon = "☑" if self.checkbox_vars[vm_name].get() else "☐"
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=vm_name,
                values=(icon, idx, vm_name, insta, username, password,
                        tfa, port, status_txt, "📋", "▶/■", "Login", "✖"),
                tags=(tag,))

        self.tree.heading("check", text="☑ Tất cả" if self.select_all_var.get() else "☐ Tất cả")
        self.update_selected_count()


    # Sửa lại on_tree_click_users
    def on_tree_click_users(self, event):
        region = self.tree.identify("region", event.x, event.y)
        
        # Click vào header "Tất cả" để toggle all
        if region == "heading":
            col_id = self.tree.identify_column(event.x)
            if col_id == "#1":  # Cột checkbox
                self.toggle_select_all()
            return
        
        if region != "cell":
            return
            
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not row_id or not col_id:
            return

        col = self.tree["columns"][int(col_id[1:]) - 1]

        # Xử lý click vào checkbox
        if col == "check":
            var = self.checkbox_vars.get(row_id)
            if var:
                var.set(not var.get())
                # Cập nhật icon
                new_icon = "☑" if var.get() else "☐"
                self.tree.set(row_id, "check", new_icon)
                self.update_selected_count()
            return
        
        # Các cột hành động khác giữ nguyên
        if col == "log":
            self.open_log_window(row_id)
        elif col == "toggle":
            status_now = self.tree.set(row_id, "status") or "Tắt"
            if status_now == "Bật":
                self.quit_vm(row_id)
            else:
                self.launch_vm(row_id)

        elif col == "login":
            self.login_vm(row_id)
        elif col == "delete":
            self.delete_vm(row_id)

    # Thêm hàm toggle_select_all
    def toggle_select_all(self):
        new_state = not self.select_all_var.get()
        self.select_all_var.set(new_state)

        for vm_name, var in self.checkbox_vars.items():
            var.set(new_state)
            self.tree.set(vm_name, "check", "☑" if new_state else "☐")

        self.tree.heading("check", text="☑ Tất cả" if new_state else "☐ Tất cả")
        self.update_selected_count()



    # def write_log(self, vm_name, msg):
    #     self.vm_logs.setdefault(vm_name, []).append(msg)
    #     if hasattr(self, "log_windows") and vm_name in self.log_windows:
    #         w = self.log_windows[vm_name]
    #         if w.winfo_exists() and hasattr(w, "append_log"):
    #             w.append_log(msg)


    def open_log_window(self, vm_name):
        if not hasattr(self, "log_windows"):
            self.log_windows = {}

        # Nếu cửa sổ log đã mở rồi thì focus lại
        if vm_name in self.log_windows and self.log_windows[vm_name].winfo_exists():
            self.log_windows[vm_name].focus()
            return

        # Tạo cửa sổ mới
        log_win = tk.Toplevel()
        log_win.title(f"Log - {vm_name}")
        log_win.geometry("600x400")

        # Frame chứa text và nút xóa
        top_frame = ttk.Frame(log_win)
        top_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(top_frame, text=f"Lịch sử log của {vm_name}", 
                font=("Segoe UI", 10, "bold")).pack(side="left")

        # Nút xóa log
        def clear_log():
            text_log.config(state="normal")
            text_log.delete("1.0", "end")
            text_log.config(state="disabled")
            self.vm_logs[vm_name] = []  # Xóa log trong bộ nhớ
            
        ttk.Button(top_frame, text="🗑️ Xóa lịch sử", 
                command=clear_log).pack(side="right", padx=5)

        # Text widget hiển thị log
        text_log = tk.Text(log_win, wrap="word", state="disabled", 
                        bg="#111", fg="#0f0", insertbackground="white")
        text_log.pack(fill="both", expand=True, padx=5, pady=5)

        # Hiển thị log đã lưu (nếu có)
        if vm_name in self.vm_logs:
            text_log.config(state="normal")
            for log_entry in self.vm_logs[vm_name]:
                text_log.insert("end", log_entry + "\n")
            text_log.see("end")
            text_log.config(state="disabled")

        # Lưu lại cửa sổ log và Text widget
        self.log_windows[vm_name] = log_win
        log_win.text_log = text_log

    def write_log(self, vm_name, message):
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"{timestamp} | {message}"

        # Lưu bộ nhớ (thread-safe)
        with self.vm_logs_lock:
            self.vm_logs.setdefault(vm_name, []).append(log_entry)

        # Log to file as well
        self.logger.info(f"[{vm_name}] {message}")

        # Nếu cửa sổ log đang mở → cập nhật an toàn bằng _ui
        if hasattr(self, "log_windows") and vm_name in self.log_windows:
            log_win = self.log_windows[vm_name]
            if log_win.winfo_exists():
                def _append():
                    text_log = log_win.text_log
                    text_log.config(state="normal")
                    text_log.insert("end", log_entry + "\n")
                    text_log.see("end")
                    text_log.config(state="disabled")
                self._ui(_append)



    # ======= Cài ứng dụng cho các máy đã chọn =======
    def install_app_to_selected(self):
        # Lấy danh sách máy được chọn
        selected_vms = [vm_name for vm_name, var in self.checkbox_vars.items() if var.get()]
        
        if not selected_vms:
            messagebox.showwarning("Chưa chọn máy ảo", 
                                  "Vui lòng chọn ít nhất một máy ảo từ danh sách!")
            return
        
        # Chọn file APK/XAPK
        apk_path = filedialog.askopenfilename(
            title="Chọn file cài đặt (APK/XAPK)",
            filetypes=[("Android App Package", "*.apk *.xapk"), ("All files", "*.*")]
        )
        
        if not apk_path:
            return
        
        # Xác nhận cài đặt
        confirm = messagebox.askyesno(
            "Xác nhận cài đặt",
            f"Bạn có chắc muốn cài {os.path.basename(apk_path)}\nvào {len(selected_vms)} máy ảo đã chọn?"
        )
        
        if not confirm:
            return
        
        # Cài đặt song song bằng threading
        messagebox.showinfo("Đang cài đặt", 
                           f"Đang cài {os.path.basename(apk_path)} vào {len(selected_vms)} máy ảo...")
        
        for vm_name in selected_vms:
            # Đọc dữ liệu cũ từ JSON (nếu có)
            path = os.path.join(DATA_DIR, f"{vm_name}.json")
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    port = str(data.get("port", "")).strip()   # chỉ lưu số, vd "5554"
                    if not port.isdigit():
                        self.write_log(vm_name, "⚠️ Port rỗng hoặc không hợp lệ trong JSON.")
                        continue
                    device = self.to_device_id(port)
            except Exception as e:
                self.logger.error(f"Error reading VM config for {vm_name}: {e}")
            threading.Thread(
                target=self.install_apk_to_vm,
                args=(vm_name, device, apk_path),
                daemon=True
            ).start()

    def install_apk_to_vm(self, vm_name, device, apk_path):
        try:
            if not device or not device.startswith("emulator-"):
                self.write_log(vm_name, f"⚠️ Device id không hợp lệ: {device}")
                return

            self.write_log(vm_name, f"⏳ Đang cài {os.path.basename(apk_path)}...")
            cmd = [ADB_EXE, "-s", device, "install", "-r", apk_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.stdout:
                self.write_log(vm_name, f"📝 Output: {result.stdout.strip()}")
            if result.stderr:
                self.write_log(vm_name, f"⚠️ Error: {result.stderr.strip()}")

            if result.returncode == 0:
                self.write_log(vm_name, f"✅ Cài thành công {os.path.basename(apk_path)}")
            else:
                self.write_log(vm_name, f"❌ Lỗi (code {result.returncode}) khi cài ứng dụng")

        except subprocess.TimeoutExpired:
            self.write_log(vm_name, f"⏱️ Timeout khi cài ứng dụng")
        except Exception as e:
            self.write_log(vm_name, f"❌ Lỗi khi cài: {e}")


    # ======= Hàm thêm máy ảo =======
    def add_vm(self):
        # Tạo custom dialog để nhập tên
        dialog = tk.Toplevel(self)
        dialog.title("Thêm máy ảo")
        dialog.geometry("480x180")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Frame chính
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Label
        ttk.Label(main_frame, text="Tên máy ảo mới:",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        # Entry
        name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=50)
        name_entry.pack(fill=tk.X, pady=(0, 5))
        name_entry.focus()

        # Lưu ý
        ttk.Label(main_frame, text="⚠️ Lưu ý: Không đặt tên tiếng Việt hoặc có khoảng trắng",
                 font=("Segoe UI", 9), foreground="red").pack(anchor="w", pady=(0, 15))

        # Result storage
        result = {"vm_name": None}

        def on_submit():
            vm_name = name_var.get().strip()
            if not vm_name:
                messagebox.showwarning("Lỗi", "Vui lòng nhập tên máy ảo!", parent=dialog)
                return

            # Kiểm tra tên có phải là reserved filename không
            if vm_name in self.RESERVED_FILENAMES:
                messagebox.showerror("Tên không hợp lệ",
                    f"Tên '{vm_name}' là tên dành riêng của hệ thống!\n"
                    f"Vui lòng chọn tên khác!",
                    parent=dialog)
                return

            # Kiểm tra xem file .json tương ứng đã tồn tại chưa
            path = os.path.join(DATA_DIR, f"{vm_name}.json")
            if os.path.exists(path):
                messagebox.showerror("Tên đã tồn tại",
                    f"Máy ảo '{vm_name}' đã có trong dữ liệu.\n"
                    f"Vui lòng nhập tên khác!",
                    parent=dialog)
                return

            result["vm_name"] = vm_name
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="✅ Tạo", command=on_submit,
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Hủy", command=on_cancel,
                  width=15).pack(side=tk.LEFT, padx=5)

        # Chờ dialog đóng
        dialog.wait_window()

        vm_name = result["vm_name"]
        if not vm_name:
            return

        # === Tạo máy ảo thật trong LDPlayer ===
        try:
            subprocess.run([LDCONSOLE_EXE, "add", "--name", vm_name],
                        creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run([LDCONSOLE_EXE, "modify", "--name", vm_name,
                            "--resolution", DEFAULT_VM_RESOLUTION,
                            "--cpu", DEFAULT_VM_CPU,
                            "--memory", DEFAULT_VM_MEMORY],
                        creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)
            result = subprocess.run(
                [LDCONSOLE_EXE, "list2"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            vm_id = None
            for line in result.stdout.strip().splitlines():
                parts = line.split(",")
                if len(parts) >= 2 and parts[1].strip() == vm_name:
                    vm_id = parts[0].strip()
                    break

            if vm_id:
                # Modify config: Add ADB Debug + Enable Root Mode + Change device model/manufacturer
                self.modify_vm_config(vm_id, vm_name, add_adb_debug=True, set_root_mode=True)
            else:
                self.logger.warning(f"Cannot determine VM ID for {vm_name}. Skipping config modification.")


            messagebox.showinfo("Thành công",
                                f"Đã tạo máy ảo {vm_name}")
        except Exception as e:
            self.logger.exception(f"Error creating VM {vm_name}")
            messagebox.showerror("Lỗi", f"Không thể tạo máy ảo mới:\n{e}")
            return

        # === Lưu dữ liệu vào data/ ===
        data = {
            "id":vm_id,
            "vm_name": vm_name,
            "insta_name": "",
            "username": "",
            "password": "",
            "2fa": "",
            "port":""
        }
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)

        self.refresh_list()

    # ======= Hàm copy máy ảo =======
    def copy_vm(self):
        """Copy máy ảo với logic đơn giản"""

        # Lấy danh sách VM hiện có từ LDPlayer
        all_vms = self.get_ld_list_full()  # [(id, name, status), ...]

        if not all_vms:
            messagebox.showwarning("Copy máy ảo", "Không có máy ảo nào trong hệ thống!")
            return

        vm_names = [vm[1] for vm in all_vms]  # Lấy danh sách tên VM

        # Tạo dialog chọn VM nguồn và nhập tên mới
        dialog = tk.Toplevel(self)
        dialog.title("Copy máy ảo")
        dialog.geometry("520x260")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Frame chính
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Chọn VM nguồn
        ttk.Label(main_frame, text="Chọn máy ảo để copy:",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        source_var = tk.StringVar()
        source_combo = ttk.Combobox(main_frame, textvariable=source_var,
                                    values=vm_names, state="readonly", width=55)
        source_combo.pack(fill=tk.X, pady=(0, 15))
        if vm_names:
            source_combo.current(0)

        # Nhập tên VM mới
        ttk.Label(main_frame, text="Tên máy ảo mới:",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))

        new_name_var = tk.StringVar()
        new_name_entry = ttk.Entry(main_frame, textvariable=new_name_var, width=57)
        new_name_entry.pack(fill=tk.X, pady=(0, 5))
        new_name_entry.focus()

        # Lưu ý
        ttk.Label(main_frame, text="⚠️ Lưu ý: Không đặt tên tiếng Việt hoặc có khoảng trắng",
                 font=("Segoe UI", 9), foreground="red").pack(anchor="w", pady=(0, 15))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        def do_copy():
            source_vm = source_var.get()
            new_vm = new_name_var.get().strip()

            if not source_vm:
                messagebox.showwarning("Lỗi", "Vui lòng chọn máy ảo nguồn!", parent=dialog)
                return

            if not new_vm:
                messagebox.showwarning("Lỗi", "Vui lòng nhập tên máy ảo mới!", parent=dialog)
                return

            # Kiểm tra tên có phải là reserved filename không
            if new_vm in self.RESERVED_FILENAMES:
                messagebox.showerror("Tên không hợp lệ",
                    f"Tên '{new_vm}' là tên dành riêng của hệ thống!\n"
                    f"Vui lòng chọn tên khác.",
                    parent=dialog)
                return

            # Kiểm tra tên trùng với VM hiện có
            if new_vm in vm_names:
                messagebox.showerror("Lỗi",
                    f"Tên máy ảo '{new_vm}' đã tồn tại!\nVui lòng chọn tên khác.",
                    parent=dialog)
                return

            # Kiểm tra VM nguồn có đang chạy không
            source_status = None
            for vm_id, vm_name, status in all_vms:
                if vm_name == source_vm:
                    source_status = status
                    break

            if source_status == "Bật":
                messagebox.showwarning("Không thể copy",
                    f"Máy ảo '{source_vm}' đang chạy!\n\n"
                    f"Vui lòng tắt máy ảo trước khi copy.",
                    parent=dialog)
                return

            # Đóng dialog trước khi thực hiện
            dialog.destroy()

            # Thực hiện copy trong thread riêng
            def run_copy():
                try:
                    self.write_log(new_vm, f"🔄 Bắt đầu copy từ '{source_vm}'...")

                    # Chạy lệnh ldconsole copy
                    cmd = [LDCONSOLE_EXE, "copy", "--name", new_vm, "--from", source_vm]
                    self.logger.info(f"Executing: {' '.join(cmd)}")

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore',
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=120
                    )

                    self.logger.info(f"Copy return code: {result.returncode}")
                    if result.stdout:
                        self.logger.info(f"Copy stdout: {result.stdout}")
                    if result.stderr:
                        self.logger.info(f"Copy stderr: {result.stderr}")

                    # Đợi một chút để LDPlayer xử lý
                    time.sleep(3)

                    # Kiểm tra xem VM mới đã được tạo chưa bằng cách query lại
                    verify_result = subprocess.run(
                        [LDCONSOLE_EXE, "list2"],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=10
                    )

                    vm_created = False
                    new_vm_id = None
                    for line in verify_result.stdout.splitlines():
                        parts = line.split(",")
                        if len(parts) >= 2 and parts[1].strip() == new_vm:
                            vm_created = True
                            new_vm_id = parts[0].strip()
                            break

                    if not vm_created:
                        # VM không được tạo - thực sự lỗi
                        error_msg = f"Lỗi khi copy máy ảo:\n\n"
                        error_msg += f"Return code: {result.returncode}\n"
                        if result.stdout:
                            error_msg += f"Output: {result.stdout}\n"
                        if result.stderr:
                            error_msg += f"Error: {result.stderr}\n"
                        error_msg += f"\nMáy ảo '{new_vm}' không được tạo."

                        self.write_log(new_vm, f"❌ {error_msg}")
                        self._ui(lambda: messagebox.showerror("Lỗi Copy", error_msg))
                        return

                    # VM đã được tạo - coi như thành công
                    self.write_log(new_vm, f"✅ Copy thành công từ '{source_vm}'")
                    self.logger.info(f"VM '{new_vm}' has been created successfully (ID: {new_vm_id})")

                    # Modify config: Change device model/manufacturer (KHÔNG thêm ADB Debug và Root Mode)
                    if new_vm_id:
                        self.write_log(new_vm, "🔧 Đang cập nhật cấu hình thiết bị...")
                        self.modify_vm_config(new_vm_id, new_vm, add_adb_debug=False, set_root_mode=False)
                    else:
                        self.logger.warning(f"Cannot determine VM ID for {new_vm}. Skipping config modification.")

                    # Refresh danh sách để tự động tạo file JSON
                    self._ui(self.refresh_list)

                    # Thông báo thành công
                    self._ui(lambda: messagebox.showinfo("Thành công",
                        f"Đã copy máy ảo '{source_vm}' thành '{new_vm}'"))

                except subprocess.TimeoutExpired:
                    self.write_log(new_vm, "⏱️ Timeout khi copy máy ảo!")
                    self._ui(lambda: messagebox.showerror("Lỗi", "Timeout khi copy máy ảo!"))
                except Exception as e:
                    self.logger.exception(f"Error copying VM")
                    self.write_log(new_vm, f"❌ Lỗi khi copy: {e}")
                    self._ui(lambda: messagebox.showerror("Lỗi", f"Không thể copy máy ảo:\n{e}"))

            # Chạy trong thread riêng để không block UI
            threading.Thread(target=run_copy, daemon=True).start()

        ttk.Button(btn_frame, text="✅ Copy", command=do_copy,
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Hủy", command=dialog.destroy,
                  width=15).pack(side=tk.LEFT, padx=5)

    # ===== Hàm bật/tắt =====
    def toggle_vm(self, name, status_label, btn_toggle):
        current = status_label.cget("text")
        if current == "Bật":
            self.quit_vm(name, status_label, btn_toggle)
        else:
            self.launch_vm(name, status_label, btn_toggle)

    def launch_vm(self, name, *_args):
        try:
            self.write_log(name, f"Bắt đầu bật máy ảo {name}...")
            subprocess.run([LDCONSOLE_EXE, "launch", "--name", name], creationflags=subprocess.CREATE_NO_WINDOW)
            self._ui(lambda: self.tree.set(name, "status", "Đang bật…"))
            threading.Thread(target=self.wait_status, args=(name, "Bật"), daemon=True).start()
        except Exception as e:
            self.logger.exception(f"Error launching VM {name}")
            self.write_log(name, f"Lỗi khi bật: {e}")
            messagebox.showerror("Lỗi", f"Không thể bật {name}:\n{e}")



    def quit_vm(self, name, *_args):
        try:
            self.write_log(name, f"Bắt đầu tắt máy ảo {name}...")
            subprocess.run([LDCONSOLE_EXE, "quit", "--name", name], creationflags=subprocess.CREATE_NO_WINDOW)
            self._ui(lambda: self.tree.set(name, "status", "Đang tắt…"))

            # Đóng log window + xóa log
            if hasattr(self, "log_windows") and name in self.log_windows:
                w = self.log_windows[name]
                if w.winfo_exists():
                    self._ui(w.destroy)
                del self.log_windows[name]

            with self.vm_logs_lock:
                self.vm_logs.pop(name, None)

            threading.Thread(target=self.wait_status, args=(name, "Tắt"), daemon=True).start()
        except Exception as e:
            self.logger.exception(f"Error quitting VM {name}")
            self.write_log(name, f"Lỗi khi tắt: {e}")
            messagebox.showerror("Lỗi", f"Không thể tắt {name}:\n{e}")



    def wait_status(self, name, target):
        # target: "Bật" hoặc "Tắt"
        wait_text = "Đang bật…" if target == "Bật" else "Đang tắt…"
        self._ui(lambda: self.tree.set(name, "status", wait_text))

        for _ in range(MAX_RETRY_VM_STATUS):
            time.sleep(VM_STATUS_CHECK_INTERVAL)
            for n, s in self.get_ld_list():
                if n == name:
                    if s == target:
                        self._ui(lambda: self.tree.set(name, "status", s))
                        self.write_log(name, f"{'Bật' if target=='Bật' else 'Tắt'} máy thành công")
                        return
                    break

        self._ui(lambda: self.tree.set(name, "status", "Không xác định"))
        self.write_log(name, f"Timeout khi chờ máy {target.lower()}")
        self.logger.warning(f"VM {name} status timeout waiting for {target}")



    # ===== Lấy trạng thái LDPlayer =====
    def get_ld_list(self):
        """Legacy function - trả về (name, status)"""
        try:
            output = subprocess.check_output([LDCONSOLE_EXE, "list2"],
                                            text=True, encoding="utf-8")
            devices = []
            for line in output.strip().splitlines():
                parts = line.split(",")
                if len(parts) >= 5:
                    name = parts[1]
                    status = "Bật" if parts[4] == "1" else "Tắt"
                    devices.append((name, status))
            return devices
        except Exception as e:
            self.logger.error(f"Error getting LDPlayer list: {e}")
            return []

    def get_ld_list_full(self):
        """
        Lấy đầy đủ thông tin VM từ ldconsole list2

        Output format: id,name,title,topWindowHandle,isRunning,pid1,pid2,width,height,dpi
        Ví dụ: 0,alfacellularjogja-0,0,0,0,-1,-1,333,592,120
               1,alfacellularjogja-1,140644042,1102383538,1,55176,25952,333,592,120

        Cột 4 (index 4): isRunning = 0 (Tắt) hoặc 1 (Bật)

        Returns:
            list: [(id, name, status), ...] với status là "Bật" hoặc "Tắt"
        """
        try:
            output = subprocess.check_output(
                [LDCONSOLE_EXE, "list2"],
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            devices = []
            for line in output.strip().splitlines():
                parts = line.split(",")
                if len(parts) >= 5:
                    vm_id = parts[0].strip()
                    vm_name = parts[1].strip()
                    is_running = parts[4].strip()

                    # Cột 4 (isRunning): 0 = Tắt, 1 = Bật
                    status = "Bật" if is_running == "1" else "Tắt"

                    devices.append((vm_id, vm_name, status))

            self.logger.info(f"Found {len(devices)} VMs in LDPlayer")
            return devices

        except Exception as e:
            self.logger.error(f"Error getting LDPlayer list: {e}")
            return []

    # ===== Xóa máy ảo =====
    def delete_vm(self, name):
        confirm = messagebox.askyesno("Xác nhận",
                                     f"Bạn có chắc muốn xóa {name}?")
        if not confirm:
            return
        try:
            subprocess.run([LDCONSOLE_EXE, "remove", "--name", name], 
                          creationflags=subprocess.CREATE_NO_WINDOW)
            path = os.path.join(DATA_DIR, f"{name}.json")
            if os.path.exists(path):
                os.remove(path)
            time.sleep(1)
            self.refresh_list()
            self.logger.info(f"Successfully deleted VM: {name}")
        except Exception as e:
            self.logger.exception(f"Error deleting VM {name}")
            messagebox.showerror("Lỗi", f"Không thể xóa {name}:\n{e}")

    # ===== Login demo =====
    def login_vm(self, name):
        """Fixed version với logic rõ ràng hơn"""
        
        # Đọc dữ liệu cũ từ JSON
        path = os.path.join(DATA_DIR, f"{name}.json")
        existing_data = ""
        existing_port = ""
        
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                username = data.get("username", "")
                password = data.get("password", "")
                key_2fa = data.get("2fa", "")
                existing_port = data.get("port", "")
                
                if username or password or key_2fa:
                    existing_data = f"{username}|{password}|{key_2fa}"
        except Exception:
            pass
        
        # Tạo dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Đăng nhập {name}")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # UI Components
        ttk.Label(dialog, text=f"Nhập thông tin đăng nhập cho {name}", 
                font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        # Port input
        port_frame = ttk.Frame(dialog)
        port_frame.pack(padx=20, pady=(0, 10), fill="x")
        ttk.Label(port_frame, text="Port:", width=10).pack(side="left")
        port_entry = ttk.Entry(port_frame, width=15, font=("Consolas", 10))
        port_entry.pack(side="left", padx=5)
        if existing_port:
            port_entry.insert(0, existing_port)
        
        ttk.Label(dialog, text="Định dạng: username|password|2fa_key", 
                foreground="gray").pack()
        
        # Text widget
        text_frame = ttk.Frame(dialog)
        text_frame.pack(padx=20, pady=10, fill="both", expand=True)
        text_input = tk.Text(text_frame, height=6, width=50, font=("Consolas", 10))
        text_input.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(text_frame, command=text_input.yview)
        scrollbar.pack(side="right", fill="y")
        text_input.config(yscrollcommand=scrollbar.set)
        
        # Placeholder logic
        is_placeholder = {"value": False}
        placeholder_text = "example@gmail.com|MyPassword123|ABCD EFGH IJKL MNOP"
        
        if existing_data:
            text_input.insert("1.0", existing_data)
            text_input.config(foreground="black")
        else:
            text_input.insert("1.0", placeholder_text)
            text_input.config(foreground="gray")
            is_placeholder["value"] = True
            
            def on_focus_in(event):
                if is_placeholder["value"]:
                    text_input.delete("1.0", "end")
                    text_input.config(foreground="black")
                    is_placeholder["value"] = False
            
            def on_focus_out(event):
                content = text_input.get("1.0", "end-1c").strip()
                if not content:
                    text_input.insert("1.0", placeholder_text)
                    text_input.config(foreground="gray")
                    is_placeholder["value"] = True
            
            text_input.bind("<FocusIn>", on_focus_in)
            text_input.bind("<FocusOut>", on_focus_out)
        
        # Result storage - FIX: Thêm flag should_login
        result = {"data": None, "port": None, "should_login": False}
        
        # Helper function để validate và lấy data
        def get_input_data():
            """Validate và trả về (port, username, password, key_2fa) hoặc None"""
            port_value = port_entry.get().strip()
            if not port_value:
                messagebox.showerror("Lỗi", "Port không được để trống!")
                return None
            
            content = text_input.get("1.0", "end-1c").strip()
            
            # Trường hợp chỉ lưu port
            if is_placeholder["value"] or not content:
                return (port_value, None, None, None)
            
            # Parse login info
            try:
                parts = content.split("|")
                if len(parts) != 3:
                    messagebox.showerror("Lỗi", "Sai định dạng! Phải là: username|password|2fa")
                    return None
                
                username = parts[0].strip()
                password = parts[1].strip()
                key_2fa = parts[2].strip()
                
                if not username or not password or not key_2fa:
                    messagebox.showerror("Lỗi", "Không được để trống các trường!")
                    return None
                
                return (port_value, username, password, key_2fa)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể parse dữ liệu: {e}")
                return None
        
        # Helper function để lưu vào JSON
        def save_to_json(port_value, username=None, password=None, key_2fa=None):
            """Lưu data vào JSON file"""
            try:
                # Đọc data hiện tại
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                except:
                    data = {}
                
                # Update port
                data["port"] = port_value
                
                # Update login info nếu có
                if username and password and key_2fa:
                    data["username"] = username
                    data["password"] = password
                    data["2fa"] = key_2fa
                
                # Ghi file
                with open(path, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, ensure_ascii=False, indent=2)
                
                return True
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu dữ liệu: {e}")
                return False
        
        # Button handlers
        def on_save_data():
            """Chỉ lưu data, không đăng nhập"""
            data = get_input_data()
            if data is None:
                return
            
            port_value, username, password, key_2fa = data
            
            # Lưu vào file
            if save_to_json(port_value, username, password, key_2fa):
                if username:
                    messagebox.showinfo("Thành công", "Đã lưu thông tin đăng nhập!")
                else:
                    messagebox.showinfo("Thành công", "Đã lưu port!")
            
            # KHÔNG đóng dialog, user có thể tiếp tục chỉnh sửa
        
        def on_submit():
            """Lưu data VÀ đăng nhập"""
            data = get_input_data()
            if data is None:
                return
            
            port_value, username, password, key_2fa = data
            
            # Kiểm tra có đủ thông tin để đăng nhập không
            if not username or not password or not key_2fa:
                messagebox.showerror("Lỗi", "Cần nhập đầy đủ thông tin để đăng nhập!")
                return
            
            # Lưu vào file
            if not save_to_json(port_value, username, password, key_2fa):
                return
            
            # Set flag và đóng dialog
            result["port"] = port_value
            result["data"] = f"{username}|{password}|{key_2fa}"
            result["should_login"] = True  # FIX: Set flag này
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="💾 Lưu", command=on_save_data, 
                width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✅ Đăng nhập", command=on_submit, 
                width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Hủy", command=on_cancel, 
                width=15).pack(side="left", padx=5)
        
        # Chờ dialog đóng
        dialog.wait_window()
        
        # FIX: Kiểm tra flag đúng cách
        if not result["should_login"]:
            return
        
        input_dialog = result["data"]
        port = result["port"]
        
        if not input_dialog or not port:
            return
        
        # Parse lại để đăng nhập
        try:
            parts = input_dialog.split("|")
            username, password, key_2fa = parts[0].strip(), parts[1].strip(), parts[2].strip()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi parse data: {e}")
            return
        
        # Thực hiện đăng nhập
        def run_login():
            device = self.to_device_id(port)
            if not device:
                self.write_log(name, f"⚠️ Port không hợp lệ: {port}")
                return

            ok = self.login_handler.auto_login(name, device, username, password, key_2fa)
            if ok:
                self.write_log(name, "✅ Đăng nhập thành công!")
            else:
                self.write_log(name, "❌ Đăng nhập thất bại.")

        
        threading.Thread(target=run_login, daemon=True).start()

