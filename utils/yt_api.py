# -*- coding: utf-8 -*-
"""
YouTube API Utilities
Quản lý API keys, gọi YouTube Data API v3, và xử lý dữ liệu video
"""

import os
import re
import json
from datetime import datetime, timezone
import requests

# ========================= CẤU HÌNH =========================
BASE_URL = "https://www.googleapis.com/youtube/v3"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "yt-multi-stream/1.0"})

# ========================= QUẢN LÝ API KEYS =========================
class APIKeyManager:
    """Quản lý việc đọc/ghi và xoay vòng API keys"""
    
    def __init__(self, api_file_path: str):
        self.api_file = api_file_path
        self.keys = []
        self.current_index = 0
        self.refresh()
    
    def refresh(self):
        """Tải lại danh sách API keys từ file"""
        self.keys = self.load_keys()
        self.current_index = 0
    
    def load_keys(self) -> list:
        """Đọc API keys từ file"""
        if not os.path.exists(self.api_file):
            return []
        with open(self.api_file, "r", encoding="utf-8") as f:
            keys = [line.strip() for line in f if line.strip()]
        return keys
    
    def save_keys(self, keys: list):
        """Lưu danh sách API keys vào file"""
        os.makedirs(os.path.dirname(self.api_file), exist_ok=True)
        with open(self.api_file, "w", encoding="utf-8") as f:
            f.write("\n".join(keys))
        self.refresh()
    
    def next_key(self) -> str:
        """Lấy API key tiếp theo (round-robin)"""
        if not self.keys:
            raise RuntimeError("Chưa có API key. Hãy thêm trong nút API.")
        key = self.keys[self.current_index % len(self.keys)]
        self.current_index += 1
        return key
    
    def has_keys(self) -> bool:
        """Kiểm tra xem có API key nào không"""
        return len(self.keys) > 0

    
# ========================= GỌI YOUTUBE API =========================
def call_youtube_api(path: str, params: dict, api_key_manager, retry_all_keys: bool = True):
    """
    Gọi YouTube Data API v3 với cơ chế retry khi gặp lỗi quota/403/400

    Args:
        path: Endpoint path (vd: "channels", "playlistItems", "videos")
        params: Query parameters
        api_key_manager: Đối tượng quản lý API keys (APIKeyManager hoặc MultiAPIManager)
        retry_all_keys: Nếu True, thử hết tất cả keys khi gặp lỗi

    Returns:
        JSON response từ API

    Raises:
        RuntimeError: Khi tất cả keys đều thất bại
    """
    last_error = None

    # Duck typing: Hỗ trợ cả APIKeyManager và MultiAPIManager
    if hasattr(api_key_manager, 'get_keys'):
        # MultiAPIManager
        keys = api_key_manager.get_keys("youtube") or []
    else:
        # APIKeyManager (backward compatible)
        keys = api_key_manager.keys or []

    max_tries = len(keys) if retry_all_keys else 1

    for i in range(max(1, max_tries)):
        # Lấy API key tùy theo loại manager
        if hasattr(api_key_manager, 'get_next_youtube_key'):
            # MultiAPIManager
            api_key = api_key_manager.get_next_youtube_key()
        else:
            # APIKeyManager (backward compatible)
            api_key = api_key_manager.next_key()

        if not api_key:
            raise RuntimeError("Chưa có API key. Hãy thêm trong nút API.")

        request_params = dict(params or {})
        request_params["key"] = api_key

        try:
            response = SESSION.get(
                f"{BASE_URL}/{path}",
                params=request_params,
                timeout=20
            )

            if response.status_code == 200:
                return response.json()

            # Lỗi 4xx (quota/forbidden) -> thử key khác
            last_error = f"HTTP {response.status_code}: {response.text[:200]}"

        except Exception as e:
            last_error = str(e)

    raise RuntimeError(f"Lỗi gọi YouTube API: {last_error or 'Không rõ'}")


