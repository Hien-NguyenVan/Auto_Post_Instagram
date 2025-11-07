# get_tiktok_videos.py
from datetime import datetime, timezone
import yt_dlp


def is_real_tiktok_video(entry):
    """Kiểm tra xem entry TikTok có phải video thật (không phải slideshow ảnh)."""
    if not entry:
        return False

    # Nếu có danh sách định dạng, kiểm tra có format nào có video codec
    formats = entry.get("formats") or []
    for f in formats:
        vcodec = f.get("vcodec")
        if vcodec and vcodec.lower() != "none":
            return True

    # Hoặc nếu entry có vcodec riêng
    if entry.get("vcodec") and entry["vcodec"].lower() != "none":
        return True

    # Không có video stream → slideshow
    return False


def fetch_tiktok_videos(url, max_videos=30):
    """Lấy danh sách video TikTok từ tài khoản (profile hoặc link playlist)."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,     # Lấy chi tiết từng video
        'playlistend': max_videos, # Giới hạn số video tối đa
        'skip_download': True,     # Không tải video
    }

    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get('entries') or [info]  # Có thể là 1 video hoặc list

        for e in entries:
            if not e:
                continue
            if not is_real_tiktok_video(e):  # Bỏ qua slideshow ảnh
                continue

            ts = e.get('timestamp', 0)
            published_at = (
                datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if ts else None
            )

            videos.append({
                'title': e.get('title', ''),
                'publishedAt': published_at,
                'url': e.get('webpage_url', ''),
                'status': 'unpost'
            })

    return videos


if __name__ == "__main__":
    print("=== TikTok Video Fetcher ===")
    channel_url = input("Nhập link kênh TikTok: ").strip()
    print("\nĐang lấy dữ liệu...\n")

    try:
        videos = fetch_tiktok_videos(channel_url)
        if not videos:
            print("⚠️ Không tìm thấy video nào hoặc link không hợp lệ.")
        else:
            print(f"✅ Đã tìm thấy {len(videos)} video:\n")
            for i, v in enumerate(videos, 1):
                print(f"{i}. {v['title']}")
                print(f"   Ngày đăng: {v['publishedAt']}")
                print(f"   Link: {v['url']}\n")
    except Exception as e:
        print("❌ Lỗi:", e)
