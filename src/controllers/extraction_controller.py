from threading import Thread
from collections.abc import Callable
from typing import Any

from views.main_frame import MainFrame
from views import dialogs

from services.ffprobe_service import FFprobeService

from models.media_attrs import MediaAttrs
from models.media_timestamps import MediaTimestamps

from utils.timestamp_untils import ms_to_timestamp
from utils.log_utils import logger


class ExtractionController:
    def __init__(
        self,
        media_attrs: MediaAttrs,
        timestamps: MediaTimestamps,
        ffprobe_service: FFprobeService,
        parent_view: MainFrame,
        after_extraction_command: Callable[..., Any],
    ):
        self._media_attrs: MediaAttrs = media_attrs
        self._timestamps: MediaTimestamps = timestamps

        self._ffprobe_service: FFprobeService = ffprobe_service
        self._parent_view: MainFrame = parent_view

        self._after_extraction_command: Callable[..., Any] = after_extraction_command

        self._extraction_thread: Thread | None = None

    def extract_data(self) -> None:
        """Extracts metadata via FFprobe on a separate thread"""
        if self._extraction_thread is not None and self._extraction_thread.is_alive():
            return

        self._extraction_thread = Thread(target=self._extract_data_worker, daemon=True)
        self._extraction_thread.start()

    def _extract_data_worker(self) -> None:
        if self._media_attrs.input_file is None:
            return

        result: str | None = self._ffprobe_service.get_media_attrs(
            filepath=self._media_attrs.input_file
        )

        self._parent_view.after(0, self._extraction_cleanup, result)

    def _extraction_cleanup(self, result: str | None) -> None:
        self._extraction_thread = None

        if result is None:
            dialogs.show_error(
                master=self._parent_view,
                title="FFprobe Error!",
                message="Extracting metadata failed!",
            )
            return

        parsed: bool = self._parse_attributes(result=result)

        if not parsed:
            dialogs.show_error(
                master=self._parent_view,
                title="Missing Metadata!",
                message="File missing metadata!",
            )
            return

        self._initialize_timestamps()
        self._after_extraction_command()

    def _parse_attributes(self, result: str) -> bool:
        """
        Parses through returned JSON
        and gets clean values for video frame rate,
        resolution, and duration
        """

        import json

        try:
            data = json.loads(result)
        except json.JSONDecodeError as e:
            logger.exception(str(e))
            return False

        streams = data.get("streams", [])
        formats = data.get("format", {})

        if not streams:
            return False

        video_stream = next(
            (stream for stream in streams if stream.get("codec_type") == "video"),
            None,
        )

        if video_stream is None:
            return False

        width = video_stream.get("width")
        height = video_stream.get("height")
        avg_frame_rate = video_stream.get("avg_frame_rate")
        duration: str | None = formats.get("duration")

        if None in (width, height) or avg_frame_rate is None or duration is None:
            return False

        if "N/A" in str(avg_frame_rate) or "N/A" in str(duration):
            return False

        has_audio: bool = any(stream.get("codec_type") == "audio" for stream in streams)

        self._media_attrs.base_resolution = f"{width}x{height}"
        self._media_attrs.average_fps_str = avg_frame_rate
        self._media_attrs.full_duration_seconds = float(duration)
        self._media_attrs.full_duration_ms = int(
            self._media_attrs.full_duration_seconds * 1000
        )
        self._media_attrs.has_audio = has_audio

        return True

    def _initialize_timestamps(self) -> None:
        self._timestamps.end_time = ms_to_timestamp(self._media_attrs.full_duration_ms)

        self._timestamps.full_duration = ms_to_timestamp(
            self._media_attrs.full_duration_ms
        )

        self._timestamps.trimmed_duration = ms_to_timestamp(
            self._media_attrs.full_duration_ms
        )
