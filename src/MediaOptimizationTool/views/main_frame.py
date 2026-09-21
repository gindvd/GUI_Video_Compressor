import customtkinter as ctk
from tkinter import Event

from collections.abc import Callable
from typing import Any

from CTkMenuBar import CTkMenuBar, CustomDropdownMenu

from views.media_player_frame import MediaPlayerFrame
from views.settings_frame import SettingsFrame


class MainFrame(ctk.CTkFrame):

    def __init__(self, master: Any, **kwargs):
        super().__init__(master=master, **kwargs)

        self.on_open_file: Callable[..., Any] | None = None
        self.on_exit: Callable[..., Any] | None = None
        self.on_open_frame_viewer: Callable[..., Any] | None = None
        self.on_show_about: Callable[..., Any] | None = None
        self.on_show_license: Callable[..., Any] | None = None
        self.on_show_third_party_licenses: Callable[..., Any] | None = None
        self.on_file_entry_submitted: Callable[..., Any] | None = None
        self.on_compress: Callable[..., Any] | None = None

        self._build_menubar()
        self._build()

    def _build_menubar(self) -> None:
        menubar = CTkMenuBar(self)

        file_btn = menubar.add_cascade("File")
        tools_btn = menubar.add_cascade("Tools")
        help_btn = menubar.add_cascade("Help")

        file_drop = CustomDropdownMenu(widget=file_btn)
        file_drop.add_option(option="Open", command=self._handle_open_file)
        file_drop.add_separator()
        file_drop.add_option(option="Exit", command=self._handle_exit)

        tools_drop = CustomDropdownMenu(widget=tools_btn)
        tools_drop.add_option(
            option="Frame Viewer",
            command=self._handle_open_frame_viewer,
        )

        help_drop = CustomDropdownMenu(widget=help_btn)
        help_drop.add_option(option="About", command=self._handle_show_about)
        help_drop.add_separator()
        help_drop.add_option(option="License", command=self._handle_show_license)
        help_drop.add_option(
            option="3rd Party Licenses",
            command=self._handle_show_third_party_licenses,
        )

    def _build(self) -> None:
        frame_color = ("gray78", "gray22")

        self._file_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=frame_color)
        self._file_frame.pack(padx=0, pady=0, fill="x", anchor="n")
        self._file_frame.columnconfigure(0, weight=1)

        self._file_entry = ctk.CTkEntry(self._file_frame, height=30)
        self._file_entry.bind("<Return>", self._handle_file_entry_submit)
        self._file_entry.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self._browse_btn = ctk.CTkButton(
            self._file_frame,
            text="Browse",
            command=self._handle_open_file,
        )
        self._browse_btn.grid(row=0, column=1, padx=10, pady=5)

        # Content Area - Video Preview left, Settings right
        self._content_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self._content_frame.pack(padx=0, pady=0, fill="both", anchor="center", expand=True)
        self._content_frame.columnconfigure(0, weight=1)
        self._content_frame.rowconfigure(0, weight=1)

        # Media player frame
        self._media_player_frame = MediaPlayerFrame(
            master=self._content_frame,
            corner_radius=0,
            fg_color="transparent",
        )
        self._media_player_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Settings frame
        self._settings_frame = SettingsFrame(
            self._content_frame, corner_radius=0, fg_color="transparent"
        )
        self._settings_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")

        self._compress_btn_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color=frame_color
        )
        self._compress_btn_frame.pack(padx=0, pady=0, fill="x", anchor="s")

        self._compress_btn = ctk.CTkButton(
            self._compress_btn_frame,
            width=150,
            height=35,
            text="Compress",
            state="disabled",
            command=self._handle_compress,
        )
        self._compress_btn.pack(padx=10, pady=10)

    def _handle_open_file(self) -> None:
        if self.on_open_file:
            self.on_open_file()

    def _handle_exit(self) -> None:
        if self.on_exit:
            self.on_exit()

    def _handle_compress(self) -> None:
        if self.on_compress:
            self.on_compress()

    def _handle_file_entry_submit(self, event: Event) -> None:
        if self.on_file_entry_submitted:
            item = event.widget.get().strip()

            self.on_file_entry_submitted(item)

    def _handle_open_frame_viewer(self) -> None:
        if self.on_open_frame_viewer:
            self.on_open_frame_viewer()

    def _handle_show_about(self) -> None:
        if self.on_show_about:
            self.on_show_about()

    def _handle_show_license(self) -> None:
        if self.on_show_license:
            self.on_show_license()

    def _handle_show_third_party_licenses(self) -> None:
        if self.on_show_third_party_licenses:
            self.on_show_third_party_licenses()

    @property
    def file_entry(self) -> str:
        return self._file_entry.get().strip()

    @file_entry.setter
    def file_entry(self, filepath: str) -> None:
        self._file_entry.delete(0, "end")
        self._file_entry.insert(0, filepath)

    @property
    def compress_btn_state(self) -> str:
        return self._compress_btn.cget("state")

    @compress_btn_state.setter
    def compress_btn_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._compress_btn.configure(state=state)

    @property
    def browse_btn_state(self) -> str:
        return self._browse_btn.cget("state")

    @browse_btn_state.setter
    def browse_btn_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._browse_btn.configure(state=state)

    @property
    def settings_frame(self) -> Any:
        return self._settings_frame

    @property
    def media_player_frame(self) -> Any:
        return self._media_player_frame
