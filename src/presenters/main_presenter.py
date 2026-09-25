from os import path
from typing import Any
from collections.abc import Callable

from models.app_state import AppState

from presenters.settings_presenter import SettingsPresenter
from presenters.gif_settings_presenter import GifSettingsPresenter
from presenters.media_player_presenter import MediaPlayerPresenter
from presenters.frame_viewer_presenter import FrameViewerPresenter

from controllers.ffmpeg_controller import FFmpegController
from controllers.extraction_controller import ExtractionController

from views import dialogs
from views.main_frame import MainFrame
from views.frame_viewer import FrameViewer

from services.ffmpeg_service import FFmpegService
from services.ffprobe_service import FFprobeService
from services.vlc_playback_service import VLCService

from utils.resolution_utils import get_list_of_smaller_resolutions


class MainPresenter:

    def __init__(
        self,
        app_state: AppState,
        view: MainFrame,
        ffmpeg_service: FFmpegService,
        ffprobe_service: FFprobeService,
        vlc_playback_service: VLCService,
        on_exit_command: Callable[[], None],
    ) -> None:
        self._app_state: AppState = app_state
        self._view: MainFrame = view

        self._ffmpeg_service: FFmpegService = ffmpeg_service
        self._ffprobe_service: FFprobeService = ffprobe_service
        self._vlc_service: VLCService = vlc_playback_service

        self.ffmpeg_controller: FFmpegController = FFmpegController(
            parent_view=self._view,
            ffmpeg_service=self._ffmpeg_service,
            app_state=self._app_state,
            on_restore_ui=lambda: self._view.after(0, self.restore_ui),
        )

        self._extraction_controller: ExtractionController = ExtractionController(
            media_attrs=self._app_state.media,
            timestamps=self._app_state.timestamps,
            ffprobe_service=self._ffprobe_service,
            parent_view=self._view,
            after_extraction_command=lambda: self._view.after(
                0, self.update_settings_and_load_media
            ),
        )

        self._settings_presenter: SettingsPresenter = SettingsPresenter(
            optimize_settings=self._app_state.settings,
            settings_view=self._view.settings_frame,
            ffmpeg_controller=self.ffmpeg_controller,
            disable_ui_command=self.disable_ui,
            restore_ui_command=self.restore_ui
        )

        self._gif_presenter: GifSettingsPresenter = GifSettingsPresenter(
            gif_settings=self._app_state.gif_settings,
            gif_view=self._view.gif_frame,
            ffmpeg_controller=self.ffmpeg_controller,
            disable_ui_command=self.disable_ui,
            restore_ui_command=self.restore_ui
        )

        self._media_player_presenter: MediaPlayerPresenter = MediaPlayerPresenter(
            media_attrs=self._app_state.media,
            timestamps=self._app_state.timestamps,
            media_player_view=self._view.media_player_frame,
            vlc_service=self._vlc_service,
        )

        self._frame_viewer: FrameViewer | None = None
        self._frame_viewer_presenter: FrameViewerPresenter | None = None

        self._on_exit_command: Callable[[], None] = on_exit_command

        self._bind_view()

    def on_open_file(self) -> None:
        item = self._browse_files()
        self._handle_files(item)

    def on_file_entry_submit(self, item) -> None:
        self._handle_files(item)

    def on_show_about(self) -> None:
        dialogs.show_about(master=self._view)

    def on_show_license(self) -> None:
        dialogs.show_license(master=self._view)

    def on_show_third_party_licenses(self) -> None:
        dialogs.show_third_party_licenses(master=self._view)

    def open_frame_viewer(self) -> None:
        """Open new window with Frame Viewer for individual frame view and extraction"""

        if (
            self._app_state.media.input_file == ""
            or self._app_state.media.input_file is None
        ):
            dialogs.show_warning(
                master=self._view,
                title="Missing File",
                message="Video file not loaded!",
            )
            return

        if self._frame_viewer is not None and self._frame_viewer.winfo_exists():
            self._frame_viewer.focus()
            return

        self._frame_viewer = FrameViewer(self._view)

        self._frame_viewer_presenter = FrameViewerPresenter(
            frame_viewer=self._frame_viewer,
            ffmpeg_service=self._ffmpeg_service,
            media_attrs=self._app_state.media,
        )

        self._frame_viewer_presenter.load_media()

    def on_exit(self) -> None:
        """Closes all background processes before destroying the app"""
        self.ffmpeg_controller.shutdown()
        self._vlc_service.shutdown()

        self._view.after(1, self._on_exit_command)

    def update_settings_and_load_media(self) -> None:
        self._calculate_base_fps()
        self._update_resolution_dropdown_values()
        self._update_audio_settings()
        self._load_media()

        self.restore_ui()
    
    def disable_ui(self) -> None:
        self._view.settings_frame.compress_btn_state = "disabled"
        self._view.gif_frame.create_button_state = "disabled"
        self._view.browse_btn_state = "disabled"

    def restore_ui(self) -> None:
        self._view.settings_frame.compress_btn_state = "normal"
        self._view.gif_frame.create_button_state = "normal"
        self._view.browse_btn_state = "normal"

    def _calculate_base_fps(self) -> None:
        try:
            num, den = self._app_state.media.average_fps_str.split("/")
            self._app_state.media.average_fps_int = int(
                (round(int(num) / 2.0) * 2) / (round(int(den) / 2.0) * 2)    
            )
        except (ValueError, ZeroDivisionError):
            try:
                self._app_state.media.average_fps_int = int(
                    self._app_state.media.average_fps_str
                )
            except ValueError:
                self._app_state.media.average_fps_int = 30

        self._update_fps_dropdown_values()

    def _update_fps_dropdown_values(self) -> None:
        fps: int = self._app_state.media.average_fps_int

        values = []
        fps_list = [120, 60, 30, 24, 15]

        # set video's current FPS as only choice if less than 15 FPS
        if fps < fps_list[-1]:
            values.append(str(fps))

            self._view.settings_frame.frames_dropdown = values
            return

        for i in fps_list:
            if i <= fps:
                values.append(str(i))

        self._view.settings_frame.frames_dropdown = values

    def _update_resolution_dropdown_values(self) -> None:
        updated_resolutions: list[str] = get_list_of_smaller_resolutions(
            self._app_state.media.base_resolution
        )

        self._view.settings_frame.resolution_dropdown = updated_resolutions

    def _update_audio_settings(self) -> None:
        has_audio = self._app_state.media.has_audio
        self._settings_presenter.update_audio_settings(has_audio)

    def _load_media(self) -> None:
        self._media_player_presenter.load_media(
            media_file=self._app_state.media.input_file
        )

    def _browse_files(self) -> str | tuple | None:
        from tkinter import filedialog

        return filedialog.askopenfilename(
            parent=self._view,
            initialdir=path.expanduser("~"),
            filetypes=[
                ("Video Files", "*.mp4 *.mov *.mkv *.avi *.webm"),
            ],
        )

    def _handle_files(self, filepath: str | tuple | None) -> None:
        if filepath is None or filepath == "" or filepath == ():
            return

        if isinstance(filepath, tuple):
            dialogs.show_warning(
                master=self._view,
                title="File Error!",
                message="Cannot load multiple files at once!",
            )
            return

        self.disable_ui()

        if not self._compatible_file(filepath):
            dialogs.show_warning(
                master=self._view, title="Invalid File", message="File not compatible!"
            )

            self.restore_ui()
            return

        self._app_state.media.input_file = filepath

        if self._view.file_entry == "" or self._view.file_entry is None:
            self._view.file_entry = filepath

        self._extraction_controller.extract_data()

    def _compatible_file(self, item: str) -> bool:
        if not path.isfile(item):
            return False

        _, ext = path.splitext(item)
        ext = ext.lower()
        # Checks if files is not a supported media file
        if ext not in (".mp4", ".webm", ".mov", ".mkv", ".avi"):
            return False

        return True

    def _bind_view(self):
        self._view.on_open_file = self.on_open_file
        self._view.on_file_entry_submitted = self.on_file_entry_submit
        self._view.on_show_about = self.on_show_about
        self._view.on_show_license = self.on_show_license
        self._view.on_show_third_party_licenses = self.on_show_third_party_licenses
        self._view.on_open_frame_viewer = self.open_frame_viewer
        self._view.on_exit = self.on_exit