# ========================= XỬ LÝ CHANNEL =========================
def extract_channel_id(url: str, api_key_manager) -> str:
    """
    Trích xuất Channel ID từ URL YouTube
    Hỗ trợ:
    - /channel/UCxxxx
    - /@handle (có dấu .)

    Args:
        url: URL của kênh YouTube
        api_key_manager: Đối tượng quản lý API keys (APIKeyManager hoặc MultiAPIManager)
    """
    # Dạng /channel/UCxxxx
    match = re.search(r"youtube\.com/channel/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    
    # Dạng /@handle (hỗ trợ dấu .)
    match = re.search(r"youtube\.com/@([\w.-]+)", url)
    if match:
        handle = match.group(1).split("/")[0]  # xử lý trường hợp có /featured, /videos...
        data = call_youtube_api(
            "channels",
            {"part": "id", "forHandle": handle},
            api_key_manager
        )
        items = data.get("items", [])
        if items:
            return items[0]["id"]
    
    raise ValueError(f"Không thể lấy Channel ID từ URL: {url}")



def get_uploads_playlist_id(channel_id: str, api_key_manager) -> str:
    """
    Lấy Playlist ID của uploads từ Channel ID

    Args:
        channel_id: ID của kênh
        api_key_manager: Đối tượng quản lý API keys (APIKeyManager hoặc MultiAPIManager)

    Returns:
        Playlist ID của uploads (UUxxxx...)

    Raises:
        RuntimeError: Khi không tìm thấy kênh
    """
    data = call_youtube_api(
        "channels",
        {"part": "contentDetails", "id": channel_id},
        api_key_manager
    )
    items = data.get("items", [])
    if not items:
        raise RuntimeError("Không tìm thấy kênh.")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


# ========================= XỬ LÝ VIDEO =========================
def iter_playlist_videos_newer_than(
    playlist_id: str,
    cutoff_time: datetime,
    api_key_manager
):
    """
    Duyệt playlist và yield các video có publishedAt > cutoff_time
    Duyệt từ mới nhất về cũ, dừng khi gặp video cũ hơn cutoff_time

    Args:
        playlist_id: ID của playlist (uploads playlist)
        cutoff_time: Mốc thời gian (UTC) để lọc
        api_key_manager: Đối tượng quản lý API keys (APIKeyManager hoặc MultiAPIManager)

    Yields:
        tuple: (video_id, published_at_iso_string)
    """
    next_page_token = None
    
    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50
        }
        if next_page_token:
            params["pageToken"] = next_page_token
        
        data = call_youtube_api("playlistItems", params, api_key_manager)
        items = data.get("items", [])
        
        if not items:
            break
        
        for item in items:
            video_id = item["contentDetails"]["videoId"]
            published_at = item["snippet"]["publishedAt"]
            published_time = iso_to_datetime(published_at)
            
            if published_time > cutoff_time:
                yield video_id, published_at
            else:
                # Các video sau đều cũ hơn -> dừng
                return
        
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break


def fetch_video_details(video_ids: list, api_key_manager) -> list:
    """
    Lấy thông tin chi tiết của các video

    Args:
        video_ids: Danh sách video IDs
        api_key_manager: Đối tượng quản lý API keys (APIKeyManager hoặc MultiAPIManager)

    Returns:
        List of dict với các trường: title, publishedAt, duration, url
    """
    results = []
    
    # Gọi API theo batch 50 videos
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        data = call_youtube_api(
            "videos",
            {
                "part": "snippet,contentDetails",
                "id": ",".join(chunk)
            },
            api_key_manager
        )
        
        for item in data.get("items", []):
            results.append({
                "title": item["snippet"]["title"],
                "publishedAt": item["snippet"]["publishedAt"],
                "duration": item["contentDetails"]["duration"],
                "url": f"https://www.youtube.com/watch?v={item['id']}",
                 "status": "unpost"
            })
    
    return results


# ========================= XỬ LÝ THỜI GIAN =========================
def parse_vn_datetime(date_string: str, vn_timezone) -> datetime:
    """
    Parse datetime string theo định dạng Việt Nam (dd/mm/yyyy HH:MM)
    
    Args:
        date_string: Chuỗi ngày giờ (vd: "15/01/2024 10:30")
        vn_timezone: Timezone object cho VN (UTC+7)
    
    Returns:
        datetime object với timezone VN
    """
    return datetime.strptime(date_string.strip(), "%d/%m/%Y %H:%M").replace(tzinfo=vn_timezone)


