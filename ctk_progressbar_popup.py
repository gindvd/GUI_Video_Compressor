import customtkinter as ctk

class ProgressbarPopup(ctk.CTK):
  def __init__(self):
    self.title("Progress Bar")
    self.resizable(False, False)
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self.progressbar = ctk.CTkProgressBar(self, 
                                          orientation='horizontal', 
                                          mode='indeterminate')

    self.progressbar.pack(padx=10, pady=10)

  def start(self):
    self.progressbar.start()

  def destroy(self):
    self.quit()