import os, asyncio, re
from pathlib import Path
from typing import Optional, Tuple
import yt_dlp
from config import config

PATTERNS = {
    "dailymotion": re.compile(r"dailymotion\.com/video/", re.I),
    "vimeo": re.compile(r"vimeo\.com/\d+", re.I),
    "vk": re.compile(r"vk\.com/video", re.I),
    "tiktok": re.compile(r"tiktok\.com|vm\.tiktok\.com", re.I),
    "reddit": re.compile(r"reddit\.com/r/", re.I),
    "threads": re.compile(r"threads\.net/", re.I),
    "xiaohongshu": re.compile(r"xhslink\.com|xiaohongshu\.com", re.I),
}

def detect_platform(url: str) -> Optional[str]:
    for name, pat in PATTERNS.items():
        if pat.search(url):
            return name
    return "unknown"

async def download_media(url: str) -> Tuple[Optional[str], Optional[str]]:
    loop = asyncio.get_event_loop()
    opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": os.path.join(config.DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    def _dl():
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                fid = info["id"]
                for ext in ("mp4", "webm", "mkv", "mov"):
                    p = os.path.join(config.DOWNLOAD_DIR, f"{fid}.{ext}")
                    if os.path.isfile(p):
                        return p
                for f in Path(config.DOWNLOAD_DIR).iterdir():
                    if f.is_file() and fid in f.name:
                        return str(f)
                return None
            except Exception as e:
                raise e
    try:
        fp = await loop.run_in_executor(None, _dl)
        return (fp, None) if fp else (None, "File not found after download.")
    except Exception as e:
        return (None, f"Download error: {str(e)[:200]}")

async def get_file_size(fp: str) -> int:
    return os.path.getsize(fp)

def clean_up(fp: str):
    try:
        if os.path.isfile(fp):
            os.remove(fp)
    except:
        pass
