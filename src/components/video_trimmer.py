from tkinter import Variable, DoubleVar
import customtkinter as ctk

import vlc
from os import PathLike

from utils import DEVICE_OS
from CTkTrimSlider import CTkTrimSlider

class VideoTrimmer(ctk.CTkFrame):
  def __init__(self, master, vlc_cmd: PathLike | str) -> None:
    super().__init__(master=master, corner_radius=0)
    self._vlc_cmd = vlc_cmd
    
    self._duration: int = 0

    self._media: vlc.Media | None = None
    self._update_id: str | None = None
    self._is_seeking: bool = False
    self._seek_reset_id: str | None = None
    self._is_muted: bool = False
    
    self._start_time: Variable = DoubleVar(self, value=0)
    self._end_time: Variable = DoubleVar(self, value=1)
    self._current_time: Variable = DoubleVar(self, value=0.5)

    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._instance: vlc.Instance = self._platform_specific_inst()
    self._instance.log_unset()
    self._vid_player = self._instance.media_player_new()

    self._vid_panel = ctk.CTkFrame(self, width=750, height=400, fg_color="black", corner_radius=0)
    self._vid_panel.pack(fill='both', expand=True)

    self._control_panel = ctk.CTkFrame(self, width=750, corner_radius=0)
    self._control_panel.pack(fill='both', expand=True)

    self._create_control_panel()

    self._time_panel = ctk.CTkFrame(self, width=750, corner_radius=0)
    self._time_panel.pack(fill='both', expand=True)

    self._create_time_panel()

  def _platform_specific_inst(self):
    if DEVICE_OS == "Windows":
        return vlc.Instance(["--quiet","--verbose=0", "--aout=directsound", f"--plugin-path={self._vlc_cmd}"])

    return vlc.Instance(["--quiet","--verbose=0", "--aout=pulse", "--no-xlib"])
  
  def _create_control_panel(self) -> None:
    self._play_pause_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=65,
                                                        height=30,
                                                        text="Play",
                                                        state="disabled",
                                                        command=self._play_pause)

    self._play_pause_btn.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

    self._trim_slider = CTkTrimSlider(self._control_panel, 
                                      width=500, 
                                      state="disabled",
                                      left_button_command=self._set_start_time,
                                      right_button_command=self._set_end_time,
                                      center_button_command=self._seek,
                                      left_button_var=self._start_time, 
                                      right_button_var=self._end_time,
                                      center_button_var=self._current_time)

    self._trim_slider.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")

    self._curtime_lbl: ctk.CTkLabel = ctk.CTkLabel(self._control_panel, text="00:00:00.000")
    self._curtime_lbl.grid(row=0, column=2, padx=10, pady=10, sticky="nswe")

    self._volume_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                    width=50,
                                                    height=30,
                                                    text="Mute",
                                                    state="disabled",
                                                    command=self._toggle_mute)

    self._volume_btn.grid(row=0, column=3, padx=10, pady=10, sticky="nswe")

    self._vol_popup = ctk.CTkFrame(self, corner_radius=8)
    self._vol_popup_visible: bool = False
    self._vol_hide_id: str | None = None

    self._volume_slider: ctk.CTkSlider = ctk.CTkSlider(self._vol_popup,
                                                       height=120,
                                                       width=20,
                                                       from_=0,
                                                       to=100,
                                                       number_of_steps=100,
                                                       state="disabled",
                                                       orientation="vertical",
                                                       command=self._set_volume)
    self._volume_slider.set(100)
    self._volume_slider.pack(padx=6, pady=8)

    self._volume_btn.bind("<Enter>", self._show_vol_popup)
    self._volume_btn.bind("<Leave>", self._schedule_hide_vol_popup)
    self._vol_popup.bind("<Enter>", self._cancel_hide_vol_popup)
    self._vol_popup.bind("<Leave>", self._schedule_hide_vol_popup)
    self._volume_slider.bind("<Enter>", self._cancel_hide_vol_popup)
    self._volume_slider.bind("<Leave>", self._schedule_hide_vol_popup)

  def _create_time_panel(self) -> None:
    ctk.CTkLabel(self._time_panel, text="New Duration:").grid(row=0, column=0, padx=10, pady=5, sticky="nswe")

    self._current_duration_lbl: ctk.CTkLabel = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._current_duration_lbl.grid(row=0, column=1, padx=10, pady=5, sticky="nswe")

    ctk.CTkLabel(self._time_panel, text="Video Duration:").grid(row=0, column=2, padx=10, pady=5, sticky="nswe")

    self._duration_lbl: ctk.CTkLabel = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._duration_lbl.grid(row=0, column=3, padx=10, pady=5, sticky="nswe")

  def _play_pause(self) -> None:
    state = self._vid_player.get_state()

    if state == vlc.State.Ended:
      self._restart_media(int(self._start_time.get()))
      return

    if self._vid_player.is_playing():
      self._vid_player.pause()
      self._play_pause_btn.configure(text="Play")
    else:
      current_ms = self._vid_player.get_time()
      end_ms = int(self._end_time.get())
      if current_ms >= end_ms:
        start_ms = int(self._start_time.get())
        self._vid_player.set_time(start_ms)
        self._current_time.set(start_ms)
        self._curtime_lbl.configure(text=self._ms_text_converter(start_ms))
      self._vid_player.play()
      self._play_pause_btn.configure(text='Pause')

  def _display_video(self) -> None:
    if DEVICE_OS == "Linux":
      self._vid_player.set_xwindow(self._vid_panel.winfo_id())
    elif DEVICE_OS == "Windows":
      self._vid_player.set_hwnd(self._vid_panel.winfo_id())

  def _update_progress(self):
    state = self._vid_player.get_state()

    if state == vlc.State.Playing and not self._is_seeking:
      current_time_ms = self._vid_player.get_time()
      end_time_ms = int(self._end_time.get())

      if current_time_ms >= end_time_ms:
        self._vid_player.pause()
        self._vid_player.set_time(end_time_ms)
        self._play_pause_btn.configure(text="Play")
        current_time_ms = end_time_ms

      self._current_time.set(current_time_ms)
      self._curtime_lbl.configure(text=self._ms_text_converter(current_time_ms))

    elif state == vlc.State.Ended:
      end_time_ms = int(self._end_time.get())
      self._current_time.set(end_time_ms)
      self._curtime_lbl.configure(text=self._ms_text_converter(end_time_ms))
      self._play_pause_btn.configure(text="Play")

    self._update_id = self.after(33, self._update_progress)
  
  def _seek(self, value):
    self._is_seeking = True
    target = int(value)

    state = self._vid_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)
    else:
      self._vid_player.set_time(target)

    self._curtime_lbl.configure(text=self._ms_text_converter(target))
    self._schedule_seek_reset()
  
  def _set_start_time(self, value):
    self._is_seeking = True
    target = int(value)
    self._current_time.set(target)

    state = self._vid_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)
    else:
      self._vid_player.set_time(target)

    self._curtime_lbl.configure(text=self._ms_text_converter(target))
    self._schedule_seek_reset()

    new_duration = int(self._end_time.get()) - target
    self._current_duration_lbl.configure(text=self._ms_text_converter(new_duration))

  def _set_end_time(self, value):
    self._is_seeking = True
    target = int(value)
    self._current_time.set(target)

    state = self._vid_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)
    else:
      self._vid_player.set_time(target)
    
    self._curtime_lbl.configure(text=self._ms_text_converter(target))
    self._schedule_seek_reset()

    new_duration = target - int(self._start_time.get())
    self._current_duration_lbl.configure(text=self._ms_text_converter(new_duration))
  
  def _schedule_seek_reset(self) -> None:
    if self._seek_reset_id is not None:
      self.after_cancel(self._seek_reset_id)
    self._seek_reset_id = self.after(150, self._reset_seeking)

  def _reset_seeking(self) -> None:
    self._is_seeking = False
    self._seek_reset_id = None

  def set_vid_values(self, duration: float) -> None:
    self._duration = int(duration * 1000)
    self._trim_slider.configure(require_redraw=True, to=self._duration, number_of_steps=self._duration, state="normal")

    self._start_time.set(0)
    self._current_time.set(0)
    self._end_time.set(self._duration)
    

    self._current_duration_lbl.configure(text=self._ms_text_converter(self._duration))
    self._duration_lbl.configure(text=self._ms_text_converter(self._duration)) 

  def set_video(self, vid_file: PathLike | str) -> None:
    if self._update_id is not None:
      self.after_cancel(self._update_id)
      self._update_id = None

    self._vid_player.stop()
    
    # unloads old media files before loading new media
    if self._media is not None:
      self._media.release()
      self._media = None
    
    self._vid_player.release()
    
    self._vid_player = self._instance.media_player_new()
    self._media = self._instance.media_new(vid_file)
    self._vid_player.set_media(self._media)

    self._display_video()

    self._set_volume(100)
    self._is_muted = False
    self._vid_player.audio_set_mute(self._is_muted)

    self._play_pause_btn.configure(state="normal")
    self._volume_btn.configure(state="normal")
    self._volume_slider.configure(state="normal")

    self._vid_player.play()
    self._play_pause_btn.configure(text="Pause")
    self.after(200, self._pause_initial_frame)

    self._update_progress()

  def _pause_initial_frame(self) -> None:
    if self._vid_player.is_playing():
      self._vid_player.pause()
      self._vid_player.set_time(0)
      self._play_pause_btn.configure(text="Play")
      self._current_time.set(0)
      self._curtime_lbl.configure(text="00:00:00.000")

  def _restart_media(self, seek_ms: int, paused: bool = False) -> None:
    self._vid_player.set_media(self._media)
    self._display_video()
    self._vid_player.play()
    if paused:
      self.after(100, lambda: self._seek_and_pause(seek_ms))
    else:
      self.after(100, lambda: self._vid_player.set_time(seek_ms))
      self._play_pause_btn.configure(text='Pause')

  def _seek_and_pause(self, seek_ms: int, retries: int = 10) -> None:
    state = self._vid_player.get_state()
    if state not in (vlc.State.Playing, vlc.State.Paused):
      if retries > 0:
        self.after(50, lambda: self._seek_and_pause(seek_ms, retries - 1))
      return
    self._vid_player.set_time(seek_ms)
    self._vid_player.pause()
    self._play_pause_btn.configure(text="Play")
    self._current_time.set(seek_ms)
    self._curtime_lbl.configure(text=self._ms_text_converter(seek_ms))

  def _toggle_mute(self) -> None:
    self._is_muted = not self._is_muted
    self._vid_player.audio_set_mute(self._is_muted)

    if self._is_muted:
      self._volume_btn.configure(text="Unmute")
      self._volume_slider.set(0)
    else:
      self._volume_btn.configure(text="Mute")
      self._volume_slider.set(10)
      self._set_volume(10)

  def _set_volume(self, value: int) -> None:
    volume = int(value)
    self._vid_player.audio_set_volume(volume)
    if volume == 0 and not self._is_muted:
      self._is_muted = True
      self._vid_player.audio_set_mute(True)
      self._volume_btn.configure(text="Unmute")
    elif volume > 0 and self._is_muted:
      self._is_muted = False
      self._vid_player.audio_set_mute(False)
      self._volume_btn.configure(text="Mute")

  def _show_vol_popup(self, event=None) -> None:
    if self._vol_hide_id is not None:
      self.after_cancel(self._vol_hide_id)
      self._vol_hide_id = None

    if self._vol_popup_visible:
      return

    self._volume_btn.update_idletasks()
    btn_x = self._volume_btn.winfo_rootx() - self.winfo_rootx()
    btn_y = self._volume_btn.winfo_rooty() - self.winfo_rooty()
    btn_w = self._volume_btn.winfo_width()
    popup_w = self._vol_popup.winfo_reqwidth()

    x = btn_x + (btn_w - popup_w) // 2
    y = btn_y - self._vol_popup.winfo_reqheight() - 4

    self._vol_popup.place(x=x, y=y)
    self._vol_popup.lift()
    self._vol_popup_visible = True

  def _schedule_hide_vol_popup(self, event=None) -> None:
    if self._vol_hide_id is not None:
      self.after_cancel(self._vol_hide_id)
    self._vol_hide_id = self.after(300, self._hide_vol_popup)

  def _cancel_hide_vol_popup(self, event=None) -> None:
    if self._vol_hide_id is not None:
      self.after_cancel(self._vol_hide_id)
      self._vol_hide_id = None

  def _hide_vol_popup(self) -> None:
    self._vol_popup.place_forget()
    self._vol_popup_visible = False
    self._vol_hide_id = None

  def release(self) -> None:
    if self._update_id is not None:
      self.after_cancel(self._update_id)
      self._update_id = None

    if self._seek_reset_id is not None:
      self.after_cancel(self._seek_reset_id)
      self._seek_reset_id = None

    self._vid_player.stop()
    self._vid_player.release()
    self._instance.release()

  @property
  def start_time_ms(self) -> int:
    return int(self._start_time.get())

  @property
  def duration_ms(self) -> int:
    return int(self._end_time.get()) - int(self._start_time.get())
  
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