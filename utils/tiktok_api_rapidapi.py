"""
TikTok API Integration using RapidAPI (tiktok-api23)

API Endpoints:
- User Info: https://tiktok-api23.p.rapidapi.com/api/user/info
- User Posts: https://tiktok-api23.p.rapidapi.com/api/user/posts
- Video Download: https://tiktok-api23.p.rapidapi.com/api/download/video
"""
import subprocess
import json
import re
import os
import time
from datetime import datetime, timezone


def extract_tiktok_username(url):
    """
    Trích xuất username từ URL TikTok

    Input: https://www.tiktok.com/@theanh28entertainment
    Output: theanh28entertainment
    """
    # Pattern: @username sau tiktok.com/
    match = re.search(r'tiktok\.com/@([^/?&#]+)', url)
    if match:
        return match.group(1)

    # Nếu chỉ có @username
    if url.startswith('@'):
        return url[1:]

    return url.strip()


def get_tiktok_secuid(username, api_key, log_callback=None):
    """
    Lấy secUid từ username TikTok

    Args:
        username: Tên kênh (không có @)
        api_key: RapidAPI key
        log_callback: Hàm log (optional)

    Returns:
        str: secUid hoặc None nếu lỗi
    """
    log = log_callback or (lambda msg: print(msg))

    url = "https://tiktok-api23.p.rapidapi.com/api/user/info"

    # Build curl command
    cmd = [
        "curl", "-s", "-X", "GET",
        f"{url}?uniqueId={username}",
        "-H", f"x-rapidapi-key: {api_key}",
        "-H", "x-rapidapi-host: tiktok-api23.p.rapidapi.com"
    ]

    try:
        log(f"🔍 Đang lấy thông tin kênh @{username}...")

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
            return None

        # Parse JSON
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            log(f"❌ Lỗi parse JSON: {e}")
            log(f"Response: {result.stdout[:200]}")
            return None

        # Extract secUid
        try:
            secuid = data["userInfo"]["user"]["secUid"]
            log(f"✅ Đã lấy được secUid của @{username}")
            return secuid
        except KeyError as e:
            log(f"❌ Không tìm thấy secUid trong response: {e}")
            return None

    except subprocess.TimeoutExpired:
        log(f"⏱️ Timeout khi lấy thông tin kênh")
        return None
    except Exception as e:
        log(f"❌ Lỗi khi lấy secUid: {e}")
        return None


def fetch_tiktok_videos_with_count(secuid, count, username, api_key, log_callback=None):
    """
    Lấy danh sách video từ kênh TikTok với số lượng xác định

    Args:
        secuid: secUid của kênh
        count: Số lượng video cần lấy
        username: Tên kênh (để ghép URL)
        api_key: RapidAPI key
        log_callback: Hàm log (optional)

    Returns:
        list: Danh sách video [{id, desc, createTime, video_url, publishedAt}, ...]
    """
    log = log_callback or (lambda msg: print(msg))

    url = "https://tiktok-api23.p.rapidapi.com/api/user/posts"

    videos = []
    cursor = "0"
    total_fetched = 0

    log(f"🎯 Cần lấy {count} video từ kênh...")

    while len(videos) < count:
        # Build curl command
        cmd = [
            "curl", "-s", "-X", "GET",
            f"{url}?secUid={secuid}&count=35&cursor={cursor}",
            "-H", f"x-rapidapi-key: {api_key}",
            "-H", "x-rapidapi-host: tiktok-api23.p.rapidapi.com"
        ]

        try:
            log(f"📥 Đang lấy video (cursor={cursor}, đã có {len(videos)}/{count})...")

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
                break

            # Parse JSON
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                log(f"❌ Lỗi parse JSON: {e}")
                break

            # Extract videos from itemList
            item_list = data.get("data", {}).get("itemList", [])

            if not item_list:
                log(f"⚠️ Không còn video nào (đã lấy {len(videos)} video)")
                break

            # Process each video
            for item in item_list:
                # Skip pinned videos
                if item.get("isPinnedItem") == True:
                    continue

                # Extract required fields
                video_id = item.get("id")
                desc = item.get("desc", "")
                create_time = item.get("createTime")

                if not video_id or create_time is None:
                    continue

                # Build video URL
                video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"

                # Convert timestamp to ISO string
                try:
                    dt = datetime.fromtimestamp(int(create_time), tz=timezone.utc)
                    published_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except:
                    continue

                videos.append({
                    "id": video_id,
                    "desc": desc,
                    "createTime": int(create_time),
                    "video_url": video_url,
                    "publishedAt": published_iso
                })

                # Stop if we have enough videos
                if len(videos) >= count:
                    break

            # Get next cursor for pagination
            next_cursor = data.get("data", {}).get("cursor")

            if not next_cursor or next_cursor == cursor:
                log(f"⚠️ Không có cursor tiếp theo (đã lấy {len(videos)} video)")
                break

            cursor = str(next_cursor)
            total_fetched += len(item_list)

        except subprocess.TimeoutExpired:
            log(f"⏱️ Timeout khi lấy video")
            break
        except Exception as e:
            log(f"❌ Lỗi khi lấy video: {e}")
            break

    # Trim to exact count
    videos = videos[:count]
    log(f"✅ Đã lấy được {len(videos)} video")

    return videos


