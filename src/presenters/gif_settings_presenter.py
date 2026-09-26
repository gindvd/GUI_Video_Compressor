from os import path
from collections.abc import Callable

from models.gif_settings import GifSettings

from views.gif_settings_frame import GifSettingsFrame

from controllers.ffmpeg_controller import FFmpegController


class GifSettingsPresenter():
    def __init__(
        self, 
        gif_settings: GifSettings, 
        gif_view: GifSettingsFrame,
        ffmpeg_controller: FFmpegController,
        disable_ui_command: Callable[[], None],
        restore_ui_command: Callable[[], None]
    ) -> None: 

        self._gif_settings: GifSettings = gif_settings
        self._gif_view: GifSettingsFrame = gif_view

        self._ffmpeg_controller: FFmpegController = ffmpeg_controller

        self._disable_ui : Callable[[], None] = disable_ui_command
        self._restore_ui : Callable[[], None] = restore_ui_command

        self._bind_view()
    
    def on_resolution_change(self, value: str) -> None:
        self._gif_settings.resolution = value
    
    def on_frame_rate_change(self, value: str) -> None:
        self._gif_settings.fps = value
    
    def on_loop_change(self, value: str) -> None:
        if value == "Infinite":
            loop_num = 0
        elif value == "1x":
            loop_num = -1
        elif value == "2x":
            loop_num = 1
        elif value == "5x":
            loop_num = 4
        elif value == "10x":
            loop_num = 9
        else:
            return

        self._gif_settings.loops = loop_num
    
    def on_create(self) -> None:
        self._disable_ui()

        if not self._get_output_directory():
            self._restore_ui()
            return
        
        self._ffmpeg_controller.create_gif()

        self._restore_ui()

    def _get_output_directory(self) -> bool:
        from tkinter import filedialog

        output_directory: str = filedialog.askdirectory(
            parent=self._gif_view,
            title="GIF Output Selection",
            initialdir=path.expanduser("~"),
        )

        if output_directory == "":
            return False

        self._ffmpeg_controller.create_gif_output_file(output_directory)

        return True
    
    def _bind_view(self) -> None:
        self._gif_view.on_resolution_change = self.on_resolution_change
        self._gif_view.on_frame_rate_change = self.on_frame_rate_change
        self._gif_view.on_loop_change = self.on_loop_change

        self._gif_view.on_create = self.on_create