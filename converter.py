import os, asyncio, subprocess
from pathlib import Path
from typing import Optional, Tuple
from config import config

CMDS = {
    "mp3": ["ffmpeg", "-i", "{i}", "-vn", "-acodec", "libmp3lame", "-q:a", "2", "{o}"],
    "mp4": ["ffmpeg", "-i", "{i}", "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "{o}"],
    "mov": ["ffmpeg", "-i", "{i}", "-c:v", "prores_ks", "-c:a", "pcm_s16le", "{o}"],
    "gif": ["ffmpeg", "-i", "{i}", "-vf", "fps=10,scale=480:-1", "{o}"],
    "mkv": ["ffmpeg", "-i", "{i}", "-c:v", "libx264", "-c:a", "aac", "{o}"],
    "webm_to_mp4": ["ffmpeg", "-i", "{i}", "-c:v", "libx264", "-c:a", "aac", "{o}"],
    "mp4_to_mp3": ["ffmpeg", "-i", "{i}", "-vn", "-acodec", "libmp3lame", "-q:a", "2", "{o}"],
    "mp4_to_gif": ["ffmpeg", "-i", "{i}", "-vf", "fps=10,scale=480:-1", "{o}"],
    "mov_to_mp4": ["ffmpeg", "-i", "{i}", "-c:v", "libx264", "-c:a", "aac", "{o}"],
    "mkv_to_mp4": ["ffmpeg", "-i", "{i}", "-c:v", "libx264", "-c:a", "aac", "{o}"],
}

async def convert_media(inp: str, target: str, conv_key: str = None) -> Tuple[Optional[str], Optional[str]]:
    stem = Path(inp).stem
    out = os.path.join(config.CONVERTED_DIR, f"{stem}.{target}")
    if not conv_key:
        src = Path(inp).suffix.lstrip(".").lower()
        conv_key = f"{src}_to_{target}" if src != target else target
    cmd_tpl = CMDS.get(conv_key) or CMDS.get(target)
    if not cmd_tpl:
        return None, f"No converter for {target}"
    cmd = [p.replace("{i}", inp).replace("{o}", out) for p in cmd_tpl]
    def _run():
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[:200])
        return os.path.isfile(out)
    try:
        ok = await asyncio.get_event_loop().run_in_executor(None, _run)
        return (out, None) if ok else (None, "Conversion failed")
    except Exception as e:
        return None, f"Error: {str(e)}"

async def get_file_size(fp: str) -> int:
    return os.path.getsize(fp)

def clean_up(fp: str):
    try:
        if os.path.isfile(fp):
            os.remove(fp)
    except:
        pass
