from pathlib import Path
from datetime import datetime
from os import PathLike

import shutil
import platform

ROOT_DIR: PathLike = Path(__file__).parents[1]
DEVICE_OS: str = platform.system()

def get_ffmpeg_cmd() -> PathLike | None:
  if DEVICE_OS == "Windows":
    fmmpeg_rel_path = "lib/win32/ffmpeg.exe"

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

def get_ffprboe_cmd() -> PathLike | None:
  if DEVICE_OS == "Windows":
    ffprobe_rel_path = "lib/win32/ffprobe.exe"

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

def create_logs(err_msg: str):
  now = datetime.now()
  basename = str(now) + ".log"

  log_directory = ROOT_DIR / 'logs'
  log_directory.mkdir(exist_ok=True)
  log_file = log_directory / basename

  with open(log_file, 'w') as f:
    f.write(err_msg)