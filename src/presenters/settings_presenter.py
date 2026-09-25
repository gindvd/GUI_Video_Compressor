from sys import platform
from os import path
from collections.abc import Callable

from models.optimize_settings import OptimizeSettings

from views.settings_frame import SettingsFrame

from controllers.ffmpeg_controller import FFmpegController

from services.hardware_detection_service import (
    gpu_manufacturers,
)
from services.settings_rules import (
    containers_for,
    audio_codecs_for,
    codecs_for,
    preset_supported,
)


class SettingsPresenter:

    _BASE_VIDEO_CODECS = ["libx264", "libx265", "libvpx-vp9", "libsvtav1"]

    def __init__(
        self, 
        optimize_settings: OptimizeSettings, 
        settings_view: SettingsFrame,
        ffmpeg_controller: FFmpegController,
        disable_ui_command: Callable[[], None],
        restore_ui_command: Callable[[], None]
    ):
        self._optimize_settings: OptimizeSettings = optimize_settings
        self._settings_view: SettingsFrame = settings_view
        self._ffmpeg_controller = ffmpeg_controller

        self._disable_ui : Callable[[], None] = disable_ui_command
        self._restore_ui : Callable[[], None] = restore_ui_command

        self._initialize_video_codec_values()
        self._bind_settings_view()
    
    def on_compress(self) -> None:
        self._disable_ui()

        if not self._get_output_directory():
            self._restore_ui()
            return
        
        self._ffmpeg_controller.optimize_media()

    def on_video_codec_change(self, value: str) -> None:
        self._optimize_settings.video_codec = value

        compatible_containers = containers_for(value)

        self._settings_view.container_dropdown = compatible_containers
        self._settings_view.container = compatible_containers[0]

        self.on_container_change(compatible_containers[0])

        if not preset_supported(value):
            self._settings_view.set_preset_speed_state(False)
            self._optimize_settings.preset = None

        else:
            self._settings_view.set_preset_speed_state(True)
            self._optimize_settings.preset = self._settings_view.preset_speed.lower()

    def on_container_change(self, value: str) -> None:
        self._optimize_settings.container = value

        compatible_audio_codecs = audio_codecs_for(value)

        self._settings_view.audio_codec_dropdown = compatible_audio_codecs
        self._settings_view.audio_codec = compatible_audio_codecs[0]

        self._optimize_settings.audio_codec = self._settings_view.audio_codec

    def on_resolution_change(self, value: str) -> None:
        self._optimize_settings.resolution = value

    def on_frame_rate_change(self, value: str) -> None:
        self._optimize_settings.frame_rate = value

    def on_quality_change(self, value: int) -> None:
        self._optimize_settings.quality = value

    def on_audio_codec_change(self, value: str) -> None:
        self._optimize_settings.audio_codec = value

    def on_audio_bitrate_change(self, value: str) -> None:
        self._optimize_settings.audio_bitrate = value

    def on_remove_audio_toggle(self, remove_audio: bool) -> None:
        self._optimize_settings.include_audio = not remove_audio

        if remove_audio:
            self._settings_view.set_audio_codec_state(False)
            self._settings_view.set_audio_bitrate_state(False)

            self._optimize_settings.audio_codec = None
            self._optimize_settings.audio_bitrate = None

        else:
            self._settings_view.set_audio_codec_state(True)
            self._settings_view.set_audio_bitrate_state(True)

            self._optimize_settings.audio_codec = self._settings_view.audio_codec
            self._optimize_settings.audio_bitrate = self._settings_view.audio_bitrate

    def on_preset_speed_change(self, value: str) -> None:
        self._optimize_settings.preset = value.lower()

    def update_audio_settings(self, has_audio: bool) -> None:

        self._settings_view.set_audio_codec_state(has_audio)
        self._settings_view.set_audio_bitrate_state(has_audio)

        self._settings_view.set_remove_audio_state(has_audio)
        self._settings_view.remove_audio = not has_audio
        self._optimize_settings.include_audio = has_audio

    def _initialize_video_codec_values(self) -> None:
        video_codecs: list[str] = []

        try:
            manufacturers_names: list[str] = gpu_manufacturers()
        except Exception:
            manufacturers_names = []

        for name in manufacturers_names:
            if name == "Intel" and platform.startswith("linux"):
                name = "Intel-Linux"
            
            if name in ["Adapter", ""]:
                continue

            video_codecs.extend(codecs_for(name))

        video_codecs.extend(self._BASE_VIDEO_CODECS)

        # Remove any duped values
        video_codecs = list(dict.fromkeys(video_codecs))

        self._settings_view.video_codec_dropdown = video_codecs
        self._settings_view.video_codec = video_codecs[0]

        self.on_video_codec_change(video_codecs[0])
    
    def _get_output_directory(self) -> bool:
        from tkinter import filedialog

        output_directory: str = filedialog.askdirectory(
            parent=self._settings_view,
            title="File Output Selection",
            initialdir=path.expanduser("~"),
        )

        if output_directory == "":
            return False

        self._ffmpeg_controller.create_output_file(output_directory)

        return True

    def _bind_settings_view(self) -> None:
        self._settings_view.on_video_codec_change = self.on_video_codec_change
        self._settings_view.on_container_change = self.on_container_change
        self._settings_view.on_resolution_change = self.on_resolution_change
        self._settings_view.on_frame_rate_change = self.on_frame_rate_change
        self._settings_view.on_quality_change = self.on_quality_change
        self._settings_view.on_audio_codec_change = self.on_audio_codec_change
        self._settings_view.on_audio_bitrate_change = self.on_audio_bitrate_change
        self._settings_view.on_remove_audio_toggle = self.on_remove_audio_toggle
        self._settings_view.on_preset_speed_change = self.on_preset_speed_change

        self._settings_view.on_compress = self.on_compress
