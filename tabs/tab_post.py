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
import csv
import time
import queue
import threading
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter import ttk  # For Treeview only
import customtkinter as ctk
from ui_theme import *

from config import LDCONSOLE_EXE, DATA_DIR, ADB_EXE
from constants import WAIT_MEDIUM, WAIT_LONG, WAIT_SHORT, WAIT_EXTRA_LONG, TIMEOUT_MINUTE
from utils.send_file import send_file_api
from utils.post import InstagramPost
from utils.delete_file import clear_dcim, clear_pictures
from utils.vm_manager import vm_manager
from utils.api_manager_multi import multi_api_manager
from utils.yt_api import (
    check_api_key_valid,
    extract_channel_id,
    get_uploads_playlist_id,
    iter_playlist_videos_newer_than,
    fetch_video_details,
    filter_videos_by_mode,
    iso_to_datetime
)
from utils.tiktok_api_new import (
    check_tiktok_api_key_valid,
    extract_tiktok_handle,
    fetch_tiktok_videos,
    convert_to_output_format
)
from utils.download_dlp import download_tiktok_direct_url, download_video_api


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
                 account_display=None, title="", status="draft", is_paused=True, post_now=False, log_callback=None):
        self.id = post_id
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        self.scheduled_time_vn = scheduled_time_vn  # datetime object or None
        self.vm_name = vm_name
        self.account_display = account_display or "Chưa chọn"
        self.title = title or self.video_name
        self.status = status  # draft, pending, processing, posted, failed
        self.is_paused = is_paused  # True = dừng, False = chạy
        self.post_now = post_now  # True = đăng ngay khi Start
        self.stop_requested = False  # Flag để yêu cầu dừng ngay lập tức
        self.logs = []
        self.log_callback = log_callback

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
            "is_paused": self.is_paused,
            "post_now": self.post_now
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
            is_paused=data.get("is_paused", True),
            post_now=data.get("post_now", False)
        )

    def log(self, message):
        """Add log message"""
        timestamp = datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
        # Gọi callback realtime
        if self.log_callback:
            self.log_callback(self.id, log_entry)


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
        # ✅ FIX BUG #5: Không dùng shared auto_poster nữa
        # Mỗi thread sẽ tạo InstagramPost riêng với post_id specific callback
        self.running_posts = set()  # Track posts being processed

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
                        # ✅ FIX BUG #2: Skip posts quá cũ (quá 10 phút)
                        time_diff = (now - post.scheduled_time_vn).total_seconds()
                        max_delay = 600  # 10 phút

                        if time_diff > max_delay:
                            # Quá cũ, skip và đánh dấu failed
                            self.logger.warning(f"Post {post.id} quá cũ ({time_diff/60:.1f} phút), bỏ qua")
                            post.log(f"⏰ Post quá cũ (trễ {time_diff/60:.1f} phút), tự động bỏ qua")
                            post.status = "failed"
                            post.is_paused = True
                            self.ui_queue.put(("status_update", post.id, "failed"))
                            save_scheduled_posts(self.posts)
                            continue

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
        vm_name_cached = None  # ✅ FIX BUG #4: Cache VM info locally
        try:
            # ✅ FIX BUG #5: Tạo InstagramPost riêng cho post này với callback dùng post.id
            def post_specific_log_callback(vm_name, message):
                """Log callback specific cho post này"""
                post.log(message)

            auto_poster = InstagramPost(log_callback=post_specific_log_callback)

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

            # Check if video_path is a URL or local file
            is_url = post.video_path.startswith("http")
            temp_video_path = None

            if is_url:
                # Detect platform from URL
                # If contains youtube.com or youtu.be -> YouTube
                # Otherwise -> TikTok (default)
                is_youtube = "youtube.com" in post.video_path or "youtu.be" in post.video_path

                if is_youtube:
                    # Download YouTube video
                    post.log(f"📥 Đang tải video YouTube từ URL...")
                    try:
                        video_path = download_video_api(
                            post.video_path,
                            log_callback=lambda msg: post.log(msg)
                        )

                        if not video_path or not os.path.exists(video_path):
                            post.log(f"❌ Không thể tải video YouTube")
                            post.status = "failed"
                            self.ui_queue.put(("status_update", post.id, "failed"))
                            self.running_posts.discard(post.id)
                            save_scheduled_posts(self.posts)
                            return

                        post.log(f"✅ Đã tải video YouTube: {os.path.basename(video_path)}")
                        temp_video_path = video_path  # Mark for cleanup later
                        post.video_path = video_path  # Update to local path

                    except Exception as e:
                        post.log(f"❌ Lỗi khi tải video YouTube: {e}")
                        post.status = "failed"
                        self.ui_queue.put(("status_update", post.id, "failed"))
                        self.running_posts.discard(post.id)
                        save_scheduled_posts(self.posts)
                        return

                else:
                    # Default: TikTok (hoặc bất kỳ URL nào không phải YouTube)
                    post.log(f"📥 Đang tải video TikTok từ URL...")
                    try:
                        video_path = download_tiktok_direct_url(
                            post.video_path,
                            log_callback=lambda msg: post.log(msg)
                        )

                        if not video_path or not os.path.exists(video_path):
                            post.log(f"❌ Không thể tải video TikTok")
                            post.status = "failed"
                            self.ui_queue.put(("status_update", post.id, "failed"))
                            self.running_posts.discard(post.id)
                            save_scheduled_posts(self.posts)
                            return

                        post.log(f"✅ Đã tải video TikTok: {os.path.basename(video_path)}")
                        temp_video_path = video_path  # Mark for cleanup later
                        post.video_path = video_path  # Update to local path

                    except Exception as e:
                        post.log(f"❌ Lỗi khi tải video TikTok: {e}")
                        post.status = "failed"
                        self.ui_queue.put(("status_update", post.id, "failed"))
                        self.running_posts.discard(post.id)
                        save_scheduled_posts(self.posts)
                        return

                time.sleep(WAIT_SHORT)

            else:
                # Check if local video file exists
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
            if not vm_manager.acquire_vm(post.vm_name, timeout=5400, caller=f"Post:{post.title[:20]}"):
                post.log(f"⏱️ Timeout chờ máy ảo '{post.vm_name}' sau 1.5 giờ")
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
                    # VM đang chạy → Reboot để đảm bảo trạng thái sạch (QUEUE-BASED)
                    post.log(f"⚠️ Máy ảo '{post.vm_name}' đang chạy - Reboot để đảm bảo trạng thái sạch")

                    # ✅ KHÔNG reset ADB server toàn cục (ảnh hưởng tất cả VMs khác!)
                    # LDPlayer sẽ tự động setup lại ADB connection khi reboot

                    subprocess.run(
                        [LDCONSOLE_EXE, "reboot", "--name", post.vm_name],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # VM chưa chạy → Bật mới
                    post.log(f"🚀 Bật máy ảo '{post.vm_name}'...")

                    # ✅ KHÔNG reset ADB server toàn cục (ảnh hưởng tất cả VMs khác!)
                    # LDPlayer sẽ tự động setup lại ADB connection khi launch

                    subprocess.run(
                        [LDCONSOLE_EXE, "launch", "--name", post.vm_name],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

            except Exception as e:
                post.log(f"⚠️ Không thể kiểm tra trạng thái VM: {e}")
                # Nếu lỗi kiểm tra, cố gắng bật VM
                post.log(f"🚀 Bật máy ảo '{post.vm_name}'...")
                subprocess.run(
                    [LDCONSOLE_EXE, "launch", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

            # Wait for VM to be fully ready
            post.log(f"⏳ Chờ máy ảo '{post.vm_name}' khởi động hoàn toàn...")
            if not vm_manager.wait_vm_ready(post.vm_name, LDCONSOLE_EXE, timeout=120):
                post.log(f"⏱️ Timeout - Máy ảo '{post.vm_name}' không khởi động được")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))
                return

            # Wait for ADB to connect
            if not vm_manager.wait_adb_ready(adb_address, ADB_EXE, timeout=TIMEOUT_MINUTE):
                post.log(f"⏱️ Timeout - ADB không kết nối được đến '{adb_address}'")
                post.log(f"🛑 Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Check stop request after VM start
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu - Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Clear DCIM and Pictures folders before sending file
            post.log(f"🗑️ Xóa DCIM và Pictures...")
            try:
                clear_dcim(adb_address, log_callback=lambda msg: post.log(msg))
                clear_pictures(adb_address, log_callback=lambda msg: post.log(msg))
                post.log(f"✅ Đã xóa DCIM và Pictures")
            except Exception as e:
                post.log(f"⚠️ Lỗi khi xóa DCIM/Pictures: {e}")

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
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
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
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Check stop request before posting
            if post.stop_requested:
                post.log(f"🛑 Đã dừng theo yêu cầu - Đang tắt máy ảo...")
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
                post.status = "failed"
                post.is_paused = True
                self.ui_queue.put(("status_update", post.id, "failed"))
                self.running_posts.discard(post.id)
                save_scheduled_posts(self.posts)
                return

            # Post to Instagram
            post.log(f"📲 Đang đăng video: {post.title}")
            # ✅ FIX BUG #5: Dùng auto_poster local thay vì shared
            success = auto_poster.auto_post(
                post.vm_name, adb_address, post.title,
                use_launchex=True, ldconsole_exe=LDCONSOLE_EXE
            )

            if not success:
                post.log(f"❌ Đăng bài thất bại")
                post.status = "failed"
                self.ui_queue.put(("status_update", post.id, "failed"))

                # Cleanup
                subprocess.run(
                    [LDCONSOLE_EXE, "quit", "--name", post.vm_name],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
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
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
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
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
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
            vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
            time.sleep(WAIT_EXTRA_LONG)
            post.log(f"✅ Đã tắt máy ảo hoàn toàn")

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
                vm_manager.wait_vm_stopped(post.vm_name, LDCONSOLE_EXE, timeout=60)  # Đợi VM tắt hoàn toàn
                time.sleep(WAIT_EXTRA_LONG)
            except:
                pass

        finally:
            # ========== RELEASE VM LOCK ==========
            if vm_acquired:
                vm_manager.release_vm(post.vm_name, caller=f"Post:{post.title[:20]}")
                post.log(f"🔓 Đã giải phóng máy ảo '{post.vm_name}'")

            # ========== CLEANUP TEMP FILE ==========
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                    post.log(f"🗑️ Đã xóa file temp: {os.path.basename(temp_video_path)}")
                except Exception as e:
                    post.log(f"⚠️ Không thể xóa file temp: {e}")

            self.running_posts.discard(post.id)
            save_scheduled_posts(self.posts)


# ==================== GUI ====================
class PostTab(ctk.CTkFrame):
    """Scheduled Post Tab UI - Modern Windows 11 Style"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.logger = logging.getLogger(__name__)
        self.ui_queue = queue.Queue()
        self.posts = load_scheduled_posts()
        self.scheduler = None
        self.log_windows = {}
        self.checked_posts = {}  # Dictionary để lưu trạng thái checkbox {post_id: True/False}
        self.sort_by = "time"  # Mặc định sắp xếp theo thời gian: time, vm, status, name
        self.sort_order = "asc"  # asc = tăng dần, desc = giảm dần
        self.is_shutting_down = False  # Flag để track shutdown state
        self.is_running_all = False  # Flag để track trạng thái "Chạy tất cả"
        self.control_buttons = []  # List các buttons cần disable khi đang chạy

        # ✅ FIX BUG #1: Reset state khi load app
        # Khi app restart, force pause tất cả posts để tránh tự động chạy
        for post in self.posts:
            if post.status in ["pending", "processing"]:
                post.is_paused = True  # Force pause
                post.status = "pending"  # Reset về pending
                self.logger.info(f"Reset post {post.id} to paused state after app restart")
            post.log_callback = self.append_log_line

        # Save lại state đã reset
        save_scheduled_posts(self.posts)

        self.build_ui()
        self.load_posts_to_table(auto_sort=True)  # ✅ Sort lần đầu khi load app
        self.start_scheduler()
        self.after(200, self.process_ui_queue)

    def append_log_line(self, post_id, line):
        """Append log line realtime to log window if open"""
        if hasattr(self, "log_windows") and post_id in self.log_windows:
            win = self.log_windows[post_id]
            if win.winfo_exists():
                txt = win.text_log

                def safe_append():
                    # Kiểm tra widget còn tồn tại
                    if not txt.winfo_exists():
                        return
                    try:
                        txt.config(state="normal")
                        txt.insert("end", line + "\n")
                        txt.see("end")
                        txt.config(state="disabled")
                    except Exception:
                        # Tránh crash nếu widget bị đóng giữa chừng
                        pass

                # Thread-safe append
                win.after(0, safe_append)

    def build_ui(self):
        """Build UI components - Modern Windows 11 Style"""
        # Apply CustomTkinter theme
        apply_ctk_theme()

        # Container cho tất cả các nút
        buttons_container = ctk.CTkFrame(self, fg_color="transparent")
        buttons_container.pack(fill=tk.X, padx=DIMENSIONS["spacing_md"], pady=(DIMENSIONS["spacing_md"], DIMENSIONS["spacing_sm"]))

        # ====== HÀNG 1: IMPORT VIDEO ======
        row1_label = ctk.CTkLabel(
            buttons_container,
            text="📥 Import Video",
            font=(FONTS["family"], FONTS["size_medium"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        )
        row1_label.pack(anchor="w", pady=(0, DIMENSIONS["spacing_xs"]))

        row1 = ctk.CTkFrame(buttons_container, **get_frame_style("panel"))
        row1.pack(fill=tk.X, pady=(0, DIMENSIONS["spacing_sm"]))

        ctk.CTkButton(
            row1,
            text="📁 Nhập File",
            command=self.import_files,
            **get_button_style("primary"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row1,
            text="📂 Nhập Folder",
            command=self.import_folder,
            **get_button_style("primary"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row1,
            text="📺 Nhập từ YouTube/TikTok",
            command=self.import_channel,
            **get_button_style("primary"),
            width=180
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row1,
            text="📥 Nhập CSV",
            command=self.import_from_csv,
            **get_button_style("secondary"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        # ====== HÀNG 2: CẤU HÌNH HÀNG LOẠT ======
        row2_label = ctk.CTkLabel(
            buttons_container,
            text="⚙️ Cấu hình hàng loạt",
            font=(FONTS["family"], FONTS["size_medium"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        )
        row2_label.pack(anchor="w", pady=(0, DIMENSIONS["spacing_xs"]))

        row2 = ctk.CTkFrame(buttons_container, **get_frame_style("panel"))
        row2.pack(fill=tk.X, pady=(0, DIMENSIONS["spacing_sm"]))

        ctk.CTkButton(
            row2,
            text="⚡ Lên lịch hàng loạt",
            command=self.bulk_schedule,
            **get_button_style("warning"),
            width=160
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row2,
            text="⚙️ Đặt máy ảo hàng loạt",
            command=self.bulk_assign_vm,
            **get_button_style("success"),
            width=180
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        # ====== HÀNG 3: ĐIỀU KHIỂN & XUẤT DỮ LIỆU ======
        row3_label = ctk.CTkLabel(
            buttons_container,
            text="🎮 Điều khiển & Xuất dữ liệu",
            font=(FONTS["family"], FONTS["size_medium"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        )
        row3_label.pack(anchor="w", pady=(0, DIMENSIONS["spacing_xs"]))

        row3 = ctk.CTkFrame(buttons_container, **get_frame_style("panel"))
        row3.pack(fill=tk.X, pady=(0, DIMENSIONS["spacing_sm"]))

        ctk.CTkButton(
            row3,
            text="▶ Chạy tất cả",
            command=self.run_all_videos,
            **get_button_style("success"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row3,
            text="⏸ Dừng tất cả",
            command=self.stop_all_videos,
            **get_button_style("danger"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row3,
            text="🗑️ Xóa đã chọn",
            command=self.delete_selected_videos,
            **get_button_style("danger"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row3,
            text="📤 Xuất CSV",
            command=self.export_to_csv,
            **get_button_style("secondary"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkButton(
            row3,
            text="🔑 Quản lý API",
            command=self.open_api_manager,
            **get_button_style("warning"),
            width=140
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        # ====== FILTER BAR ======
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill=tk.X, padx=DIMENSIONS["spacing_md"], pady=(DIMENSIONS["spacing_sm"], 0))

        ctk.CTkLabel(
            filter_bar,
            text="🔍 Sắp xếp theo:",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        ).pack(side=tk.LEFT, padx=(0, DIMENSIONS["spacing_md"]))

        # Combobox chọn tiêu chí sắp xếp
        self.sort_combo = ctk.CTkComboBox(
            filter_bar,
            values=["Thời gian đăng", "Máy ảo", "Trạng thái", "Tên video"],
            command=self.on_sort_change,
            width=160,
            corner_radius=DIMENSIONS["corner_radius_medium"],
            border_color=COLORS["border_medium"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            fg_color=COLORS["bg_secondary"]
        )
        self.sort_combo.set("Thời gian đăng")
        self.sort_combo.pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"])

        # Nút đổi chiều sắp xếp
        self.sort_order_btn = ctk.CTkButton(
            filter_bar,
            text="⬆️ Tăng dần",
            command=self.toggle_sort_order,
            **get_button_style("secondary"),
            width=120
        )
        self.sort_order_btn.pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"])

        # Label hiển thị số lượng video
        self.count_label = ctk.CTkLabel(
            filter_bar,
            text="",
            font=(FONTS["family"], FONTS["size_small"]),
            text_color=COLORS["text_secondary"]
        )
        self.count_label.pack(side=tk.RIGHT, padx=DIMENSIONS["spacing_md"])

        # ====== TABLE CONTAINER ======
        table_outer = ctk.CTkFrame(self, fg_color="transparent")
        table_outer.pack(fill=tk.BOTH, expand=True, padx=DIMENSIONS["spacing_md"], pady=(DIMENSIONS["spacing_sm"], DIMENSIONS["spacing_md"]))

        # Title for table
        table_title = ctk.CTkLabel(
            table_outer,
            text="📋 Danh Sách Video Đã Lên Lịch",
            font=(FONTS["family"], FONTS["size_medium"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        )
        table_title.pack(anchor="w", pady=(0, DIMENSIONS["spacing_xs"]))

        # Table container with panel style
        table_container = ctk.CTkFrame(table_outer, **get_frame_style("panel"))
        table_container.pack(fill=tk.BOTH, expand=True)

        table_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        # Treeview with ttk (CustomTkinter doesn't have table widget)
        columns = ("checkbox", "stt", "video", "edit", "scheduled_time", "account", "status", "log", "delete")

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

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10
        )

        # Configure alternating row colors (striped)
        self.tree.tag_configure("oddrow", background=COLORS["surface_2"])
        self.tree.tag_configure("evenrow", background=COLORS["bg_secondary"])

        # Headers
        self.tree.heading("checkbox", text="☐", command=self.toggle_all_checkboxes)
        self.tree.heading("stt", text="STT")
        self.tree.heading("video", text="Tên Video")
        self.tree.heading("edit", text="⚙️")
        self.tree.heading("scheduled_time", text="Thời Gian Đăng")
        self.tree.heading("account", text="Tài Khoản")
        self.tree.heading("status", text="Trạng Thái")
        self.tree.heading("log", text="Log")
        self.tree.heading("delete", text="Xóa")

        # Columns
        self.tree.column("checkbox", width=40, anchor=tk.CENTER)
        self.tree.column("stt", width=50, anchor=tk.CENTER)
        self.tree.column("video", width=250)
        self.tree.column("edit", width=50, anchor=tk.CENTER)
        self.tree.column("scheduled_time", width=130, anchor=tk.CENTER)
        self.tree.column("account", width=160)
        self.tree.column("status", width=110, anchor=tk.CENTER)
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
        # ✅ Block khi đang chạy tất cả
        if self.is_running_all:
            messagebox.showwarning(
                "Không thể thực hiện",
                "⚠️ Đang ở chế độ 'Chạy tất cả'!\n\n"
                "Vui lòng nhấn '⏸ Dừng tất cả' để import files."
            )
            return

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
        # ✅ Block khi đang chạy tất cả
        if self.is_running_all:
            messagebox.showwarning(
                "Không thể thực hiện",
                "⚠️ Đang ở chế độ 'Chạy tất cả'!\n\n"
                "Vui lòng nhấn '⏸ Dừng tất cả' để import folder."
            )
            return

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

    def import_channel(self):
        """Import videos from YouTube or TikTok channel"""
        # ✅ Block khi đang chạy tất cả
        if self.is_running_all:
            messagebox.showwarning(
                "Không thể thực hiện",
                "⚠️ Đang ở chế độ 'Chạy tất cả'!\n\n"
                "Vui lòng nhấn '⏸ Dừng tất cả' để import channel."
            )
            return

        # Dialog to select platform and input channel URL
        dialog = tk.Toplevel(self)
        dialog.title("Nhập kênh YouTube/TikTok")
        dialog.geometry("600x400")
        dialog.grab_set()

        # Header
        ttk.Label(
            dialog,
            text="📺 Nhập kênh YouTube hoặc TikTok",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(20, 10))

        # Platform selection
        platform_frame = ttk.Labelframe(dialog, text="Chọn nền tảng", padding=10)
        platform_frame.pack(padx=20, pady=10, fill="x")

        platform_var = tk.StringVar(value="youtube")

        ttk.Radiobutton(
            platform_frame,
            text="📺 YouTube",
            variable=platform_var,
            value="youtube"
        ).pack(side="left", padx=20)

        ttk.Radiobutton(
            platform_frame,
            text="🎵 TikTok",
            variable=platform_var,
            value="tiktok"
        ).pack(side="left", padx=20)

        # Example label (updates based on platform)
        example_label = ttk.Label(
            dialog,
            text="",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        example_label.pack(pady=5)

        # Input frame
        input_frame = ttk.Frame(dialog)
        input_frame.pack(padx=20, pady=10, fill="x")

        ttk.Label(input_frame, text="Link kênh:", width=12).pack(side="left")
        entry_url = ttk.Entry(input_frame, width=50, font=("Segoe UI", 10))
        entry_url.pack(side="left", padx=5, fill="x", expand=True)

        # YouTube video count frame (only shown for YouTube)
        count_frame = ttk.Frame(dialog)
        count_frame.pack(padx=20, pady=5, fill="x")

        ttk.Label(count_frame, text="Số lượng video:", width=12).pack(side="left")
        entry_count = ttk.Spinbox(count_frame, from_=1, to=100, width=10)
        entry_count.set(20)
        entry_count.pack(side="left", padx=5)

        ttk.Label(
            count_frame,
            text="(Lấy N video mới nhất)",
            font=("Segoe UI", 9),
            foreground="gray"
        ).pack(side="left", padx=5)

        # YouTube filter frame (only shown for YouTube)
        filter_frame = ttk.Frame(dialog)
        filter_frame.pack(padx=20, pady=5, fill="x")

        ttk.Label(filter_frame, text="Loại video:", width=12).pack(side="left")

        mode_var = tk.StringVar(value="both")

        ttk.Radiobutton(
            filter_frame,
            text="📱 Shorts (<182s)",
            variable=mode_var,
            value="shorts"
        ).pack(side="left", padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="🎬 Long (≥182s)",
            variable=mode_var,
            value="long"
        ).pack(side="left", padx=5)

        ttk.Radiobutton(
            filter_frame,
            text="🎯 Cả 2",
            variable=mode_var,
            value="both"
        ).pack(side="left", padx=5)

        # Status label
        status_label = ttk.Label(dialog, text="", foreground="blue")
        status_label.pack(pady=10)

        # Update UI based on platform selection
        def on_platform_change(*args):
            if platform_var.get() == "youtube":
                example_label.config(text="Ví dụ: https://www.youtube.com/@channelname hoặc https://www.youtube.com/c/channelname")
                count_frame.pack(padx=20, pady=5, fill="x")
                filter_frame.pack(padx=20, pady=5, fill="x")
            else:
                example_label.config(text="Ví dụ: https://www.tiktok.com/@tiin.vn")
                count_frame.pack_forget()
                filter_frame.pack_forget()

        platform_var.trace_add("write", on_platform_change)
        on_platform_change()  # Initial update

        entry_url.focus()

        result = {"ok": False, "videos": [], "platform": ""}

        def on_fetch():
            url = entry_url.get().strip()
            if not url:
                messagebox.showerror("Lỗi", "Vui lòng nhập link kênh!", parent=dialog)
                return

            platform = platform_var.get()

            try:
                if platform == "youtube":
                    # ========== YOUTUBE ==========
                    # Check YouTube API key
                    youtube_key = multi_api_manager.get_next_youtube_key()
                    if not youtube_key:
                        messagebox.showerror(
                            "Lỗi",
                            "❌ Không có YouTube API key!\n\n"
                            "Vui lòng thêm YouTube API key trong:\n"
                            "🔑 Quản lý API → Tab YouTube API",
                            parent=dialog
                        )
                        return

                    # Get video count
                    try:
                        video_count = int(entry_count.get())
                        if video_count < 1:
                            raise ValueError
                    except ValueError:
                        messagebox.showerror("Lỗi", "Số lượng video phải >= 1", parent=dialog)
                        return

                    status_label.config(text=f"⏳ Đang quét kênh YouTube...", foreground="blue")
                    dialog.update()

                    # Extract channel ID
                    channel_id = extract_channel_id(url, multi_api_manager)
                    uploads_playlist_id = get_uploads_playlist_id(channel_id, multi_api_manager)

                    # Get latest videos (filter while fetching to get exactly N videos matching the mode)
                    from datetime import datetime, timezone
                    very_old_time = datetime(2000, 1, 1, tzinfo=timezone.utc)  # Get all videos since 2000

                    mode = mode_var.get()
                    videos = []
                    checked_count = 0
                    max_check = 200  # Tối đa check 200 video để tránh loop vô hạn

                    status_label.config(text=f"⏳ Đang quét kênh YouTube...", foreground="blue")
                    dialog.update()

                    # Lặp qua từng video và lọc trong lúc lấy
                    for vid_id, pub_time in iter_playlist_videos_newer_than(uploads_playlist_id, very_old_time, multi_api_manager):
                        checked_count += 1

                        # Fetch thông tin video này để check duration
                        video_details = fetch_video_details([vid_id], multi_api_manager)

                        if video_details:
                            video = video_details[0]

                            # Filter by mode
                            filtered = filter_videos_by_mode([video], mode)

                            if filtered:
                                videos.append(filtered[0])
                                status_label.config(
                                    text=f"⏳ Đã tìm thấy {len(videos)}/{video_count} video phù hợp (đã check {checked_count} video)...",
                                    foreground="blue"
                                )
                                dialog.update()

                                # Dừng khi đủ số lượng cần
                                if len(videos) >= video_count:
                                    break

                        # Dừng nếu đã check quá nhiều video
                        if checked_count >= max_check:
                            status_label.config(
                                text=f"⚠️ Đã check {max_check} video, chỉ tìm thấy {len(videos)} video phù hợp",
                                foreground="orange"
                            )
                            dialog.update()
                            break

                    if not videos:
                        status_label.config(text="❌ Không tìm thấy video nào", foreground="red")

                        mode_text = {
                            "shorts": "Shorts (<182s)",
                            "long": "Long (≥182s)",
                            "both": "tất cả"
                        }.get(mode, mode)

                        messagebox.showwarning(
                            "Không có video",
                            f"Không tìm thấy video {mode_text} nào từ kênh này (đã check {checked_count} video)",
                            parent=dialog
                        )
                        return

                    # Filter: only keep videos with valid URL
                    valid_videos = [v for v in videos if v.get("url")]

                    if not valid_videos:
                        status_label.config(text="❌ Không có video hợp lệ", foreground="red")

                        messagebox.showwarning(
                            "Không có video hợp lệ",
                            f"Tìm thấy {len(videos)} video nhưng không có video nào có URL hợp lệ.",
                            parent=dialog
                        )
                        return

                    status_label.config(
                        text=f"✅ Tìm thấy {len(valid_videos)} video hợp lệ",
                        foreground="green"
                    )

                    result["ok"] = True
                    result["videos"] = valid_videos
                    result["platform"] = "youtube"
                    result["channel_name"] = url.split("/")[-1]

                else:
                    # ========== TIKTOK ==========
                    # Check TikTok API key
                    tiktok_key = multi_api_manager.get_next_tiktok_key()
                    if not tiktok_key:
                        messagebox.showerror(
                            "Lỗi",
                            "❌ Không có TikTok API key!\n\n"
                            "Vui lòng thêm TikTok API key trong:\n"
                            "🔑 Quản lý API → Tab TikTok API",
                            parent=dialog
                        )
                        return

                    # Extract handle
                    handle = extract_tiktok_handle(url)
                    status_label.config(text=f"⏳ Đang quét kênh @{handle}...", foreground="blue")
                    dialog.update()

                    # Fetch videos from TikTok (get ALL videos, no time filter)
                    def log_msg(msg):
                        status_label.config(text=msg)
                        dialog.update()

                    all_videos = fetch_tiktok_videos(handle, tiktok_key, log_callback=log_msg)

                    if not all_videos:
                        status_label.config(text="❌ Không tìm thấy video nào", foreground="red")
                        messagebox.showwarning(
                            "Không có video",
                            f"Không tìm thấy video nào từ kênh @{handle}",
                            parent=dialog
                        )
                        return

                    # Filter: only keep videos with valid URL (no time check)
                    valid_videos = [v for v in all_videos if v.get("video_url")]

                    if not valid_videos:
                        status_label.config(text="❌ Không có video hợp lệ", foreground="red")
                        messagebox.showwarning(
                            "Không có video hợp lệ",
                            f"Tìm thấy {len(all_videos)} video nhưng không có video nào có URL hợp lệ.",
                            parent=dialog
                        )
                        return

                    # Convert to output format
                    converted = convert_to_output_format(valid_videos)

                    status_label.config(
                        text=f"✅ Tìm thấy {len(converted)} video hợp lệ",
                        foreground="green"
                    )

                    result["ok"] = True
                    result["videos"] = converted
                    result["platform"] = "tiktok"
                    result["channel_name"] = handle

                # Wait a bit before closing
                dialog.after(1000, dialog.destroy)

            except Exception as e:
                status_label.config(text=f"❌ Lỗi: {e}", foreground="red")
                messagebox.showerror("Lỗi", f"Không thể lấy video:\n{e}", parent=dialog)

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="✅ Quét kênh", command=on_fetch, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Hủy", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)

        # Bind Enter key
        entry_url.bind("<Return>", lambda e: on_fetch())

        dialog.wait_window()

        # Process results
        if result["ok"] and result["videos"]:
            videos = result["videos"]
            platform = result["platform"]
            channel_name = result.get("channel_name", "channel")

            # Create ScheduledPost for each video
            new_posts = []
            for idx, vid in enumerate(videos):
                post_id = f"{platform}_{channel_name}_{int(time.time() * 1000)}_{idx}"

                # Use video URL as "video_path" (will be downloaded when posting)
                post = ScheduledPost(
                    post_id=post_id,
                    video_path=vid["url"],  # Store video URL
                    scheduled_time_vn=None,
                    vm_name=None,
                    account_display="Chưa chọn",
                    title=vid["title"][:100],  # Limit title length
                    status="draft",
                    log_callback=self.append_log_line
                )

                new_posts.append(post)

            # Add to posts list
            self.posts.extend(new_posts)
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

            platform_display = "YouTube" if platform == "youtube" else "TikTok"
            messagebox.showinfo(
                "Thành công",
                f"✅ Đã thêm {len(new_posts)} video {platform_display} từ {channel_name}\n\n"
                f"Click vào cột ⚙️ để đặt lịch cho từng video."
            )

    def bulk_schedule(self):
        """Lên lịch hàng loạt cho các video trong table - chỉ áp thời gian"""
        # ✅ Block khi đang chạy tất cả
        if self.is_running_all:
            messagebox.showwarning(
                "Không thể thực hiện",
                "⚠️ Đang ở chế độ 'Chạy tất cả'!\n\n"
                "Vui lòng nhấn '⏸ Dừng tất cả' để lên lịch."
            )
            return

        # Lấy tất cả video trong table
        if not self.posts:
            messagebox.showinfo("Thông báo", "Không có video nào trong danh sách!")
            return

        # Dialog - CustomTkinter style
        dialog = ctk.CTkToplevel(self)
        dialog.title("Lên lịch hàng loạt")
        dialog.geometry("550x420")
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["bg_primary"])

        # Info
        ctk.CTkLabel(
            dialog,
            text=f"⚡ Lên lịch hàng loạt cho video",
            font=(FONTS["family"], FONTS["size_large"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        ).pack(pady=10)

        ctk.CTkLabel(
            dialog,
            text="(Máy ảo của mỗi video sẽ được giữ nguyên)",
            font=(FONTS["family"], FONTS["size_small"]),
            text_color=COLORS["text_secondary"]
        ).pack(pady=2)

        # ========== PHẠM VI VIDEO ==========
        range_frame = ctk.CTkFrame(dialog, fg_color=COLORS["bg_secondary"], corner_radius=DIMENSIONS["corner_radius_medium"])
        range_frame.pack(fill="x", padx=20, pady=(10, 5))

        # Title
        ctk.CTkLabel(
            range_frame,
            text="📌 Phạm vi video áp dụng",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Row: Start and End index
        index_row = ctk.CTkFrame(range_frame, fg_color="transparent")
        index_row.pack(fill="x", padx=10, pady=5)

        # Start index
        ctk.CTkLabel(index_row, text="Từ video thứ:", width=110, anchor="w").pack(side="left")
        entry_start_index = ctk.CTkEntry(index_row, width=80)
        entry_start_index.insert(0, "1")
        entry_start_index.pack(side="left", padx=5)

        # End index
        ctk.CTkLabel(index_row, text="Đến video thứ:", width=110, anchor="w").pack(side="left", padx=(20, 0))
        entry_end_index = ctk.CTkEntry(index_row, width=80)
        entry_end_index.insert(0, "999")
        entry_end_index.pack(side="left", padx=5)

        # Info label
        info_label = ctk.CTkLabel(
            range_frame,
            text=f"💡 Tổng số video hiện tại: {len(self.posts)}",
            font=(FONTS["family"], FONTS["size_small"]),
            text_color=COLORS["accent"]
        )
        info_label.pack(anchor="w", padx=10, pady=(5, 10))

        # ========== THỜI GIAN ==========
        time_frame = ctk.CTkFrame(dialog, fg_color=COLORS["bg_secondary"], corner_radius=DIMENSIONS["corner_radius_medium"])
        time_frame.pack(fill="x", padx=20, pady=5)

        # Title
        ctk.CTkLabel(
            time_frame,
            text="⏰ Cài đặt thời gian",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Start date picker
        ctk.CTkLabel(
            time_frame,
            text="Ngày bắt đầu (dd/mm/yyyy):",
            font=(FONTS["family"], FONTS["size_normal"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(5, 0))

        entry_start_date = ctk.CTkEntry(time_frame, width=400)
        default_date = datetime.now(VN_TZ).strftime("%d/%m/%Y")
        entry_start_date.insert(0, default_date)
        entry_start_date.pack(padx=10, pady=5)

        # Time slots
        ctk.CTkLabel(
            time_frame,
            text="Khung giờ (cách nhau bởi dấu phẩy):",
            font=(FONTS["family"], FONTS["size_normal"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(5, 0))

        ctk.CTkLabel(
            time_frame,
            text="Ví dụ: 06:00, 10:00, 18:00, 22:00",
            font=(FONTS["family"], FONTS["size_small"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=10)

        entry_time_slots = ctk.CTkEntry(time_frame, width=400)
        entry_time_slots.insert(0, "06:00, 10:00, 18:00, 22:00")
        entry_time_slots.pack(padx=10, pady=(5, 10))

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
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="✅ Áp dụng",
            command=on_apply,
            **get_button_style("success"),
            width=140
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame,
            text="❌ Hủy",
            command=dialog.destroy,
            **get_button_style("secondary"),
            width=140
        ).pack(side=tk.LEFT, padx=5)

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

    def bulk_assign_vm(self):
        """Đặt máy ảo hàng loạt cho các video trong table - chỉ áp máy ảo"""
        # ✅ Block khi đang chạy tất cả
        if self.is_running_all:
            messagebox.showwarning(
                "Không thể thực hiện",
                "⚠️ Đang ở chế độ 'Chạy tất cả'!\n\n"
                "Vui lòng nhấn '⏸ Dừng tất cả' để đặt máy ảo."
            )
            return

        # Lấy tất cả video trong table
        if not self.posts:
            messagebox.showinfo("Thông báo", "Không có video nào trong danh sách!")
            return

        # Lấy danh sách máy ảo
        vm_list = get_vm_list_with_insta()
        if not vm_list:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy máy ảo nào!\n\nVui lòng thêm máy ảo trong tab 'Quản lý User'.")
            return

        # Dialog - CustomTkinter style
        dialog = ctk.CTkToplevel(self)
        dialog.title("Đặt máy ảo hàng loạt")
        dialog.geometry("600x550")
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["bg_primary"])

        # Info
        ctk.CTkLabel(
            dialog,
            text=f"⚙️ Đặt máy ảo hàng loạt cho video",
            font=(FONTS["family"], FONTS["size_large"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        ).pack(pady=10)

        ctk.CTkLabel(
            dialog,
            text="(Thời gian của mỗi video sẽ được giữ nguyên)",
            font=(FONTS["family"], FONTS["size_small"]),
            text_color=COLORS["text_secondary"]
        ).pack(pady=2)

        # ========== PHẠM VI VIDEO ==========
        range_frame = ctk.CTkFrame(dialog, fg_color=COLORS["bg_secondary"], corner_radius=DIMENSIONS["corner_radius_medium"])
        range_frame.pack(fill="x", padx=20, pady=(10, 5))

        # Title
        ctk.CTkLabel(
            range_frame,
            text="📌 Phạm vi video áp dụng",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Row: Start and End index
        index_row = ctk.CTkFrame(range_frame, fg_color="transparent")
        index_row.pack(fill="x", padx=10, pady=5)

        # Start index
        ctk.CTkLabel(index_row, text="Từ video thứ:", width=110, anchor="w").pack(side="left")
        entry_start_index = ctk.CTkEntry(index_row, width=80)
        entry_start_index.insert(0, "1")
        entry_start_index.pack(side="left", padx=5)

        # End index
        ctk.CTkLabel(index_row, text="Đến video thứ:", width=110, anchor="w").pack(side="left", padx=(20, 0))
        entry_end_index = ctk.CTkEntry(index_row, width=80)
        entry_end_index.insert(0, "999")
        entry_end_index.pack(side="left", padx=5)

        # Info label
        info_label = ctk.CTkLabel(
            range_frame,
            text=f"💡 Tổng số video hiện tại: {len(self.posts)}",
            font=(FONTS["family"], FONTS["size_small"]),
            text_color=COLORS["accent"]
        )
        info_label.pack(anchor="w", padx=10, pady=(5, 10))

        # ========== CHỌN MÁY ẢO ==========
        vm_outer_frame = ctk.CTkFrame(dialog, fg_color=COLORS["bg_secondary"], corner_radius=DIMENSIONS["corner_radius_medium"])
        vm_outer_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # Title
        ctk.CTkLabel(
            vm_outer_frame,
            text="🖥️ Chọn máy ảo",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            vm_outer_frame,
            text="Các máy ảo sẽ được áp dụng theo thứ tự (round-robin):",
            font=(FONTS["family"], FONTS["size_small"]),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=10, pady=(0, 5))

        # Scrollable frame for VM checkboxes - Using CTkScrollableFrame
        scrollable_frame = ctk.CTkScrollableFrame(
            vm_outer_frame,
            height=180,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=DIMENSIONS["corner_radius_small"]
        )
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Checkboxes for each VM
        vm_vars = []
        for vm_info in vm_list:
            var = tk.BooleanVar(value=True)  # Default: all selected
            vm_vars.append((vm_info, var))
            ctk.CTkCheckBox(
                scrollable_frame,
                text=vm_info["display"],
                variable=var,
                font=(FONTS["family"], FONTS["size_normal"]),
                text_color=COLORS["text_primary"],
                fg_color=COLORS["success"],
                hover_color=COLORS["success_hover"]
            ).pack(anchor="w", padx=5, pady=2)

        # Select/Deselect all buttons
        btn_select_frame = ctk.CTkFrame(vm_outer_frame, fg_color="transparent")
        btn_select_frame.pack(fill="x", padx=10, pady=(0, 10))

        def select_all():
            for _, var in vm_vars:
                var.set(True)

        def deselect_all():
            for _, var in vm_vars:
                var.set(False)

        ctk.CTkButton(
            btn_select_frame,
            text="✅ Chọn tất cả",
            command=select_all,
            **get_button_style("success"),
            width=140
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_select_frame,
            text="❌ Bỏ chọn tất cả",
            command=deselect_all,
            **get_button_style("secondary"),
            width=140
        ).pack(side="left", padx=5)

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

            # Get selected VMs
            selected_vms = [vm_info for vm_info, var in vm_vars if var.get()]
            if not selected_vms:
                messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 máy ảo", parent=dialog)
                return

            # Apply VMs to posts (only within range)
            vm_index = 0
            applied_count = 0

            for idx, post in enumerate(self.posts, start=1):
                # Chỉ áp dụng cho video trong phạm vi
                if idx < start_idx or idx > end_idx:
                    continue

                # Áp dụng máy ảo theo round-robin
                vm_info = selected_vms[vm_index]
                post.vm_name = vm_info["vm_name"]
                post.account_display = vm_info["display"]

                # Nếu đã có thời gian thì set pending, chưa thì để draft
                if post.scheduled_time_vn:
                    post.status = "pending"
                    # Mặc định để paused, người dùng phải nhấn Start để chạy
                    post.is_paused = True
                else:
                    post.status = "draft"

                applied_count += 1

                # Move to next VM
                vm_index += 1
                if vm_index >= len(selected_vms):
                    vm_index = 0

            result["ok"] = True
            result["applied_count"] = applied_count
            result["start_idx"] = start_idx
            result["end_idx"] = min(end_idx, len(self.posts))
            result["vm_count"] = len(selected_vms)
            dialog.destroy()

        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="✅ Áp dụng",
            command=on_apply,
            **get_button_style("success"),
            width=140
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame,
            text="❌ Hủy",
            command=dialog.destroy,
            **get_button_style("secondary"),
            width=140
        ).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()

        if result["ok"]:
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

            applied_count = result.get("applied_count", 0)
            start_idx = result.get("start_idx", 1)
            end_idx = result.get("end_idx", len(self.posts))
            vm_count = result.get("vm_count", 0)

            messagebox.showinfo(
                "Thành công",
                f"✅ Đã đặt máy ảo thành công!\n\n"
                f"📊 Phạm vi: Video {start_idx} đến {end_idx}\n"
                f"✔️ Đã áp dụng: {applied_count} video\n"
                f"🖥️ Số máy ảo: {vm_count}"
            )

    def export_to_csv(self):
        """Xuất danh sách video ra CSV để backup"""
        if not self.posts:
            messagebox.showinfo("Thông báo", "Không có video nào để xuất!")
            return

        # Hỏi vị trí lưu file
        default_name = f"backup_posts_{datetime.now(VN_TZ).strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name,
            title="Xuất danh sách video"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(['vị_trí_file', 'thời_gian_đăng', 'máy_ảo', 'trạng_thái'])

                # Data
                for post in self.posts:
                    time_str = post.scheduled_time_vn.strftime("%d/%m/%Y %H:%M") if post.scheduled_time_vn else ""
                    vm_name = post.vm_name or ""
                    status = post.status or "draft"

                    writer.writerow([
                        post.video_path,
                        time_str,
                        vm_name,
                        status
                    ])

            messagebox.showinfo(
                "Thành công",
                f"✅ Đã xuất {len(self.posts)} video ra CSV!\n\n"
                f"📁 File: {os.path.basename(file_path)}"
            )

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất CSV:\n{e}")

    def import_from_csv(self):
        """Nhập danh sách video từ CSV"""
        # Confirm nếu đã có posts
        if self.posts:
            confirm = messagebox.askyesno(
                "Xác nhận",
                "⚠️ Bạn đang có video trong danh sách!\n\n"
                "Nhập CSV sẽ THAY THẾ toàn bộ danh sách hiện tại.\n\n"
                "Bạn có muốn tiếp tục không?"
            )
            if not confirm:
                return

        # Chọn file CSV
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Chọn file CSV để nhập"
        )

        if not file_path:
            return

        try:
            imported_posts = []
            errors = []
            line_num = 0

            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # Skip header

                if not header:
                    raise ValueError("File CSV rỗng!")

                for row in reader:
                    line_num += 1

                    if len(row) < 4:
                        errors.append(f"Dòng {line_num}: Thiếu cột (cần 4 cột)")
                        continue

                    video_path = row[0].strip()
                    time_str = row[1].strip()
                    vm_name = row[2].strip()
                    status = row[3].strip()

                    # Validate video file exists
                    if not os.path.exists(video_path):
                        errors.append(f"Dòng {line_num}: File không tồn tại: {video_path}")
                        continue

                    # Parse time
                    scheduled_time = None
                    if time_str:
                        try:
                            scheduled_time = datetime.strptime(time_str, "%d/%m/%Y %H:%M")
                            scheduled_time = scheduled_time.replace(tzinfo=VN_TZ)
                        except:
                            errors.append(f"Dòng {line_num}: Thời gian không hợp lệ: {time_str}")
                            continue

                    # Create post
                    post_id = f"post_{int(time.time() * 1000)}_{line_num}"
                    post = ScheduledPost(
                        post_id=post_id,
                        video_path=video_path,
                        scheduled_time_vn=scheduled_time,
                        vm_name=vm_name if vm_name else None,
                        account_display=None,
                        title=os.path.basename(video_path),
                        status=status if status else "draft",
                        is_paused=True,
                        log_callback=self.append_log_line
                    )

                    # Set account_display from VM
                    if post.vm_name:
                        vm_list = get_vm_list_with_insta()
                        for vm_info in vm_list:
                            if vm_info["vm_name"] == post.vm_name:
                                post.account_display = vm_info["display"]
                                break

                    imported_posts.append(post)

            # Replace current posts
            self.posts = imported_posts
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

            # Show result
            if errors:
                error_msg = "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_msg += f"\n... và {len(errors) - 10} lỗi khác"

                messagebox.showwarning(
                    "Nhập CSV hoàn tất",
                    f"✅ Đã nhập {len(imported_posts)} video\n"
                    f"⚠️ Có {len(errors)} lỗi:\n\n{error_msg}"
                )
            else:
                messagebox.showinfo(
                    "Thành công",
                    f"✅ Đã nhập {len(imported_posts)} video từ CSV!"
                )

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể nhập CSV:\n{e}")

    def open_api_manager(self):
        """Mở dialog quản lý API keys cho YouTube và TikTok"""
        multi_api_manager.refresh()

        # Main dialog
        dialog = tk.Toplevel(self)
        dialog.title("Quản lý API Keys")
        dialog.geometry("800x550")
        dialog.grab_set()

        # Notebook (tabs)
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: YouTube
        youtube_frame = ttk.Frame(notebook)
        notebook.add(youtube_frame, text="📺 YouTube API")
        self._build_api_tab(youtube_frame, "youtube", dialog)

        # Tab 2: TikTok
        tiktok_frame = ttk.Frame(notebook)
        notebook.add(tiktok_frame, text="🎵 TikTok API")
        self._build_api_tab(tiktok_frame, "tiktok", dialog)

        # Info label
        info_label = ttk.Label(
            dialog,
            text="💡 File lưu tại: data/api/apis.json",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        info_label.pack(pady=(0, 10))

    def _build_api_tab(self, parent, platform, dialog):
        """Xây dựng nội dung cho 1 tab API"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Listbox
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        listbox = tk.Listbox(list_frame, height=15, font=("Courier", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        # Status label
        status_label = ttk.Label(frame, text="", foreground="blue")
        status_label.pack(fill=tk.X, pady=(0, 10))

        # Load keys
        def load_keys():
            listbox.delete(0, tk.END)
            keys = multi_api_manager.get_keys(platform)
            for i, k in enumerate(keys):
                display = f"[{i+1}] {k[:30]}...{k[-10:]}" if len(k) > 45 else f"[{i+1}] {k}"
                listbox.insert(tk.END, display)
            status_label.config(text=f"📊 Tổng: {len(keys)} API keys", foreground="blue")

        load_keys()

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        def add_key():
            from tkinter import simpledialog
            key = simpledialog.askstring(
                f"Thêm {platform.upper()} API",
                f"Nhập {platform.upper()} API key:",
                parent=dialog
            )
            if key and key.strip():
                if multi_api_manager.add_key(platform, key.strip()):
                    load_keys()
                    status_label.config(text="✅ Đã thêm API key mới", foreground="green")
                else:
                    status_label.config(text="⚠️ API key đã tồn tại", foreground="orange")

        def remove_key():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Xóa", "Hãy chọn 1 key để xóa", parent=dialog)
                return

            idx = sel[0]
            confirm = messagebox.askyesno(
                "Xác nhận",
                f"Xóa API key #{idx+1}?",
                parent=dialog
            )
            if confirm:
                if multi_api_manager.remove_key(platform, idx):
                    load_keys()
                    status_label.config(text=f"✅ Đã xóa API key #{idx+1}", foreground="green")

        def copy_key():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Copy", "Hãy chọn 1 key để copy", parent=dialog)
                return

            idx = sel[0]
            keys = multi_api_manager.get_keys(platform)
            if 0 <= idx < len(keys):
                dialog.clipboard_clear()
                dialog.clipboard_append(keys[idx])
                status_label.config(text=f"✅ Đã copy API key #{idx+1} vào clipboard", foreground="green")

        ttk.Button(btn_frame, text="➕ Thêm", command=add_key, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🗑️ Xóa", command=remove_key, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="📋 Copy", command=copy_key, width=12).pack(side=tk.LEFT, padx=3)

        # Buttons Row 2: Check API
        btn_frame2 = ttk.Frame(frame)
        btn_frame2.pack(fill=tk.X, pady=(5, 0))

        def check_selected():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Kiểm tra", "Hãy chọn 1 key để kiểm tra", parent=dialog)
                return

            idx = sel[0]
            keys = multi_api_manager.get_keys(platform)
            if idx >= len(keys):
                return

            api_key = keys[idx]
            status_label.config(text=f"⏳ Đang kiểm tra API key #{idx+1}...", foreground="blue")
            dialog.update()

            def do_check():
                if platform == "youtube":
                    result = check_api_key_valid(api_key)
                else:  # tiktok
                    result = check_tiktok_api_key_valid(api_key)

                dialog.after(0, lambda: show_check_result(idx, result))

            threading.Thread(target=do_check, daemon=True).start()

        def show_check_result(idx, result):
            msg = result["message"]
            if result.get("quota_remaining") is not None:
                msg += f" (Quota: {result['quota_remaining']})"

            color = "green" if result["valid"] else "red"
            status_label.config(text=f"API key #{idx+1}: {msg}", foreground=color)

        def check_all():
            keys = multi_api_manager.get_keys(platform)
            if not keys:
                messagebox.showinfo("Kiểm tra tất cả", "Không có API key nào để kiểm tra", parent=dialog)
                return

            status_label.config(text="⏳ Đang kiểm tra tất cả API keys...", foreground="blue")
            dialog.update()

            def do_check_all():
                results = []
                for i, api_key in enumerate(keys):
                    if platform == "youtube":
                        result = check_api_key_valid(api_key)
                    else:  # tiktok
                        result = check_tiktok_api_key_valid(api_key)
                    results.append((i+1, result))

                dialog.after(0, lambda: show_all_results(results))

            threading.Thread(target=do_check_all, daemon=True).start()

        def show_all_results(results):
            valid_count = sum(1 for _, r in results if r["valid"])
            invalid_count = len(results) - valid_count

            summary = f"✓ Hoàn thành: {valid_count} keys hoạt động, {invalid_count} keys lỗi"
            status_label.config(text=summary, foreground="green" if invalid_count == 0 else "orange")

            details = []
            for idx, result in results:
                status_icon = "✓" if result["valid"] else "✗"
                details.append(f"Key #{idx}: {status_icon} {result['message']}")

            detail_msg = "\n".join(details)

            detail_win = tk.Toplevel(dialog)
            detail_win.title("Kết quả kiểm tra API keys")
            detail_win.geometry("600x400")
            detail_win.grab_set()

            txt = tk.Text(detail_win, wrap="word", font=("Courier", 9))
            txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            txt.insert("1.0", detail_msg)
            txt.config(state="disabled")

            ttk.Button(detail_win, text="Đóng", command=detail_win.destroy).pack(pady=5)

        ttk.Button(btn_frame2, text="🔍 Kiểm tra key đã chọn", command=check_selected, width=22).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame2, text="🔍 Kiểm tra tất cả", command=check_all, width=18).pack(side=tk.LEFT, padx=3)

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
                status="draft",
                log_callback=self.append_log_line
            )

            self.posts.append(post)

        # Save và refresh
        save_scheduled_posts(self.posts)
        self.load_posts_to_table()
        messagebox.showinfo(
            "Thành công",
            f"Đã thêm {len(files)} video vào danh sách.\nClick vào cột ⚙️ để đặt lịch cho từng video."
        )

    def load_posts_to_table(self, auto_sort=False):
        """Load posts to table

        Args:
            auto_sort: Nếu True, tự động sắp xếp theo self.sort_by.
                      Nếu False, giữ nguyên thứ tự trong self.posts (không sort).
                      Mặc định False để giữ nguyên vị trí khi edit.
        """
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        # ✅ CHỈ SORT khi auto_sort=True (khi user dùng nút lọc)
        if auto_sort:
            # Sắp xếp theo tiêu chí được chọn
            if self.sort_by == "time":
                # Sắp xếp theo thời gian (None values last)
                sorted_posts = sorted(
                    self.posts,
                    key=lambda p: (p.scheduled_time_vn is None, p.scheduled_time_vn or datetime.min.replace(tzinfo=VN_TZ)),
                    reverse=(self.sort_order == "desc")
                )
            elif self.sort_by == "vm":
                # Sắp xếp theo máy ảo (None/empty last)
                sorted_posts = sorted(
                    self.posts,
                    key=lambda p: (p.vm_name is None or p.vm_name == "", p.vm_name or ""),
                    reverse=(self.sort_order == "desc")
                )
            elif self.sort_by == "status":
                # Sắp xếp theo trạng thái (draft, pending, processing, posted, failed)
                status_order = {"draft": 0, "pending": 1, "processing": 2, "posted": 3, "failed": 4}
                sorted_posts = sorted(
                    self.posts,
                    key=lambda p: status_order.get(p.status, 99),
                    reverse=(self.sort_order == "desc")
                )
            elif self.sort_by == "name":
                # Sắp xếp theo tên video
                sorted_posts = sorted(
                    self.posts,
                    key=lambda p: p.title.lower(),
                    reverse=(self.sort_order == "desc")
                )
            else:
                # Mặc định: theo thời gian
                sorted_posts = sorted(
                    self.posts,
                    key=lambda p: (p.scheduled_time_vn is None, p.scheduled_time_vn or datetime.min.replace(tzinfo=VN_TZ)),
                    reverse=(self.sort_order == "desc")
                )
        else:
            # ✅ KHÔNG SORT: Giữ nguyên thứ tự hiện tại
            sorted_posts = self.posts

        # Add to table
        for idx, post in enumerate(sorted_posts, start=1):
            status_icon = {
                "draft": "⚙️ Chưa cấu hình",
                "pending": "⏳ Chờ",
                "processing": "🔄 Đang đăng",
                "posted": "✅ Đã đăng",
                "failed": "❌ Thất bại"
            }.get(post.status, post.status)

            # Hiển thị thời gian
            if post.post_now:
                scheduled_time_display = "⚡ Đăng ngay"
            elif post.scheduled_time_vn:
                scheduled_time_display = post.scheduled_time_vn.strftime("%d/%m/%Y %H:%M")
            else:
                scheduled_time_display = "Chưa đặt"

            # Checkbox status
            checkbox_icon = "☑" if self.checked_posts.get(post.id, False) else "☐"

            # Striped rows
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                tk.END,
                iid=post.id,
                values=(
                    checkbox_icon,
                    idx,
                    post.title,  # Hiển thị title thay vì video_name
                    "⚙️",
                    scheduled_time_display,
                    post.account_display,
                    status_icon,
                    "📋",
                    "✖"
                ),
                tags=(tag,)
            )

        # Cập nhật icon header checkbox dựa trên trạng thái hiện tại
        if self.posts:
            checked_count = sum(1 for post in self.posts if self.checked_posts.get(post.id, False))
            if checked_count == len(self.posts):
                self.tree.heading("checkbox", text="☑", command=self.toggle_all_checkboxes)
            else:
                self.tree.heading("checkbox", text="☐", command=self.toggle_all_checkboxes)

        # Cập nhật label đếm số lượng video
        total = len(self.posts)
        draft = sum(1 for p in self.posts if p.status == "draft")
        pending = sum(1 for p in self.posts if p.status == "pending")
        processing = sum(1 for p in self.posts if p.status == "processing")
        posted = sum(1 for p in self.posts if p.status == "posted")
        failed = sum(1 for p in self.posts if p.status == "failed")

        self.count_label.configure(
            text=f"📊 Tổng: {total} | ⚙️ Chưa cấu hình: {draft} | ⏳ Chờ: {pending} | "
                 f"🔄 Đang đăng: {processing} | ✅ Đã đăng: {posted} | ❌ Thất bại: {failed}"
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

        # ✅ CHỈ CHO XEM LOG khi đang chạy tất cả
        if self.is_running_all and col != "log":
            messagebox.showwarning(
                "Không thể chỉnh sửa",
                "⚠️ Đang ở chế độ 'Chạy tất cả'!\n\n"
                "Vui lòng nhấn '⏸ Dừng tất cả' để chỉnh sửa."
            )
            return

        if col == "checkbox":
            # Toggle checkbox
            self.checked_posts[post.id] = not self.checked_posts.get(post.id, False)
            self.load_posts_to_table()
        elif col == "edit":
            self.edit_post_config(post)
        elif col == "log":
            self.open_log_window(post)
        elif col == "delete":
            self.delete_post(post)

    def run_all_videos(self):
        """Chạy tất cả video có thể chạy được (không hiện popup)"""
        # ✅ Set flag để khoá table
        self.is_running_all = True

        started_count = 0
        now = datetime.now(VN_TZ)

        for post in self.posts:
            # Bỏ qua các trường hợp không thể chạy
            if post.status == "draft":
                continue
            if post.status == "posted":
                continue
            if post.status == "processing":
                continue

            # Bỏ qua nếu đang chạy rồi
            if not post.is_paused:
                continue

            # Kiểm tra thời gian (nếu không phải đăng ngay)
            if not post.post_now:
                if post.scheduled_time_vn and post.scheduled_time_vn <= now:
                    # Thời gian đã qua, bỏ qua
                    continue

            # Kích hoạt video này
            if post.post_now:
                post.scheduled_time_vn = datetime.now(VN_TZ)
                post.post_now = False
                post.log("⚡ Đăng ngay - Đã set thời gian = hiện tại (từ 'Chạy tất cả')")

            post.is_paused = False
            post.log("▶ Đã được kích hoạt từ 'Chạy tất cả'")
            started_count += 1

        # Lưu và refresh nếu có thay đổi
        if started_count > 0:
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

    def stop_all_videos(self):
        """Dừng tất cả video đang chạy (không hiện popup)"""
        # ✅ Clear flag để mở khoá table
        self.is_running_all = False

        stopped_count = 0

        for post in self.posts:
            # Chỉ dừng video đang chạy (is_paused = False)
            if post.is_paused:
                continue

            # Không cho dừng video đang processing hoặc đã posted
            if post.status == "processing":
                continue
            if post.status == "posted":
                continue

            # Dừng video này
            post.is_paused = True
            post.log("⏸ Đã được dừng từ 'Dừng tất cả'")
            stopped_count += 1

        # Lưu và refresh nếu có thay đổi
        if stopped_count > 0:
            save_scheduled_posts(self.posts)
            self.load_posts_to_table()

    def delete_selected_videos(self):
        """Xóa tất cả video đã được chọn checkbox"""
        # ✅ Block khi đang chạy tất cả
        if self.is_running_all:
            messagebox.showwarning(
                "Không thể thực hiện",
                "⚠️ Đang ở chế độ 'Chạy tất cả'!\n\n"
                "Vui lòng nhấn '⏸ Dừng tất cả' để xóa videos."
            )
            return

        # Lấy danh sách post_id đã được chọn
        selected_ids = [post_id for post_id, checked in self.checked_posts.items() if checked]

        if not selected_ids:
            messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất 1 video để xóa")
            return

        # Kiểm tra xem có video nào đang processing không
        processing_count = 0
        for post in self.posts:
            if post.id in selected_ids and post.status == "processing":
                processing_count += 1

        if processing_count > 0:
            messagebox.showwarning(
                "Cảnh báo",
                f"Có {processing_count} video đang đăng, không thể xóa!\n\nVui lòng bỏ chọn các video đang đăng."
            )
            return

        # Xác nhận xóa
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa {len(selected_ids)} video đã chọn?"
        )

        if not confirm:
            return

        # Xóa các video đã chọn
        self.posts = [post for post in self.posts if post.id not in selected_ids]

        # Xóa khỏi checked_posts
        for post_id in selected_ids:
            if post_id in self.checked_posts:
                del self.checked_posts[post_id]

        # Lưu và refresh
        save_scheduled_posts(self.posts)
        self.load_posts_to_table()

        messagebox.showinfo("Thành công", f"Đã xóa {len(selected_ids)} video")

    def toggle_all_checkboxes(self):
        """Chọn/Bỏ chọn tất cả checkbox khi click vào header"""
        if not self.posts:
            return

        # Kiểm tra xem có bao nhiêu video đã được chọn
        checked_count = sum(1 for post in self.posts if self.checked_posts.get(post.id, False))

        # Nếu tất cả đã chọn → bỏ chọn tất cả
        # Nếu chưa chọn hết → chọn tất cả
        should_check = (checked_count < len(self.posts))

        # Cập nhật trạng thái cho tất cả video
        for post in self.posts:
            self.checked_posts[post.id] = should_check

        # Refresh bảng (load_posts_to_table sẽ tự động cập nhật icon header)
        self.load_posts_to_table()

    def on_sort_change(self, event=None):
        """Xử lý khi thay đổi tiêu chí sắp xếp"""
        selected = self.sort_combo.get()

        # Map từ text hiển thị sang sort_by value
        sort_map = {
            "Thời gian đăng": "time",
            "Máy ảo": "vm",
            "Trạng thái": "status",
            "Tên video": "name"
        }

        self.sort_by = sort_map.get(selected, "time")
        self.load_posts_to_table(auto_sort=True)  # ✅ Sort khi user chọn tiêu chí

    def toggle_sort_order(self):
        """Đổi chiều sắp xếp (tăng dần <-> giảm dần)"""
        if self.sort_order == "asc":
            self.sort_order = "desc"
            self.sort_order_btn.configure(text="⬇️ Giảm dần")
        else:
            self.sort_order = "asc"
            self.sort_order_btn.configure(text="⬆️ Tăng dần")

        self.load_posts_to_table(auto_sort=True)  # ✅ Sort khi user đổi chiều

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
            text=f"📹 File gốc: {post.video_name}",
            font=("Segoe UI", 9)
        ).pack(pady=(10, 5))

        # Title input
        title_frame = ttk.Frame(dialog)
        title_frame.pack(padx=20, pady=(0, 10), fill="x")
        ttk.Label(title_frame, text="Tên video:", width=12).pack(side="left")
        title_entry = ttk.Entry(title_frame, width=50, font=("Segoe UI", 10))
        title_entry.pack(side="left", padx=5, fill="x", expand=True)
        title_entry.insert(0, post.title)  # Load existing title

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
                # Đăng ngay - sẽ set thời gian khi nhấn Start
                scheduled_time = None
                post_now_flag = True
            else:
                # Chọn thời gian cụ thể từ wheel picker
                try:
                    day = int(wheel_day.get())
                    month = int(wheel_month.get())
                    year = int(wheel_year.get())
                    hour = int(wheel_hour.get())
                    minute = int(wheel_minute.get())

                    scheduled_time = datetime(year, month, day, hour, minute, tzinfo=VN_TZ)
                    post_now_flag = False
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
            post.post_now = post_now_flag
            post.title = title_entry.get().strip() or post.video_name  # Save custom title
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
        win.geometry("800x480")
        win.grab_set()

        # Text widget
        txt = tk.Text(win, wrap="word", state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)

        # Show existing logs
        if post.logs:
            txt.config(state="normal")
            txt.insert("1.0", "\n".join(post.logs))
            txt.see("end")
            txt.config(state="disabled")

        win.text_log = txt
        self.log_windows[post.id] = win

        # Buttons frame
        btns = tk.Frame(win)
        btns.pack(fill=tk.X, pady=5)

        def clear_logs():
            post.logs.clear()
            txt.config(state="normal")
            txt.delete("1.0", tk.END)
            txt.config(state="disabled")

        ttk.Button(btns, text="Xóa lịch sử", command=clear_logs).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Đóng", command=win.destroy).pack(side=tk.RIGHT, padx=4)

    def delete_post(self, post: ScheduledPost):
        """Delete a scheduled post"""
        if post.status == "processing":
            messagebox.showwarning("Cảnh báo", "Không thể xóa post đang xử lý!")
            return

        # Xóa trực tiếp không cần confirm
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

        except:
            pass

        self.after(200, self.process_ui_queue)

    def cleanup(self):
        """
        ✅ Cleanup khi đóng app - Dừng THẬT SỰ tất cả threads và tắt VMs
        """
        if self.is_shutting_down:
            return  # Tránh cleanup nhiều lần

        self.is_shutting_down = True
        self.logger.info("=" * 50)
        self.logger.info("🛑 BẮT ĐẦU CLEANUP TAB_POST")
        self.logger.info("=" * 50)

        try:
            # 1️⃣ Stop scheduler
            if self.scheduler and self.scheduler.is_alive():
                self.logger.info("⏸️ Đang dừng scheduler...")
                self.scheduler.stop()
                self.scheduler.join(timeout=5)  # Đợi tối đa 5 giây
                if self.scheduler.is_alive():
                    self.logger.warning("⚠️ Scheduler không dừng sau 5 giây")
                else:
                    self.logger.info("✅ Scheduler đã dừng")

            # 2️⃣ Set stop_requested cho TẤT CẢ posts đang chạy
            running_posts = [p for p in self.posts if p.status == "processing"]
            if running_posts:
                self.logger.info(f"🛑 Đang dừng {len(running_posts)} posts đang chạy...")
                for post in running_posts:
                    post.stop_requested = True
                    post.is_paused = True
                    post.status = "pending"  # Reset về pending
                    self.logger.info(f"   - Dừng post: {post.id} ({post.title})")

            # 3️⃣ Đợi threads kết thúc (timeout 10 giây)
            self.logger.info("⏳ Đợi threads kết thúc (timeout 10s)...")
            import time
            wait_start = time.time()
            while time.time() - wait_start < 10:
                if not self.scheduler or not hasattr(self.scheduler, 'running_posts'):
                    break
                if len(self.scheduler.running_posts) == 0:
                    self.logger.info("✅ Tất cả threads đã kết thúc")
                    break
                time.sleep(0.5)
            else:
                remaining = len(self.scheduler.running_posts) if self.scheduler and hasattr(self.scheduler, 'running_posts') else 0
                if remaining > 0:
                    self.logger.warning(f"⚠️ Còn {remaining} threads chưa kết thúc sau 10s")

            # 4️⃣ Tắt TẤT CẢ VMs đang được sử dụng bởi posts
            self.logger.info("🛑 Đang tắt tất cả VMs...")
            import subprocess
            from config import get_ldconsole_path

            # Collect tất cả VMs từ posts
            vms_to_check = set()
            for post in self.posts:
                if post.vm_name:
                    vms_to_check.add(post.vm_name)

            self.logger.info(f"📋 Kiểm tra {len(vms_to_check)} VMs...")

            # Check từng VM xem có đang chạy không, rồi tắt
            ldconsole = get_ldconsole_path()
            if ldconsole and vms_to_check:
                try:
                    # List tất cả VMs đang chạy
                    result = subprocess.run(
                        [ldconsole, "list2"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=10
                    )

                    running_vms = set()
                    for line in result.stdout.splitlines():
                        parts = line.split(",")
                        if len(parts) >= 5:
                            vm_name = parts[1].strip()
                            is_running = (parts[4].strip() == "1")
                            if is_running and vm_name in vms_to_check:
                                running_vms.add(vm_name)

                    self.logger.info(f"🔍 Tìm thấy {len(running_vms)} VMs đang chạy: {running_vms}")

                    # Tắt từng VM đang chạy
                    for vm_name in running_vms:
                        try:
                            self.logger.info(f"   🛑 Tắt VM: {vm_name}")
                            subprocess.run(
                                [ldconsole, "quit", "--name", vm_name],
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                timeout=10
                            )
                            self.logger.info(f"   ✅ Đã gửi lệnh tắt VM: {vm_name}")
                        except Exception as e:
                            self.logger.error(f"   ❌ Lỗi khi tắt VM {vm_name}: {e}")

                    if len(running_vms) > 0:
                        self.logger.info("⏳ Chờ 3 giây để VMs tắt...")
                        import time
                        time.sleep(3)

                except Exception as e:
                    self.logger.error(f"❌ Lỗi khi check/tắt VMs: {e}")

            # 5️⃣ Save state cuối cùng
            self.logger.info("💾 Lưu state cuối cùng...")
            save_scheduled_posts(self.posts)
            self.logger.info("✅ Đã lưu state")

            self.logger.info("=" * 50)
            self.logger.info("✅ CLEANUP TAB_POST HOÀN TẤT")
            self.logger.info("=" * 50)

        except Exception as e:
            self.logger.exception(f"❌ Lỗi trong cleanup: {e}")

    def __del__(self):
        """Cleanup when tab is destroyed"""
        self.cleanup()
##test commit