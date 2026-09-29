import customtkinter as ctk
from tkinter import Event

from collections.abc import Callable
from typing import Any


class DownloaderView(ctk.CTkToplevel):
    def __init__(self, master: Any, **kwargs) -> None:
        super().__init__(master=master, **kwargs)

        self.title("YouTube Downloader")
        self.resizable(False, False)

        self.on_url_entry: Callable[[str], None] | None = None
        self.on_download: Callable[[str], None] | None = None
        self.on_container_change: Callable[[str], None] | None = None

        self._container = ctk.StringVar(self, value="mp4")
        self._error_msg = ctk.StringVar(self, value="")

        self._build()
        self._bind_entry()

        self.lift()
    
    def _build(self) -> None:
        """Builds and places all widgets and UI elements"""

        # YouTube Link entry  and warning label
        ctk.CTkLabel(
            master=self, 
            text="YouTube URL:"
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=(8,0),
            sticky="w",
        )

        self._url_entry = ctk.CTkEntry(
            master=self, 
            placeholder_text="Enter YouTube Link",
            width=500)
        self._url_entry.grid(
            row=0,
            column=1,
            columnspan=2,
            padx=8,
            pady=(8,0),
            sticky="ew"
        )

        self._error_label = ctk.CTkLabel(
            master=self, 
            textvariable=self._error_msg,
            font=ctk.CTkFont(size=11),
            text_color="red"
        )
        self._error_label.grid(
            row=1,
            column=1,
            padx=8,
            pady=4,
            sticky="w",
        )

        # File format
        ctk.CTkLabel(
            master=self, 
            text="Format:"
        ).grid(
            row=2,
            column=0,
            padx=8,
            pady=8,
            sticky="e"
        )

        self._container_dropdown = ctk.CTkComboBox(
            master=self,
            values=["mp4", "webm", "mkv", "mov"],
            state="readonly",
            command=self._handle_container_change,
            variable=self._container,
        )
        self._container_dropdown.grid(
            row=2, 
            column=1, 
            padx=8, 
            pady=8,
            sticky="w"
        )

        # Download button
        self._download_btn = ctk.CTkButton(
            master=self,
            text="Download",
            state="disabled",
            command=self._handle_download,   
        )
        self._download_btn.grid(
            row=2,
            column=2,
            padx=8,
            pady=8,
            sticky="e"
        )
    
    def _bind_entry(self) -> None:
        self._url_entry.bind(
            sequence="<Control-v>",
            command=lambda x: self.after(10, self._handle_url_entry, x),
            add="+"
        )
        self._url_entry.bind(
            sequence="<Return>",
            command=lambda x: self.after(10, self._handle_url_entry, x),
            add="+"
        )
        self._url_entry.bind(
            sequence="<BackSpace>",
            command=lambda x: self.after(10, self._handle_url_entry, x),
            add="+"
        )
        self._url_entry.bind(
            sequence="<KeyPress>",
            command=lambda x: self.after(10, self._handle_url_entry, x),
            add="+"
        )
        self._url_entry.bind(
            sequence="<Delete>",
            command=self._clear,
            add="+"
        )
        self._url_entry.bind(
            sequence="<Control-z>",
            command=self._clear,
            add="+"
        )
        self._url_entry.bind(
            sequence="<Control-y>",
            command=self._clear,
            add="+"
        )
    
    def _handle_url_entry(self, event: Event| None = None) -> None:
        if self.on_url_entry:
            url = self._url_entry.get().strip()

            self.on_url_entry(url)
    
    def _handle_download(self, event: Event | None = None) -> None:
        if self.on_download:
            url = self._url_entry.get().strip()

            self.on_download(url)
    
    def _handle_container_change(self, value:str) -> None:
        self._container.set(value)

        if self.on_container_change:
            self.on_container_change(value)
    
    def _clear(self, event: Event| None = None) -> None:
        self._url_entry.delete(0, ctk.END)

        self._error_msg.set("")
    
    @property
    def container(self) -> str:
        return self._container.get()

    @container.setter
    def container(self, value: str) -> None:
        self._container.set(value)

    @property
    def error_message(self) -> str:
        return self._error_msg.get()

    @error_message.setter
    def error_message(self, value: str) -> None:
        self._error_msg.set(value)
    
    @property
    def download_btn_state(self) -> str:
        return self._download_btn.cget("state")

    @download_btn_state.setter
    def download_btn_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._download_btn.configure(state=state)
