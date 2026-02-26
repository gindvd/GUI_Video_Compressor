import customtkinter as ctk
from tkVideoPlayer import TkinterVideo as TkV

class VideoPlayer(ctk.CTkFrame):
  def __init__(self):
    super().__init__()

    self["bg"] = 'black'
    
    self.video_file = ""
    self.video_player = TkV(master=self, scaled=True, keep_aspect=True, 
                            consistent_frame_rate=True,  bg="black")
    
    self.video_player.set_resampling_method(1)
    self.video_player.pack(expand=True, fill=both, padx=10, pady=10)
    self.video_player.bind("<<Duration>>", self.update_duration)
    self.video_player.bind("<<SecondChanged>>", self.update_scale)
    self.video_player.bind("<<Ended>>", self.video_ended)
    
    self.progress_slider = ctk.CTkSlider(master=self, from_=-1, to=1, number+of+steps=1, command=self.seek)