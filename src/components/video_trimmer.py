import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

import vlc
import platform
import shutil

from datetime import time

class VideoTrimmer(ctk.CTkFrame):
  def __init__(self, parent):
    super().__init__(parent, corner_radius=0)
    self._parent = parent

    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._instance = self._platform_specific_inst()
    self._instance.log_unset()
    self._vid_player = self._instance.media_player_new()

    self._vid_panel = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
    self._vid_panel.pack(fill='both', expand=True, padx=5, pady=10)

    self._control_panel = ctk.CTkFrame(self, corner_radius=0)
    self._control_panel.pack(fill='x', padx=5)

    self._create_control_panel()

    self._time_panel = ctk.CTkFrame(self, corner_radius=0)
    self._time_panel.pack(fill='x', padx=5, pady=(0,5))

    self._create_time_panel()

  def _platform_specific_inst(self):

    if platform.system() == "Windows":

      try:
        vlc_path = os.path.abspath("lib/win32/vlc-win32.exe")

      except FileNotFoundError:
        close = CTkMessagebox(title="Missing VLC Exe", 
                              message="vlc-win32.exe is missing from lib/win32 folder!", 
                              icon="cancel",
                              option_1="Ok")
        
        if close.get() == "Ok":
          self.destroy()
        
    
      else:
        return vlc.Instance("--plugin-path={}".format(vlc_path))
    
    else:
      if not shutil.which("vlc"):
          close = CTkMessagebox(title="Missing VLC", 
                              message="VLC not a recognized command!", 
                              icon="cancel",
                              option_1="Ok")
        
          if close.get() == "Ok":
            self.destroy()

      return vlc.Instance("--no-xlib")
      
  def _create_control_panel(self):
    self._play_pause_btn = ctk.CTkButton(self._control_panel, 
                                         text="Play",
                                         state="disabled",
                                         command=self._play_pause)

    self._play_pause_btn.pack(padx=5, pady=5)

  def _create_time_panel(self):
    ctk.CTkLabel(self._time_panel, text="Video Duration:").grid(row=0, column=0, padx=10, pady=5)

    self._dur_lbl = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._dur_lbl.grid(row=0, column=1, padx=10, pady=5)

    ctk.CTkLabel(self._time_panel, text="Current Time:").grid(row=0, column=2, padx=10, pady=5)

    self._curtime_lbl = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._curtime_lbl.grid(row=0, column=3, padx=10, pady=5)
  
  def set_duration(self, duration):
    vid_dur_ms = duration[:duration.find('.')+4]
    self._dur_lbl.configure(text=vid_dur_ms)

  def _play_pause(self):
    playing = self._vid_player.is_playing()

    if not playing:
      self._vid_player.play()
      self._play_pause_btn.configure(text='Pause')
    
    elif playing:
      self._vid_player.pause()
      self._play_pause_btn.configure(text="Play")
  
  def set_video(self, vid_file):
    self.update()

    video = self._instance.media_new(vid_file)
    self._vid_player.set_media(video)

    self._display_video()

    self._play_pause_btn.configure(state="normal")

    self._play_pause()
    self.after(50, self._play_pause)

    self._update_progress()

  def _display_video(self):
    if platform.system() == "Linux":
      self._vid_player.set_xwindow(self._vid_panel.winfo_id())
    elif platform.system() == "Windows":
      self._vid_player.set_hwnd(self._vid_panel.winfo_id())

  def _update_progress(self):
    current_time_ms = self._vid_player.get_time()
    current_time = self._ms_to_isoformat(current_time_ms)

    self._curtime_lbl.configure(text=current_time)
    self.after(100, self._update_progress)

  @staticmethod
  def _ms_to_isoformat(ms):
    seconds = ms // 1000
    ms_remainder = ms % 1000

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms_remainder:03d}"