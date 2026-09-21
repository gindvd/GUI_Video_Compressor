import customtkinter as ctk

from collections.abc import Callable
from typing import Any


class ProgressbarPopup(ctk.CTkToplevel):
    """Pop up for displaying progress bar while background task is preformed"""

    def __init__(self, master: Any, command: Callable[..., Any], **kwargs) -> None:
        super().__init__(master, **kwargs)

        self.title("Compression in Progress")
        self.resizable(False, False)

        self._bar_frame = ctk.CTkFrame(self, corner_radius=0)

        self._progressbar = ctk.CTkProgressBar(
            self._bar_frame,
            height=15,
            width=300,
            orientation="horizontal",
            mode="indeterminate",
            determinate_speed=0.75,
        )

        self._progressbar.pack(padx=30, pady=50)

        self._bar_frame.pack(expand=True, fill="both")

        self._cancel_btn = ctk.CTkButton(self, text="Cancel", command=command)

        self._cancel_btn.pack(side="right", padx=10, pady=10)

        # Cancels compression if progress bar is closed
        self.protocol("WM_DELETE_WINDOW", command)

    def run_progressbar(self) -> None:
        """Starts the progression bar"""
        self._progressbar.start()
        
        self.lift()
        self.update_idletasks() 

    def destroy_window(self) -> None:
        """Destroys the popup window"""
        self._progressbar.stop()
        self.destroy()
