from io import BytesIO
from os import path
from threading import Lock, Thread

from PIL import Image, ImageTk

from models.media_attrs import MediaAttrs

from views.frame_viewer import FrameViewer
from views import dialogs

from services.ffmpeg_service import FFmpegService

from utils.timestamp_untils import ms_to_timestamp


class FrameViewerPresenter:
    def __init__(
        self,
        frame_viewer: FrameViewer,
        ffmpeg_service: FFmpegService,
        media_attrs: MediaAttrs,
    ) -> None:

        self._frame_viewer: FrameViewer = frame_viewer
        self._ffmpeg_service: FFmpegService = ffmpeg_service
        self._media_attrs: MediaAttrs = media_attrs

        self._current_frame: int = 0
        self._current_ms: int = 0
        self._total_frames: int = 0
        self._frame_duration_ms: int = 0

        self._frame_img: Image.Image | None = None
        self._tk_frame_img: ImageTk.PhotoImage | None = None

        self._seek_id: str | None = None
        self._frame_request: int = 0
        self._frame_lock = Lock()
        self._frame_thread: Thread | None = None
        self._pending_frame: tuple[int, str, str] | None = None

        self._current_media: str | None = None

        self._bind_view()

    def load_media(self) -> None:
        if self._media_attrs.input_file is None:
            return

        self._current_media = self._media_attrs.input_file
        self._current_frame = 0
        self._current_ms = 0

        fps = self._media_attrs.average_fps_int
        duration_ms = self._media_attrs.full_duration_ms
        if fps is None or fps <= 0 or duration_ms is None or duration_ms < 0:
            self._display_error()
            return

        # Keep sub-1 ms frame durations from becoming zero at very high rates.
        self._frame_duration_ms = max(1, int(1000 / fps))

        self._total_frames = int(duration_ms / self._frame_duration_ms)

        steps = max(self._total_frames, 1)

        self._frame_viewer.configure_frame_slider(
            to=self._media_attrs.full_duration_ms,
            number_of_steps=steps,
        )

        self._frame_viewer.current_time_ms = 0
        self._frame_viewer.next_btn_state = "normal"
        self._frame_viewer.frame_slider_state = "normal"
        self._frame_viewer.save_button_state = "normal"

        self._frame_viewer.frame_rate = str(self._media_attrs.average_fps_int)
        self._frame_viewer.total_frames = str(self._total_frames)
        self._frame_viewer.current_frame = "0"
        self._frame_viewer.timestamp = ms_to_timestamp(0)

        self._extract_frame(ms=0)

    def on_save_frame(self) -> None:
        if self._frame_img is None:
            return

        if self._current_media is None:
            return

        if self._current_media != self._media_attrs.input_file:
            self.load_media()
            return

        from tkinter import filedialog

        # Gets basename of media file
        fullname, _ = path.splitext(self._current_media)
        name = path.basename(fullname)

        # Opens file dialog to get new file name, and save directory from a user
        file = filedialog.asksaveasfilename(
            parent=self._frame_viewer,
            title="Save As",
            initialdir=path.expanduser("~"),
            initialfile=f"{name}_frame_{self._current_frame}",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
            confirmoverwrite=True,
        )

        if file == "" or file is None or file == ():
            return

        _, ext = path.splitext(file)
        ext = ext.lower()
        # Only allows files to be saved a jpeg or png
        if ext not in (".png", ".jpg", ".jpeg"):
            dialogs.show_warning(
                master=self._frame_viewer,
                title="Incompatible File Type",
                message=f"Screenshot cannot be saved as {ext}!",
            )
            return

        # Use PIL functions to save frame
        try:
            self._frame_img.save(file)

        except Exception:
            dialogs.show_error(
                master=self._frame_viewer,
                title="Screenshot Error",
                message="Failed to Take screenshot",
            )
        else:
            dialogs.show_success(
                master=self._frame_viewer,
                title="Screenshot Successful",
                message=f"Screenshot taken!\n{file}",
            )

    def on_previous_frame_change(self) -> None:
        """Calculates timestamps to get the exact previous frame"""
        target = self._current_ms - self._frame_duration_ms
        target = max(0, target)
        self._frame_viewer.current_time_ms = target
        self._seek_to(target)

    def on_next_frame_change(self) -> None:
        """Calculates timestamps to get the exact next frame"""
        target = self._current_ms + self._frame_duration_ms
        target = min(target, self._media_attrs.full_duration_ms)
        self._frame_viewer.current_time_ms = target
        self._seek_to(target)

    def on_slider_move(self, value: int) -> None:
        if self._seek_id is not None:
            self._frame_viewer.after_cancel(self._seek_id)
        self._seek_id = self._frame_viewer.after(50, self._seek_to, value)

    def on_canvas_resize(self) -> None:
        if self._frame_viewer.image_id is not None:
            self._display_frame()

        if self._frame_viewer.text_id is not None:
            self._display_error()

    def _seek_to(self, value: float) -> None:
        self._seek_id = None

        if self._current_media != self._media_attrs.input_file:
            self.load_media()
            return

        self._current_ms = max(0, min(int(value), self._media_attrs.full_duration_ms))
        self._update_ui()
        self._extract_frame(ms=self._current_ms)

    def _update_ui(self) -> None:
        self._frame_viewer.current_time_ms = self._current_ms
        self._frame_viewer.timestamp = ms_to_timestamp(int(self._current_ms))

        if self._frame_duration_ms > 0:
            self._current_frame = int(self._current_ms / self._frame_duration_ms)
        else:
            self._current_frame = 0

        self._frame_viewer.current_frame = str(self._current_frame)

        if self._current_ms <= 0:
            self._frame_viewer.previous_btn_state = "disabled"

        elif self._current_ms > 0:
            self._frame_viewer.previous_btn_state = "normal"

        if self._current_ms >= self._media_attrs.full_duration_ms:
            self._frame_viewer.next_btn_state = "disabled"

        elif self._current_ms < self._media_attrs.full_duration_ms:
            self._frame_viewer.next_btn_state = "normal"

    def _extract_frame(self, ms: float) -> None:
        """Extract an exact frame off the UI thread."""
        input_file = self._current_media
        if input_file is None:
            return

        # Loads media if new media was loaded in  app
        # while frame viewer was still open
        if input_file != self._media_attrs.input_file:
            self.load_media()
            return

        with self._frame_lock:
            self._frame_request += 1
            request_id = self._frame_request
            timestamp = ms_to_timestamp(int(ms))
            self._pending_frame = (request_id, input_file, timestamp)

            # Keep only one FFmpeg worker
            # While it runs, newer requests replacethe pending request
            if self._frame_thread is not None:
                return

            self._frame_thread = Thread(
                target=self._extract_frame_worker,
                name="ffmpeg-frame-extract",
                daemon=True,
            )

            self._frame_thread.start()

    def _extract_frame_worker(self) -> None:
        """Thread to handle frame exctraction without blocking the main thread"""
        with self._frame_lock:
            request = self._pending_frame
            self._pending_frame = None
            if request is None:
                self._frame_thread = None
                return

        request_id, input_file, timestamp = request
        frame_img: Image.Image | None = None

        # FFmpeg Service does error handling, returns None if error raised
        frame_bytes: bytes | None = self._ffmpeg_service.extract_frame(
            input_file=input_file, timestamp=timestamp
        )

        if frame_bytes:
            try:
                # Creates a copy image to display
                # convert forces loading before BytesIO is discarded.
                frame_img = Image.open(BytesIO(frame_bytes)).convert("RGB")

            except Exception:
                frame_img = None
        

        # Tk widgets and ImageTk objects dealt with on the main thread
        self._frame_viewer.after(0, self._finish_frame_extract, request_id, frame_img)

    def _finish_frame_extract(
        self, request_id: int, frame_img: Image.Image | None
    ) -> None:
        """Displays frame or error before restarting frame extraction if necessary"""
        with self._frame_lock:
            self._frame_thread = None
            has_pending = self._pending_frame is not None

        # Only displays something if a new frame hasn't been selected uring the extraction process
        if request_id == self._frame_request:
            if frame_img is None:
                self._display_error()
            else:
                self._frame_img = frame_img
                self._display_frame()

        if not has_pending:
            return

        if self._frame_thread is not None:
            return

        # Extracts a new frame if one was requested while extraction process was still running
        # and extraction process is not already running
        with self._frame_lock:
            self._frame_thread = Thread(
                target=self._extract_frame_worker,
                name="ffmpeg-frame-extract",
                daemon=True,
            )
            self._frame_thread.start()

    def _display_error(self) -> None:
        """Deletes previous frame or existing error message before displaying new error message"""
        if self._frame_img is not None:
            self._frame_img = None

        if self._tk_frame_img is not None:
            self._tk_frame_img = None

        if self._frame_viewer.save_button_state == "normal":
            self._frame_viewer.save_button_state = "disabled"

        self._frame_viewer.display_error()

    def _display_frame(self) -> None:
        """Calculates images size to fit inside canvas, then displays image"""
        if self._frame_img is None:
            return

        canvas_width = self._frame_canvas.winfo_width()
        canvas_height = self._frame_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        img_width, img_height = self._frame_img.size

        scale = min(canvas_width / img_width, canvas_height / img_height)

        # Prevent enlarging
        scale = min(scale, 1.0)

        new_width = max(1, int(img_width * scale))
        new_height = max(1, int(img_height * scale))

        resized = self._frame_img.resize(
            (new_width, new_height), Image.Resampling.LANCZOS
        )

        self._tk_frame_img = ImageTk.PhotoImage(resized)

        x = canvas_width // 2
        y = canvas_height // 2

        self._frame_viewer.display_frame(x=x, y=y, frame=self._tk_frame_img)

        if self._frame_viewer.save_button_state == "disabled":
            self._frame_viewer.save_button_state = "normal"

    def _bind_view(self) -> None:
        self._frame_viewer.on_save_frame = self.on_save_frame
        self._frame_viewer.on_previous_frame_change = self.on_previous_frame_change
        self._frame_viewer.on_next_frame_change = self.on_next_frame_change
        self._frame_viewer.on_slider_move = self.on_slider_move
        self._frame_viewer.on_canvas_resize = self.on_canvas_resize

        self._frame_canvas = self._frame_viewer.frame_canvas
