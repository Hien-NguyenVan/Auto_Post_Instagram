import os
import re
import uuid
import subprocess
from yt_dlp import YoutubeDL


class YouTubeDownloader:
    """
    Trình tải video YouTube bằng yt-dlp (bản tối ưu FullHD + bypass SABR).
    - Ưu tiên client Android để tránh lỗi 403
    - Cho phép fallback sang Web client để lấy stream 1080p (DASH)
    - Tự động merge audio + video và chuyển mã sang H.264 nếu cần
    """

    def __init__(self, output_dir="temp", log_callback=None):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.log_callback = log_callback or (lambda msg: print(msg))

    def log(self, msg):
        try:
            self.log_callback(msg)
        except Exception:
            print(msg)

    def download_video(self, url):
        try:
            temp_id = uuid.uuid4().hex[:8]
            output_template = os.path.join(self.output_dir, f"{temp_id}.%(ext)s")
            self.log(f"📥 Đang tải video từ: {url}")

            # ====== Cấu hình yt-dlp cho YouTube ======
            ydl_opts = {
                "outtmpl": output_template,
                "format": (
                "bestvideo[vcodec^=avc1][height<=1080]+bestaudio[ext=m4a]/"  # Ưu tiên H.264
                "bestvideo[height<=1080]+bestaudio[ext=m4a]/"                # Fallback mọi codec
                "best[height<=1080]"),
                "merge_output_format": "mp4",
                "quiet": True,
                "no_warnings": True,
                "retries": 3,
                "fragment_retries": 3,
                "http_headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Linux; Android 10; SM-G960F) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Mobile Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                },
                "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
            }

            # ====== Bắt đầu tải ======
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = info["requested_downloads"][0]["filepath"]
                title = info.get("title", "unknown")

            video_path = os.path.abspath(video_path)
            if not os.path.exists(video_path):
                self.log("❌ Không tìm thấy file sau khi tải.")
                for f in os.listdir(self.output_dir):
                    self.log("  - " + f)
                return None

            self.log(f"✅ Đã tải xong video: {title}")
            self.log(f"📁 File: {video_path}")

            # ====== Kiểm tra codec ======
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=codec_name",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path
                ],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            codec = (probe.stdout or "").strip().lower()
            self.log(f"🎞️ Codec hiện tại: {codec or 'unknown'}")

            # ====== Nếu không phải H.264 thì chuyển mã ======
            if codec not in ("h264", "avc1"):
                converted_path = os.path.join(self.output_dir, f"converted_{temp_id}.mp4")
                self.log(f"⚙️ Đang chuyển mã {codec or 'unknown'} → H.264 ...")

                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", video_path,
                        "-c:v", "libx264", "-preset", "fast",
                        "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart",
                        converted_path,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                try:
                    os.remove(video_path)
                except Exception:
                    pass

                video_path = converted_path
                self.log("✅ Đã chuyển mã sang H.264 thành công.")

            self.log(f"🏁 Hoàn tất: {video_path}")
            return video_path

        except Exception as e:
            self.log(f"❌ Lỗi tải video: {e}")
            return None


