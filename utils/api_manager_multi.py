"""
Multi-Platform API Manager
Quản lý API keys cho YouTube và TikTok
"""
import os
import json


class MultiAPIManager:
    """
    Quản lý API keys cho nhiều platform (YouTube, TikTok)

    File structure:
    data/api/apis.json
    {
        "youtube": ["key1", "key2", ...],
        "tiktok": ["key1", "key2", ...]
    }
    """

    def __init__(self, api_file_path):
        self.api_file = api_file_path
        self.ensure_file()
        self.data = self.load_all()
        self.youtube_index = 0
        self.tiktok_index = 0

    def ensure_file(self):
        """Tạo file API nếu chưa tồn tại"""
        os.makedirs(os.path.dirname(self.api_file), exist_ok=True)
        if not os.path.exists(self.api_file):
            default_data = {
                "youtube": [],
                "tiktok": []
            }
            with open(self.api_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

    def load_all(self):
        """Load tất cả API keys"""
        try:
            with open(self.api_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"youtube": [], "tiktok": []}

    def save_all(self, data):
        """Lưu tất cả API keys"""
        with open(self.api_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.data = data

    def get_keys(self, platform):
        """Lấy danh sách keys của 1 platform"""
        return self.data.get(platform, [])

    def set_keys(self, platform, keys):
        """Set danh sách keys cho 1 platform"""
        self.data[platform] = keys
        self.save_all(self.data)

    def add_key(self, platform, key):
        """Thêm 1 key mới"""
        if platform not in self.data:
            self.data[platform] = []
        if key not in self.data[platform]:
            self.data[platform].append(key)
            self.save_all(self.data)
            return True
        return False

    def remove_key(self, platform, index):
        """Xóa key theo index"""
        if platform in self.data and 0 <= index < len(self.data[platform]):
            self.data[platform].pop(index)
            self.save_all(self.data)
            return True
        return False

    def get_next_youtube_key(self):
        """Lấy key YouTube tiếp theo (round-robin)"""
        keys = self.get_keys("youtube")
        if not keys:
            return None

        key = keys[self.youtube_index]
        self.youtube_index = (self.youtube_index + 1) % len(keys)
        return key

    def get_next_tiktok_key(self):
        """Lấy key TikTok tiếp theo (round-robin)"""
        keys = self.get_keys("tiktok")
        if not keys:
            return None

        key = keys[self.tiktok_index]
        self.tiktok_index = (self.tiktok_index + 1) % len(keys)
        return key

    def refresh(self):
        """Reload từ file"""
        self.data = self.load_all()


# Singleton instance
API_FILE_PATH = os.path.join(os.getcwd(), "data", "api", "apis.json")
multi_api_manager = MultiAPIManager(API_FILE_PATH)
