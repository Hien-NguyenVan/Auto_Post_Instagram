import os, sys, uuid, subprocess
from yt_dlp import YoutubeDL

# --- Kiểm tra đầu vào ---
if len(sys.argv) < 2:
    print("❌ Thiếu ID video")
    sys.exit(1)

video_id = sys.argv[1].strip()

# Tự động nhận biết dạng video (Shorts hay video thường)
if "http" in video_id:
    url = video_id
elif len(video_id) == 11:  # ID YouTube thường dài 11 ký tự
    url = f"https://www.youtube.com/watch?v={video_id}"
else:
    url = f"https://www.youtube.com/shorts/{video_id}"

# --- Tạo thư mục lưu ---
output_dir = "/data/storage"
os.makedirs(output_dir, exist_ok=True)
temp_id = uuid.uuid4().hex[:8]
output_template = os.path.join(output_dir, f"{temp_id}.%(ext)s")

# --- Cấu hình yt_dlp ---
ydl_opts = {
    "outtmpl": output_template,
    # 🔥 Ưu tiên video <=1080p (có thể WebM, sẽ merge sang MP4)
    "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "merge_output_format": "mp4",

    # chạy im lặng, không log
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,

    # retry khi lỗi mạng
    "retries": 3,
    "fragment_retries": 3,

    # Giả lập desktop Chrome để tránh giới hạn chất lượng
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    },
}

try:
    # --- Tải video ---
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = info["requested_downloads"][0]["filepath"]

    video_path = os.path.abspath(video_path)

    # --- Kiểm tra codec video ---
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ],
        capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    codec = (probe.stdout or "").strip().lower()

    # --- Nếu không phải H.264 thì convert ---
    if codec not in ("h264", "avc1"):
        converted = os.path.join(output_dir, f"converted_{temp_id}.mp4")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                converted,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.remove(video_path)
        video_path = converted

    # ✅ In đường dẫn tuyệt đối để n8n đọc được
    print(os.path.abspath(video_path))

except Exception as e:
    print(f"❌ Lỗi: {e}")
    sys.exit(1)
