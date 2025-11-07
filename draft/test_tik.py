import subprocess
import os
import json
import unicodedata
import re
import uuid

DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def remove_accents(s):
    nfkd_form = unicodedata.normalize('NFKD', s)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')
    only_ascii = re.sub(r'[^\w\s.-]', '_', only_ascii)
    only_ascii = re.sub(r'\s+', '_', only_ascii)
    return only_ascii

def download_video(url):
    request_id = str(uuid.uuid4())
    output_dir = os.path.join(DOWNLOAD_DIR, request_id)
    os.makedirs(output_dir, exist_ok=True)

    print(f"📥 Lấy thông tin video: {url}")
    info_cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
    info = subprocess.run(info_cmd, capture_output=True, text=True)
    if info.returncode != 0:
        print("❌ Lỗi lấy thông tin:", info.stderr)
        return

    data = json.loads(info.stdout)
    title = remove_accents(data.get("title", "video"))[:100]
    vid = data.get("id", "")
    filename = f"{title}_{vid}.%(ext)s"
    full_path = os.path.join(output_dir, filename)

    print("▶️ Bắt đầu tải...")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "-o", full_path,
        "--merge-output-format", "mp4",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Tải thành công!\nLưu tại: {output_dir}")
    else:
        print("❌ Lỗi tải:", result.stderr)

if __name__ == "__main__":
    link = input("Nhập link video cần tải: ").strip()
    download_video(link)
