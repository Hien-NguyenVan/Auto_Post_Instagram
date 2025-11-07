import os, sys, uuid, subprocess, shlex

if len(sys.argv) < 2:
    print("❌ Thiếu ID hoặc URL video")
    sys.exit(1)

video_id = sys.argv[1].strip()
if video_id.startswith("http"):
    url = video_id
else:
    url = f"https://www.youtube.com/watch?v={video_id}"  # dùng dạng watch cho Shorts

output_dir = "/data/storage"
os.makedirs(output_dir, exist_ok=True)
temp_id = uuid.uuid4().hex[:8]
output_path = os.path.join(output_dir, f"{temp_id}.mp4")

# ▶️ Cấu hình yt-dlp (đa client fallback)
cmd = [
    "yt-dlp",
    "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "--merge-output-format", "mp4",
    "-o", output_path,
    "--no-warnings", "--quiet",
    "--extractor-args", "youtube:player_client=android,web_embedded,web_music,web",
    url,
]

print("▶️ Command:", " ".join(shlex.quote(c) for c in cmd))
res = subprocess.run(cmd, capture_output=True, text=True)

if res.returncode != 0:
    print(f"❌ Lỗi tải:\n{res.stderr.strip()}")
    sys.exit(1)

print(os.path.abspath(output_path))