# ==========================================================
# 🟣 HÀM TẢI VIDEO TIKTOK RIÊNG BIỆT
# ==========================================================
def download_tiktok_video(url, output_dir="temp", log_callback=None):
    """
    Tải video TikTok (có cả hình + tiếng, merge như YouTube).
    """
    log = log_callback or (lambda msg: print(msg))
    os.makedirs(output_dir, exist_ok=True)

    import uuid
    temp_id = uuid.uuid4().hex[:8]
    output_template = os.path.join(output_dir, f"tiktok_{temp_id}.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": (
                "bestvideo[vcodec^=avc1][height<=1080]+bestaudio[ext=m4a]/"  # Ưu tiên H.264
                "bestvideo[height<=1080]+bestaudio[ext=m4a]/"                # Fallback mọi codec
                "best[height<=1080]"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 10; SM-G960F) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Mobile Safari/537.36"
            )
        },
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

    try:
        log(f"📥 [TikTok] Đang tải video từ: {url}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = info["requested_downloads"][0]["filepath"]

        video_path = os.path.abspath(video_path)
        if not os.path.exists(video_path):
            raise FileNotFoundError("File không tồn tại sau khi tải.")

        # ====== Kiểm tra codec ======
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        codec = (probe.stdout or "").strip().lower()
        log(f"🎞️ [TikTok] Codec hiện tại: {codec or 'unknown'}")

        # ====== Nếu không phải H.264 thì convert ======
        if codec not in ("h264", "avc1"):
            converted = os.path.join(output_dir, f"converted_tiktok_{temp_id}.mp4")
            log(f"⚙️ [TikTok] Đang chuyển mã {codec or 'unknown'} → H.264 ...")

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
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            os.remove(video_path)
            video_path = converted
            log("✅ [TikTok] Đã chuyển mã sang H.264 thành công.")

        log(f"🏁 [TikTok] Hoàn tất: {video_path}")
        return video_path

    except Exception as e:
        log(f"❌ [TikTok] Lỗi tải video: {e}")
        return None


def download_tiktok_direct_url(url, output_dir="temp", log_callback=None):
    """
    Download TikTok video từ direct URL (url_list[1] từ DumplingAI API)
    Sử dụng curl thay vì yt-dlp
    """
    log = log_callback or (lambda msg: print(msg))

    os.makedirs(output_dir, exist_ok=True)

    import uuid
    temp_id = uuid.uuid4().hex[:8]
    output_path = os.path.join(output_dir, f"tiktok_{temp_id}.mp4")

    try:
        log(f"📥 [TikTok Direct] Đang tải video từ URL trực tiếp...")

        # Dùng curl để download
        cmd = [
            "curl", "-s", "-L",
            url,
            "-o", output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=120
        )

        if result.returncode != 0:
            log(f"❌ [TikTok Direct] Lỗi curl: {result.stderr}")
            return None

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            log(f"❌ [TikTok Direct] File tải về rỗng hoặc không tồn tại")
            return None

        # ====== Kiểm tra codec ======
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                output_path
            ],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        codec = (probe.stdout or "").strip().lower()
        log(f"🎞️ [TikTok Direct] Codec hiện tại: {codec or 'unknown'}")

        # ====== Nếu không phải H.264 thì convert ======
        if codec not in ("h264", "avc1"):
            converted = os.path.join(output_dir, f"converted_tiktok_{temp_id}.mp4")
            log(f"⚙️ [TikTok Direct] Đang chuyển mã {codec or 'unknown'} → H.264 ...")

            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", output_path,
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    converted,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            os.remove(output_path)
            output_path = converted
            log("✅ [TikTok Direct] Đã chuyển mã sang H.264 thành công.")

        log(f"🏁 [TikTok Direct] Hoàn tất: {output_path}")
        return os.path.abspath(output_path)

    except subprocess.TimeoutExpired:
        log(f"⏱️ [TikTok Direct] Timeout khi tải video")
        return None
    except Exception as e:
        log(f"❌ [TikTok Direct] Lỗi tải video: {e}")
        return None


# ==========================================================
# 🟢 API CHÍNH DÙNG CHUNG CHO CẢ YOUTUBE & TIKTOK
# ==========================================================
def download_video_api(url, output_dir="temp", log_callback=None):
    """
    API: tải video YouTube hoặc TikTok tùy theo URL.
    Trả về đường dẫn file mp4 tuyệt đối hoặc None nếu lỗi.
    """
    try:
        # 🧠 Phân loại nền tảng
        if "tiktok.com" in url.lower():
            return download_tiktok_video(url, output_dir, log_callback)

        # Mặc định là YouTube
        downloader = YouTubeDownloader(output_dir=output_dir, log_callback=log_callback)
        path = downloader.download_video(url)
        return os.path.abspath(path) if path and os.path.exists(path) else None

    except Exception as e:
        if log_callback:
            log_callback(f"❌ Lỗi API tải video: {e}")
        else:
            print(f"❌ Lỗi API tải video: {e}")
        return None


# === Demo test ===
if __name__ == "__main__":
    # test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_url = "https://www.tiktok.com/@t.theo03/video/7569061713396501781"
    result = download_video_api(test_url)
    print("Kết quả:", result)
