import re, json, requests

API_KEY = "AIzaSyD8zroPPIHkLPxu6JjKkwroo6FbKrsfck4"
BASE = "https://www.googleapis.com/youtube/v3"
S = requests.Session()

def api(path, **params):
    params["key"] = API_KEY
    return S.get(f"{BASE}/{path}", params=params).json()

def get_channel_id(url: str) -> str:
    m = re.search(r"youtube\.com/channel/([A-Za-z0-9_-]+)", url)
    if m: return m.group(1)
    m = re.search(r"youtube\.com/@([\w-]+)", url)
    if m:
        j = api("channels", part="id", forHandle=m.group(1))
        return j["items"][0]["id"]
    raise ValueError("URL kênh không hợp lệ")

def get_uploads_playlist_id(cid: str) -> str:
    j = api("channels", part="contentDetails", id=cid)
    return j["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_all_video_ids(pid: str):
    ids, token = [], None
    while True:
        j = api("playlistItems", part="contentDetails", playlistId=pid, maxResults=50, pageToken=token)
        ids += [it["contentDetails"]["videoId"] for it in j.get("items", [])]
        token = j.get("nextPageToken")
        if not token: break
    return ids

def get_video_briefs(ids):
    out = []
    for i in range(0, len(ids), 50):
        j = api("videos", part="snippet,contentDetails", id=",".join(ids[i:i+50]))
        out += [{
            "title": it["snippet"]["title"],
            "publishedAt": it["snippet"]["publishedAt"],
            "duration": it["contentDetails"]["duration"],
            "url": f"https://www.youtube.com/watch?v={it['id']}"
        } for it in j.get("items", [])]
    return out


if __name__ == "__main__":
    url = r"https://www.youtube.com/@Wolfgang_Poker/featured"
    cid = get_channel_id(url)
    pid = get_uploads_playlist_id(cid)
    ids = get_all_video_ids(pid)
    brief = get_video_briefs(ids)
    with open("youtube_videos_compact.json", "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
