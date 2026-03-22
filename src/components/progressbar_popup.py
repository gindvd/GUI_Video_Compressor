import customtkinter as ctk

class ProgressbarPopup(ctk.CTkToplevel):
  def __init__(self, parent: object):
    super().__init__(parent)
    self._parent: object = parent

    self.title("Compression in Progress")
    self.resizable(False, False)

    self.lift()
    
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
                                                 command=self._parent.cancel_compression)  

    self._cancel_compression_btn.pack(side="right", padx=10, pady=10)

    
  
  def run_progressbar(self):
    self._progressbar.start()

  def destroy_window(self):
    self.destroy()