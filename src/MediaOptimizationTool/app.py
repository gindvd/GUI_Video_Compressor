from os import path
from shutil import which
from sys import platform

if platform.startswith("win"):
    from ctypes import windll

    windll.shcore.SetProcessDpiAwareness(2)

import customtkinter as ctk
from tkinter import PhotoImage

from utils.resource_paths import resource_path, setup_vlc_environment

from models.app_state import AppState
from models.media_attrs import MediaAttrs
from models.optimize_settings import OptimizeSettings
from models.media_timestamps import MediaTimestamps

from services.ffmpeg_service import FFmpegService
from services.ffprobe_service import FFprobeService
from services.vlc_playback_service import VLCService

from views.main_frame import MainFrame

from presenters.main_presenter import MainPresenter


class App(ctk.CTk):

    _FFMPEG: str = "ffmpeg"
    _FFPROBE: str = "ffprobe"
    _VLC: str = "vlc"

    def __init__(self):
        super().__init__()

        self.title("Media Optimization Tool")
        self.resizable(True, True)

        width = 1040
        height = 655

        self.geometry(f"{width}x{height}")
        self.minsize(width, height)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._ffmpeg_service = None
        self._ffprobe_service = None
        self._vlc_service = None

        if platform.startswith("win"):
            self._win_app_setup()
        elif platform.startswith("linux"):
            self._linux_app_setup()
        else:
            raise SystemExit("Incompatible Device!")

        self._app_state = AppState(
            media=MediaAttrs(),
            settings=OptimizeSettings(),
            timestamps=MediaTimestamps(),
        )

        self._main_frame = MainFrame(master=self, corner_radius=0)

        self._main_frame.pack(fill="both", expand=True)

        self._main_presenter = MainPresenter(
            app_state=self._app_state,
            view=self._main_frame,
            ffmpeg_service=self._ffmpeg_service,
            ffprobe_service=self._ffprobe_service,
            vlc_playback_service=self._vlc_service,
            on_exit_command=self.quit,
        )

        self.protocol("WM_DELETE_WINDOW", self._main_presenter.on_exit)

    def _win_app_setup(self) -> None:
        # Set dpi awareness for Windows PCs with high dpi monitors
        ffmpeg_path: str = resource_path(path.join("bin", f"{self._FFMPEG}.exe"))
        self._check_file(ffmpeg_path)
        self._ffmpeg_service = FFmpegService(path=ffmpeg_path)

        ffprobe_path: str = resource_path(path.join("bin", f"{self._FFPROBE}.exe"))
        self._check_file(ffprobe_path)
        self._ffprobe_service = FFprobeService(path=ffprobe_path)

        vlc_path: str = resource_path(path.join("bin", f"{self._VLC}", "plugins"))
        self._check_path(vlc_path)
        self._vlc_service = VLCService(path=vlc_path)

        icon_path: str = resource_path(
            path.join("assets", "images", "icons", "thestrawhat.ico")
        )

        self._check_file(icon_path)

        # Sets app icon for Windows
        self.iconbitmap(icon_path)

    def _linux_app_setup(self) -> None:

        missing = [
            x for x in (self._FFMPEG, self._FFPROBE, self._VLC) if which(x) is None
        ]

        if missing:
            raise SystemExit(f"Missing dependency: {', '.join(missing)}")

        self._ffmpeg_service = FFmpegService(path=self._FFMPEG)
        self._ffprobe_service = FFprobeService(path=self._FFPROBE)
        self._vlc_service = VLCService(path=self._VLC)

        icon_path: str = resource_path(
            path.join("assets", "images", "icons", "thestrawhat.png")
        )

        self._check_file(icon_path)

        icon = PhotoImage(file=icon_path)
        # Sets app icon for Linux
        self.iconphoto(True, icon)

    @staticmethod
    def _check_file(abs_path: str) -> None:
        if not path.isfile(abs_path):
            raise SystemExit(f"Missing dependency: {abs_path}")

    @staticmethod
    def _check_path(abs_path: str) -> None:
        if not path.exists(abs_path):
            raise SystemExit(f"Missing dependency: {abs_path}")
