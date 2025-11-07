# utils/tiktok_api.py
from datetime import datetime, timezone
import yt_dlp


def fetch_tiktok_videos(url, max_videos=30):
    """Lấy danh sách video TikTok từ tài khoản"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'playlistend': max_videos,
        'skip_download': True,
    }

    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        entries = info.get('entries') or [info]

        for e in entries:
            if not e:
                continue
            
            # ✅ Bỏ qua slideshow (ảnh + nhạc)
            if not is_real_tiktok_video(e):
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

def is_real_tiktok_video(entry):
    """Kiểm tra xem entry TikTok có phải video thật (không phải slideshow ảnh)."""
    # Một số trường hợp có vcodec nằm trong entry["formats"]
    if not entry:
        return False

    # Nếu có list format, kiểm tra có format nào có vcodec != none
    formats = entry.get("formats") or []
    for f in formats:
        vcodec = f.get("vcodec")
        if vcodec and vcodec.lower() != "none":
            return True

    # Nếu không có formats, nhưng có vcodec riêng
    if entry.get("vcodec") and entry["vcodec"].lower() != "none":
        return True

    # Nếu không có video stream (vcodec=none) → slideshow ảnh
    return False

def fetch_tiktok_videos_newer_than(url, cutoff_dt):
    """Chỉ lấy video mới hơn cutoff_dt"""
    all_videos = fetch_tiktok_videos(url)
    return [
        v for v in all_videos
        if v['publishedAt']
        and datetime.strptime(v['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > cutoff_dt
    ]
