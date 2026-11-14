from os import path
from shutil import which
from tkinter import PhotoImage

from app import App

from models.app_state import AppState
from models.services import Services

from services.ffmpeg_service import FFmpegService
from services.ffprobe_service import FFprobeService
from services.vlc_playback_service import VLCService

from utils.resource_paths import resource_path
from utils.file_utils import check_file


def initialize_linux(app_state: AppState) -> App:
    
    missing = [
        x for x in ("ffmpeg", "ffprobe", "vlc") if which(x) is None
    ]

    if missing:
        raise SystemExit(f"Missing dependency: {', '.join(missing)}")

    services = Services(
        ffmpeg_service=FFmpegService(ffmpeg_path="ffmpeg"),
        ffprobe_service=FFprobeService(path="ffprobe"),
        vlc_service=VLCService(path="vlc")
    )

    app: App = App(app_state=app_state, services=services)

    icon_path: str = resource_path(
        path.join("assets", "images", "icons", "thestrawhat.png")
    )
    check_file(icon_path)

    app.iconphoto(True, PhotoImage(file=icon_path))

    return app