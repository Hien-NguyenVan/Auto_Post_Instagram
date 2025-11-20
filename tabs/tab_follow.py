# -*- coding: utf-8 -*-
"""
YouTube Multi-Stream Watcher GUI
- Nút API: quản lý list API key từ E:\tool_ld\data\api\apis.json (YouTube & TikTok)
- Nút "Thêm luồng" (góc trên bên phải)
- Bảng liệt kê luồng: STT, Tên luồng, Theo dõi trang, Thời gian quét, Trạng thái, Chạy, Dừng, Log, Sửa, Xóa
- Mỗi luồng chạy độc lập & đồng thời (thread)
- Lần đầu: lấy video có publishedAt > start_time (giờ VN)
- Về sau: chỉ lấy video có publishedAt > video mới nhất trong file kết quả
- Lọc: Shorts (<60s), Long (>=60s), hoặc Cả 2
- Lưu kết quả mỗi luồng: E:\tool_ld\data\output\<slug_ten_luong>.json  (chỉ 4 trường: title, publishedAt, duration, url)
"""
import subprocess
import os
import re
import json
import time
import queue
import threading
import logging
from datetime import datetime, timezone, timedelta
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk  # For Treeview only
import customtkinter as ctk
from ui_theme import *
import traceback
import sys
from utils.download_dlp import download_video_api
from utils.send_file import send_file_api
from utils.post import InstagramPost
from utils.delete_file import clear_dcim, clear_pictures
from utils.file_checker import verify_file_after_push
from utils.vm_manager import vm_manager
from utils.text_utils import remove_keywords_from_text, remove_all_hashtags
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from config import LDCONSOLE_EXE, ADB_EXE, VM_DATA_DIR, get_vm_id_from_name
from constants import WAIT_SHORT, WAIT_MEDIUM, WAIT_LONG, WAIT_EXTRA_LONG, TIMEOUT_DEFAULT, TIMEOUT_MINUTE
from utils.api_manager_multi import multi_api_manager
from utils.tiktok_api_rapidapi import (
    extract_tiktok_username,
    get_tiktok_secuid,
    fetch_tiktok_videos_latest,
    filter_videos_newer_than,
    convert_to_output_format,
    download_tiktok_video,
    check_tiktok_api_key_valid
)
from utils.yt_api import check_api_key_valid

class StoppableWorker:
    """Helper class để chạy tác vụ có thể dừng"""
    
    def __init__(self, stop_event):
        self.stop_event = stop_event
        self.current_process = None
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    def run_blocking_func(self, func, *args, timeout=300, check_interval=1, **kwargs):
        """
        Chạy hàm blocking với khả năng dừng
        
        Args:
            func: Hàm cần chạy
            timeout: Thời gian tối đa (giây)
            check_interval: Kiểm tra stop_event mỗi X giây
        
        Returns:
            (success, result, reason)
        """
        future = self.executor.submit(func, *args, **kwargs)
        
        elapsed = 0
        while elapsed < timeout:
            if self.stop_event.is_set():
                future.cancel()
                return (False, None, "stopped")
            
            if future.done():
                try:
                    result = future.result(timeout=0.1)
                    return (True, result, "completed")
                except Exception as e:
                    return (False, None, f"error: {e}")
            
            time.sleep(check_interval)
            elapsed += check_interval
        
        future.cancel()
        return (False, None, "timeout")
    
    def run_subprocess(self, cmd_list, timeout=300, check_interval=0.5):
        """
        Chạy subprocess với khả năng dừng
        
        Returns:
            (success, returncode, reason)
        """
        try:
            self.current_process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            elapsed = 0
            while elapsed < timeout:
                if self.stop_event.is_set():
                    self._kill_process()
                    return (False, None, "stopped")
                
                retcode = self.current_process.poll()
                if retcode is not None:
                    return (True, retcode, "completed")
                
                time.sleep(check_interval)
                elapsed += check_interval
            
            self._kill_process()
            return (False, None, "timeout")
            
        except Exception as e:
            return (False, None, f"error: {e}")
        finally:
            self.current_process = None
    
    def _kill_process(self):
        """Kill process an toàn"""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except:
                try:
                    self.current_process.kill()
                except:
                    pass
    
    def cleanup(self):
        """Cleanup resources"""
        self._kill_process()
        self.executor.shutdown(wait=False)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.yt_api import (
    extract_channel_id,
    get_uploads_playlist_id,
    iter_playlist_videos_newer_than,
    fetch_video_details,
    filter_videos_by_mode,
    parse_vn_datetime,
    iso_to_datetime,
    datetime_to_iso,
    check_api_key_valid
)


def get_vm_list_with_insta():
    """Lấy danh sách máy ảo kèm tên Instagram từ data/vm/"""
    vm_list = []
    try:
        if not os.path.exists(VM_DATA_DIR):
            return vm_list

        files = [f for f in os.listdir(VM_DATA_DIR) if f.endswith(".json")]
        for f in files:
            path = os.path.join(VM_DATA_DIR, f)
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                vm_name = data.get("vm_name", "")
                insta_name = data.get("insta_name", "")
                display = f"{vm_name} - {insta_name}" if insta_name else vm_name
                vm_list.append({"vm_name": vm_name, "display": display})
    except Exception as e:
        print(f"Lỗi khi đọc danh sách máy ảo: {e}")
    
    return vm_list
def show_exception_dialog(title: str, err: Exception):
    tb = traceback.format_exc(limit=3)
    messagebox.showerror(title, f"{err}\n\n{tb}")

# ========================= CẤU HÌNH ĐƯỜNG DẪN =========================
OUTPUT_DIR = "data/output"
STREAMS_META = os.path.join(OUTPUT_DIR, "streams.json")

# ========================= HẰNG SỐ / TIỆN ÍCH =========================
VN_TZ = timezone(timedelta(hours=7))  # Asia/Ho_Chi_Minh (UTC+7)
LOCK = threading.Lock()  # khóa chung cho trạng thái chia sẻ

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(STREAMS_META):
        with open(STREAMS_META, "w", encoding="utf-8") as f:
            json.dump({"streams": []}, f, ensure_ascii=False, indent=2)

def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\-_\s]+", "", name)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "stream"

def load_streams_meta():
    ensure_dirs()
    with open(STREAMS_META, "r", encoding="utf-8") as f:
        return json.load(f)

