import os
from dataclasses import dataclass, field

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "raj169k")
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloads")
    CONVERTED_DIR: str = os.getenv("CONVERTED_DIR", "converted")
    MAX_FILE_SIZE: int = 45 * 1024 * 1024
    
    PLATFORMS: dict = field(default_factory=lambda: {
        "dailymotion": "Dailymotion",
        "vimeo": "Vimeo",
        "vk": "VK",
        "tiktok": "TikTok",
        "reddit": "Reddit",
        "threads": "Threads",
        "xiaohongshu": "Xiaohongshu",
    })
    
    CONVERSIONS: dict = field(default_factory=lambda: {
        "mp3": "MP3 Converter",
        "mp4": "MP4 Converter",
        "mp4_to_mp3": "MP4 to MP3",
        "mov": "MOV",
        "mov_to_mp4": "MOV to MP4",
        "gif": "GIF",
        "mp4_to_gif": "MP4 to GIF",
        "mkv": "MKV",
        "mkv_to_mp4": "MKV to MP4",
        "webm_to_mp4": "WEBM to MP4",
    })

    def __post_init__(self):
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN required!")
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(self.CONVERTED_DIR, exist_ok=True)

config = Config()
