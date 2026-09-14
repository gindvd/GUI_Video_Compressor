import customtkinter as ctk
from collections.abc import Callable
from typing import Any


class ProgressbarPopup(ctk.CTkToplevel):
    """Pop up for displaying progress bar while background task is preformed"""

    def __init__(self, master: Any, cmd: Callable[..., Any]) -> None:
        super().__init__(master)

        self.title("Compression in Progress")
        self.resizable(False, False)

        self._btn_frame = ctk.CTkFrame(self, corner_radius=0)

        self._progressbar = ctk.CTkProgressBar(
            self._btn_frame,
            height=15,
            width=300,
            orientation="horizontal",
            mode="indeterminate",
            determinate_speed=0.75,
        )

        self._progressbar.pack(padx=30, pady=50)

        self._btn_frame.pack(expand=True, fill="both")

        self._cancel_compression_btn = ctk.CTkButton(self, text="Cancel", command=cmd)

        self._cancel_compression_btn.pack(side="right", padx=10, pady=10)

        # Cancels compression if progress bar is closed
        self.protocol("WM_DELETE_WINDOW", cmd)

    def run_progressbar(self) -> None:
        """Starts the progression bar"""
        self._progressbar.start()

    def destroy_window(self) -> None:
        """Destroys the popup window"""
        self.destroy()
