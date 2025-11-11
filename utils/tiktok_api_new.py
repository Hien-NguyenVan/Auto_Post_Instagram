"""
TikTok API Integration using DumplingAI
"""
import subprocess
import json
import re
from datetime import datetime, timezone


def extract_tiktok_handle(url):
    """
    Trích xuất handle từ URL TikTok

    Input: https://www.tiktok.com/@tiin.vn
    Output: tiin.vn
    """
    # Pattern: @handle sau tiktok.com/
    match = re.search(r'tiktok\.com/@([^/?&#]+)', url)
    if match:
        return match.group(1)

    # Nếu chỉ có @handle
    if url.startswith('@'):
        return url[1:]

    return url.strip()


def fetch_tiktok_videos(handle, api_key, log_callback=None):
    """
    Lấy danh sách video từ kênh TikTok qua DumplingAI API

    Args:
        handle: Tên kênh (không có @)
        api_key: Bearer token
        log_callback: Hàm log (optional)

    Returns:
        list: Danh sách video parsed
    """
    log = log_callback or (lambda msg: print(msg))

    # Prepare curl command
    url = "https://app.dumplingai.com/api/v1/get-tiktok-profile-videos"

    headers = [
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json"
    ]

    body = json.dumps({"handle": handle})

    cmd = [
        "curl", "-s", "-X", "POST", url,
        *headers,
        "-d", body
    ]

    try:
        log(f"🔍 Đang lấy danh sách video từ @{handle}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=30
        )

        if result.returncode != 0:
            log(f"❌ Lỗi curl: {result.stderr}")
            return []

        # Parse JSON
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            log(f"❌ Lỗi parse JSON: {e}")
            log(f"Response: {result.stdout[:200]}")
            return []

        # Extract aweme_list
        aweme_list = data.get("aweme_list", [])
        if not aweme_list:
            log(f"⚠️ Không tìm thấy video nào từ @{handle}")
            return []

        log(f"✅ Tìm thấy {len(aweme_list)} video từ API")

        # Parse videos
        videos = parse_tiktok_response(aweme_list, log)
        log(f"✅ Parse thành công {len(videos)} video hợp lệ")

        return videos

    except subprocess.TimeoutExpired:
        log(f"⏱️ Timeout khi gọi API TikTok")
        return []
    except Exception as e:
        log(f"❌ Lỗi khi lấy video TikTok: {e}")
        return []


def parse_tiktok_response(aweme_list, log_callback=None):
    """
    Parse danh sách video từ aweme_list

    Trích xuất:
    - aweme_id
    - desc (caption)
    - create_time (Unix timestamp)
    - video.play_addr.url_list[1]

    Returns:
        list: [{"aweme_id", "desc", "create_time", "video_url", "publishedAt_iso"}, ...]
    """
    log = log_callback or (lambda msg: print(msg))

    videos = []

    for item in aweme_list:
        try:
            # Extract required fields
            aweme_id = item.get("aweme_id")
            desc = item.get("desc", "")
            create_time = item.get("create_time")

            if not aweme_id or create_time is None:
                continue

            # Extract video URL from url_list[1]
            video = item.get("video", {})
            play_addr = video.get("play_addr", {})
            url_list = play_addr.get("url_list", [])

            # Validation: url_list phải có ít nhất 2 phần tử
            if len(url_list) < 2:
                log(f"⚠️ Video {aweme_id}: url_list không đủ, bỏ qua")
                continue

            video_url = url_list[1]

            if not video_url:
                log(f"⚠️ Video {aweme_id}: url_list[1] rỗng, bỏ qua")
                continue

            # Convert create_time to ISO 8601
            try:
                dt = datetime.fromtimestamp(int(create_time), tz=timezone.utc)
                published_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                log(f"⚠️ Video {aweme_id}: create_time không hợp lệ")
                continue

            videos.append({
                "aweme_id": aweme_id,
                "desc": desc,
                "create_time": int(create_time),
                "video_url": video_url,
                "publishedAt_iso": published_iso
            })

        except Exception as e:
            log(f"⚠️ Lỗi parse video: {e}")
            continue

    return videos


def filter_videos_newer_than(videos, cutoff_dt, log_callback=None):
    """
    Lọc video có create_time > cutoff_dt

    Args:
        videos: List từ parse_tiktok_response()
        cutoff_dt: datetime object (UTC)
        log_callback: Hàm log

    Returns:
        list: Video mới hơn cutoff_dt
    """
    log = log_callback or (lambda msg: print(msg))

    filtered = []
    for v in videos:
        video_time = datetime.fromtimestamp(v["create_time"], tz=timezone.utc)

        if video_time > cutoff_dt:
            filtered.append(v)

    if filtered:
        log(f"🎯 Tìm thấy {len(filtered)} video mới (sau {cutoff_dt.strftime('%d/%m/%Y %H:%M')})")

    return filtered


def convert_to_output_format(videos):
    """
    Convert sang format giống YouTube để lưu vào JSON

    Output format:
    {
        "title": desc,
        "publishedAt": ISO string,
        "duration": "unknown",
        "url": video_url,
        "status": "unpost"
    }
    """
    output = []
    for v in videos:
        output.append({
            "title": v["desc"] or f"TikTok Video {v['aweme_id']}",
            "publishedAt": v["publishedAt_iso"],
            "duration": "unknown",  # TikTok không có duration
            "url": v["video_url"],
            "status": "unpost"
        })

    return output


def check_tiktok_api_key_valid(api_key, timeout=15):
    """
    Kiểm tra TikTok API key (DumplingAI) có hoạt động không

    Args:
        api_key: Bearer token từ DumplingAI
        timeout: Timeout cho request (giây)

    Returns:
        dict với các key:
        - valid (bool): API key có hoạt động không
        - message (str): Thông báo chi tiết
        - quota_remaining (int|None): None (DumplingAI không có quota header)
    """
    try:
        # Test với một handle TikTok phổ biến
        test_handle = "tiktok"

        url = "https://app.dumplingai.com/api/v1/get-tiktok-profile-videos"
        headers = [
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json"
        ]
        body = json.dumps({"handle": test_handle})

        cmd = [
            "curl", "-s", "-X", "POST", url,
            *headers,
            "-d", body
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=timeout
        )

        if result.returncode != 0:
            return {
                "valid": False,
                "message": f"✗ Lỗi kết nối: {result.stderr or 'Unknown error'}",
                "quota_remaining": None
            }

        # Parse response
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "valid": False,
                "message": "✗ Response không hợp lệ (không phải JSON)",
                "quota_remaining": None
            }

        # Check if có aweme_list (success response)
        if "aweme_list" in data:
            return {
                "valid": True,
                "message": "✓ API key hoạt động bình thường",
                "quota_remaining": None
            }

        # Check for error messages
        if "error" in data or "message" in data:
            error_msg = data.get("error") or data.get("message", "Unknown error")
            return {
                "valid": False,
                "message": f"✗ {error_msg}",
                "quota_remaining": None
            }

        # Unknown response
        return {
            "valid": False,
            "message": "✗ Response không xác định được",
            "quota_remaining": None
        }

    except subprocess.TimeoutExpired:
        return {
            "valid": False,
            "message": "✗ Timeout khi kiểm tra API",
            "quota_remaining": None
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"✗ Lỗi: {str(e)}",
            "quota_remaining": None
        }
