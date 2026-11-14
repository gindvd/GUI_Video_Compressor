from os import path
from shutil import which

import customtkinter as ctk

from models.app_state import AppState
from models.services import Services

from views.main_frame import MainFrame

from presenters.main_presenter import MainPresenter


class App(ctk.CTk):

    def __init__(self, app_state: AppState, services: Services):
        super().__init__()

        self.title("Media Optimization Tool")
        self.resizable(True, True)
        self.minsize(840, 500)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._main_frame = MainFrame(
            master=self, 
            corner_radius=0
        )
        self._main_frame.pack(
            fill="both", 
            expand=True
        )

        self._main_presenter = MainPresenter(
            app_state=app_state,
            view=self._main_frame,
            ffmpeg_service=services.ffmpeg_service,
            ffprobe_service=services.ffprobe_service,
            vlc_playback_service=services.vlc_service,
            on_exit_command=self.quit,
        )

        self.update()
        self.geometry(self.geometry())

        self.protocol("WM_DELETE_WINDOW", self._main_presenter.on_exit)
