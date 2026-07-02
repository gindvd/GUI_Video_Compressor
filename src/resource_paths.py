from pathlib import Path
from platform import system

import sys
import os
import shutil

def resource_path(relative_path: str = "") -> Path:
  base_path: str = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
  return Path(base_path + relative_path)

def setup_vlc_environment() -> None:
  if system() != "Windows":
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

def get_external_procs(device_os) -> list:
  if device_os == "Windows":
    return get_win_procs() 
  elif device_os == "Linux":
    return get_linux_procs()

  return [None, None, None]

def get_win_procs() -> list:
  proc_paths: list = []

  for proc in ("ffmpeg", "ffprobe", "vlc"):
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
  proc_paths: list = []

  for proc in ("ffmpeg", "ffprobe", "vlc"):
    if shutil.which(proc):
      proc_paths.append(proc)
    
    else:
      proc_paths.append(None)
  
  return proc_paths

def get_icon() -> os.PathLike | str | None:
  icon_abspath: os.PathLike = resource_path(os.path.join("assets", "images", "icons", "thestrawhat.png"))

  if not icon_abspath.is_file():
    return None
  
  return icon_abspath

def get_ico() -> os.PathLike | str | None:
  icon_abspath = resource_path(os.path.join("assets", "images", "icons", "thestrawhat.ico"))

  if not icon_abspath.is_file():
    return None
  
  return icon_abspath

def get_button_image_path(file_name: str) -> os.PathLike | str:
  image_path = resource_path(os.path.join("assets", "images", "video_control_icons", file_name))

  if not image_path.is_file():
    raise SystemExit(f"Missing image file: {file_name}")

  return image_path