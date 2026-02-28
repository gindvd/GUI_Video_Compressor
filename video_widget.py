import customtkinter as ctk
from tkVideoPlayer import TkinterVideo as TkV

class VideoPlayer(ctk.CTkFrame):
  def __init__(self):
    super().__init__()

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    self.video_file = ""
    self.duration = 0
    self.start_time = -1
    self.end_time = 1
    self.currrent_time = 0
    self.new_duration = 0
    
    self.video_player = TkinterVideo(self, scaled=True, keep_aspect=True, 
                            consistent_frame_rate=True,  bg="black")
    
    self.video_player.set_resampling_method(1)
    self.video_player.pack(expand=True, fill=both, padx=10, pady=10)
    self.video_player.bind("<<Duration>>", self.update_duration)
    self.video_player.bind("<<SecondChanged>>", self.update_scale)
    self.video_player.bind("<<Ended>>", self.video_ended)
    
    self.play_pause_btn = ctk.CTkButton(self, text="Play", command=self.play_pause)
    self.play_pause_btn.pack(padx=10, pady=10)
    
  def load_video(self, filename):
    self.video_file = filename 
    self.video_player.stop()
    
    try:
      self.video_player.load(self.video_file)
      
      self.duration = int(self.video_player.video_info()["duration"])
      self.end_time = int(self.video_player.video_info()["duration"])
      
         
    except:
      CTkMessagebox(title="Loading Failure", message="ERROR!\nMVideo file couldn't be opened!", 
                    icon="error")