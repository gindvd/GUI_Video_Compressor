import customtkinter as ctk

class ProgressbarPopup(ctk.CTkToplevel):
  def __init__(self, parent):
    super().__init__(parent)

    self.title("Progress Bar")
    self.resizable(False, False)

    self.lift()
    self.attributes("-topmost", True)
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self.progressbar = ctk.CTkProgressBar(self,
                                          orientation='horizontal', 
                                          mode='indeterminate',
                                          determinate_speed=0.75)

    self.progressbar.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
  
    self.progressbar.start()

  def destroy_window(self):
    self.destroy()