import customtkinter as ctk

class ProgressbarPopup(ctk.CTkToplevel):
  def __init__(self, master) -> None:
    super().__init__(master)
    self._master = master

    self.title("Compression in Progress")
    self.resizable(False, False)
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

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
                                                 command=self._master.cancel_compression)  

    self._cancel_compression_btn.pack(side="right", padx=10, pady=10)

    self.update_idletasks()
    master_x = self._master.winfo_x()
    master_y = self._master.winfo_y()
    master_w = self._master.winfo_width()
    master_h = self._master.winfo_height()
    popup_w = self.winfo_width()
    popup_h = self.winfo_height()
    x = master_x + (master_w - popup_w) // 2
    y = master_y + (master_h - popup_h) // 2
    self.geometry(f"+{x}+{y}")

    self.lift(self._master)
    self.attributes("-topmost", True)
    self.after(200, lambda: self.attributes("-topmost", False))
    self.grab_set()
    self.focus()

    # Cancels compression if progress bar is closed
    self.protocol("WM_DELETE_WINDOW", self._master.cancel_compression)
  
  def run_progressbar(self) -> None:
    self._progressbar.start()

  def destroy_window(self) -> None:
    self.destroy()