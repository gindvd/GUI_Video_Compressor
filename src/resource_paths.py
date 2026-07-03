from pathlib import Path

import sys
import os
import shutil

def resource_path(relative_path: str = "") -> Path:
  """ Get absolute paths of resources """
  base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
  return base_path / relative_path

def setup_vlc_environment() -> None:
  """ Set up VLC paths for the python-vlc library to use bundled VLC dlls / plugins in the lib folder """

  vlc_dir = resource_path(os.path.join("lib", "vlc"))

  if not vlc_dir.is_dir():
    return
  
  os.environ['PYTHON_VLC_MODULE_PATH'] = str(vlc_dir)
  os.environ['PYTHON_VLC_LIB_PATH'] = str(vlc_dir / "libvlc.dll")

  # add dlls explicitly
  if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(str(vlc_dir))

  os.environ['PATH'] = str(vlc_dir) + os.pathsep + os.environ.get('PATH', '')

def get_dependencies(device_os: str) -> list[Path | str]:
  if device_os == "Windows":
    return get_win_dependencies()
  elif device_os == "Linux":
    return get_linux_dependencies()

  raise SystemExit(f"App not compatible with {device_os}")

def get_win_dependencies() -> list[Path]:
  """ Gets the paths for FFmpeg, FFprobe, and VLC in the lib folder """
  proc_paths: list[Path | None] = []

  for proc in ("ffmpeg", "ffprobe", "vlc"):
    # gets path of the vlc plugins folder
    if proc == "vlc":
      abs_path = resource_path(os.path.join("lib", "vlc", "plugins"))
      
      if not abs_path.is_dir():
          raise SystemExit(f"Missing dependency: {proc} missing from lib folder!")
      
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
        raise SystemExit(f"Missing dependency: {proc} missing from lib folder!")
  
  return proc_paths

def get_linux_dependencies() -> list[str]:
  """ get command strings for linux """
  proc_paths: list[str] = []

  for proc in ("ffmpeg", "ffprobe", "vlc"):
    if shutil.which(proc):
      proc_paths.append(proc)
    
    else:
      raise SystemExit(f"Missing dependency: {proc}")
  
  return proc_paths

def get_icon() -> Path | None:
  """ Get path of png icon file """
  icon_abspath: Path = resource_path(os.path.join("assets", "images", "icons", "thestrawhat.png"))

  if not icon_abspath.is_file():
    return None
  
  return icon_abspath

def get_ico() -> Path | None:
  """ Get path of ico file """
  icon_abspath: Path = resource_path(os.path.join("assets", "images", "icons", "thestrawhat.ico"))

  if not icon_abspath.is_file():
    return None
  
  return icon_abspath

def get_button_image_path(file_name: str) -> Path:
  """ Get paths of button icons stored in the assets/images folder """
  image_path = resource_path(os.path.join("assets", "images", "video_control_icons", file_name))

  if not image_path.is_file():
    raise SystemExit(f"Missing image file: {file_name}")

  return image_path