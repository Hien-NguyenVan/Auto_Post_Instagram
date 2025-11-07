"""
Scheduled Post Tab - Đặt lịch đăng video từ PC

Features:
- Import video từ file hoặc folder
- Đặt lịch đăng bài theo thời gian
- Tự động bật VM, gửi file, đăng bài, xóa file, tắt VM
- Log realtime cho mỗi post
"""
import os
import json
import time
import queue
import threading
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from tkinter import messagebox, filedialog
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config import LDCONSOLE_EXE, DATA_DIR
from constants import WAIT_MEDIUM, WAIT_LONG, WAIT_SHORT
from utils.send_file import send_file_api
from utils.post import InstagramPost
from utils.delete_file import clear_dcim
from utils.vm_manager import vm_manager


# ==================== CONSTANTS ====================
VN_TZ = timezone(timedelta(hours=7))
SCHEDULED_POSTS_FILE = os.path.join("data", "scheduled_posts.json")
SCHEDULED_VIDEOS_DIR = os.path.join("temp", "scheduled")
os.makedirs(SCHEDULED_VIDEOS_DIR, exist_ok=True)


# ==================== WHEEL PICKER WIDGET ====================
class WheelPicker(tk.Frame):
    """Custom wheel picker widget - iOS style"""

    def __init__(self, parent, values, default_value=None, width=10):
        super().__init__(parent)
        self.values = values
        self.current_index = 0

        if default_value is not None and default_value in values:
            self.current_index = values.index(default_value)

        # Canvas for wheel effect
        self.canvas = tk.Canvas(
            self,
            width=width * 10,
            height=150,
            bg="white",
            highlightthickness=1,
            highlightbackground="#ccc"
        )
        self.canvas.pack()

        # Draw items
        self.item_height = 30
        self.visible_items = 5
        self.center_y = 75

        # Bind mouse wheel
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-1>", self.on_click)

        self.draw_wheel()

    def draw_wheel(self):
        """Draw wheel items"""
        self.canvas.delete("all")

        # Draw center selection box
        self.canvas.create_rectangle(
            0, self.center_y - self.item_height // 2,
            self.canvas.winfo_reqwidth(), self.center_y + self.item_height // 2,
            outline="#007AFF", width=2, fill="#E3F2FD"
        )

        # Draw items
        start_index = max(0, self.current_index - 2)
        end_index = min(len(self.values), start_index + self.visible_items)

        for i in range(start_index, end_index):
            offset = (i - self.current_index) * self.item_height
            y_pos = self.center_y + offset

            # Calculate opacity based on distance from center
            distance = abs(i - self.current_index)
            if distance == 0:
                font_size = 16
                font_weight = "bold"
                fill_color = "#000000"
            elif distance == 1:
                font_size = 14
                font_weight = "normal"
                fill_color = "#666666"
            else:
                font_size = 12
                font_weight = "normal"
                fill_color = "#999999"

            self.canvas.create_text(
                self.canvas.winfo_reqwidth() // 2, y_pos,
                text=str(self.values[i]),
                font=("Segoe UI", font_size, font_weight),
                fill=fill_color,
                tags=f"item_{i}"
            )

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scroll"""
        if event.delta > 0:
            self.scroll_up()
        else:
            self.scroll_down()

    def on_click(self, event):
        """Handle click to select item"""
        y = event.y
        offset = (y - self.center_y) / self.item_height
        new_index = self.current_index + round(offset)

        if 0 <= new_index < len(self.values):
            self.current_index = new_index
            self.draw_wheel()

    def scroll_up(self):
        """Scroll up (decrease index)"""
        if self.current_index > 0:
            self.current_index -= 1
            self.draw_wheel()

    def scroll_down(self):
        """Scroll down (increase index)"""
        if self.current_index < len(self.values) - 1:
            self.current_index += 1
            self.draw_wheel()

    def get(self):
        """Get current selected value"""
        return self.values[self.current_index]


# ==================== DATA MODELS ====================
class ScheduledPost:
    """Một post được đặt lịch"""

    def __init__(self, post_id, video_path, scheduled_time_vn=None, vm_name=None,
                 account_display=None, title="", status="draft", is_paused=True):
        self.id = post_id
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        self.scheduled_time_vn = scheduled_time_vn  # datetime object or None
        self.vm_name = vm_name
        self.account_display = account_display or "Chưa chọn"
        self.title = title or self.video_name
        self.status = status  # draft, pending, processing, posted, failed
        self.is_paused = is_paused  # True = dừng, False = chạy
        self.stop_requested = False  # Flag để yêu cầu dừng ngay lập tức
        self.logs = []

    def to_dict(self):
        return {
            "id": self.id,
            "video_path": self.video_path,
            "video_name": self.video_name,
            "scheduled_time_vn": self.scheduled_time_vn.strftime("%d/%m/%Y %H:%M") if self.scheduled_time_vn else None,
            "vm_name": self.vm_name,
            "account_display": self.account_display,
            "title": self.title,
            "status": self.status,
            "is_paused": self.is_paused
        }

    @staticmethod
    def from_dict(data):
        scheduled_time = None
        if data.get("scheduled_time_vn"):
            scheduled_time = datetime.strptime(data["scheduled_time_vn"], "%d/%m/%Y %H:%M")
            scheduled_time = scheduled_time.replace(tzinfo=VN_TZ)

        return ScheduledPost(
            post_id=data["id"],
            video_path=data["video_path"],
            scheduled_time_vn=scheduled_time,
            vm_name=data.get("vm_name"),
            account_display=data.get("account_display"),
            title=data.get("title", ""),
            status=data.get("status", "draft"),
            is_paused=data.get("is_paused", True)
        )

    def log(self, message):
        """Add log message"""
        timestamp = datetime.now(VN_TZ).strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]


# ==================== DATA PERSISTENCE ====================
def load_scheduled_posts():
    """Load scheduled posts from JSON"""
    if not os.path.exists(SCHEDULED_POSTS_FILE):
        return []

    try:
        with open(SCHEDULED_POSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ScheduledPost.from_dict(p) for p in data.get("posts", [])]
    except Exception as e:
        logging.error(f"Error loading scheduled posts: {e}")
        return []


def save_scheduled_posts(posts):
    """Save scheduled posts to JSON"""
    try:
        data = {"posts": [p.to_dict() for p in posts]}
        with open(SCHEDULED_POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving scheduled posts: {e}")


def get_vm_list_with_insta():
    """Lấy danh sách máy ảo kèm tên Instagram từ data/"""
    vm_list = []
    try:
        if not os.path.exists(DATA_DIR):
            return vm_list

        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
        for f in files:
            path = os.path.join(DATA_DIR, f)
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                vm_name = data.get("vm_name", "")
                insta_name = data.get("insta_name", "")
                port = data.get("port", "")
                if vm_name and port:  # Only include VMs with valid port
                    display = f"{vm_name} - {insta_name}" if insta_name else vm_name
                    vm_list.append({
                        "vm_name": vm_name,
                        "display": display,
                        "port": port
                    })
    except Exception as e:
        logging.error(f"Error reading VM list: {e}")

    return vm_list


# ==================== SCHEDULER ====================
class PostScheduler(threading.Thread):
    """Background scheduler để check và post video đúng giờ"""

    def __init__(self, posts, ui_queue):
        super().__init__(daemon=True)
        self.posts = posts  # List of ScheduledPost
        self.ui_queue = ui_queue
        self.stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)
        self.auto_poster = InstagramPost(log_callback=self.log_callback)
        self.running_posts = set()  # Track posts being processed

    def log_callback(self, vm_name, message):
        """Callback from InstagramPost"""
        # Find the post for this VM and add log
        for post in self.posts:
            if post.vm_name == vm_name and post.status == "processing":
                post.log(message)
                self.ui_queue.put(("log_update", post.id, message))
                break

    def stop(self):
        self.stop_event.set()

    def run(self):
        """Main scheduler loop"""
        self.logger.info("Post scheduler started")

        while not self.stop_event.is_set():
            try:
                now = datetime.now(VN_TZ)

                # Check each pending post
                for post in self.posts[:]:  # Copy list to avoid modification issues
                    if post.status != "pending":
                        continue

                    if post.id in self.running_posts:
                        continue

                    # Chỉ chạy nếu post đang ở trạng thái running (is_paused=False)
                    if post.is_paused:
                        continue

                    # Check if it's time to post
                    if now >= post.scheduled_time_vn:
                        # Start posting in a separate thread
                        self.running_posts.add(post.id)
                        threading.Thread(
                            target=self.process_post,
                            args=(post,),
                            daemon=True
                        ).start()

                # Sleep for 30 seconds before next check
                for _ in range(30):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.exception("Error in scheduler loop")
                time.sleep(5)

        self.logger.info("Post scheduler stopped")

    def process_post(self, post: ScheduledPost):
        """Process a single scheduled post"""
        vm_acquired = False
        try:
            post.status = "processing"
            post.stop_requested = False  # Reset flag
            post.log(f"🚀 Bắt đầu xử lý post: {post.title}")
            self.ui_queue.put(("status_update", post.id, "processing"))

            # Check stop request
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu")
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Check if video file exists
            if not os.path.exists(post.video_path):
                post.log(f"❌ File video không tồn tại: {post.video_path}")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Get VM info
            vm_file = os.path.join(DATA_DIR, f"{post.vm_name}.json")
            if not os.path.exists(vm_file):
                post.log(f"❌ Không tìm thấy thông tin VM: {post.vm_name}")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            with open(vm_file, "r", encoding="utf-8") as f:
                vm_info = json.load(f)

            port = vm_info.get("port")
            if not port:
                post.log(f"❌ VM không có port: {post.vm_name}")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            adb_address = f"emulator-{port}"

            # ========== ACQUIRE VM LOCK ==========
            post.log(f"🔒 Chờ máy ảo '{post.vm_name}' sẵn sàng...")
            if not vm_manager.acquire_vm(post.vm_name, timeout=600, caller=f"Post:{post.title[:20]}"):
                post.log(f"⏱️ Timeout chờ máy ảo '{post.vm_name}' sau 10 phút")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            vm_acquired = True
            post.log(f"✅ Đã khóa máy ảo '{post.vm_name}'")

            # Check if VM is running
            try:
                result = subprocess.run(
                    [LDCONSOLE_EXE, "list2"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                is_running = False
                for line in result.stdout.splitlines():
                    parts = line.split(",")
                    if len(parts) >= 5 and parts[1].strip() == post.vm_name:
                        is_running = (parts[4].strip() == "1")
                        break

                if is_running:
                    post.log(f"⚠️ Máy ảo '{post.vm_name}' đang chạy - bỏ qua")
                    post.status = "failed"
                    self.ui_queue.put(("status_update", post.id, "failed"))
                    self.running_posts.discard(post.id)
                    save_scheduled_posts(self.posts)
                    return

            except Exception as e:
                post.log(f"⚠️ Không thể kiểm tra trạng thái VM: {e}")

            # Start VM
            post.log(f"🚀 Bật máy ảo '{post.vm_name}'...")
            subprocess.run(
                [LDCONSOLE_EXE, "launch", "--name", post.vm_name],
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Wait for VM to be fully ready
            post.log(f"⏳ Chờ máy ảo '{post.vm_name}' khởi động hoàn toàn...")
            if not vm_manager.wait_vm_ready(post.vm_name, LDCONSOLE_EXE, timeout=60):
                post.log(f"⏱️ Timeout - Máy ảo '{post.vm_name}' không khởi động được")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))
                return

            # Wait a bit more for ADB to connect
            post.log(f"⏳ Chờ ADB kết nối...")
            time.sleep(WAIT_MEDIUM)

            # Check stop request after VM start
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu - Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Send file to VM
            post.log(f"📤 Gửi file vào máy ảo...")
            try:
                success_push = send_file_api(
                    post.video_path,
                    post.vm_name,
                    log_callback=lambda msg: post.log(msg)
                )
            except Exception as e:
                success_push = False
                post.log(f"❌ Lỗi gửi file: {e}")

            if not success_push:
                post.log(f"❌ Gửi file thất bại")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))

                # Cleanup
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            post.log(f"✅ Đã gửi file thành công")
            time.sleep(WAIT_MEDIUM)

            # Check stop request after sending file
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu - Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Reboot VM
            post.log(f"🔄 Khởi động lại máy ảo...")
            subprocess.run(
                [LDCONSOLE_EXE, "reboot", "--name", post.vm_name],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(WAIT_LONG)

            # Check stop request after reboot
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu - Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Post to Instagram
            post.log(f"📲 Đang đăng video: {post.title}")
            success = self.auto_poster.auto_post(post.vm_name, adb_address, post.title)

            if not success:
                post.log(f"❌ Đăng bài thất bại")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))

                # Cleanup
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            post.log(f"✅ Đã đăng thành công!")

            # Check stop request after posting
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu - Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Delete file from VM
            post.log(f"🗑️ Xóa file trong máy ảo...")
            try:
                clear_dcim(adb_address, log_callback=lambda msg: post.log(msg))
            except Exception as e:
                post.log(f"⚠️ Lỗi khi xóa file: {e}")

            time.sleep(WAIT_MEDIUM)

            # Check stop request after deleting files
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu - Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Turn off VM
            post.log(f"🛑 Tắt máy ảo...")
            subprocess.run(
                [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(WAIT_SHORT)

            # Mark as posted
            post.status = "posted"
            post.log(f"✅ Hoàn tất!")
            self.ui_queue.put(("status_update", post.id, "posted"))

        except Exception as e:
            self.logger.exception(f"Error processing post {post.id}")
            post.log(f"❌ Lỗi: {e}")
            post.status = "failed"
            self.ui_queue.put(("status_update", post.id, "failed"))

            # Cleanup VM
            try:
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            except:
                pass

        finally:
            # ========== RELEASE VM LOCK ==========
            if vm_acquired:
                vm_manager.release_vm(post.vm_name, caller=f"Post:{post.title[:20]}")
                post.log(f"🔓 Đã giải phóng máy ảo '{post.vm_name}'")

            self.running_posts.discard(post.id)
            save_scheduled_posts(self.posts)


# ==================== GUI ====================
class PostTab(ttk.Frame):
    """Scheduled Post Tab UI"""

    def __init__(self, parent):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.ui_queue = queue.Queue()
        self.posts = load_scheduled_posts()
        self.scheduler = None
        self.log_windows = {}

        self.build_ui()
        self.load_posts_to_table()
        self.start_scheduler()
        self.after(200, self.process_ui_queue)

    def build_ui(self):
        """Build UI components"""
        # Top bar with buttons
        top_bar = ttk.Frame(self)
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Button(
            top_bar,
            text="📁 Nhập File",
            command=self.import_files,
            bootstyle="info",
            width=16
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            top_bar,
            text="📂 Nhập Folder",
            command=self.import_folder,
            bootstyle="info",
            width=16
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            top_bar,
            text="⚡ Lên lịch hàng loạt",
            command=self.bulk_schedule,
            bootstyle="warning",
            width=18
        ).pack(side=tk.LEFT, padx=3)

        ttk.Label(
            top_bar,
            text="💡 Đặt lịch đăng video tự động từ PC",
            font=("Segoe UI", 11, "bold"),
            bootstyle="primary"
        ).pack(side=tk.LEFT, padx=20)

        # Table with labelframe
        table_container = ttk.Labelframe(self, text="📋 Danh Sách Video Đã Lên Lịch", bootstyle="primary")
        table_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        table_frame = ttk.Frame(table_container)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("stt", "video", "edit", "scheduled_time", "account", "status", "control", "log", "delete")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18
        )

        # Configure alternating row colors (striped)
        self.tree.tag_configure("oddrow", background="#f0f0f0")
        self.tree.tag_configure("evenrow", background="white")

        # Headers
        self.tree.heading("stt", text="STT")
        self.tree.heading("video", text="Tên Video")
        self.tree.heading("edit", text="⚙️")
        self.tree.heading("scheduled_time", text="Thời Gian Đăng")
        self.tree.heading("account", text="Tài Khoản")
        self.tree.heading("status", text="Trạng Thái")
        self.tree.heading("control", text="Dừng/Chạy")
        self.tree.heading("log", text="Log")
        self.tree.heading("delete", text="Xóa")

        # Columns
        self.tree.column("stt", width=50, anchor=tk.CENTER)
        self.tree.column("video", width=250)
        self.tree.column("edit", width=50, anchor=tk.CENTER)
        self.tree.column("scheduled_time", width=130, anchor=tk.CENTER)
        self.tree.column("account", width=160)
        self.tree.column("status", width=110, anchor=tk.CENTER)
        self.tree.column("control", width=80, anchor=tk.CENTER)
        self.tree.column("log", width=60, anchor=tk.CENTER)
        self.tree.column("delete", width=60, anchor=tk.CENTER)

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind click
        self.tree.bind("<Button-1>", self.on_tree_click)

    def import_files(self):
        """Import video files"""
        files = filedialog.askopenfilenames(
            title="Chọn video để đăng",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )

        if files:
            self.add_posts_from_files(list(files))

    def import_folder(self):
        """Import all videos from a folder"""
        folder = filedialog.askdirectory(title="Chọn folder chứa video")

        if folder:
            video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')
            files = []

            for filename in os.listdir(folder):
                if filename.lower().endswith(video_extensions):
                    files.append(os.path.join(folder, filename))

            if files:
                self.add_posts_from_files(files)
            else:
                messagebox.showinfo("Thông báo", "Không tìm thấy video nào trong folder")

    def bulk_schedule(self):
        """Lên lịch hàng loạt cho các video trong table - chỉ áp thời gian"""
        # Lấy tất cả video trong table
        if not self.posts:
            messagebox.showinfo("Thông báo", "Không có video nào trong danh sách!")
            return

        # Dialog
        dialog = tk.Toplevel(self)
        dialog.title("Lên lịch hàng loạt")
        dialog.geometry("550x420")
        dialog.grab_set()

        # Info
        ttk.Label(
            dialog,
            text=f"⚡ Lên lịch hàng loạt cho video",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=10)

        ttk.Label(
            dialog,
            text="(Máy ảo của mỗi video sẽ được giữ nguyên)",
            font=("Segoe UI", 9),
            foreground="gray"
        ).pack(pady=2)

        # ========== PHẠM VI VIDEO ==========
        range_frame = ttk.Labelframe(dialog, text="📌 Phạm vi video áp dụng", padding=10)
        range_frame.pack(fill="x", padx=20, pady=(10, 5))

        # Row: Start and End index
        index_row = ttk.Frame(range_frame)
        index_row.pack(fill="x", pady=5)

        # Start index
        ttk.Label(index_row, text="Từ video thứ:", width=15).pack(side="left")
        entry_start_index = ttk.Spinbox(index_row, from_=1, to=999, width=10)
        entry_start_index.set(1)
        entry_start_index.pack(side="left", padx=5)

        # End index
        ttk.Label(index_row, text="Đến video thứ:", width=15).pack(side="left", padx=(20, 0))
        entry_end_index = ttk.Spinbox(index_row, from_=1, to=999, width=10)
        entry_end_index.set(999)
        entry_end_index.pack(side="left", padx=5)

        # Info label
        info_label = ttk.Label(
            range_frame,
            text=f"💡 Tổng số video hiện tại: {len(self.posts)}",
            font=("Segoe UI", 9),
            foreground="#0066cc"
        )
        info_label.pack(anchor="w", pady=(5, 0))

        # ========== THỜI GIAN ==========
        time_frame = ttk.Labelframe(dialog, text="⏰ Cài đặt thời gian", padding=10)
        time_frame.pack(fill="x", padx=20, pady=5)

        # Start date picker
        ttk.Label(time_frame, text="Ngày bắt đầu (dd/mm/yyyy):").pack(anchor="w", pady=(5, 0))
        entry_start_date = ttk.Entry(time_frame, width=50)
        default_date = datetime.now(VN_TZ).strftime("%d/%m/%Y")
        entry_start_date.insert(0, default_date)
        entry_start_date.pack(pady=5)

        # Time slots
        ttk.Label(time_frame, text="Khung giờ (cách nhau bởi dấu phẩy):").pack(anchor="w", pady=(5, 0))
        ttk.Label(
            time_frame,
            text="Ví dụ: 06:00, 10:00, 18:00, 22:00",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(anchor="w")
        entry_time_slots = ttk.Entry(time_frame, width=50)
        entry_time_slots.insert(0, "06:00, 10:00, 18:00, 22:00")
        entry_time_slots.pack(pady=5)

        result = {"ok": False}

        def on_apply():
            # Parse start and end index
            try:
                start_idx = int(entry_start_index.get())
                end_idx = int(entry_end_index.get())

                if start_idx < 1:
                    messagebox.showerror("Lỗi", "Chỉ số bắt đầu phải >= 1", parent=dialog)
                    return

                if end_idx < start_idx:
                    messagebox.showerror("Lỗi", "Chỉ số kết thúc phải >= chỉ số bắt đầu", parent=dialog)
                    return
            except ValueError:
                messagebox.showerror("Lỗi", "Chỉ số không hợp lệ", parent=dialog)
                return

            # Parse start date
            try:
                start_date = datetime.strptime(entry_start_date.get().strip(), "%d/%m/%Y")
                start_date = start_date.replace(tzinfo=VN_TZ)
            except:
                messagebox.showerror("Lỗi", "Ngày bắt đầu không hợp lệ. Dùng định dạng dd/mm/yyyy", parent=dialog)
                return

            # Parse time slots
            time_slots_str = entry_time_slots.get().strip()
            if not time_slots_str:
                messagebox.showerror("Lỗi", "Vui lòng nhập khung giờ", parent=dialog)
                return

            time_slots = []
            for slot in time_slots_str.split(","):
                slot = slot.strip()
                try:
                    # Parse HH:MM
                    parts = slot.split(":")
                    if len(parts) != 2:
                        raise ValueError
                    hour = int(parts[0])
                    minute = int(parts[1])
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError
                    time_slots.append((hour, minute))
                except:
                    messagebox.showerror("Lỗi", f"Khung giờ '{slot}' không hợp lệ. Dùng định dạng HH:MM", parent=dialog)
                    return

            if not time_slots:
                messagebox.showerror("Lỗi", "Không có khung giờ nào hợp lệ", parent=dialog)
                return

            # Apply schedule to posts (only within range)
            current_date = start_date
            slot_index = 0
            now = datetime.now(VN_TZ)

            # Đếm số video được áp dụng
            applied_count = 0

            for idx, post in enumerate(self.posts, start=1):
                # Chỉ áp dụng cho video trong phạm vi
                if idx < start_idx or idx > end_idx:
                    continue

                hour, minute = time_slots[slot_index]
                scheduled_time = current_date.replace(hour=hour, minute=minute)

                # Chỉ cập nhật thời gian, không thay đổi vm_name
                post.scheduled_time_vn = scheduled_time

                # Nếu đã có máy ảo thì set pending, chưa thì để draft
                if post.vm_name:
                    post.status = "pending"
                    # Mặc định để paused, người dùng phải nhấn Start để chạy
                    post.is_paused = True
                else:
                    post.status = "draft"

                applied_count += 1

                # Move to next slot
                slot_index += 1
                if slot_index >= len(time_slots):
                    slot_index = 0
                    current_date += timedelta(days=1)

            result["ok"] = True
            result["applied_count"] = applied_count
            result["start_idx"] = start_idx
            result["end_idx"] = min(end_idx, len(self.posts))
            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="✅ Áp dụng", command=on_apply, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Hủy", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()

        if result["ok"]:
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

            applied_count = result.get("applied_count", 0)
            start_idx = result.get("start_idx", 1)
            end_idx = result.get("end_idx", len(self.posts))

            messagebox.showinfo(
                "Thành công",
                f"✅ Đã áp thời gian thành công!\n\n"
                f"📊 Phạm vi: Video {start_idx} đến {end_idx}\n"
                f"✔️ Đã áp dụng: {applied_count} video"
            )

    def add_posts_from_files(self, files):
        """Add multiple posts from file list - thêm vào table trước, click vào để config"""
        # Thêm tất cả video vào table với status "draft"
        for idx, file_path in enumerate(files):
            post_id = f"post_{int(time.time() * 1000)}_{idx}"
            video_name = os.path.basename(file_path)

            post = ScheduledPost(
                post_id=post_id,
                video_path=file_path,
                scheduled_time_vn=None,
                vm_name=None,
                account_display="Chưa chọn",
                title=os.path.splitext(video_name)[0],
                status="draft"
            )

            self.posts.append(post)

        # Save và refresh
        save_scheduled_posts(self.posts)
        self.load_posts_to_table()
        messagebox.showinfo(
            "Thành công",
            f"Đã thêm {len(files)} video vào danh sách.\nClick vào cột ⚙️ để đặt lịch cho từng video."
        )

    def load_posts_to_table(self):
        """Load posts to table"""
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Sort by scheduled time (None values last)
        sorted_posts = sorted(
            self.posts,
            key=lambda p: (p.scheduled_time_vn is None, p.scheduled_time_vn or datetime.min.replace(tzinfo=VN_TZ))
        )

        # Add to table
        for idx, post in enumerate(sorted_posts, start=1):
            status_icon = {
                "draft": "⚙️ Chưa cấu hình",
                "pending": "⏳ Chờ",
                "processing": "🔄 Đang đăng",
                "posted": "✅ Đã đăng",
                "failed": "❌ Thất bại"
            }.get(post.status, post.status)

            scheduled_time_display = post.scheduled_time_vn.strftime("%d/%m/%Y %H:%M") if post.scheduled_time_vn else "Chưa đặt"

            # Xác định nút Start/Stop
            if post.status == "posted":
                control_button = "-"  # Đã đăng thành công, không cho phép gì
            elif post.status == "draft":
                control_button = "-"  # Chưa cấu hình thì chưa có nút
            elif post.status == "processing":
                control_button = "⏹ Dừng"  # Đang đăng, cho phép dừng
            else:
                # status = pending hoặc failed
                control_button = "▶ Chạy" if post.is_paused else "⏸ Dừng"

            # Striped rows
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                tk.END,
                iid=post.id,
                values=(
                    idx,
                    post.video_name,
                    "⚙️",
                    scheduled_time_display,
                    post.account_display,
                    status_icon,
                    control_button,
                    "📋",
                    "✖"
                ),
                tags=(tag,)
            )

    def on_tree_click(self, event):
        """Handle tree click"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)

        if not row_id or not col_id:
            return

        col = self.tree["columns"][int(col_id.strip("#")) - 1]

        # Find post
        post = None
        for p in self.posts:
            if p.id == row_id:
                post = p
                break

        if not post:
            return

        if col == "edit":
            self.edit_post_config(post)
        elif col == "control":
            self.toggle_post_control(post)
        elif col == "log":
            self.open_log_window(post)
        elif col == "delete":
            self.delete_post(post)

    def toggle_post_control(self, post: ScheduledPost):
        """Toggle start/stop cho post"""
        # Không cho phép toggle với draft hoặc posted
        if post.status == "draft":
            messagebox.showinfo("Thông báo", "Vui lòng cấu hình post trước khi chạy!")
            return

        if post.status == "posted":
            messagebox.showinfo("Thông báo", "Post đã đăng thành công, không thể dừng!")
            return

        # Nếu đang processing → yêu cầu dừng ngay lập tức
        if post.status == "processing":
            confirm = messagebox.askyesno(
                "Xác nhận dừng",
                f"⚠️ Post đang trong quá trình đăng!\n\n"
                f"Video: {post.video_name}\n\n"
                f"Bạn có chắc muốn dừng ngay lập tức?\n"
                f"(Máy ảo sẽ được tắt)"
            )
            if confirm:
                post.stop_requested = True
                post.log("🛑 Người dùng yêu cầu dừng ngay lập tức")
                messagebox.showinfo("Đã yêu cầu dừng", "Đang dừng post và tắt máy ảo...")
            return

        # Nếu đang dừng và muốn chạy → kiểm tra thời gian
        if post.is_paused:
            # Kiểm tra thời gian phải là tương lai
            now = datetime.now(VN_TZ)
            if post.scheduled_time_vn <= now:
                messagebox.showerror(
                    "Lỗi",
                    f"⚠️ Không thể chạy vì thời gian đăng đã qua!\n\n"
                    f"Thời gian đã đặt: {post.scheduled_time_vn.strftime('%d/%m/%Y %H:%M')}\n"
                    f"Thời gian hiện tại: {now.strftime('%d/%m/%Y %H:%M')}\n\n"
                    f"Vui lòng click vào ⚙️ để đặt lại thời gian."
                )
                return

        # Toggle trạng thái
        post.is_paused = not post.is_paused

        # Lưu và refresh
        save_scheduled_posts(self.posts)
        self.load_posts_to_table()

        if post.is_paused:
            messagebox.showinfo("Đã dừng", f"Đã dừng post:\n{post.video_name}")
        else:
            messagebox.showinfo("Đã chạy", f"Đã kích hoạt post:\n{post.video_name}\n\nSẽ tự động đăng vào: {post.scheduled_time_vn.strftime('%d/%m/%Y %H:%M')}")

    def edit_post_config(self, post: ScheduledPost):
        """Edit post configuration (VM và thời gian)"""
        if post.status in ["processing", "posted"]:
            messagebox.showwarning("Cảnh báo", "Không thể sửa post đã đăng hoặc đang đăng!")
            return

        vm_list = get_vm_list_with_insta()
        if not vm_list:
            messagebox.showerror("Lỗi", "Không có máy ảo nào. Vui lòng thêm máy ảo trước!")
            return

        vm_displays = [vm["display"] for vm in vm_list]

        # Dialog
        dialog = tk.Toplevel(self)
        dialog.title("Cấu hình video")
        dialog.geometry("720x500")
        dialog.grab_set()

        # Video info
        ttk.Label(
            dialog,
            text=f"📹 {post.video_name}",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=10)

        # Account selection
        ttk.Label(dialog, text="Chọn tài khoản:").pack(anchor="w", padx=20, pady=(10, 0))
        combo_vm = ttk.Combobox(dialog, values=vm_displays, state="readonly", width=50)
        combo_vm.pack(padx=20, pady=5)

        # Pre-select existing VM
        if post.vm_name:
            for i, vm in enumerate(vm_list):
                if vm["vm_name"] == post.vm_name:
                    combo_vm.current(i)
                    break
        elif vm_displays:
            combo_vm.current(0)

        # ========== THỜI GIAN ĐĂNG ==========
        ttk.Label(dialog, text="Thời gian đăng:").pack(pady=(10, 5))

        # Radio button để chọn "Đăng ngay" hoặc "Chọn thời gian"
        schedule_mode = tk.StringVar(value="schedule")  # "now" hoặc "schedule"

        radio_frame = ttk.Frame(dialog)
        radio_frame.pack(pady=5)

        ttk.Radiobutton(
            radio_frame,
            text="📅 Chọn thời gian cụ thể",
            variable=schedule_mode,
            value="schedule"
        ).pack(side="left", padx=10)

        ttk.Radiobutton(
            radio_frame,
            text="⚡ Đăng ngay",
            variable=schedule_mode,
            value="now"
        ).pack(side="left", padx=10)

        # Label hiển thị thời gian khi chọn "Đăng ngay"
        now_time_label = ttk.Label(
            dialog,
            text="",
            font=("Segoe UI", 9),
            foreground="#007acc"
        )
        now_time_label.pack(pady=3)

        def update_now_label(*args):
            if schedule_mode.get() == "now":
                now_plus_1 = datetime.now(VN_TZ) + timedelta(minutes=1)
                now_time_label.config(
                    text=f"⏰ Sẽ đăng vào: {now_plus_1.strftime('%d/%m/%Y %H:%M')} (sau 1 phút)"
                )
            else:
                now_time_label.config(text="")

        schedule_mode.trace_add("write", update_now_label)
        update_now_label()  # Initial update

        # Default time
        if post.scheduled_time_vn:
            default_dt = post.scheduled_time_vn
        else:
            default_dt = datetime.now(VN_TZ) + timedelta(minutes=5)

        # Wheel picker frame
        picker_frame = ttk.Frame(dialog)
        picker_frame.pack(pady=10)

        # Day picker
        day_frame = ttk.Frame(picker_frame)
        day_frame.grid(row=0, column=0, padx=5)
        ttk.Label(day_frame, text="Ngày").pack()
        wheel_day = WheelPicker(
            day_frame,
            values=list(range(1, 32)),
            default_value=default_dt.day,
            width=6
        )
        wheel_day.pack()

        # Month picker
        month_frame = ttk.Frame(picker_frame)
        month_frame.grid(row=0, column=1, padx=5)
        ttk.Label(month_frame, text="Tháng").pack()
        wheel_month = WheelPicker(
            month_frame,
            values=list(range(1, 13)),
            default_value=default_dt.month,
            width=6
        )
        wheel_month.pack()

        # Year picker
        year_frame = ttk.Frame(picker_frame)
        year_frame.grid(row=0, column=2, padx=5)
        ttk.Label(year_frame, text="Năm").pack()
        wheel_year = WheelPicker(
            year_frame,
            values=list(range(2024, 2031)),
            default_value=default_dt.year,
            width=8
        )
        wheel_year.pack()

        # Hour picker
        hour_frame = ttk.Frame(picker_frame)
        hour_frame.grid(row=0, column=3, padx=5)
        ttk.Label(hour_frame, text="Giờ").pack()
        wheel_hour = WheelPicker(
            hour_frame,
            values=[f"{i:02d}" for i in range(24)],
            default_value=f"{default_dt.hour:02d}",
            width=6
        )
        wheel_hour.pack()

        # Minute picker
        minute_frame = ttk.Frame(picker_frame)
        minute_frame.grid(row=0, column=4, padx=5)
        ttk.Label(minute_frame, text="Phút").pack()
        wheel_minute = WheelPicker(
            minute_frame,
            values=[f"{i:02d}" for i in range(60)],
            default_value=f"{default_dt.minute:02d}",
            width=6
        )
        wheel_minute.pack()

        # Hàm để toggle enable/disable wheel picker
        def toggle_picker_state(*args):
            mode = schedule_mode.get()
            state = "normal" if mode == "schedule" else "disabled"

            # Disable/enable tất cả wheel picker
            for wheel in [wheel_day, wheel_month, wheel_year, wheel_hour, wheel_minute]:
                if mode == "schedule":
                    wheel.canvas.config(state="normal", bg="white")
                else:
                    wheel.canvas.config(state="disabled", bg="#e0e0e0")

        # Bind radio button change
        schedule_mode.trace_add("write", toggle_picker_state)

        # Initial state
        toggle_picker_state()

        result = {"ok": False}

        def on_save():
            vm_idx = combo_vm.current()
            if vm_idx < 0:
                messagebox.showerror("Lỗi", "Vui lòng chọn tài khoản", parent=dialog)
                return

            # Kiểm tra mode: "now" hoặc "schedule"
            mode = schedule_mode.get()

            if mode == "now":
                # Đăng ngay = hiện tại + 1 phút
                scheduled_time = datetime.now(VN_TZ) + timedelta(minutes=1)
            else:
                # Chọn thời gian cụ thể từ wheel picker
                try:
                    day = int(wheel_day.get())
                    month = int(wheel_month.get())
                    year = int(wheel_year.get())
                    hour = int(wheel_hour.get())
                    minute = int(wheel_minute.get())

                    scheduled_time = datetime(year, month, day, hour, minute, tzinfo=VN_TZ)
                except ValueError as e:
                    messagebox.showerror("Lỗi", f"Thời gian không hợp lệ: {e}", parent=dialog)
                    return

                # Kiểm tra giờ đăng không được là quá khứ (chỉ khi chọn thời gian cụ thể)
                now = datetime.now(VN_TZ)
                if scheduled_time < now:
                    messagebox.showerror(
                        "Lỗi",
                        f"⚠️ Thời gian đăng không thể là quá khứ!\n\n"
                        f"Thời gian đã chọn: {scheduled_time.strftime('%d/%m/%Y %H:%M')}\n"
                        f"Thời gian hiện tại: {now.strftime('%d/%m/%Y %H:%M')}",
                        parent=dialog
                    )
                    return

            # Update post
            vm_info = vm_list[vm_idx]
            post.vm_name = vm_info["vm_name"]
            post.account_display = vm_info["display"]
            post.scheduled_time_vn = scheduled_time
            post.status = "pending"
            # Mặc định là paused, người dùng phải nhấn Start để chạy
            post.is_paused = True

            result["ok"] = True
            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="💾 Lưu", command=on_save, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Hủy", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()

        if result["ok"]:
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

    def open_log_window(self, post: ScheduledPost):
        """Open log window for a post"""
        if post.id in self.log_windows and self.log_windows[post.id].winfo_exists():
            self.log_windows[post.id].focus()
            return

        win = tk.Toplevel(self)
        win.title(f"Log - {post.video_name}")
        win.geometry("700x400")

        # Text widget
        txt = tk.Text(win, wrap="word", state="disabled", bg="#111", fg="#0f0")
        txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Show existing logs
        if post.logs:
            txt.config(state="normal")
            txt.insert("1.0", "\n".join(post.logs))
            txt.see("end")
            txt.config(state="disabled")

        win.text_log = txt
        self.log_windows[post.id] = win

        # Close button
        ttk.Button(win, text="Đóng", command=win.destroy).pack(pady=5)

    def delete_post(self, post: ScheduledPost):
        """Delete a scheduled post"""
        if post.status == "processing":
            messagebox.showwarning("Cảnh báo", "Không thể xóa post đang xử lý!")
            return

        confirm = messagebox.askyesno(
            "Xác nhận",
            f"Bạn có chắc muốn xóa:\n{post.video_name}?"
        )

        if confirm:
            self.posts.remove(post)
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

    def start_scheduler(self):
        """Start background scheduler"""
        if self.scheduler and self.scheduler.is_alive():
            return

        self.scheduler = PostScheduler(self.posts, self.ui_queue)
        self.scheduler.start()
        self.logger.info("Post scheduler started")

    def process_ui_queue(self):
        """Process UI updates from scheduler"""
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "status_update":
                    _, post_id, new_status = msg

                    # Update table
                    status_icon = {
                        "pending": "⏳ Chờ",
                        "processing": "🔄 Đang đăng",
                        "posted": "✅ Đã đăng",
                        "failed": "❌ Thất bại"
                    }.get(new_status, new_status)

                    try:
                        self.tree.set(post_id, "status", status_icon)
                    except:
                        pass

                elif msg_type == "log_update":
                    _, post_id, log_msg = msg

                    # Update log window if open
                    if post_id in self.log_windows and self.log_windows[post_id].winfo_exists():
                        win = self.log_windows[post_id]
                        txt = win.text_log
                        txt.config(state="normal")
                        txt.insert("end", log_msg + "\n")
                        txt.see("end")
                        txt.config(state="disabled")

        except:
            pass

        self.after(200, self.process_ui_queue)

    def __del__(self):
        """Cleanup when tab is destroyed"""
        if self.scheduler:
            self.scheduler.stop()
