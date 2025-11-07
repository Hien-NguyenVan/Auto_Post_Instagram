import os, sys, uuid, subprocess, json

if len(sys.argv) < 2:
    print("? Thi?u ID video")
    sys.exit(1)

video_id = sys.argv[1].strip()
url = f"https://www.youtube.com/shorts/{video_id}"

output_dir = "/data/storage"
os.makedirs(output_dir, exist_ok=True)
temp_id = uuid.uuid4().hex[:8]
output_path = os.path.join(output_dir, f"{temp_id}.mp4")

# ?? G?i yt-dlp CLI (nhu test_tik.py)
cmd = [
    "yt-dlp",
    "-f", "bestvideo+bestaudio/best",
    "--merge-output-format", "mp4",
    "-o", output_path,
    url
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    print(f"? L?i t?i: {result.stderr.strip()}")
    sys.exit(1)

# ? In duy nh?t du?ng d?n d? n8n d?c
print(os.path.abspath(output_path))
