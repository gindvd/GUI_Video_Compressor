from glob import glob
from os import path, remove
from threading import Thread
from collections.abc import Callable

from views.main_frame import MainFrame
from views import dialogs

from models.app_state import AppState

from services.ffmpeg_service import FFmpegService
from services.exit_status import ExitStatus

from widgets.progressbar_popup import ProgressbarPopup


class FFmpegController:
    def __init__(
        self,
        parent_view: MainFrame,
        ffmpeg_service: FFmpegService,
        app_state: AppState,
        on_restore_ui: Callable[[], None],
        scan_and_load: Callable[[str], None]
    ) -> None:

        self._parent_view: MainFrame = parent_view
        self._ffmpeg_service: FFmpegService = ffmpeg_service
        self._app_state: AppState = app_state

        self._on_restore_ui: Callable[[], None] = on_restore_ui
        self._scan_and_load: Callable[[str], None] = scan_and_load

        self._progressbar_popup: ProgressbarPopup | None = None
        self._process_thread: Thread | None = None 

    def optimize_media(self) -> None:
        if (
            self._process_thread is not None
            and self._process_thread.is_alive()
        ):
            return

        self._progressbar_popup = ProgressbarPopup(
            master=self._parent_view,
            title="Optimization in Progress",
            command=self.cancel_process,
        )
        self._progressbar_popup.run_progressbar()

        self._process_thread = Thread(
            target=self._optimize_media_worker,
            daemon=True,
        )
        self._process_thread.start()
    
    def create_gif(self) -> None:
        if (
            self._process_thread is not None
            and self._process_thread.is_alive()
        ):
            return
        
        self._progressbar_popup = ProgressbarPopup(
            master=self._parent_view,
            title="GIF Creation in Progress",
            command=self.cancel_process,
        )
        self._progressbar_popup.run_progressbar()

        self._process_thread = Thread(
            target=self._create_gif_worker,
            daemon=True,
        )
        self._process_thread.start()

    def download_video(self, url: str, ext: str, output_file: str) -> None:
        """Downloads YouTube Video in background on separate thread"""

        if (
            self._process_thread is not None
            and self._process_thread.is_alive()
        ):
            return

        self._progressbar_popup = ProgressbarPopup(
            master=self._parent_view,
            title="Download in Progress",
            command=self.cancel_process,
        )
        self._progressbar_popup.run_progressbar()

        self._process_thread = Thread(
            target=self._download_video_worker,
            args=(url, ext, output_file),
            daemon=True,
        )

        self._process_thread.start()

    def cancel_process(self) -> None:
        self._ffmpeg_service.terminate_process()
    
    def shutdown(self) -> None:
        self.cancel_process()

        if (
            self._process_thread is not None
            and self._process_thread.is_alive()
        ):
            self._process_thread.join(timeout=1)

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
    
    def create_gif_output_file(self, directory: str) -> None:
        if self._app_state.media.input_file is None:
            return

        fullname, _ = path.splitext(self._app_state.media.input_file)
        name = path.basename(fullname)
        new_name = f"{name}.gif"

        output_file = path.join(directory, new_name)

        if path.exists(output_file):
            output_file = self._uniquify(output_file)

        self._app_state.gif_settings.output_file = output_file
    
    def _optimize_media_worker(self) -> None:
        if self._app_state.media.input_file is None:
            return

        if self._app_state.media.output_file is None:
            return

        status: ExitStatus = self._ffmpeg_service.optimize(
            app_state=self._app_state
        )

        self._parent_view.after(
            0, self._cleanup, status, self._app_state.media.output_file
        )
    
    def _download_video_worker(self, url: str, ext: str, output_file: str) -> None:
        """Worker for yt-dlp video download"""

        status: ExitStatus = self._ffmpeg_service.download_video(
            url=url,
            ext=ext,
            output_file=output_file,
        )

        self._parent_view.after(0, self._download_cleanup, status, output_file)
    
    def _create_gif_worker(self) -> None:
        if self._app_state.media.input_file is None:
            return
        
        if self._app_state.gif_settings.output_file is None:
            return
        
        status: ExitStatus = self._ffmpeg_service.create_gif(
            app_state=self._app_state
        )

        self._parent_view.after(
            0, self._cleanup, status, self._app_state.gif_settings.output_file
        )
    
    def _cleanup(self, status: ExitStatus, output_file: str) -> None:
        self._process_thread = None

        if self._progressbar_popup is not None:
            self._progressbar_popup.destroy()
            self._progressbar_popup = None

        if status in (ExitStatus.ERROR, ExitStatus.TERMINATED):
            self._remove_partial_output(output_file)

        if status == ExitStatus.ERROR:
            dialogs.show_error(
                master=self._parent_view,
                title="FFmpeg Error",
                message="FFmpeg encountered an error!\nCheck logs!",
            )
        elif status == ExitStatus.TERMINATED:
            dialogs.show_info(
                master=self._parent_view,
                title="Process Terminated",
                message="FFmpeg cancelled!",
            )
        elif status == ExitStatus.SUCCESS:
            dialogs.show_success(
                master=self._parent_view,
                title="FFmpeg Complete",
                message="FFmpeg process complete!",
            )
        elif status == ExitStatus.BUSY:
            dialogs.show_info(
                master=self._parent_view,
                title="Process Running",
                message="""
                    FFmpeg currently running!\n
                    Please wait until current process finished!
                """,
            )

        self._on_restore_ui()

    def _download_cleanup(self, status: ExitStatus, output_file: str) -> None:
        self._process_thread = None

        if self._progressbar_popup is not None:
            self._progressbar_popup.destroy()
            self._progressbar_popup = None
        
        if status in (ExitStatus.ERROR, ExitStatus.TERMINATED):
            self._remove_partial_output(output_file)
            self._remove_download_partials(output_file)

        if status == ExitStatus.ERROR:
            dialogs.show_error(
                master=self._parent_view,
                title="Download Error",
                message="yt-dlp encountered an error!\nCheck logs!",
            )
        elif status == ExitStatus.TERMINATED:
            dialogs.show_info(
                master=self._parent_view,
                title="Process Terminated",
                message="Download cancelled!",
            )
        elif status == ExitStatus.SUCCESS:
            dialogs.show_success(
                master=self._parent_view,
                title="Download Complete",
                message="Video download complete!",
            )

            self._scan_and_load(output_file)

        self._on_restore_ui()

    def _remove_download_partials(self, output_file: str) -> None:
        """Removes yt-dlp temporary and partial files from the output directory"""
        output_path = path.abspath(output_file)
        output_folder = path.dirname(output_path)
        output_name = path.basename(output_path)
        base, _ = path.splitext(output_name)

        patterns = [
            f"{base}.f*.mp4",
            f"{base}.f*.webm",
            f"{base}.f*.m4a",
            f"{base}.f*.opus",
            f"{base}.f*.part",
            f"{base}.part",
            f"{base}.ytdl",
            f"{base}.temp",
        ]

        for pattern in patterns:
            for temp_file in glob(path.join(output_folder, pattern)):
                self._remove_partial_output(temp_file)
    
    def _remove_partial_output(self, output_file: str) -> None:
        try:
            if path.isfile(output_file):
                remove(output_file)
        except OSError:
            pass

    @staticmethod
    def _uniquify(file_path: str) -> str:
        """Adds unique number to filename, if file already exists"""
        filename, extension = path.splitext(file_path)
        counter = 1

        while path.exists(file_path):
            file_path = filename + " (" + str(counter) + ")" + extension
            counter += 1

        return file_path
