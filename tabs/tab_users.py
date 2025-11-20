import os
import json
import subprocess
import threading
import time
import logging
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk  # For Treeview only
import customtkinter as ctk
from ui_theme import *

from utils.login import InstagramLogin
from config import LDCONSOLE_EXE, ADB_EXE, VM_DATA_DIR, get_vm_id_from_name
from constants import (
    MAX_RETRY_VM_STATUS, VM_STATUS_CHECK_INTERVAL
)

os.makedirs(VM_DATA_DIR, exist_ok=True)


class UsersTab(ctk.CTkFrame):
    """Users Tab - Modern Windows 11 Style"""

    # Danh sách tên file JSON dành riêng (không phải VM) trong thư mục data/
    RESERVED_FILENAMES = ["scheduled_posts"]  # streams và apis nằm trong subfolder nên không bị conflict

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.logger = logging.getLogger(__name__)
        self.login_handler = InstagramLogin(log_callback=self.write_log)

        # VM logs
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

        cols = ("stt","vm","insta","user","pass","tfa","port","status","log","toggle","login")

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

        # Width & align (đồng bộ, không lệch)
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
            text="🔌 Xem port",
            command=self.show_adb_devices,
            **get_button_style("secondary"),
            width=140
        ).pack(side="left", padx=DIMENSIONS["spacing_sm"])

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

    # ======= Xem ADB Devices =======
    def show_adb_devices(self):
        """Hiển thị cửa sổ với kết quả lệnh 'adb devices'"""
        # Chạy lệnh adb devices
        try:
            result = subprocess.run(
                [ADB_EXE, "devices"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            output = result.stdout.strip()
            if result.returncode != 0:
                output = f"Error (returncode: {result.returncode}):\n{result.stderr}"
        except Exception as e:
            output = f"Lỗi khi chạy lệnh adb devices:\n{str(e)}"

        # Tạo cửa sổ popup
        popup = tk.Toplevel(self)
        popup.title("ADB Devices - Danh sách Port")
        popup.geometry("600x400")
        popup.resizable(True, True)

        # Frame tiêu đề
        header_frame = ttk.Frame(popup)
        header_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            header_frame,
            text="📱 Kết quả lệnh: adb devices",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        # Nút refresh
        def refresh_output():
            try:
                result = subprocess.run(
                    [ADB_EXE, "devices"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                new_output = result.stdout.strip()
                if result.returncode != 0:
                    new_output = f"Error (returncode: {result.returncode}):\n{result.stderr}"
            except Exception as e:
                new_output = f"Lỗi khi chạy lệnh adb devices:\n{str(e)}"

            text_widget.config(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", new_output)
            text_widget.config(state="disabled")

        ttk.Button(
            header_frame,
            text="🔄 Làm mới",
            command=refresh_output
        ).pack(side="right", padx=5)

        # Text widget hiển thị output
        text_widget = tk.Text(
            popup,
            wrap="word",
            state="disabled",
            bg="#1e1e1e",
            fg="#00ff00",
            insertbackground="white",
            font=("Consolas", 10)
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Scrollbar
        scrollbar = ttk.Scrollbar(text_widget, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)

        # Hiển thị output
        text_widget.config(state="normal")
        text_widget.insert("1.0", output)
        text_widget.config(state="disabled")

        # Nút đóng
        ttk.Button(
            popup,
            text="Đóng",
            command=popup.destroy
        ).pack(pady=(0, 10))

    # ======= Load / Refresh danh sách =======
    # Sửa lại refresh_list
    def refresh_list(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        # Lấy tất cả VM từ LDPlayer list2
        all_vms = self.get_ld_list_full()  # [(id, name, status), ...]

        # Kiểm tra và tạo/cập nhật file JSON cho các VM
        for vm_id, vm_name, status in all_vms:
            # Bỏ qua nếu tên VM trùng với file JSON đặc biệt
            if vm_name in self.RESERVED_FILENAMES:
                self.logger.warning(f"VM name '{vm_name}' is reserved. Skipping JSON creation.")
                continue

            # ✅ v1.5.36: Lưu file theo {vm_id}.json thay vì {vm_name}.json
            json_path = os.path.join(VM_DATA_DIR, f"{vm_id}.json")

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
            else:
                # ✅ v1.5.36: Cập nhật vm_name nếu đã đổi tên
                try:
                    with open(json_path, "r", encoding="utf-8") as fp:
                        data = json.load(fp)

                    old_name = data.get("vm_name", "")
                    if old_name != vm_name:
                        data["vm_name"] = vm_name
                        with open(json_path, "w", encoding="utf-8") as fp:
                            json.dump(data, fp, ensure_ascii=False, indent=2)
                        self.logger.info(f"Updated vm_name: {vm_id} ({old_name} -> {vm_name})")
                except Exception as e:
                    self.logger.error(f"Failed to update vm_name for {vm_id}: {e}")

        # ✅ v1.5.36: Cleanup orphaned JSON files (VMs đã bị xóa)
        try:
            existing_ids = {vm_id for vm_id, _, _ in all_vms}
            for filename in os.listdir(VM_DATA_DIR):
                if filename.endswith(".json"):
                    file_id = filename.replace(".json", "")
                    if file_id not in existing_ids:
                        orphan_path = os.path.join(VM_DATA_DIR, filename)
                        os.remove(orphan_path)
                        self.logger.info(f"Removed orphaned file: {filename} (VM khong con ton tai)")
        except Exception as e:
            self.logger.error(f"Error during orphaned files cleanup: {e}")

        # Hiển thị tất cả VM (bỏ qua các VM có tên reserved)
        displayed_vms = [(vm_id, vm_name, status_txt) for vm_id, vm_name, status_txt in all_vms
                         if vm_name not in self.RESERVED_FILENAMES]

        for idx, (vm_id, vm_name, status_txt) in enumerate(displayed_vms, start=1):
            # ✅ v1.5.36: Đọc file theo {vm_id}.json
            json_path = os.path.join(VM_DATA_DIR, f"{vm_id}.json")

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

            # Thêm vào tree với striped rows
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", iid=vm_name,
                values=(idx, vm_name, insta, username, password,
                        tfa, port, status_txt, "📋", "▶/■", "Login"),
                tags=(tag,))


    # Click handler for tree
    def on_tree_click_users(self, event):
        region = self.tree.identify("region", event.x, event.y)

        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not row_id or not col_id:
            return

        col = self.tree["columns"][int(col_id[1:]) - 1]

        # Xử lý các cột hành động
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

    # ===== Login demo =====
    def login_vm(self, name):
        """Fixed version với logic rõ ràng hơn"""

        # ✅ v1.5.36: Tìm VM ID từ tên máy ảo
        vm_id = get_vm_id_from_name(name)
        if not vm_id:
            messagebox.showerror("Lỗi", f"Không tìm thấy file cấu hình cho máy ảo '{name}'")
            return

        # Đọc dữ liệu cũ từ JSON
        path = os.path.join(VM_DATA_DIR, f"{vm_id}.json")
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