def get_video_download_link(video_url, api_key, log_callback=None):
    """
    Lấy direct download link từ video URL

    Args:
        video_url: URL video TikTok (https://www.tiktok.com/@username/video/ID)
        api_key: RapidAPI key
        log_callback: Hàm log (optional)

    Returns:
        str: Direct download link hoặc None nếu lỗi
    """
    log = log_callback or (lambda msg: print(msg))

    url = "https://tiktok-api23.p.rapidapi.com/api/download/video"

    # Build curl command
    cmd = [
        "curl", "-s", "-X", "GET",
        f"{url}?url={video_url}",
        "-H", f"x-rapidapi-key: {api_key}",
        "-H", "x-rapidapi-host: tiktok-api23.p.rapidapi.com"
    ]

    try:
        log(f"🔗 Đang lấy link download...")

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
            return None

        # Parse JSON
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            log(f"❌ Lỗi parse JSON: {e}")
            log(f"📋 Response: {result.stdout[:500]}")
            return None

        # Debug: Log response structure
        log(f"📋 Response keys: {list(data.keys())}")

        # Extract play URL
        try:
            play_url = data["play"]
            log(f"✅ Đã lấy được link download")
            return play_url
        except KeyError as e:
            log(f"❌ Không tìm thấy link download trong response: {e}")
            log(f"📋 Available keys: {list(data.keys())}")
            log(f"📋 Full response: {json.dumps(data, indent=2)[:1000]}")
            return None

    except subprocess.TimeoutExpired:
        log(f"⏱️ Timeout khi lấy link download")
        return None
    except Exception as e:
        log(f"❌ Lỗi khi lấy link download: {e}")
        return None


def fetch_tiktok_videos_latest(secuid, username, api_key, log_callback=None):
    """
    Lấy 35 video mới nhất từ kênh TikTok (cho tab_follow)

    Args:
        secuid: secUid của kênh
        username: Tên kênh (để ghép URL)
        api_key: RapidAPI key
        log_callback: Hàm log (optional)

    Returns:
        list: Danh sách video [{id, desc, createTime, video_url, publishedAt}, ...]
    """
    log = log_callback or (lambda msg: print(msg))

    url = "https://tiktok-api23.p.rapidapi.com/api/user/posts"

    # Build curl command (cursor=0, lấy 35 video đầu)
    cmd = [
        "curl", "-s", "-X", "GET",
        f"{url}?secUid={secuid}&count=35&cursor=0",
        "-H", f"x-rapidapi-key: {api_key}",
        "-H", "x-rapidapi-host: tiktok-api23.p.rapidapi.com"
    ]

    try:
        log(f"📥 Đang quét video mới từ kênh...")

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
            return []

        # Extract videos from itemList
        item_list = data.get("data", {}).get("itemList", [])

        if not item_list:
            log(f"⚠️ Không tìm thấy video nào")
            return []

        videos = []

        # Process each video
        for item in item_list:
            # Skip pinned videos
            if item.get("isPinnedItem") == True:
                continue

            # Extract required fields
            video_id = item.get("id")
            desc = item.get("desc", "")
            create_time = item.get("createTime")

            if not video_id or create_time is None:
                continue

            # Build video URL
            video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"

            # Convert timestamp to ISO string
            try:
                dt = datetime.fromtimestamp(int(create_time), tz=timezone.utc)
                published_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except:
                continue

            videos.append({
                "id": video_id,
                "desc": desc,
                "createTime": int(create_time),
                "video_url": video_url,
                "publishedAt": published_iso
            })

        log(f"✅ Đã lấy được {len(videos)} video")
        return videos

    except subprocess.TimeoutExpired:
        log(f"⏱️ Timeout khi quét video")
        return []
    except Exception as e:
        log(f"❌ Lỗi khi quét video: {e}")
        return []


