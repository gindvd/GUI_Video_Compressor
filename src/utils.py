from pathlib import Path
from datetime import datetime
from os import PathLike

import shutil
import platform

ROOT_DIR: PathLike = Path(__file__).parents[1]
DEVICE_OS: str = platform.system()

def get_ffmpeg_cmd() -> PathLike | str | None:
  if DEVICE_OS == "Windows":
    ffmpeg_rel_path = Path("lib/win32/ffmpeg.exe")

    try:
      ffmpeg_abs_path = ROOT_DIR / ffmpeg_rel_path
    
    except FileNotFoundError:
      return None

    else:
      return ffmpeg_abs_path
  
  elif DEVICE_OS == "Linux":
    if not shutil.which("ffmpeg"):
      return None
    
    return "ffmpeg"
  
  return None

def get_ffprboe_cmd() -> PathLike | str | None:
  if DEVICE_OS == "Windows":
    ffprobe_rel_path = Path("lib/win32/ffprobe.exe")

    try:
      ffprobe_abs_path = ROOT_DIR / ffprobe_rel_path
    
    except FileNotFoundError:
      return None

    else:
      return ffprobe_abs_path
  
  elif DEVICE_OS == "Linux":
    if not shutil.which("ffprobe"):
      return None
    
    return "ffprobe"

  return None

def get_vlc_cmd() -> PathLike | str | None:
    if DEVICE_OS == "Windows":
      try:
        vlc_path = ROOT_DIR / Path("lib/win32/vlc-win32.exe")

      except FileNotFoundError:
        return None
    
      else:
        return vlc_path
    
    elif DEVICE_OS == "Linux":
      if not shutil.which("vlc"):
        return None

      return "vlc"
    
    return None

def create_logs(err_msg: str) -> None:
  now = datetime.now()
  basename = Path(str(now) + ".log")

  log_directory = ROOT_DIR / Path('logs')
  log_directory.mkdir(exist_ok=True)
  log_file = log_directory / basename

  with open(log_file, 'w') as f:
    f.write(err_msg)