import customtkinter as ctk

from collections.abc import Callable
from typing import Any


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master: Any, **kwargs) -> None:
        super().__init__(master=master, **kwargs)

        self.on_video_codec_change: Callable[[str], Any] | None = None
        self.on_container_change: Callable[[str], Any] | None = None
        self.on_resolution_change: Callable[[str], Any] | None = None
        self.on_frame_rate_change: Callable[[str], Any] | None = None
        self.on_quality_change: Callable[[int], Any] | None = None
        self.on_audio_codec_change: Callable[[str], Any] | None = None
        self.on_audio_bitrate_change: Callable[[str], Any] | None = None
        self.on_remove_audio_toggle: Callable[[bool], Any] | None = None
        self.on_preset_speed_change: Callable[[str], Any] | None = None

        self._video_codec = ctk.StringVar(self, value="libx264")
        self._container = ctk.StringVar(self, value="mp4")
        self._resolution = ctk.StringVar(self, value="1920x1080")
        self._frame_rate = ctk.StringVar(self, value="60")
        self._preset_speed = ctk.StringVar(self, value="Medium")
        self._audio_codec = ctk.StringVar(self, value="aac")
        self._audio_bitrate = ctk.StringVar(self, value="128k")
        self._remove_audio = ctk.BooleanVar(self, value=False)

        self._quality = ctk.DoubleVar(self, value=90.0)
        self._quality_text = ctk.StringVar(self, value="90%")

        self._build()

    def _build(self) -> None:
        """Builds the settings panel with widgets for video, audio, and optimization options."""
        section_color = ("gray75", "gray25")
        header_font = ctk.CTkFont(size=14, weight="bold")

        self._video_section = ctk.CTkFrame(
            self,
            fg_color=section_color,
            corner_radius=10,
        )
        self._video_section.pack(fill="x", padx=(5, 10), pady=10)
        self._video_section.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._video_section,
            text="Video Settings",
            font=header_font,
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

        self._build_video_section()

        self._audio_section = ctk.CTkFrame(
            self,
            fg_color=section_color,
            corner_radius=10,
        )
        self._audio_section.pack(fill="x", padx=(5, 10), pady=0)
        self._audio_section.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._audio_section,
            text="Audio Settings",
            font=header_font,
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

        self._build_audio_section()

        self._optimization_section = ctk.CTkFrame(
            self,
            fg_color=section_color,
            corner_radius=10,
        )
        self._optimization_section.pack(fill="x", padx=(5, 10), pady=10)
        self._optimization_section.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._optimization_section,
            text="Optimization Settings",
            font=header_font,
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

        self._build_optimization_section()

    def _build_video_section(self) -> None:
        ctk.CTkLabel(self._video_section, text="Codec:").grid(
            row=1,
            column=0,
            padx=10,
            pady=6,
            sticky="w",
        )

        self._video_codec_dropdown = ctk.CTkComboBox(
            self._video_section,
            values=["libx264", "libx265", "libsvtav1", "libvpx-vp9"],
            state="readonly",
            command=self._handle_video_codec_change,
            variable=self._video_codec,
        )
        self._video_codec_dropdown.grid(row=1, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(self._video_section, text="Format:").grid(
            row=2,
            column=0,
            padx=10,
            pady=6,
            sticky="w",
        )

        self._container_dropdown = ctk.CTkComboBox(
            self._video_section,
            values=["mp4", "mkv", "mov"],
            state="readonly",
            command=self._handle_container_change,
            variable=self._container,
        )
        self._container_dropdown.grid(row=2, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(self._video_section, text="Resolution:").grid(
            row=3,
            column=0,
            padx=10,
            pady=6,
            sticky="w",
        )

        self._resolution_dropdown = ctk.CTkComboBox(
            self._video_section,
            values=[
                "3840x2160",
                "2560x1440",
                "1920x1080",
                "1280x720",
                "854x480",
                "640x360",
            ],
            state="readonly",
            command=self._handle_resolution_change,
            variable=self._resolution,
        )
        self._resolution_dropdown.grid(row=3, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(self._video_section, text="FPS:").grid(
            row=4,
            column=0,
            padx=10,
            pady=6,
            sticky="w",
        )

        self._frames_dropdown = ctk.CTkComboBox(
            self._video_section,
            values=["60", "30", "24", "15"],
            state="readonly",
            command=self._handle_frame_rate_change,
            variable=self._frame_rate,
        )
        self._frames_dropdown.grid(row=4, column=1, padx=10, pady=6, sticky="ew")

        quality_row = ctk.CTkFrame(self._video_section, fg_color="transparent")
        quality_row.grid(
            row=5,
            column=0,
            columnspan=2,
            padx=10,
            pady=(6, 10),
            sticky="ew",
        )
        quality_row.columnconfigure(1, weight=1)

        ctk.CTkLabel(quality_row, text="Quality:").grid(
            row=0,
            column=0,
            padx=(0, 8),
            sticky="w",
        )

        self._quality_slider = ctk.CTkSlider(
            quality_row,
            width=175,
            button_corner_radius=4,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self._handle_quality_change,
            variable=self._quality,
        )
        self._quality_slider.grid(row=0, column=1, padx=(0, 8), sticky="ew")

        self._quality_perc_lbl = ctk.CTkLabel(
            quality_row,
            textvariable=self._quality_text,
            width=40,
        )
        self._quality_perc_lbl.grid(row=0, column=2, sticky="e")

    def _build_audio_section(self) -> None:
        ctk.CTkLabel(self._audio_section, text="Codec:").grid(
            row=1,
            column=0,
            padx=10,
            pady=6,
            sticky="w",
        )

        self._audio_codec_dropdown = ctk.CTkComboBox(
            self._audio_section,
            values=["aac", "mp3", "libopus"],
            state="readonly",
            command=self._handle_audio_codec_change,
            variable=self._audio_codec,
        )
        self._audio_codec_dropdown.grid(row=1, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(self._audio_section, text="Bitrate:").grid(
            row=2,
            column=0,
            padx=10,
            pady=6,
            sticky="w",
        )

        self._audio_bitrate_dropdown = ctk.CTkComboBox(
            self._audio_section,
            values=["256k", "192k", "128k", "96k"],
            state="readonly",
            command=self._handle_audio_bitrate_change,
            variable=self._audio_bitrate,
        )
        self._audio_bitrate_dropdown.grid(row=2, column=1, padx=10, pady=6, sticky="ew")

        self._rm_aud_chkbox = ctk.CTkCheckBox(
            self._audio_section,
            text="Remove Audio",
            command=self._handle_remove_audio_toggle,
            variable=self._remove_audio,
        )
        self._rm_aud_chkbox.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=10,
            pady=(6, 10),
            sticky="w",
        )

    def _build_optimization_section(self) -> None:
        ctk.CTkLabel(self._optimization_section, text="Speed:").grid(
            row=1,
            column=0,
            padx=10,
            pady=6,
            sticky="w",
        )

        self._preset_speed_dropdown = ctk.CTkComboBox(
            self._optimization_section,
            values=[
                "Veryfast",
                "Faster",
                "Fast",
                "Medium",
                "Slow",
                "Slower",
                "Veryslow",
            ],
            state="readonly",
            command=self._handle_preset_speed_change,
            variable=self._preset_speed,
        )
        self._preset_speed_dropdown.grid(
            row=1,
            column=1,
            padx=10,
            pady=(6, 12),
            sticky="ew",
        )

    # Handlers
    def _handle_video_codec_change(self, value: str) -> None:
        self._video_codec.set(value)

        if self.on_video_codec_change:
            self.on_video_codec_change(value)

    def _handle_container_change(self, value: str) -> None:
        self._container.set(value)

        if self.on_container_change:
            self.on_container_change(value)

    def _handle_resolution_change(self, value: str) -> None:
        self._resolution.set(value)

        if self.on_resolution_change:
            self.on_resolution_change(value)

    def _handle_frame_rate_change(self, value: str) -> None:
        self._frame_rate.set(value)

        if self.on_frame_rate_change:
            self.on_frame_rate_change(value)

    def _handle_quality_change(self, value: float) -> None:
        quality_value = int(round(value))

        self._quality.set(float(quality_value))
        self._quality_text.set(f"{quality_value}%")

        if self.on_quality_change:
            self.on_quality_change(quality_value)

    def _handle_audio_codec_change(self, value: str) -> None:
        self._audio_codec.set(value)

        if self.on_audio_codec_change:
            self.on_audio_codec_change(value)

    def _handle_audio_bitrate_change(self, value: str) -> None:
        self._audio_bitrate.set(value)

        if self.on_audio_bitrate_change:
            self.on_audio_bitrate_change(value)

    def _handle_remove_audio_toggle(self) -> None:
        value = self._remove_audio.get()

        if self.on_remove_audio_toggle:
            self.on_remove_audio_toggle(value)

    def _handle_preset_speed_change(self, value: str) -> None:
        self._preset_speed.set(value)

        if self.on_preset_speed_change:
            self.on_preset_speed_change(value)

    # State setters
    def set_audio_codec_state(self, enabled: bool) -> None:
        self._audio_codec_dropdown.configure(
            state="readonly" if enabled else "disabled"
        )

    def set_audio_bitrate_state(self, enabled: bool) -> None:
        self._audio_bitrate_dropdown.configure(
            state="readonly" if enabled else "disabled"
        )

    def set_remove_audio_state(self, enabled: bool) -> None:
        self._rm_aud_chkbox.configure(state="normal" if enabled else "disabled")

    def set_preset_speed_state(self, enabled: bool) -> None:
        self._preset_speed_dropdown.configure(
            state="readonly" if enabled else "disabled"
        )

    # Dropdown values
    @property
    def video_codec_dropdown(self) -> list:
        return list(self._video_codec_dropdown.cget("values"))

    @video_codec_dropdown.setter
    def video_codec_dropdown(self, values: list[str]) -> None:
        self._video_codec_dropdown.configure(values=values)

        if self.video_codec not in values and values:
            self.video_codec = values[0]

    @property
    def container_dropdown(self) -> list:
        return list(self._container_dropdown.cget("values"))

    @container_dropdown.setter
    def container_dropdown(self, values: list[str]) -> None:
        self._container_dropdown.configure(values=values)

        if self.container not in values and values:
            self.container = values[0]

    @property
    def resolution_dropdown(self) -> list:
        return list(self._resolution_dropdown.cget("values"))

    @resolution_dropdown.setter
    def resolution_dropdown(self, values: list[str]) -> None:
        self._resolution_dropdown.configure(values=values)

        if self.resolution not in values and values:
            self.resolution = values[0]

    @property
    def frames_dropdown(self) -> list:
        return list(self._frames_dropdown.cget("values"))

    @frames_dropdown.setter
    def frames_dropdown(self, values: list[str]) -> None:
        self._frames_dropdown.configure(values=values)

        if self.frame_rate not in values and values:
            self.frame_rate = values[0]

    @property
    def audio_codec_dropdown(self) -> list:
        return list(self._audio_codec_dropdown.cget("values"))

    @audio_codec_dropdown.setter
    def audio_codec_dropdown(self, values: list[str]) -> None:
        self._audio_codec_dropdown.configure(values=values)

        if self.audio_codec not in values and values:
            self.audio_codec = values[0]

    @property
    def audio_bitrate_dropdown(self) -> list:
        return list(self._audio_bitrate_dropdown.cget("values"))

    @audio_bitrate_dropdown.setter
    def audio_bitrate_dropdown(self, values: list[str]) -> None:
        self._audio_bitrate_dropdown.configure(values=values)

        if self.audio_bitrate not in values and values:
            self.audio_bitrate = values[0]

    @property
    def preset_speed_dropdown(self) -> list:
        return list(self._preset_speed_dropdown.cget("values"))

    @preset_speed_dropdown.setter
    def preset_speed_dropdown(self, values: list[str]) -> None:
        self._preset_speed_dropdown.configure(values=values)

        if self._preset_speed.get() not in values and values:
            self.preset_speed = values[0]

    # Value properties
    @property
    def video_codec(self) -> str:
        return self._video_codec.get()

    @video_codec.setter
    def video_codec(self, value: str) -> None:
        self._video_codec.set(value)

    @property
    def container(self) -> str:
        return self._container.get()

    @container.setter
    def container(self, value: str) -> None:
        self._container.set(value)

    @property
    def resolution(self) -> str:
        return self._resolution.get()

    @resolution.setter
    def resolution(self, value: str) -> None:
        self._resolution.set(value)

    @property
    def frame_rate(self) -> str:
        return self._frame_rate.get()

    @frame_rate.setter
    def frame_rate(self, value: str) -> None:
        self._frame_rate.set(value)

    @property
    def quality(self) -> int:
        return int(round(self._quality.get()))

    @quality.setter
    def quality(self, value: int) -> None:
        value = max(0, min(100, int(value)))

        self._quality.set(float(value))
        self._quality_slider.set(value)
        self._quality_text.set(f"{value}%")

    @property
    def audio_codec(self) -> str:
        return self._audio_codec.get()

    @audio_codec.setter
    def audio_codec(self, value: str) -> None:
        self._audio_codec.set(value)

    @property
    def audio_bitrate(self) -> str:
        return self._audio_bitrate.get()

    @audio_bitrate.setter
    def audio_bitrate(self, value: str) -> None:
        self._audio_bitrate.set(value)

    @property
    def remove_audio(self) -> bool:
        return self._remove_audio.get()

    @remove_audio.setter
    def remove_audio(self, value: bool) -> None:
        self._remove_audio.set(value)

    @property
    def preset_speed(self) -> str:
        return self._preset_speed.get().lower()

    @preset_speed.setter
    def preset_speed(self, value: str) -> None:
        self._preset_speed.set(value)
