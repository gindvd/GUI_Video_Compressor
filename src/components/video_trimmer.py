import tkinter as tk
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

import vlc
from os import PathLike

from utils import DEVICE_OS
from CTkTrimSlider.ctk_trimslider import CTkTrimSlider

class VideoTrimmer(ctk.CTkFrame):
  def __init__(self, parent, vlc_cmd: PathLike | str) -> None:
    super().__init__(parent, corner_radius=0)
    self._parent = parent
    self._vlc_cmd = vlc_cmd
    
    self.duration_ms: int  = 0
    
    self._start_time: tk.Variable = tk.DoubleVar(self, value=0)
    self._end_time: tk.Variable = tk.DoubleVar(self, value=1)
    self._current_time: tk.Variable = tk.DoubleVar(self, value=0.5)

    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._instance: vlc.Instance = self._platform_specific_inst()
    self._instance.log_unset()
    self._vid_player = self._instance.media_player_new()

    self._vid_panel = ctk.CTkFrame(self, width=800, height=400, fg_color="black", corner_radius=0)
    self._vid_panel.pack(fill='both', expand=True, padx=5, pady=10)

    self._control_panel  = ctk.CTkFrame(self, corner_radius=0)
    self._control_panel.pack(fill='x', padx=5)

    self._create_control_panel()

    self._time_panel = ctk.CTkFrame(self, corner_radius=0)
    self._time_panel.pack(fill='x', padx=5, pady=(0,5))

    self._create_time_panel()

  def _platform_specific_inst(self):
    if DEVICE_OS == "Windows":
        return vlc.Instance(f"--plugin-path={self._vlc_cmd}")

    return vlc.Instance("--no-xlib")
  
  def _create_control_panel(self) -> None:
    self._play_pause_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=60,
                                                        height=30,
                                                        text="Play",
                                                        state="disabled",
                                                        command=self._play_pause)

    self._play_pause_btn.grid(row=0, column=0, padx=10, pady=5, sticky="nswe")

    self._trim_slider = CTkTrimSlider(self._control_panel, 
                                      width=600, 
                                      state="disabled", 
                                      start_variable=self._start_time, 
                                      end_variable=self._end_time, 
                                      center_variable=self._current_time)

    self._trim_slider.grid(row=0, column=1, padx=10, pady=5, sticky="nswe")

    self._curtime_lbl: ctk.CTkLabel = ctk.CTkLabel(self._control_panel, text="00:00:00.000")
    self._curtime_lbl.grid(row=0, column=2, padx=10, pady=5, sticky="nswe")

  def _create_time_panel(self) -> None:
    ctk.CTkLabel(self._time_panel, text="Video Duration:").grid(row=0, column=0, padx=10, pady=5)

    self._dur_lbl: ctk.CTkLabel = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._dur_lbl.grid(row=0, column=1, padx=10, pady=5)

  def _play_pause(self) -> None:
    playing = self._vid_player.is_playing()

    if not playing:
      self._vid_player.play()
      self._play_pause_btn.configure(text='Pause')
    
    elif playing:
      self._vid_player.pause()
      self._play_pause_btn.configure(text="Play")

  def _display_video(self) -> None:
    if DEVICE_OS == "Linux":
      self._vid_player.set_xwindow(self._vid_panel.winfo_id())
    elif DEVICE_OS == "Windows":
      self._vid_player.set_hwnd(self._vid_panel.winfo_id())

  def _update_progress(self):
    current_time_ms = self._vid_player.get_time()
    current_time = self._ms_text_converter(current_time_ms)

    self._curtime_lbl.configure(text=current_time)
    self.after(100, self._update_progress)

  def set_vid_values(self, duration: float) -> None:
    self.duration_ms = int(duration * 1000)
    self.end_time_ms = self.duration_ms

    self._dur_lbl.configure(text=self._ms_text_converter(self.duration_ms))

  def set_video(self, vid_file: PathLike | str) -> None:
    self.update()

    video = self._instance.media_new(vid_file)
    self._vid_player.set_media(video)

    self._display_video()

    self._play_pause_btn.configure(state="normal")

    self._play_pause()
    self.after(100, self._play_pause)

    self._update_progress()
  
  def get_start_time(self) -> str:
    return self._ms_text_converter(self.start_time_ms)
  
  def get_duration(self) -> str:
    return self._ms_text_converter(self.duration_ms)

  @staticmethod
  def _ms_text_converter(ms: int) -> str:
    s = ms // 1000
    ms_remainder = ms % 1000

    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)

    return f"{h:02d}:{m:02d}:{sec:02d}.{ms_remainder:03d}"