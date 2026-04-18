from pathlib import Path
from platform import system

import sys
import os


DEVICE_OS: str = system()

EXTERNAL_PROCS: tuple = ("ffmpeg", "ffprobe", "vlc")

def resource_path(relative_path: str = "") -> Path:
  if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
  else:
    base_path = Path(__file__).parents[1]
  return base_path / relative_path

def get_app_dir() -> Path:
  if getattr(sys, 'frozen', False):
    return Path(sys.executable).parent
  return Path(__file__).parents[1]

def setup_vlc_environment() -> None:
  if DEVICE_OS != "Windows":
    return

  vlc_dir = resource_path(os.path.join("lib", "vlc"))

  if not vlc_dir.is_dir():
    return

  os.environ['PYTHON_VLC_MODULE_PATH'] = str(vlc_dir)
  os.environ['PYTHON_VLC_LIB_PATH'] = str(vlc_dir / "libvlc.dll")

  # add dlls explicitly
  if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(str(vlc_dir))

  os.environ['PATH'] = str(vlc_dir) + os.pathsep + os.environ.get('PATH', '')

# Set up VLC environment at import time so it runs before any module imports vlc
setup_vlc_environment()

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
      abs_path = resource_path(os.path.join("lib", "vlc", "plugins"))
      try:
        if not abs_path.is_dir():
          raise FileNotFoundError
      
      except FileNotFoundError:
        proc_paths.append(None)
      
      else:
        proc_paths.append(abs_path)
    else:
      abs_path = resource_path(os.path.join("lib", f"{proc}.exe"))
    
      try:
        if not abs_path.is_file():
          raise FileNotFoundError
      
      except FileNotFoundError:
        proc_paths.append(None)

      else:
        proc_paths.append(abs_path)
  
  return proc_paths

def get_linux_procs() -> list:
  from shutil import which

  proc_paths: list = []

  for proc in EXTERNAL_PROCS:
    if which(proc):
      proc_paths.append(proc)
    
    else:
      proc_paths.append(None)
  
  return proc_paths

def create_logs(err_msg: str) -> None:
  from datetime import datetime
  
  now = datetime.now()
  basename = Path(now.strftime("%Y-%m-%d_%H-%M-%S") + ".log")

  log_directory = get_app_dir() / 'logs'
  log_directory.mkdir(exist_ok=True)
  log_file = log_directory / basename

  with open(log_file, 'w') as f:
    f.write(err_msg)

def get_icon() -> os.PathLike | str | None:
  icon_abspath = resource_path(os.path.join("assets", "icons", "icon.png"))

  if not icon_abspath.is_file():
    return None
  
  return icon_abspath

def get_ico() -> os.PathLike | str | None:
  icon_abspath = resource_path(os.path.join("assets", "icons", "icon.ico"))

  if not icon_abspath.is_file():
    return None
  
  return icon_abspath
  