def save_streams_meta(meta):
    ensure_dirs()
    with open(STREAMS_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def load_existing_urls(path: str) -> set:
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {d.get("url") for d in data if isinstance(d, dict)}
    except Exception:
        return set()

def newest_published_at(path: str, default_iso: str) -> datetime:
    """Đọc file kết quả để xác định mốc mới nhất; nếu không có thì dùng default_iso."""
    newest = iso_to_datetime(default_iso)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data:
                pub = d.get("publishedAt")
                if pub:
                    dtp = iso_to_datetime(pub)
                    if dtp > newest:
                        newest = dtp
        except Exception:
            pass
    return newest

def _atomic_write_json(path, data):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atomic trên Windows/Unix
    
def append_records(path: str, new_rows: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    known = {d["url"] for d in data if isinstance(d, dict) and "url" in d}
    for r in sorted(new_rows, key=lambda x: x["publishedAt"]):
        if r["url"] not in known:
            data.append(r); known.add(r["url"])
    _atomic_write_json(path, data)
    return len(new_rows)

def reset_output_file(path: str):
    """Xoá nội dung file kết quả của luồng và tạo file rỗng."""
    try:
        if os.path.exists(path):
            os.remove(path)  # xoá file cũ
        # tạo file rỗng (có thể bỏ nếu muốn để tool tự tạo lúc ghi lần đầu)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ========================= QUẢN LÝ LUỒNG =========================
class Stream:
    def __init__(self, cfg: dict, row_id: str, log_callback=None):
        self.cfg = cfg  # dict: id, name, start_vn, channels, mode, interval_min, out_path
        self.row_id = row_id
        self.thread = None
        self.stop_event = threading.Event()
        self.next_deadline = None  # datetime (UTC) cho lần chạy tiếp theo
        self.status = "Chưa chạy"
        self.logs = []
        self.log_callback = log_callback
        self.worker_helper = None

    def log(self, msg: str):
        stamp = datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M:%S")
        line = f"[{stamp}] {msg}"
        self.logs.append(line)
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
        # 🟢 gọi callback realtime
        if self.log_callback:
            self.log_callback(self.row_id, line)

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, ui_queue):
        if self.is_running():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.worker, args=(ui_queue,), daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.worker_helper:
            self.worker_helper.cleanup()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

    def worker(self, ui_queue: queue.Queue):
        self.worker_helper = StoppableWorker(self.stop_event)
        logger = logging.getLogger(f"{__name__}.Stream.{self.cfg['name']}")
        try:
            self.status = "Đang chạy (khởi tạo)"
            ui_queue.put(("status", self.row_id, self.status))
            
            default_cutoff_utc = parse_vn_datetime(self.cfg["start_vn"], VN_TZ).astimezone(timezone.utc)
            default_cutoff_iso = datetime_to_iso(default_cutoff_utc)
            cutoff_dt = newest_published_at(self.cfg["out_path"], default_cutoff_iso)

            # ✅ FIX: Không tạo shared auto_poster ở đây
            # Mỗi video sẽ tạo InstagramPost riêng để tránh log nhầm

            # ========== VÒNG LẶP CHÍNH ==========
            while not self.stop_event.is_set():
                self.log("Bắt đầu quét...")

                platform = self.cfg.get("platform", "youtube")

                # CHỈ KHAI BÁO all_new_ids KHI LÀ YOUTUBE
                all_new_ids = []

                if platform == "youtube":
                    # ========== QUÉT KÊNH YOUTUBE ==========
                    for ch_url in self.cfg["channels"]:
                        if self.stop_event.is_set():
                            self.log("🛑 Dừng quét kênh")
                            break

                        try:
                            cid = extract_channel_id(ch_url, multi_api_manager)
                            pid = get_uploads_playlist_id(cid, multi_api_manager)

                            ids = []
                            for vid, pub in iter_playlist_videos_newer_than(pid, cutoff_dt, multi_api_manager):
                                if self.stop_event.is_set():
                                    break
                                ids.append(vid)
                            
                            if ids:
                                all_new_ids.extend(ids)
                                self.log(f"[YouTube] {ch_url}: tìm thấy {len(ids)} video mới.")
                            else:
                                self.log(f"[YouTube] {ch_url}: không có video mới.")
                        except Exception as e:
                            self.log(f"[YouTube] Lỗi kênh {ch_url}: {e}")

                elif platform != "tiktok":
                    # TikTok logic đã được xử lý ở phần "XỬ LÝ VIDEO" bên dưới
                    self.log(f"Nền tảng chưa hỗ trợ: {platform}")

                
                # Check trước khi xử lý video
                if self.stop_event.is_set():
                    break
                
                # ========== XỬ LÝ VIDEO ==========
                # === Xử lý lấy video mới (YouTube hoặc TikTok) ===
                # ========== XỬ LÝ VIDEO ==========
                new_rows = []

                if self.cfg.get("platform", "youtube") == "youtube":
                    if all_new_ids:
                        details = fetch_video_details(all_new_ids, multi_api_manager)
                        for r in details:
                            if iso_to_datetime(r["publishedAt"]) <= cutoff_dt:
                                continue
                            new_rows.append(r)

                        self.log(f"Trước khi lọc mode: {len(new_rows)} video (mode={self.cfg['mode']})")

                        # Log chi tiết từng video trước khi lọc
                        from utils.yt_api import parse_iso8601_duration
                        for idx, v in enumerate(new_rows, 1):
                            duration_sec = parse_iso8601_duration(v.get("duration", "PT0S"))
                            self.log(f"  Video {idx}: {v.get('title', 'No title')[:50]}... - Duration: {duration_sec}s")

                        new_rows = filter_videos_by_mode(new_rows, self.cfg["mode"])

                        self.log(f"Sau khi lọc mode: {len(new_rows)} video")

                        if new_rows:
                            added = append_records(self.cfg["out_path"], new_rows)
                            self.log(f"Đã thêm {added}/{len(new_rows)} video mới vào file.")
                        else:
                            self.log("Không có video phù hợp sau khi lọc.")
                    else:
                        self.log("Không có video mới.")

                elif self.cfg.get("platform") == "tiktok":
                    # ========== XỬ LÝ TIKTOK ==========
                    tiktok_key = multi_api_manager.get_next_tiktok_key()
                    if not tiktok_key:
                        self.log("❌ Không có TikTok API key. Vui lòng thêm key trong tab Đăng bài → 🔑 Quản lý API")
                    else:
                        new_rows = []
                        for ch_url in self.cfg.get("channels", []):
                            if self.stop_event.is_set():
                                break
                            try:
                                # Extract username from URL
                                username = extract_tiktok_username(ch_url)
                                self.log(f"[TikTok] Đang quét @{username}...")

                                # Step 1: Get secUid
                                secuid = get_tiktok_secuid(username, tiktok_key, log_callback=self.log)
                                if not secuid:
                                    self.log(f"[TikTok] Không tìm thấy kênh @{username}")
                                    continue

                                # Step 2: Fetch latest 35 videos from TikTok
                                all_videos = fetch_tiktok_videos_latest(secuid, username, tiktok_key, log_callback=self.log)

                                # Step 3: Filter videos newer than cutoff_dt
                                filtered = filter_videos_newer_than(all_videos, cutoff_dt, self.log)

                                if filtered:
                                    # Convert to output format
                                    converted = convert_to_output_format(filtered)
                                    new_rows.extend(converted)
                                    self.log(f"[TikTok] {ch_url}: +{len(converted)} video mới.")
                                else:
                                    self.log(f"[TikTok] {ch_url}: không có video mới.")
                            except Exception as e:
                                self.log(f"[TikTok] Lỗi lấy video từ {ch_url}: {e}")

                        if new_rows:
                            added = append_records(self.cfg["out_path"], new_rows)
                            self.log(f"🎵 Đã thêm {added}/{len(new_rows)} video TikTok mới vào file.")
                        else:
                            self.log("Không có video TikTok mới.")

                else:
                    self.log(f"Nền tảng chưa hỗ trợ: {self.cfg.get('platform')}")


                self.log("Kiểm tra nếu có video cũ chưa đăng thì sẽ đăng")
   
                # ========== ĐĂNG VIDEO ==========
                try:
                    with open(self.cfg["out_path"], "r", encoding="utf-8") as f:
                        all_videos = json.load(f)

                    vm_name = self.cfg.get("vm_name")

                    for vid in all_videos:
                        vm_acquired = False  # Reset flag cho mỗi video

                        # Check trước mỗi video
                        if self.stop_event.is_set():
                            self.log("🛑 Dừng xử lý video")
                            break

                        if vid.get("status") != "unpost":
                            continue

                        url = vid.get("url", "")
                        title = vid.get("title", "<3")

                        # Apply auto remove hashtags if configured
                        auto_remove_hashtags = self.cfg.get("auto_remove_hashtags", False)
                        if auto_remove_hashtags:
                            original_title = title
                            title = remove_all_hashtags(title)
                            if title != original_title:
                                self.log(f"🗑️ Đã xóa tất cả hashtag khỏi title: {original_title} → {title}")

                        # Apply remove keywords if configured
                        remove_keywords = self.cfg.get("remove_keywords", "")
                        if remove_keywords:
                            original_title = title
                            title = remove_keywords_from_text(title, remove_keywords)
                            if title != original_title:
                                self.log(f"✏️ Đã loại bỏ từ khóa khỏi title: {original_title} → {title}")

                        self.log(f"🎬 [Bắt đầu] Xử lý video: {title}")

                        # ========== ACQUIRE VM LOCK ==========
                        self.log(f"🔒 Chờ máy ảo '{vm_name}' sẵn sàng...")
                        if not vm_manager.acquire_vm(vm_name, timeout=5400, caller=f"Follow:{self.cfg['name']}"):
                            self.log(f"⏱️ Timeout chờ máy ảo '{vm_name}' sau 1.5 giờ - Bỏ qua video")
                            continue

                        vm_acquired = True
                        self.log(f"✅ Đã khóa máy ảo '{vm_name}'")

                        # Wrap toàn bộ logic xử lý video trong try/finally để đảm bảo release
                        try:
                            # ========== KIỂM TRA MÁY ẢO (Option 3: subprocess) ==========
                            try:
                                result = subprocess.run(
                                    [LDCONSOLE_EXE, "list2"],
                                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                is_running = False
                                for line in result.stdout.splitlines():
                                    parts = line.split(",")
                                    if len(parts) >= 5 and parts[1].strip() == vm_name:
                                        is_running = (parts[4].strip() == "1")
                                        break
                            except Exception as e:
                                self.log(f"⚠️ Không thể kiểm tra trạng thái máy ảo: {e}")
                                logger.exception("Error checking VM status")
                                is_running = True  # Assume running để skip video

                            # 🧩 2️⃣ Xử lý trạng thái máy ảo (QUEUE-BASED: Đảm bảo VM ở trạng thái sạch)
                            if is_running:
                                # VM đang chạy → Reboot để đảm bảo trạng thái sạch
                                self.log(f"⚠️ Máy ảo '{vm_name}' đang chạy — Reboot để đảm bảo trạng thái sạch")

                                # ✅ KHÔNG reset ADB server toàn cục (ảnh hưởng tất cả VMs khác!)
                                # LDPlayer sẽ tự động setup lại ADB connection khi reboot

                                subprocess.run([LDCONSOLE_EXE, "reboot", "--name", vm_name],
                                            creationflags=subprocess.CREATE_NO_WINDOW)
                            else:
                                # VM chưa chạy → Bật mới
                                if self.stop_event.is_set():
                                    break

                                self.log(f"🚀 Bật máy ảo '{vm_name}' để đăng video: {title}")

                                # ✅ KHÔNG reset ADB server toàn cục (ảnh hưởng tất cả VMs khác!)
                                # LDPlayer sẽ tự động setup lại ADB connection khi launch

                                subprocess.run([LDCONSOLE_EXE, "launch", "--name", vm_name],
                                            creationflags=subprocess.CREATE_NO_WINDOW)

                            # ========== CHỜ MÁY ẢO SẴN SÀNG (Tăng timeout lên 120s) ==========
                            self.log(f"⏳ Chờ máy ảo '{vm_name}' khởi động hoàn toàn...")
                            if not vm_manager.wait_vm_ready(vm_name, LDCONSOLE_EXE, timeout=120, log_callback=self.log):
                                self.log(f"⏱️ Timeout 120s - Máy ảo '{vm_name}' không khởi động được")
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                # QUAN TRỌNG: Đợi VM tắt HOÀN TOÀN trước khi release lock
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"✅ Đã tắt máy ảo hoàn toàn")
                                continue

                            # ========== CHỜ ADB KẾT NỐI ==========
                            # ✅ v1.5.36: Tìm VM ID từ tên máy ảo
                            vm_id = get_vm_id_from_name(vm_name)
                            if not vm_id:
                                self.log(f"❌ Không tìm thấy file cấu hình cho VM: {vm_name}")
                                continue

                            vm_file = os.path.join(VM_DATA_DIR, f"{vm_id}.json")
                            with open(vm_file, "r", encoding="utf-8") as f:
                                vm_info = json.load(f)
                            port = vm_info.get("port")
                            adb_device = f"emulator-{port}"

                            # Ensure ADB connection (force connect nếu cần)
                            self.log(f"🔌 Đang kết nối ADB...")
                            if not vm_manager.ensure_adb_connected(adb_device, ADB_EXE, max_retries=3, log_callback=self.log):
                                self.log(f"❌ Không thể kết nối ADB đến '{adb_device}'")
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"❌ Lỗi kết nối ADB - Đã tắt máy ảo")
                                continue  # Skip video này

                            self.log(f"⏳ Chờ ADB sẵn sàng...")
                            if not vm_manager.wait_adb_ready(adb_device, ADB_EXE, timeout=30, log_callback=self.log):
                                self.log(f"⏱️ Timeout - ADB không kết nối được đến '{adb_device}'")
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                # QUAN TRỌNG: Đợi VM tắt HOÀN TOÀN trước khi release lock
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"✅ Đã tắt máy ảo hoàn toàn")
                                continue

                            # ========== TẢI VIDEO (Option 2: Thread + timeout) ==========
                            if self.stop_event.is_set():
                                break

                            self.log(f"📥 Đang tải video: {title}")

                            # Chọn download function dựa vào platform
                            platform = self.cfg.get("platform", "youtube")

                            if platform == "tiktok":
                                # Get TikTok API key for download
                                tiktok_key = multi_api_manager.get_next_tiktok_key()
                                if not tiktok_key:
                                    self.log(f"❌ Không có TikTok API key để tải video")
                                    self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                    self.worker_helper.run_subprocess(
                                        [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                        timeout=30
                                    )
                                    vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                    time.sleep(WAIT_EXTRA_LONG)
                                    continue

                                # Download TikTok video using RapidAPI
                                success, video_path, reason = self.worker_helper.run_blocking_func(
                                    download_tiktok_video,
                                    url,
                                    tiktok_key,
                                    log_callback=lambda msg: self.log(msg),
                                    timeout=600,  # 10 phút
                                    check_interval=2
                                )
                            else:
                                # Download YouTube video
                                success, video_path, reason = self.worker_helper.run_blocking_func(
                                    download_video_api,
                                    url,
                                    log_callback=lambda msg: self.log(msg),
                                    timeout=600,  # 10 phút
                                    check_interval=2
                                )

                            if not success:
                                if reason == "stopped":
                                    self.log("🛑 Dừng tải video")
                                    # Tắt máy ảo trước khi break
                                    self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                    self.worker_helper.run_subprocess(
                                        [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                        timeout=30
                                    )
                                    vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                    time.sleep(WAIT_EXTRA_LONG)
                                    break
                                else:
                                    self.log(f"❌ Không thể tải video: {reason}")
                                    self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                    self.worker_helper.run_subprocess(
                                        [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                        timeout=30
                                    )
                                    vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                    time.sleep(WAIT_EXTRA_LONG)
                                    self.log(f"✅ Đã tắt máy ảo hoàn toàn")
                                    continue

                            if not video_path or not os.path.exists(video_path):
                                self.log(f"❌ File video không tồn tại")
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                # QUAN TRỌNG: Chờ máy ảo tắt hoàn toàn để tránh race condition
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"✅ Đã tắt máy ảo hoàn toàn")
                                continue

                            self.log(f"✅ Đã tải xong: {video_path}")
                            time.sleep(15)

                            # ========== GỬI FILE (Option 2) ==========
                            if self.stop_event.is_set():
                                if os.path.exists(video_path):
                                    os.remove(video_path)
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                break

                            # Clear DCIM and Pictures folders before sending file
                            try:
                                # ✅ v1.5.36: Tìm VM ID từ tên máy ảo
                                vm_id = get_vm_id_from_name(vm_name)
                                if not vm_id:
                                    self.log(f"❌ Không tìm thấy file cấu hình cho VM: {vm_name}")
                                    raise Exception(f"VM config not found: {vm_name}")

                                # Read port from JSON to create adb_address
                                json_path = os.path.join(VM_DATA_DIR, f"{vm_id}.json")
                                with open(json_path, "r", encoding="utf-8") as f:
                                    vm_info = json.load(f)
                                port = vm_info.get("port")
                                adb_address = f"emulator-{port}"

                                self.log(f"🗑️ Xóa DCIM và Pictures...")
                                clear_dcim(adb_address, log_callback=lambda msg: self.log(msg))
                                clear_pictures(adb_address, log_callback=lambda msg: self.log(msg))
                                self.log(f"✅ Đã xóa DCIM và Pictures")
                            except Exception as e:
                                self.log(f"⚠️ Lỗi khi xóa DCIM/Pictures: {e}")

                            self.log(f"📤 Gửi file sang máy ảo")
                            success, success_push, reason = self.worker_helper.run_blocking_func(
                                send_file_api,
                                video_path,
                                vm_name,
                                log_callback=lambda msg: self.log(msg),
                                timeout=300,
                                check_interval=2
                            )

                            if not success or not success_push:
                                if reason == "stopped":
                                    self.log("🛑 Dừng gửi file")
                                else:
                                    self.log(f"⚠️ Gửi file thất bại: {reason}")

                                if os.path.exists(video_path):
                                    os.remove(video_path)

                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"✅ Đã tắt máy ảo")

                                if reason == "stopped":
                                    break
                                else:
                                    continue

                            self.log(f"✅ Đã gửi video sang máy ảo")

                            # ✅ v1.5.30: Verify file đã có trong VM sau khi push
                            filename = os.path.basename(video_path)
                            remote_path = f"/sdcard/DCIM/{filename}"

                            # Get expected file size
                            try:
                                local_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                            except:
                                local_size_mb = None  # Nếu không lấy được size, chỉ check tồn tại

                            # Verify với retry mechanism (wait 5s, retry 3 lần nếu chưa có)
                            self.log(f"🔍 Đang verify file trong VM...")
                            verified = verify_file_after_push(
                                vm_name,
                                remote_path,
                                expected_size_mb=local_size_mb,
                                wait_seconds=5,
                                max_retries=3,
                                log_callback=lambda msg: self.log(msg)
                            )

                            if not verified:
                                self.log(f"❌ File verification FAILED - File không có trong VM sau khi push!")

                                if os.path.exists(video_path):
                                    os.remove(video_path)

                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"✅ Đã tắt máy ảo")
                                continue  # Skip to next video

                            time.sleep(WAIT_MEDIUM)

                            # ========== ĐĂNG BÀI ==========
                            if self.stop_event.is_set():
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                break

                            self.log(f"📲 Đang đăng video: {title}")

                            # ✅ v1.5.36: Tìm VM ID từ tên máy ảo
                            vm_id = get_vm_id_from_name(vm_name)
                            if not vm_id:
                                self.log(f"❌ Không tìm thấy file cấu hình cho VM: {vm_name}")
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                break

                            vm_file = os.path.join(VM_DATA_DIR, f"{vm_id}.json")
                            with open(vm_file, "r", encoding="utf-8") as f:
                                vm_info = json.load(f)
                            port = vm_info.get("port")
                            adb_address = f"emulator-{port}"

                            # ✅ FIX: Tạo InstagramPost riêng cho video này với callback dùng title
                            def video_log_callback(vm, message):
                                """Log callback specific cho video này"""
                                self.log(f"[{title[:30]}...] {message}")

                            auto_poster = InstagramPost(log_callback=video_log_callback)

                            # Extract video filename for MediaStore broadcast retry
                            video_filename = os.path.basename(video_path) if video_path else None

                            # Call auto_post with use_launchex=True
                            def post_with_launchex():
                                return auto_poster.auto_post(
                                    vm_name, adb_address, title,
                                    use_launchex=True, ldconsole_exe=LDCONSOLE_EXE,
                                    video_filename=video_filename
                                )

                            success, success_post, reason = self.worker_helper.run_blocking_func(
                                post_with_launchex,
                                timeout=600,
                                check_interval=2
                            )

                            if not success or not success_post:
                                if reason == "stopped":
                                    self.log("🛑 Dừng đăng bài")
                                else:
                                    self.log(f"❌ Lỗi đăng bài: {reason}")

                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"✅ Đã tắt máy ảo")

                                if reason == "stopped":
                                    break
                                else:
                                    continue

                            self.log(f"✅ Đã đăng thành công: {title}")

                            # ========== XÓA FILE ==========
                            if self.stop_event.is_set():
                                self.log(f"🛑 Tắt máy ảo '{vm_name}'...")
                                self.worker_helper.run_subprocess(
                                    [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                    timeout=30
                                )
                                vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                                time.sleep(WAIT_EXTRA_LONG)
                                self.log(f"✅ Đã tắt máy ảo")
                                break

                            success, success_delete, reason = self.worker_helper.run_blocking_func(
                                clear_dcim,
                                adb_address,
                                log_callback=lambda msg: self.log(msg),
                                timeout=60,
                                check_interval=1
                            )

                            if success and success_delete:
                                self.log(f"✅ Xóa thành công")
                            else:
                                self.log(f"⚠️ Xóa file thất bại: {reason}")

                            time.sleep(WAIT_MEDIUM)

                            # ========== TẮT MÁY ẢO ==========
                            self.log(f"🛑 Tắt máy ảo '{vm_name}'")
                            self.worker_helper.run_subprocess(
                                [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                timeout=30
                            )
                            vm_manager.wait_vm_stopped(vm_name, LDCONSOLE_EXE, timeout=60)
                            time.sleep(WAIT_EXTRA_LONG)
                            self.log(f"✅ Đã tắt máy ảo hoàn toàn")

                            # ========== CẬP NHẬT TRẠNG THÁI ==========
                            vid["status"] = "post"

                            # ========== UPDATE CUTOFF_DT ==========
                            try:
                                published_iso = vid.get("publishedAt")
                                if published_iso:
                                    video_time = iso_to_datetime(published_iso)
                                    if video_time > cutoff_dt:
                                        cutoff_dt = video_time
                                        self.log(f"📅 Cập nhật cutoff → {cutoff_dt.strftime('%d/%m/%Y %H:%M')}")
                            except Exception as e:
                                self.log(f"⚠️ Không thể cập nhật cutoff_dt: {e}")

                            try:
                                if os.path.exists(video_path):
                                    os.remove(video_path)
                            except Exception as e:
                                self.log(f"⚠️ Không thể xóa {video_path}: {e}")

                            self.log(f"✅ Hoàn tất {title}")

                        finally:
                            # ========== RELEASE VM LOCK ==========
                            if vm_acquired:
                                vm_manager.release_vm(vm_name, caller=f"Follow:{self.cfg['name']}")
                                self.log(f"🔓 Đã giải phóng máy ảo '{vm_name}'")
                                vm_acquired = False

                    # Lưu progress
                    with open(self.cfg["out_path"], "w", encoding="utf-8") as f:
                        json.dump(all_videos, f, ensure_ascii=False, indent=2)


                except Exception as e:
                    self.log(f"⚠️ Lỗi xử lý video: {e}")
                    logger.exception("Error processing video")

                # NOTE: cutoff_dt đã được update ở line 707-713 SAU KHI đăng video thành công
                # KHÔNG update từ new_rows vì video có thể chưa đăng (do lỗi)

                # ========== ĐẾM NGƯỢC (Option 1: Check manual) ==========
                if self.stop_event.is_set():
                    break
                
                interval = int(self.cfg["interval_min"])
                self.next_deadline = datetime.now(timezone.utc) + timedelta(minutes=interval)
                
                while not self.stop_event.is_set():
                    now = datetime.now(timezone.utc)
                    left = int((self.next_deadline - now).total_seconds())
                    if left <= 0:
                        break
                    
                    hh = left // 3600
                    mm = (left % 3600) // 60
                    ss = left % 60
                    self.status = f"Đang chờ: {hh:02d}:{mm:02d}:{ss:02d}"
                    ui_queue.put(("status", self.row_id, self.status))
                    time.sleep(1)
            
            self.status = "Đã dừng"
            self.log("Luồng đã dừng.")


        except Exception as e:
            self.status = f"Lỗi: {e}"
            self.log(f"Lỗi không mong muốn: {e}")
            logger.exception("Unexpected error in stream worker")
            import traceback
            self.log(traceback.format_exc())
        
        finally:
            # ========== CLEANUP ==========
            if self.worker_helper:
                self.worker_helper.cleanup()
            
            # Tắt máy ảo nếu còn đang bật
            try:
                vm_name = self.cfg.get("vm_name")
                if vm_name:
                    subprocess.run(
                        [LDCONSOLE_EXE, "quit", "--name", vm_name],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=10
                    )
                    time.sleep(WAIT_LONG)
            except:
                pass
            
            ui_queue.put(("status", self.row_id, self.status))

# ========================= GIAO DIỆN =========================
class FollowTab(ctk.CTkFrame):
    """Follow Tab - Modern Windows 11 Style"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.logger = logging.getLogger(__name__)
        self.ui_queue = queue.Queue()
        self.streams = {}
        self.meta = load_streams_meta()
        self.is_shutting_down = False  # ✅ Flag để track shutdown state

        # Giao diện chính (dùng self thay vì root window)
        self.build_topbar()
        self.build_table()
        self.load_existing_streams()
        self.after(200, self.process_ui_queue)

    def append_log_line(self, row_id, line):
        # chỉ update nếu cửa sổ log đang mở
        if hasattr(self, "log_windows") and row_id in self.log_windows:
            win = self.log_windows[row_id]
            if win.winfo_exists():
                txt = win.text_log

                def safe_append():
                    # kiểm tra widget còn tồn tại
                    if not txt.winfo_exists():
                        return
                    try:
                        txt.config(state="normal")
                        txt.insert("end", line + "\n")
                        txt.see("end")
                        txt.config(state="disabled")
                    except Exception:
                        # tránh crash nếu widget bị đóng giữa chừng
                        pass

                # thread-safe append
                win.after(0, safe_append)



    def build_topbar(self):
        top = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=DIMENSIONS["corner_radius_medium"])
        top.pack(fill=tk.X, padx=DIMENSIONS["spacing_lg"], pady=(DIMENSIONS["spacing_lg"], DIMENSIONS["spacing_sm"]))

        self.btn_api = ctk.CTkButton(
            top,
            text="🔑 Quản lý API Keys",
            command=self.open_api_manager,
            **get_button_style("warning"),
            width=180
        )
        self.btn_api.pack(side=tk.LEFT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        ctk.CTkLabel(
            top,
            text="💡 Theo dõi & tự động tải video từ YouTube/TikTok",
            font=(FONTS["family"], FONTS["size_medium"], FONTS["weight_semibold"]),
            text_color=COLORS["accent"]
        ).pack(side=tk.LEFT, padx=DIMENSIONS["spacing_xl"])

        self.btn_add = ctk.CTkButton(
            top,
            text="➕ Thêm luồng mới",
            command=self.open_add_stream_dialog,
            **get_button_style("success"),
            width=180
        )
        self.btn_add.pack(side=tk.RIGHT, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

    def build_table(self):
        # Outer container with title
        outer_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=DIMENSIONS["corner_radius_medium"])
        outer_frame.pack(fill=tk.BOTH, expand=True, padx=DIMENSIONS["spacing_lg"], pady=(DIMENSIONS["spacing_sm"], DIMENSIONS["spacing_lg"]))

        # Title label
        title_label = ctk.CTkLabel(
            outer_frame,
            text="📋 Danh Sách Luồng Theo Dõi",
            font=(FONTS["family"], FONTS["size_medium"], FONTS["weight_semibold"]),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(padx=DIMENSIONS["spacing_md"], pady=(DIMENSIONS["spacing_md"], DIMENSIONS["spacing_sm"]), anchor="w")

        # Table container (using ttk.Frame for Treeview)
        table_container = ctk.CTkFrame(outer_frame, fg_color=COLORS["bg_tertiary"], corner_radius=DIMENSIONS["corner_radius_small"])
        table_container.pack(fill=tk.BOTH, expand=True, padx=DIMENSIONS["spacing_md"], pady=(0, DIMENSIONS["spacing_md"]))

        frame = tk.Frame(table_container, bg=COLORS["bg_tertiary"])
        frame.pack(fill=tk.BOTH, expand=True, padx=DIMENSIONS["spacing_sm"], pady=DIMENSIONS["spacing_sm"])

        # Apply Windows 11 Treeview styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            rowheight=40,
            font=(FONTS["family"], FONTS["size_normal"]),
            background=COLORS["bg_secondary"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_secondary"],
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            font=(FONTS["family"], FONTS["size_normal"], FONTS["weight_semibold"]),
            background=COLORS["surface_3"],
            foreground=COLORS["text_primary"],
            borderwidth=1,
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["text_on_accent"])]
        )

        columns = ("stt", "name", "account", "watch", "interval", "status", "run", "stop", "log", "edit", "delete")

        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)

        # Configure alternating row colors (striped) - Now using Windows 11 colors
        self.tree.tag_configure("oddrow", background=COLORS["bg_tertiary"])
        self.tree.tag_configure("evenrow", background=COLORS["bg_secondary"])
        self.tree.heading("stt", text="STT")
        self.tree.heading("name", text="Tên luồng")
        self.tree.heading("account", text="Tài khoản")
        self.tree.heading("watch", text="Theo dõi trang")
        self.tree.heading("interval", text="Thời gian quét")
        self.tree.heading("status", text="Trạng thái")
        self.tree.heading("run", text="Chạy")
        self.tree.heading("stop", text="Dừng")
        self.tree.heading("log", text="Log")
        self.tree.heading("edit", text="Sửa")
        self.tree.heading("delete", text="Xóa")

        self.tree.column("stt", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=180)
        self.tree.column("account", width=150)
        self.tree.column("watch", width=180, anchor=tk.CENTER)
        self.tree.column("interval", width=120, anchor=tk.CENTER)
        self.tree.column("status", width=260)
        self.tree.column("run", width=60, anchor=tk.CENTER)
        self.tree.column("stop", width=60, anchor=tk.CENTER)
        self.tree.column("log", width=60, anchor=tk.CENTER)
        self.tree.column("edit", width=60, anchor=tk.CENTER)
        self.tree.column("delete", width=60, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Click vào cột action
        self.tree.bind("<Button-1>", self.on_tree_click)

    def refresh_stt(self):
        for idx, iid in enumerate(self.tree.get_children(), start=1):
            self.tree.set(iid, "stt", str(idx))
            # Apply striped row tags
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.item(iid, tags=(tag,))

    def load_existing_streams(self):
        for cfg in self.meta.get("streams", []):
            self.add_stream_row(cfg)

    def add_stream_row(self, cfg: dict):
        vm_name = cfg.get("vm_name", "")
        account_display = cfg.get("account_display", vm_name) if vm_name else "Chưa chọn"

        iid = self.tree.insert("", tk.END, values=(
            "",  # stt sẽ set sau
            cfg["name"],
            account_display,
            f"{len(cfg['channels'])} kênh",
            f"{cfg['interval_min']} phút",
            "Chưa chạy",
            "▶", "■", "📝", "✎", "✖"
        ))
        self.refresh_stt()
        st = Stream(cfg, iid, log_callback=self.append_log_line)
        self.streams[iid] = st

    # ---------- POPUP: API MANAGER ----------
    def open_api_manager(self):
        """Mở dialog quản lý API keys cho YouTube và TikTok"""
        multi_api_manager.refresh()

        # Main dialog
        dialog = tk.Toplevel(self)
        dialog.title("Quản lý API Keys")
        dialog.geometry("800x600")
        dialog.grab_set()

        # Notebook (tabs)
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: YouTube
        youtube_frame = ttk.Frame(notebook)
        notebook.add(youtube_frame, text="📺 YouTube API")
        self._build_api_tab_follow(youtube_frame, "youtube", dialog)

        # Tab 2: TikTok
        tiktok_frame = ttk.Frame(notebook)
        notebook.add(tiktok_frame, text="🎵 TikTok API")
        self._build_api_tab_follow(tiktok_frame, "tiktok", dialog)

        # Info label
        info_label = ttk.Label(
            dialog,
            text="💡 File lưu tại: data/api/apis.json",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        info_label.pack(pady=(0, 10))

    def _build_api_tab_follow(self, parent, platform, dialog):
        """Xây dựng nội dung cho 1 tab API với chức năng Check"""
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

        # Buttons Row 1: Add, Remove, Copy
        btn_frame1 = ttk.Frame(frame)
        btn_frame1.pack(fill=tk.X, pady=(0, 5))

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

        ttk.Button(btn_frame1, text="➕ Thêm", command=add_key, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame1, text="🗑️ Xóa", command=remove_key, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame1, text="📋 Copy", command=copy_key, width=12).pack(side=tk.LEFT, padx=3)

        # Buttons Row 2: Check Selected, Check All
        btn_frame2 = ttk.Frame(frame)
        btn_frame2.pack(fill=tk.X)

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

    # ---------- POPUP: THÊM/SỬA LUỒNG ----------
    def open_add_stream_dialog(self, edit_iid=None):
        init = {
            "name": "",
            "start_vn": datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M"),
            # "platform": cfg.get("platform", "youtube"),
            "channels": "",
            "mode": "both",
            "interval_min": 60,
            "vm_name": "",
            "account_display": "",
            "remove_keywords": "",  # Từ khóa loại bỏ khỏi title
            "auto_remove_hashtags": False  # Tự động xóa tất cả hashtag

        }
        editing = False
        if edit_iid:
            editing = True
            cfg = self.streams[edit_iid].cfg
            init = {
                "name": cfg["name"],
                "start_vn": cfg["start_vn"],
                "platform": cfg.get("platform", "youtube"),
                "channels": "\n".join(cfg["channels"]),
                "mode": cfg["mode"],
                "interval_min": cfg["interval_min"],
                "vm_name": cfg.get("vm_name", ""),  # THÊM
                "account_display": cfg.get("account_display", ""),
                "remove_keywords": cfg.get("remove_keywords", ""),  # Load từ khóa
                "auto_remove_hashtags": cfg.get("auto_remove_hashtags", False)  # Load auto remove hashtags
            }

        win = tk.Toplevel(self)
        win.title("Sửa luồng" if editing else "Thêm luồng")
        win.geometry("680x700")
        win.grab_set()

        frm = tk.Frame(win)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tên luồng
        tk.Label(frm, text="Tên luồng:").pack(anchor="w")
        ent_name = ttk.Entry(frm)
        ent_name.insert(0, init["name"])
        ent_name.pack(fill=tk.X, pady=4)

        # === THÊM PHẦN NÀY: Chọn máy ảo ===
        tk.Label(frm, text="Chọn tài khoản (máy ảo):").pack(anchor="w", pady=(8, 0))
        
        vm_list = get_vm_list_with_insta()
        vm_displays = [vm["display"] for vm in vm_list]
        vm_names = [vm["vm_name"] for vm in vm_list]
        
        combo_vm = ttk.Combobox(frm, values=vm_displays, state="readonly")
        combo_vm.pack(fill=tk.X, pady=4)
        
        # Set giá trị mặc định nếu đang edit
        if init["vm_name"] and init["vm_name"] in vm_names:
            idx = vm_names.index(init["vm_name"])
            combo_vm.current(idx)
        elif vm_displays:
            combo_vm.current(0) 

        # Thời gian bắt đầu (VN)
        tk.Label(frm, text="Thời gian bắt đầu (dd/mm/yyyy HH:MM – giờ Việt Nam):").pack(anchor="w")
        ent_start = ttk.Entry(frm)
        ent_start.insert(0, init["start_vn"])
        ent_start.pack(fill=tk.X, pady=4)
        
        # Chọn nền tảng (YouTube / TikTok)
        tk.Label(frm, text="Nền tảng:").pack(anchor="w")
        platform_var = tk.StringVar(value=init.get("platform", "youtube"))
        platform_menu = ttk.Combobox(frm, textvariable=platform_var, values=["youtube", "tiktok"], state="readonly")
        platform_menu.pack(fill=tk.X, pady=4)

        # Kênh theo dõi (nhiều kênh, mỗi dòng 1 link)
        tk.Label(frm, text="Đường dẫn kênh (mỗi dòng 1 kênh").pack(anchor="w")
        txt_channels = tk.Text(frm, height=10)
        txt_channels.insert("1.0", init["channels"])
        txt_channels.pack(fill=tk.BOTH, expand=True, pady=4)

        # Radio lấy gì
        tk.Label(frm, text="Loại video lấy:").pack(anchor="w")
        mode_var = tk.StringVar(value=init["mode"])

        rd1 = ttk.Radiobutton(frm, text="Lấy Shorts (<182s)", variable=mode_var, value="shorts")
        rd2 = ttk.Radiobutton(frm, text="Lấy video dài (>=182s)", variable=mode_var, value="long")
        rd3 = ttk.Radiobutton(frm, text="Lấy cả 2", variable=mode_var, value="both")
        rd1.pack(anchor="w"); rd2.pack(anchor="w"); rd3.pack(anchor="w")

        def on_platform_change(event=None):
            platform = platform_var.get()
            if platform == "tiktok":
                # TikTok chỉ có video ngắn, nên tắt lựa chọn
                mode_var.set("both")
                rd1.config(state="disabled")
                rd2.config(state="disabled")
                rd3.config(state="disabled")
            else:
                # YouTube → bật lại tùy chọn
                rd1.config(state="normal")
                rd2.config(state="normal")
                rd3.config(state="normal")

        platform_menu.bind("<<ComboboxSelected>>", on_platform_change)
        # Gọi 1 lần để áp dụng khi mở form
        on_platform_change()

        # Thời gian quét
        tk.Label(frm, text="Thời gian quét (phút, 60-1440):").pack(anchor="w")
        spn_interval = tk.Spinbox(frm, from_=60, to=1440, increment=60)
        spn_interval.delete(0, tk.END)
        spn_interval.insert(0, str(init["interval_min"]))
        spn_interval.pack(anchor="w", pady=4)

        # Từ khóa loại bỏ
        tk.Label(frm, text="Từ khóa loại bỏ khỏi tiêu đề (phân tách bằng dấu phẩy, phân biệt hoa thường):").pack(anchor="w", pady=(8, 0))
        ent_keywords = ttk.Entry(frm)
        ent_keywords.insert(0, init["remove_keywords"])
        ent_keywords.pack(fill=tk.X, pady=4)
        tk.Label(frm, text="Ví dụ: #tiktok, #Tiktok, _R, [18+]", font=("Segoe UI", 8), fg="gray").pack(anchor="w")

        # Checkbox: Auto remove all hashtags
        auto_remove_hashtags_var = tk.BooleanVar(value=init.get("auto_remove_hashtags", False))
        chk_remove_hashtags = ttk.Checkbutton(
            frm,
            text="🗑️ Tự động xóa tất cả hashtag (bao gồm cả dấu #)",
            variable=auto_remove_hashtags_var
        )
        chk_remove_hashtags.pack(anchor="w", pady=(4, 0))

        btns = tk.Frame(frm)
        btns.pack(fill=tk.X, pady=8)

        def on_save():
            name = ent_name.get().strip()
            if not name:
                messagebox.showerror("Lỗi", "Tên luồng không được để trống.")
                return
            else:
                # kiểm tra trùng tên (nếu thêm mới hoặc đổi tên khi sửa)
                for iid, st in self.streams.items():
                    if st.cfg["name"] == name:
                        if not (editing and iid == edit_iid):
                            messagebox.showerror("Lỗi", "Tên luồng đã tồn tại. Hãy chọn tên khác.")
                            return
            selected_idx = combo_vm.current()
            if selected_idx < 0:
                messagebox.showerror("Lỗi", "Vui lòng chọn một tài khoản (máy ảo).")
                return
            
            selected_vm_name = vm_names[selected_idx]
            selected_display = vm_displays[selected_idx]
            try:
                _ = parse_vn_datetime(ent_start.get().strip(), VN_TZ)  # dd/mm/yyyy HH:MM (VN)
            except Exception:
                messagebox.showerror("Lỗi", "Thời gian bắt đầu sai định dạng. Dùng dd/mm/yyyy HH:MM (giờ VN).")
                return

            channels = [ln.strip() for ln in txt_channels.get("1.0", tk.END).splitlines() if ln.strip()]
            if not channels:
                messagebox.showerror("Lỗi", "Hãy nhập tối thiểu 1 kênh.")
                return

            mode = mode_var.get()
            if mode not in ("shorts", "long", "both"):
                messagebox.showerror("Lỗi", "Hãy chọn 1 trong 3 chế độ lấy video.")
                return

            try:
                iv = int(spn_interval.get())
                if iv < 5 or iv > 1440:
                    raise ValueError
            except Exception:
                messagebox.showerror("Lỗi", "Thời gian quét phải từ 5 đến 1440 phút.")
                return

            # Tạo cấu hình cơ sở
            slug = slugify(name)
            out_path = os.path.join(OUTPUT_DIR, f"{slug}.json")
            cfg = {
                "id": slug,
                "name": name,
                "vm_name": selected_vm_name,  # THÊM
                "account_display": selected_display,
                "start_vn": ent_start.get().strip(),
                "platform": platform_var.get(),
                "channels": channels,
                "mode": mode,
                "interval_min": iv,
                "out_path": out_path,
                "remove_keywords": ent_keywords.get().strip(),  # Lưu từ khóa
                "auto_remove_hashtags": auto_remove_hashtags_var.get()  # Lưu auto remove hashtags
            }

            meta = load_streams_meta()

            if editing:
                # --- SỬA LUỒNG ---
                if self.streams[edit_iid].is_running():
                    messagebox.showwarning("Đang chạy", "Hãy dừng luồng trước khi sửa.")
                    return

                old_cfg = self.streams[edit_iid].cfg
                old_out = old_cfg["out_path"]       # giữ nguyên file cũ

                # cập nhật cfg nhưng giữ id & out_path cũ
                cfg = {
                    "id": old_cfg["id"],            # GIỮ ID cũ để không nhân bản dòng trong streams.json
                    "name": name,
                    "vm_name": selected_vm_name,  # THÊM
                    "account_display": selected_display,
                    "start_vn": ent_start.get().strip(),
                    "platform": platform_var.get(),
                    "channels": channels,
                    "mode": mode,
                    "interval_min": iv,
                    "out_path": old_out,
                    "remove_keywords": ent_keywords.get().strip(),  # Lưu từ khóa
                    "auto_remove_hashtags": auto_remove_hashtags_var.get()  # Lưu auto remove hashtags
                }

                # xóa dữ liệu cũ để không lẫn (và tạo file rỗng)
                reset_output_file(old_out)

                # cập nhật stream & UI
                self.streams[edit_iid].cfg = cfg
                self.tree.set(edit_iid, "name", cfg["name"])
                self.tree.set(edit_iid, "account", selected_display)
                self.tree.set(edit_iid, "watch", f"{len(cfg['channels'])} kênh")
                self.tree.set(edit_iid, "interval", f"{cfg['interval_min']} phút")
                self.tree.set(edit_iid, "status", "Chưa chạy")

                # ghi meta theo id cũ
                replaced = False
                for i, old in enumerate(meta["streams"]):
                    if old["id"] == old_cfg["id"]:
                        meta["streams"][i] = cfg
                        replaced = True
                        break
                if not replaced:
                    meta["streams"].append(cfg)
                save_streams_meta(meta)

                messagebox.showinfo("OK", "Đã lưu & làm mới dữ liệu luồng (đã xoá file cũ).")
                win.destroy()
                return

            else:
                # --- THÊM LUỒNG MỚI ---
                # tạo file rỗng ngay để thấy kết quả
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)

                # ghi meta (ghi đè theo id nếu trùng)
                found = False
                for i, s in enumerate(meta["streams"]):
                    if s["id"] == cfg["id"]:
                        meta["streams"][i] = cfg
                        found = True
                        break
                if not found:
                    meta["streams"].append(cfg)
                save_streams_meta(meta)

                # thêm dòng vào bảng
                self.add_stream_row(cfg)

                messagebox.showinfo("OK", "Đã thêm luồng.")
                win.destroy()
                return

        def on_save_wrapper():
            try:
                on_save()
            except Exception as e:
                show_exception_dialog("Lỗi khi lưu luồng", e)

        ttk.Button(btns, text="💾 Lưu", command=on_save_wrapper).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Đóng", command=win.destroy).pack(side=tk.RIGHT)

    # ---------- BẢNG: CLICK HÀNH ĐỘNG ----------
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)  # '#1'..'#10'
        if not row_id or not col_id:
            return

        col = self.tree["columns"][int(col_id.strip("#")) - 1]
        if row_id not in self.streams:
            return
        stream = self.streams[row_id]

        if col == "run":
            platform = stream.cfg.get("platform", "youtube")
            if platform == "youtube" and len(multi_api_manager.get_keys("youtube")) == 0:
                messagebox.showerror("API", "Chưa có API key YouTube. Vào nút API để thêm.")
                return
            stream.start(self.ui_queue)
            self.tree.set(row_id, "status", "Đang chạy...")
        elif col == "stop":
            stream.stop()
        elif col == "log":
            self.open_log_window(stream)
        elif col == "edit":
            self.open_add_stream_dialog(edit_iid=row_id)
        elif col == "delete":
            self.delete_stream(row_id)

    def open_log_window(self, stream: Stream):
        # 🟢 nếu chưa có dict log_windows thì tạo
        if not hasattr(self, "log_windows"):
            self.log_windows = {}

        # 🟢 nếu cửa sổ log đã mở, focus lại thay vì mở mới
        if stream.row_id in self.log_windows and self.log_windows[stream.row_id].winfo_exists():
            self.log_windows[stream.row_id].focus()
            return

        # 🟢 tạo cửa sổ mới
        win = tk.Toplevel(self)
        win.title(f"Log – {stream.cfg['name']}")
        win.geometry("800x480")
        win.grab_set()

        # 🟢 tạo text widget
        txt = tk.Text(win, wrap="word", state="disabled")
        txt.pack(fill=tk.BOTH, expand=True)

        # 🟢 hiển thị sẵn log cũ (nếu có)
        if stream.logs:
            txt.config(state="normal")
            txt.insert("1.0", "\n".join(stream.logs))
            txt.see("end")
            txt.config(state="disabled")

        # 🟢 lưu để callback append_log_line có thể truy cập
        win.text_log = txt
        self.log_windows[stream.row_id] = win

        # 🟢 thêm nút Xóa và Đóng (tùy chọn)
        btns = tk.Frame(win)
        btns.pack(fill=tk.X, pady=5)

        def clear_logs():
            stream.logs.clear()
            txt.config(state="normal")
            txt.delete("1.0", tk.END)
            txt.config(state="disabled")

        ttk.Button(btns, text="Xóa lịch sử", command=clear_logs).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Đóng", command=win.destroy).pack(side=tk.RIGHT, padx=4)


    def delete_stream(self, row_id: str):
        s = self.streams[row_id]
        if s.is_running():
            if not messagebox.askyesno("Xóa", "Luồng đang chạy. Dừng và xóa?"):
                return
            s.stop()
            time.sleep(0.3)
        # xóa khỏi meta
        meta = load_streams_meta()
        meta["streams"] = [x for x in meta["streams"] if x["id"] != s.cfg["id"]]
        save_streams_meta(meta)
        # xóa khỏi UI
        self.tree.delete(row_id)
        del self.streams[row_id]
        self.refresh_stt()
        # hỏi xóa file kết quả
        if os.path.exists(s.cfg["out_path"]):
            if messagebox.askyesno("Xóa file", "Xóa luôn file kết quả của luồng?"):
                try:
                    os.remove(s.cfg["out_path"])
                except Exception:
                    pass

    # ---------- QUEUE CẬP NHẬT UI TỪ THREAD ----------
    def process_ui_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                kind = msg[0]
                if kind == "status":
                    _, row_id, status = msg
                    if row_id in self.streams:
                        self.tree.set(row_id, "status", status)
        except queue.Empty:
            pass
        self.after(200, self.process_ui_queue)

    # ---------- CLEANUP KHI ĐÓNG APP ----------
    def cleanup(self):
        """
        ✅ Cleanup khi đóng app - Dừng THẬT SỰ tất cả streams và tắt VMs
        """
        if self.is_shutting_down:
            return  # Tránh cleanup nhiều lần

        self.is_shutting_down = True
        self.logger.info("=" * 50)
        self.logger.info("🛑 BẮT ĐẦU CLEANUP TAB_FOLLOW")
        self.logger.info("=" * 50)

        try:
            # 1️⃣ Stop tất cả streams đang chạy
            running_streams = [(name, stream) for name, stream in self.streams.items()
                              if hasattr(stream, 'thread') and stream.thread and stream.thread.is_alive()]

            if running_streams:
                self.logger.info(f"🛑 Đang dừng {len(running_streams)} streams...")
                for name, stream in running_streams:
                    self.logger.info(f"   - Dừng stream: {name}")
                    try:
                        stream.stop()
                    except Exception as e:
                        self.logger.error(f"   ❌ Lỗi stop stream {name}: {e}")

            # 2️⃣ Đợi threads kết thúc (timeout 10s)
            self.logger.info("⏳ Đợi threads kết thúc (timeout 10s)...")
            import time
            for name, stream in running_streams:
                if stream.thread:
                    stream.thread.join(timeout=10)
                    if stream.thread.is_alive():
                        self.logger.warning(f"   ⚠️ Stream {name} không dừng sau 10s")
                    else:
                        self.logger.info(f"   ✅ Stream {name} đã dừng")

            # 3️⃣ Tắt tất cả VMs đang được dùng bởi streams
            self.logger.info("🛑 Đang tắt tất cả VMs...")
            vms_to_check = set()
            for stream in self.streams.values():
                vm_name = stream.cfg.get("vm_name")
                if vm_name:
                    vms_to_check.add(vm_name)

            self.logger.info(f"📋 Kiểm tra {len(vms_to_check)} VMs...")

            if vms_to_check:
                import subprocess
                try:
                    # List tất cả VMs đang chạy
                    result = subprocess.run(
                        [LDCONSOLE_EXE, "list2"],
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
                                [LDCONSOLE_EXE, "quit", "--name", vm_name],
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                timeout=10
                            )
                            self.logger.info(f"   ✅ Đã gửi lệnh tắt VM: {vm_name}")
                        except Exception as e:
                            self.logger.error(f"   ❌ Lỗi khi tắt VM {vm_name}: {e}")

                    if len(running_vms) > 0:
                        self.logger.info("⏳ Chờ 3 giây để VMs tắt...")
                        time.sleep(3)

                except Exception as e:
                    self.logger.error(f"❌ Lỗi khi check/tắt VMs: {e}")

            self.logger.info("=" * 50)
            self.logger.info("✅ CLEANUP TAB_FOLLOW HOÀN TẤT")
            self.logger.info("=" * 50)

        except Exception as e:
            self.logger.exception(f"❌ Lỗi trong cleanup: {e}")