def filter_videos_newer_than(videos, cutoff_dt, log_callback=None):
    """
    Lọc video có createTime > cutoff_dt

    Args:
        videos: List từ fetch_tiktok_videos_*()
        cutoff_dt: datetime object (UTC)
        log_callback: Hàm log

    Returns:
        list: Video mới hơn cutoff_dt
    """
    log = log_callback or (lambda msg: print(msg))

    filtered = []
    for v in videos:
        video_time = datetime.fromtimestamp(v["createTime"], tz=timezone.utc)

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
            "title": v["desc"] or f"TikTok Video {v['id']}",
            "publishedAt": v["publishedAt"],
            "duration": "unknown",
            "url": v["video_url"],
            "status": "unpost"
        })

    return output


def check_tiktok_api_key_valid(api_key, timeout=15):
    """
    Kiểm tra TikTok API key (RapidAPI) có hoạt động không

    Args:
        api_key: RapidAPI key
        timeout: Timeout cho request (giây)

    Returns:
        dict với các key:
        - valid (bool): API key có hoạt động không
        - message (str): Thông báo chi tiết
        - quota_remaining (int|None): None (RapidAPI không có quota header trong response)
    """
    try:
        # Test với một username TikTok phổ biến
        test_username = "tiktok"

        url = "https://tiktok-api23.p.rapidapi.com/api/user/info"

        cmd = [
            "curl", "-s", "-X", "GET",
            f"{url}?uniqueId={test_username}",
            "-H", f"x-rapidapi-key: {api_key}",
            "-H", "x-rapidapi-host: tiktok-api23.p.rapidapi.com"
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

        # Check if có userInfo (success response)
        if "userInfo" in data:
            return {
                "valid": True,
                "message": "✓ API key hoạt động bình thường",
                "quota_remaining": None
            }

        # Check for error messages
        if "message" in data:
            error_msg = data.get("message", "Unknown error")
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


def download_tiktok_video(video_url, api_key, log_callback=None):
    """
    Download video TikTok từ URL

    Args:
        video_url: URL video TikTok (https://www.tiktok.com/@username/video/ID)
        api_key: RapidAPI key
        log_callback: Hàm log (optional)

    Returns:
        str: Path to downloaded file hoặc None nếu lỗi
    """
    log = log_callback or (lambda msg: print(msg))

    try:
        # Step 1: Get direct download link
        log(f"🔗 Đang lấy link download cho video...")
        direct_link = get_video_download_link(video_url, api_key, log_callback=log)

        if not direct_link:
            log(f"❌ Không thể lấy link download")
            return None

        # Step 2: Download video from direct link
        log(f"📥 Đang tải video từ TikTok...")

        # Create downloads directory if not exists
        downloads_dir = "downloads"
        os.makedirs(downloads_dir, exist_ok=True)

        # Generate filename: tiktok_{timestamp}.mp4
        timestamp = int(time.time() * 1000)
        filename = f"tiktok_{timestamp}.mp4"
        output_path = os.path.join(downloads_dir, filename)

        # Download using curl
        cmd = [
            "curl", "-s", "-L",  # -L to follow redirects
            "-o", output_path,
            direct_link
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            log(f"❌ Lỗi khi tải video: {result.stderr}")
            return None

        # Check if file exists and has size > 0
        if not os.path.exists(output_path):
            log(f"❌ File không tồn tại sau khi tải")
            return None

        file_size = os.path.getsize(output_path)
        if file_size == 0:
            log(f"❌ File tải về có kích thước 0 bytes")
            os.remove(output_path)
            return None

        # Convert bytes to MB
        size_mb = file_size / (1024 * 1024)
        log(f"✅ Đã tải video TikTok: {filename} ({size_mb:.2f} MB)")

        return output_path

    except subprocess.TimeoutExpired:
        log(f"⏱️ Timeout khi tải video (quá 5 phút)")
        return None
    except Exception as e:
        log(f"❌ Lỗi khi tải video: {e}")
        return None
