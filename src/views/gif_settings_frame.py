import customtkinter as ctk

from collections.abc import Callable
from typing import Any


class GifSettingsFrame(ctk.CTkFrame):
    def __init__(self, master: Any, **kwargs) -> None:
        super().__init__(master=master, **kwargs)

        self.on_resolution_change: Callable[[str], Any] | None = None
        self.on_frame_rate_change: Callable[[str], Any] | None = None
        self.on_loop_change: Callable[[str], Any] | None = None
        self.on_create: Callable[[str], Any] | None = None

        self._resolution = ctk.StringVar(self, value="854x480")
        self._frame_rate = ctk.StringVar(self, value="24")
        self._loops = ctk.StringVar(self, value="Infinite")

        self._build()

    def _build(self) -> None:
        section_font = ctk.CTkFont(size=14, weight="bold")
        frame_color = ("gray78", "gray22")

        self._setting_section = ctk.CTkFrame(
            self,
            fg_color=frame_color,
            corner_radius=8,
        )
        self._setting_section.pack(fill="x", padx=5, pady=(0, 5))
        self._setting_section.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._setting_section,
            text="GIF Settings",
            font=section_font,
        ).grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w")

        ctk.CTkLabel(self._setting_section, text="Resolution:").grid(
            row=1,
            column=0,
            padx=8,
            pady=4,
            sticky="w",
        )

        self._resolution_dropdown = ctk.CTkComboBox(
            self._setting_section,
            values=[
                "1280x720",
                "854x480",
                "640x360",
            ],
            state="readonly",
            command=self._handle_resolution_change,
            variable=self._resolution,
        )
        self._resolution_dropdown.grid(row=1, column=1, padx=8, pady=4, sticky="ew")
        self._resolution_dropdown.set("854x480")

        ctk.CTkLabel(self._setting_section, text="Frame Rate:").grid(
            row=2,
            column=0,
            padx=8,
            pady=4,
            sticky="w",
        )

        self._frame_rate_dropdown = ctk.CTkComboBox(
            self._setting_section,
            values=[
                "24",
                "15",
                "12",
                "10",
            ],
            state="readonly",
            command=self._handle_frame_rate_change,
            variable=self._frame_rate,
        )
        self._frame_rate_dropdown.grid(row=2, column=1, padx=8, pady=4, sticky="ew")

        ctk.CTkLabel(self._setting_section, text="Loop Count:").grid(
            row=3,
            column=0,
            padx=8,
            pady=4,
            sticky="w",
        )

        self._loop_dropdown = ctk.CTkComboBox(
            self._setting_section,
            values=[
                "Infinite",
                "1x",
                "2x",
                "5x",
                "10x"
            ],
            state="readonly",
            command=self._handle_loop_change,
            variable=self._loops,
        )
        self._loop_dropdown.grid(row=3, column=1, padx=8, pady=(4, 12), sticky="ew")

        self._button_container = ctk.CTkFrame(self,
            fg_color=frame_color,
            corner_radius=8
        )
        self._button_container.pack(fill="x", padx=5, pady=(5,0), side="bottom")

        self._create_btn = ctk.CTkButton(
            self._button_container, 
            text="Create GIF",
            state="disabled",
            command=self._handle_gif_creation
        )
        self._create_btn.pack(padx=8, pady=8)
    
    def _handle_resolution_change(self, value: str) -> None:
        self._resolution.set(value)

        if self.on_resolution_change:
            self.on_resolution_change(value)
    
    def _handle_frame_rate_change(self, value: str) -> None:
        self._frame_rate.set(value)

        if self.on_frame_rate_change:
            self.on_frame_rate_change(value)
    
    def _handle_loop_change(self, value: str) -> None:
        self._loops.set(value)

        if self.on_loop_change:
            self.on_loop_change(value)
    
    def _handle_gif_creation(self, event = None) -> None:
        if self.on_create:
            self.on_create()
    
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
    def loop(self) -> str:
        return self._loops.get()

    @resolution.setter
    def loop(self, value: str) -> None:
        self._loops.set(value)
    
    @property
    def create_button_state(self) -> str:
        return self._create_btn.cget("state")

    @create_button_state.setter
    def create_button_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return
        
        self._create_btn.configure(state=state)
    