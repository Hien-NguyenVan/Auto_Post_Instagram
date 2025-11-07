import re
import json
import requests

# 🔑 Thay YOUR_API_KEY bằng khóa thật của bạn từ Google Cloud Console
API_KEY = "AIzaSyD8zroPPIHkLPxu6JjKkwroo6FbKrsfck4"
BASE_URL = "https://www.googleapis.com/youtube/v3"


def extract_channel_id(channel_url):
    """
    Lấy channel ID từ link kênh YouTube (dạng @handle hoặc /channel/ID)
    """
    # Nếu là dạng /channel/UCxxxx
    match = re.search(r"youtube\.com/channel/([a-zA-Z0-9_-]+)", channel_url)
    if match:
        return match.group(1)

    # Nếu là dạng @handle
    match = re.search(r"youtube\.com/@([a-zA-Z0-9_-]+)", channel_url)
    if match:
        handle = match.group(1)
        resp = requests.get(
            f"{BASE_URL}/channels",
            params={"forHandle": handle, "part": "id", "key": API_KEY},
        )
        data = resp.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["id"]

    raise ValueError("Không thể lấy được Channel ID từ URL này.")


def get_upload_playlist_id(channel_id):
    """Lấy ID playlist 'uploads' của kênh"""
    resp = requests.get(
        f"{BASE_URL}/channels",
        params={"part": "contentDetails", "id": channel_id, "key": API_KEY},
    )
    data = resp.json()
    return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_all_videos_from_playlist(playlist_id):
    """Lấy toàn bộ video (bao gồm shorts) từ playlist uploads"""
    videos = []
    next_page_token = None

    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "pageToken": next_page_token,
            "key": API_KEY,
        }
        resp = requests.get(f"{BASE_URL}/playlistItems", params=params)
        data = resp.json()

        for item in data.get("items", []):
            videos.append({
                "video_id": item["contentDetails"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "publishedAt": item["snippet"]["publishedAt"],
            })

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def enrich_video_details(videos):
    """Lấy thêm thông tin chi tiết cho từng video"""
    detailed_videos = []
    for i in range(0, len(videos), 50):
        chunk = videos[i:i + 50]
        ids = ",".join(v["video_id"] for v in chunk)
        resp = requests.get(
            f"{BASE_URL}/videos",
            params={"part": "snippet,statistics,contentDetails", "id": ids, "key": API_KEY},
        )
        data = resp.json()

        for item in data.get("items", []):
            detailed_videos.append({
                "video_id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "publishedAt": item["snippet"]["publishedAt"],
                "duration": item["contentDetails"]["duration"],
                "viewCount": item["statistics"].get("viewCount"),
                "likeCount": item["statistics"].get("likeCount"),
                "commentCount": item["statistics"].get("commentCount"),
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })
    return detailed_videos


def main():
    channel_url = "https://www.youtube.com/@ductrainghiem/featured"
    print("🔍 Đang lấy Channel ID...")
    channel_id = extract_channel_id(channel_url)

    print("📂 Đang lấy playlist uploads...")
    playlist_id = get_upload_playlist_id(channel_id)

    print("📺 Đang tải danh sách video...")
    videos = get_all_videos_from_playlist(playlist_id)

    print(f"✅ Đã lấy {len(videos)} video. Đang tải chi tiết...")
    detailed_videos = enrich_video_details(videos)

    # Lưu kết quả
    with open("youtube_videos.json", "w", encoding="utf-8") as f:
        json.dump(detailed_videos, f, ensure_ascii=False, indent=2)

    print("🎉 Hoàn tất! Kết quả lưu trong file youtube_videos.json")


if __name__ == "__main__":
    main()
