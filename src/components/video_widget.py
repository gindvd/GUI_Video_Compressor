import customtkinter as ctk
from tkVideoPlayer import TkinterVideo 
from CTkMessagebox import CTkMessagebox

class VideoPlayer(ctk.CTkFrame):
  def __init__(self):
    super().__init__()
    
    ctk.set_appearance_mode("System")
    stk.set_default_color_theme("blue")
    
    self._vid_file = ""
    
    self._vid_player = TkinterVideo(self, 
                                    scaled=True, 
                                    keep_aspect=True, 
                                    consistent_frame_rate=True,  
                                    bg="black")
    
    self._vid_player.set_resampling_method(1)
    self._vid_player.pack(expand=True, fill=both, padx=10, pady=10)
    self._vid_player.bind("<<Duration>>", self._update_dur)
    self._vid_player.bind("<<SecondChanged>>", self._update_scale)
    self._vid_player.bind("<<Ended>>", self._vid_ended)
    
    self._play_pause_btn = ctk.CTkButton(self, text="Play", command=self._play_pause)
    self._play_pause_btn.pack(padx=10, pady=10)
    
    
  def load_video(self, filename):
    self._vid_file = filename 
    self._vid_player.stop()
    
    try:
      self._vid_player.load(self._vid_file)
    
    except:
      CTkMessagebox(title="Loading Failure", 
                    message="ERROR!\nVideo file couldn't be opened!", 
                    icon="cancel")

  def _play_pause(self):
    if self._vid_file != "":
      if self._vid_player.is_paused():
        self._vid_player.play()
        self._play_pause_btn.configure(text="Pause")
        
      else:
        self._vid_player.pause()
        self._play_pause_btn.configure(text="Play")

  def _update_dur(self):
    pass
    
  def _update_scale(self):
    pass
    
  def _vid_ended(slef):
    pass