def iso_to_datetime(iso_string: str) -> datetime:
    """
    Chuyển ISO 8601 string (UTC Z) sang datetime object
    
    Args:
        iso_string: Chuỗi ISO 8601 (vd: "2024-01-15T10:30:00Z")
    
    Returns:
        datetime object với timezone UTC
    """
    return datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def datetime_to_iso(dt: datetime) -> str:
    """
    Chuyển datetime object sang ISO 8601 string (UTC Z)
    
    Args:
        dt: datetime object
    
    Returns:
        Chuỗi ISO 8601 ở UTC
    """
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso8601_duration(duration: str) -> int:
    """
    Parse ISO 8601 duration (PT#H#M#S) sang số giây
    
    Args:
        duration: Chuỗi duration (vd: "PT1M30S", "PT2H3M", "PT45S")
    
    Returns:
        Số giây
    
    Examples:
        >>> parse_iso8601_duration("PT1M30S")
        90
        >>> parse_iso8601_duration("PT2H3M")
        7380
    """
    hours = minutes = seconds = 0
    match = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", duration)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


# ========================= LỌC VIDEO =========================
def filter_videos_by_mode(videos: list, mode: str) -> list:
    """
    Lọc video theo độ dài (shorts/long/both)
    
    Args:
        videos: Danh sách video dict (phải có trường 'duration')
        mode: Chế độ lọc - 'shorts' (<60s), 'long' (>=60s), 'both'
    
    Returns:
        Danh sách video đã lọc
    """
    if mode == "both":
        return videos
    
    filtered = []
    for video in videos:
        duration_seconds = parse_iso8601_duration(video["duration"])
        
        if mode == "shorts" and duration_seconds < 100:
            filtered.append(video)
        elif mode == "long" and duration_seconds >= 100:
            filtered.append(video)
    
    return filtered

def check_api_key_valid(api_key: str, timeout: int = 10) -> dict:
        """
        Kiểm tra API key có hoạt động không
        
        Args:
            api_key: API key cần kiểm tra
            timeout: Timeout cho request (giây)
        
        Returns:
            dict với các key:
            - valid (bool): API key có hoạt động không
            - message (str): Thông báo chi tiết
            - quota_remaining (int|None): Quota còn lại (nếu lấy được)
        """
        try:
            # Gọi API đơn giản nhất để test - lấy thông tin về chính API key
            # Dùng endpoint search với maxResults=1 để tiết kiệm quota
            response = SESSION.get(
                f"{BASE_URL}/search",
                params={
                    "part": "id",
                    "maxResults": 1,
                    "type": "video",
                    "q": "test",
                    "key": api_key
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                # Thử lấy quota info từ headers (nếu có)
                quota_remaining = None
                if "X-Quota-Remaining" in response.headers:
                    try:
                        quota_remaining = int(response.headers["X-Quota-Remaining"])
                    except:
                        pass
                
                return {
                    "valid": True,
                    "message": "✓ API key hoạt động bình thường",
                    "quota_remaining": quota_remaining
                }
            
            elif response.status_code == 403:
                try:
                    error_data = response.json()
                    error_reason = error_data.get("error", {}).get("errors", [{}])[0].get("reason", "")
                    
                    if "quotaExceeded" in error_reason or "dailyLimitExceeded" in error_reason:
                        return {
                            "valid": False,
                            "message": "✗ API key hết quota (đã vượt giới hạn)",
                            "quota_remaining": 0
                        }
                    elif "keyInvalid" in error_reason:
                        return {
                            "valid": False,
                            "message": "✗ API key không hợp lệ",
                            "quota_remaining": None
                        }
                    else:
                        return {
                            "valid": False,
                            "message": f"✗ Lỗi 403: {error_reason}",
                            "quota_remaining": None
                        }
                except:
                    return {
                        "valid": False,
                        "message": "✗ API key bị từ chối (403 Forbidden)",
                        "quota_remaining": None
                    }
            
            elif response.status_code == 400:
                return {
                    "valid": False,
                    "message": "✗ API key không hợp lệ (400 Bad Request)",
                    "quota_remaining": None
                }
            
            else:
                return {
                    "valid": False,
                    "message": f"✗ Lỗi HTTP {response.status_code}",
                    "quota_remaining": None
                }
        
        except requests.Timeout:
            return {
                "valid": False,
                "message": "✗ Timeout - không thể kết nối đến API",
                "quota_remaining": None
            }
        
        except Exception as e:
            return {
                "valid": False,
                "message": f"✗ Lỗi: {str(e)[:100]}",
                "quota_remaining": None
            }
        
