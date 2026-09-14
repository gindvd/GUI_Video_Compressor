from os import path, remove
from threading import Thread
from collections.abc import Callable

from views.main_frame import MainFrame
from views import dialogs

from models.app_state import AppState

from services.ffmpeg_service import FFmpegService
from services.exit_status import ExitStatus

from widgets.progressbar_popup import ProgressbarPopup


class OptimizeController:
    def __init__(
        self,
        parent_view: MainFrame,
        ffmpeg_service: FFmpegService,
        app_state: AppState,
        on_restore_ui: Callable[[], None],
    ) -> None:

        self._parent_view: MainFrame = parent_view
        self._ffmpeg_service: FFmpegService = ffmpeg_service
        self._app_state: AppState = app_state
        self._on_restore_ui: Callable[[], None] = on_restore_ui

        self._progressbar_popup: ProgressbarPopup | None = None
        self._optimization_thread: Thread | None = None

    def optimize_media(self) -> None:
        if (
            self._optimization_thread is not None
            and self._optimization_thread.is_alive()
        ):
            return

        self._progressbar_popup = ProgressbarPopup(
            master=self._parent_view,
            command=self.cancel_optimization,
        )
        self._progressbar_popup.run_progressbar()

        self._optimization_thread = Thread(
            target=self._optimize_media_worker,
            daemon=True,
        )
        self._optimization_thread.start()

    def _optimize_media_worker(self) -> None:
        if self._app_state.media.input_file is None:
            return

        if self._app_state.media.output_file is None:
            return

        status = self._ffmpeg_service.optimize(
            input_file=self._app_state.media.input_file,
            file_format=self._app_state.settings.container,
            resolution=self._app_state.settings.resolution,
            codec=self._app_state.settings.video_codec,
            fps=self._app_state.settings.frame_rate,
            preset=self._app_state.settings.preset,
            quality=self._app_state.settings.quality,
            include_audio=self._app_state.settings.include_audio,
            audio_codec=self._app_state.settings.audio_codec,
            audio_bitrate=self._app_state.settings.audio_bitrate,
            start_time=self._app_state.timestamps.start_time,
            duration=self._app_state.timestamps.trimmed_duration,
            output_file=self._app_state.media.output_file,
        )

        self._parent_view.after(0, self._optimization_cleanup, status)

    def _optimization_cleanup(self, status: ExitStatus) -> None:
        self._optimization_thread = None

        if self._progressbar_popup is not None:
            self._progressbar_popup.destroy()
            self._progressbar_popup = None

        if status in (ExitStatus.ERROR, ExitStatus.TERMINATED):
            self._remove_partial_output()

        if status == ExitStatus.ERROR:
            dialogs.show_error(
                master=self._parent_view,
                title="FFmpeg Error",
                message="Error optimizing media!\nCheck logs!",
            )
        elif status == ExitStatus.TERMINATED:
            dialogs.show_info(
                master=self._parent_view,
                title="Process Terminated",
                message="Media optimization cancelled!",
            )
        elif status == ExitStatus.SUCCESS:
            dialogs.show_success(
                master=self._parent_view,
                title="Optimization Complete",
                message="Media optimized!",
            )

        self._on_restore_ui()

    def _remove_partial_output(self) -> None:
        output_file = self._app_state.media.output_file

        if output_file and path.exists(output_file):
            remove(output_file)

    def cancel_optimization(self) -> None:
        self._ffmpeg_service.terminate_process()

    def create_output_file(self, directory: str) -> None:
        if self._app_state.media.input_file is None:
            return

        fullname, _ = path.splitext(self._app_state.media.input_file)
        name = path.basename(fullname)
        new_name = f"{name}_compressed.{self._app_state.settings.container}"

        output_file = path.join(directory, new_name)

        if path.exists(output_file):
            output_file = self._uniquify(output_file)

        self._app_state.media.output_file = output_file

    @staticmethod
    def _uniquify(file_path: str) -> str:
        """Adds unique number to filename, if file already exists"""
        filename, extension = path.splitext(file_path)
        counter = 1

        while path.exists(file_path):
            file_path = filename + " (" + str(counter) + ")" + extension
            counter += 1

        return file_path

    def shutdown(self) -> None:
        self.cancel_optimization()

        if (
            self._optimization_thread is not None
            and self._optimization_thread.is_alive()
        ):
            self._optimization_thread.join(timeout=1)
