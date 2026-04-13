from pathlib import Path
from datetime import datetime
from os import PathLike

import shutil
import platform

ROOT_DIR: PathLike = Path(__file__).parents[1]
DEVICE_OS: str = platform.system()

EXTERNAL_PROCS: tuple = ("ffmpeg", "ffprobe", "vlc")

def get_external_procs() -> list:
  if DEVICE_OS == "Windows":
    return get_win_procs() 
  elif DEVICE_OS == "Linux":
    return get_linux_procs()

  return [None, None, None]

def get_win_procs() -> list:
  proc_paths: list = []

  for proc in EXTERNAL_PROCS:
    if proc == "vlc":
      abs_path = ROOT_DIR / Path(f"lib/win32/plugins")
      try:
        if not abs_path.is_dir():
          raise FileNotFoundError
      
      except FileNotFoundError:
        proc_paths.append(None)
      
      else:
        proc_paths.append(abs_path)
    else:
      abs_path = ROOT_DIR / Path(f"lib/win32/{proc}.exe")
    
      try:
        if not abs_path.is_file():
          raise FileNotFoundError
      
      except FileNotFoundError:
        proc_paths.append(None)

      else:
        proc_paths.append(abs_path)
  
  return proc_paths

def get_linux_procs() -> list:
  proc_paths: list = []

  for proc in EXTERNAL_PROCS:
    if shutil.which(proc):
      proc_paths.append(proc)
    
    else:
      proc_paths.append(None)
  
  return proc_paths

def create_logs(err_msg: str) -> None:
  now = datetime.now()
  basename = Path(now.strftime("%Y-%m-%d_%H-%M-%S") + ".log")

  log_directory = ROOT_DIR / Path('logs')
  log_directory.mkdir(exist_ok=True)
  log_file = log_directory / basename

  with open(log_file, 'w') as f:
    f.write(err_msg)

def get_icon() -> PathLike | str | None:
  icon_abspath = ROOT_DIR / Path("assets/icons/icon.png")

  if not icon_abspath.is_file():
    return None
  
  return icon_abspath
  