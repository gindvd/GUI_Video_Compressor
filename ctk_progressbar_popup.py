import customtkinter as ctk

class ProgressbarPopup(ctk.CTkToplevel):
  def __init__(self, parent):
    super().__init__(parent)
    self._parent = parent

    self.title("Progress Bar")
    self.resizable(False, False)

    self.lift()
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._progressbar = ctk.CTkProgressBar(self,
                                           orientation='horizontal', 
                                           mode='indeterminate',
                                           determinate_speed=0.75)

    self._progressbar.grid(row=0, column=0, columnspan=3, padx=50, pady=50)
  
  def run_progressbar(self):
    self.progressbar.start()

  def destroy_window(self):
    self.destroy()