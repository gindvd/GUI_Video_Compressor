import os

from ctypes import windll

try:
    windll.user32.SetProcessDpiAwarenessContext(-4)
except AttributeError:
    windll.shcore.SetProcessDpiAwareness(2)

from app import App

from models.app_state import AppState
from models.services import Services

from services.ffmpeg_service import FFmpegService
from services.ffprobe_service import FFprobeService
from services.vlc_playback_service import VLCService

from utils.resource_paths import resource_path
from utils.file_utils import check_file, check_path


def setup_vlc_environment() -> None:
    """Set up VLC paths for the python-vlc library to use bundled VLC dlls / plugins in the bin folder"""

    vlc_dir = resource_path(os.path.join("bin", "vlc"))

    if not os.path.isdir(vlc_dir):
        raise SystemError("Missing VLC plugins folder!")

    os.environ["PYTHON_VLC_MODULE_PATH"] = str(vlc_dir)
    os.environ["PYTHON_VLC_LIB_PATH"] = str(os.path.join(vlc_dir, "libvlc.dll"))

    # add dlls explicitly
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(vlc_dir))

    os.environ["PATH"] = str(vlc_dir) + os.pathsep + os.environ.get("PATH", "")


def initialize_win(app_state: AppState) -> App:
    setup_vlc_environment()
    
    ffmpeg_path: str = resource_path(os.path.join("bin", "ffmpeg.exe"))
    check_file(ffmpeg_path)

    ffprobe_path: str = resource_path(os.path.join("bin", "ffprobe.exe"))
    check_file(ffprobe_path)

    vlc_path: str = resource_path(os.path.join("bin", "vlc", "plugins"))
    check_path(vlc_path)

    services = Services(
        ffmpeg_service=FFmpegService(ffmpeg_path=ffmpeg_path),
        ffprobe_service=FFprobeService(path=ffprobe_path),
        vlc_service=VLCService(path=vlc_path)
    )

    app: App = App(app_state=app_state, services=services)

    icon_path: str = resource_path(
        os.path.join("assets", "images", "icons", "thestrawhat.ico")
    )

    app.iconbitmap(icon_path)

    return app
