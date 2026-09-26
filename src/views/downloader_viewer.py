import customtkinter as ctk
from tkinter import Event

from collections.abc import Callable
from typing import Any

class DownloadViewer(ctk.CTkToplevel):
    def __init__(self, master: Any, **kwargs) -> None:
        super().__init__(master=master, **kwargs)

        self.title("YouTube Downloader")
        self.minsize(400, 150)
        self.resizable(True, True)

        self.on_url_entry: Callable[[], None] | None = None
        self.on_download: Callable[..., None] | None = None
        self.on_container_change: Callable[str, None] | None = None

        self._container = ctk.StringVar(self, value="mp4")

        self._build()
    
    def _build(self) -> None:
        """Builds and places all widgets and UI elements"""
        fg_color = ("gray75", "gray25")
        font = ctk.CTkFont(size=14, weight="bold")

        self._url_entry = ctk.CTkEntry(self)

        self._url_entry.bind(
            sequence="<Control-V>",
            command=self._handle_url_entry,
            add="+"
        )
        self._url_entry.bind(
            sequence="<Return>",
            command=self._handle_url_entry,
            add="+"
        )

        self._url_entry.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky="ew"
        )

        self._download_btn = ctk.CTkButton(
            self,
            text="Download",
            state="disabled",
            command=self._handle_download,   
        )
        self._download_btn.grid(
            row=0,
            column=1,
            padx=10,
            pady=10
        )

        ctk.CTkLabel(self, text="Format:").grid(
            row=1,
            column=0,
            padx=10,
            pady=10,
            sticky="w",
        )

        self._container_dropdown = ctk.CTkComboBox(
            self,
            values=["mp4", "webm", "mkv", "mov"],
            state="readonly",
            command=self._handle_container_change,
            variable=self._container,
        )
        self._container_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    
    def _handle_url_entry(self, event: Event) -> None:
        if self.on_url_entry:
            url = self._url_entry.get().strip()

            self.on_url_entry(url)
    
    def _handle_download(self, event: Event) -> None:
        if self.on_download:
            url = self._url_entry.get().strip()

            self.on_download(url)
    
    def _handle_container_change(self, value:str) -> None:
        self._container.set(value)
    
    @property
    def container(self) -> str:
        return self._container.get()

    @container.setter
    def container(self, value: str) -> None:
        self._container.set(value)
    
    @property
    def download_btn_state(self) -> str:
        return self._downloads_btn.cget("state")

    @download_btn_state.setter
    def download_btn_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._download_btn.configure(state=state)
