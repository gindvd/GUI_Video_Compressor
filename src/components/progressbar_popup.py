import customtkinter as ctk
from collections.abc import Callable

class ProgressbarPopup(ctk.CTkToplevel):
  def __init__(self, master, cmd: Callable) -> None:
    super().__init__(master)
    self._master = master

    self.title("Compression in Progress")
    self.resizable(False, False)

    self._btm_frame = ctk.CTkFrame(self, corner_radius=0)

    self._progressbar = ctk.CTkProgressBar(self._btm_frame,
                                           height=15,
                                           width=300,
                                           orientation='horizontal', 
                                           mode='indeterminate',
                                           determinate_speed=0.75)

    self._progressbar.pack(padx=30, pady=50)

    self._btm_frame.pack(expand=True, fill='both')
    
    self._cancel_compression_btn = ctk.CTkButton(self, 
                                                 text="Cancel", 
                                                 command=cmd)  

    self._cancel_compression_btn.pack(side="right", padx=10, pady=10)

    # Cancels compression if progress bar is closed
    self.protocol("WM_DELETE_WINDOW", cmd)
  
  def run_progressbar(self) -> None:
    self._progressbar.start()

  def destroy_window(self) -> None:
    self.destroy()