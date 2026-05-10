import customtkinter as ctk
from tkinter import DoubleVar
from CTkMessagebox import CTkMessagebox
from CTkTrimSlider import CTkTrimSlider
from customtkinter import filedialog

import vlc
import os
from threading import Thread, Event
from PIL import Image

from utils.log_utils import logger
from utils.path_utils import get_button_image_path

class VideoTrimmer(ctk.CTkFrame):
  def __init__(self, master, vlc_cmd: os.PathLike | str, device_os: str, **kwargs) -> None:
    super().__init__(master=master, **kwargs)
    self._vlc_cmd: os.PathLike | str = vlc_cmd
    self._device_os: str = device_os

    self._media: vlc.Media | None = None
    self._is_loading: bool = False
    self._load_request: int = 0

    self._update_id: str | None = None
    self._is_seeking: bool = False
    self._seek_reset_id: str | None = None
    
    self._start_time: DoubleVar = DoubleVar(self, value=0)
    self._end_time: DoubleVar = DoubleVar(self, value=1)
    self._current_time: DoubleVar = DoubleVar(self, value=0.5)

    self._vol_hide_id: str | None = None
    self._vol_popup_visible: bool = False
    self._is_muted: bool = False
    self._volume: int = 0

    self._instance: vlc.Instance | None = None
    self._media_player: vlc.MediaPlayer | None = None

    self._play_photo: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("play_button.png")),
                                                  dark_image=Image.open(get_button_image_path("play_button.png")),
                                                  size=(18,18))
    self._pause_photo: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("pause_button.png")),
                                                   dark_image=Image.open(get_button_image_path("pause_button.png")),
                                                   size=(18,18))
    self._reverse_photo: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("reverse.png")),
                                                     dark_image=Image.open(get_button_image_path("reverse.png")),
                                                     size=(18,18))
    self._forward_photo: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("forward.png")),
                                                     dark_image=Image.open(get_button_image_path("forward.png")),
                                                     size=(18,18))
    self._mute_photo: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("muted_volume.png")),
                                                  dark_image=Image.open(get_button_image_path("muted_volume.png")),
                                                  size=(18,18))
    self._unmute_photo: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("unmuted_volume.png")),
                                                    dark_image=Image.open(get_button_image_path("unmuted_volume.png")),
                                                    size=(18,18))
    self._camera_photo: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("camera.png")),
                                                    dark_image=Image.open(get_button_image_path("camera.png")),
                                                    size=(24,24))

    self._create_ui()

  def _ensure_vlc_initialized(self) -> None:
    if self._instance is not None:
      return

    self._instance = self._platform_specific_inst()
    self._instance.log_unset()
    self._media_player = self._instance.media_player_new()

  def _platform_specific_inst(self):
    if self._device_os == "Windows":
        return vlc.Instance(["--quiet",
                             "--verbose=0", 
                             "--aout=directsound", 
                             f"--plugin-path={self._vlc_cmd}"])

    return vlc.Instance(["--quiet",
                        "--verbose=0", 
                        "--aout=pulse", 
                        "--no-xlib"])
  
  def _create_ui(self) -> None:
    self._media_viewer = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
    self._media_viewer.pack(padx=10, pady=(10, 5), fill='both', expand=True)

    self._control_panel = ctk.CTkFrame(self, width=750, fg_color=("gray75", "gray25"), corner_radius=6)
    self._control_panel.pack(padx=10, pady=0, fill='x')
    self._create_controls()

    self._time_panel = ctk.CTkFrame(self, width=750, fg_color=("gray75", "gray25"), corner_radius=6)
    self._time_panel.pack(padx=10, pady=5, fill='x')
    self._create_time_labels()
  
  def _create_controls(self) -> None:
    self._control_panel.columnconfigure(3, weight=3)

    self._play_pause_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=30,
                                                        height=30,
                                                        fg_color="transparent",
                                                        image=self._play_photo,
                                                        text="",
                                                        state="disabled",
                                                        command=self._play_pause)

    self._play_pause_btn.grid(row=0, column=0, padx=(10, 5), pady=5)

    self._reverse_10s_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=30,
                                                        height=30,
                                                        fg_color="transparent",
                                                        image=self._reverse_photo,
                                                        text="",
                                                        state="disabled",
                                                        command=self._reverse_10_seconds)

    self._reverse_10s_btn.grid(row=0, column=1, padx=5, pady=5)

    self._forward_10s_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=30,
                                                        height=30,
                                                        fg_color="transparent",
                                                        image=self._forward_photo,
                                                        text="",
                                                        state="disabled",
                                                        command=self._forward_10_seconds)

    self._forward_10s_btn.grid(row=0, column=2, padx=5, pady=5)

    self._trim_slider = CTkTrimSlider(self._control_panel, 
                                      state="disabled",
                                      left_button_command=self._set_start_time,
                                      right_button_command=self._set_end_time,
                                      center_button_command=self._seek,
                                      left_button_var=self._start_time, 
                                      right_button_var=self._end_time,
                                      center_button_var=self._current_time)
    self._trim_slider.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    self._curtime_lbl: ctk.CTkLabel = ctk.CTkLabel(self._control_panel, text="00:00:00.000")
    self._curtime_lbl.grid(row=0, column=4, padx=5, pady=5,)

    self._volume_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                    width=30,
                                                    height=30,
                                                    fg_color="transparent",
                                                    image=self._unmute_photo,
                                                    text="",
                                                    state="disabled",
                                                    command=self._toggle_mute)

    self._volume_btn.grid(row=0, column=5, padx=5, pady=5)

    self._vol_popup = ctk.CTkFrame(self, corner_radius=0)

    self._volume_slider = ctk.CTkSlider(self._vol_popup, 
                                        height=100, 
                                        width=20,
                                        button_corner_radius=4,
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

    self._screenshot_btn = ctk.CTkButton(self._control_panel,
                                         width=30,
                                         height=30,
                                         fg_color="transparent",
                                         image=self._camera_photo,
                                         text="",
                                         state="disabled",
                                         anchor="center",
                                         command=self._take_screenshot)
    
    # Windows Uicode for the Camera is not aligned with the other elements in th control panel
    # Add padding to the text label inside the button to push it up
    
    self._screenshot_btn.grid(row=0, column=6, padx=(5, 10), pady=5, sticky="nswe")

  def _create_time_labels(self) -> None:
    ctk.CTkLabel(self._time_panel, text="New Duration:").grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")

    self._current_duration_lbl: ctk.CTkLabel = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._current_duration_lbl.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="nswe")

    ctk.CTkLabel(self._time_panel, text="Start Time:").grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")

    self._start_time_lbl: ctk.CTkLabel = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._start_time_lbl.grid(row=0, column=3, padx=(5, 10), pady=5, sticky="nswe")

    ctk.CTkLabel(self._time_panel, text="End Time:").grid(row=0, column=4, padx=(10, 5), pady=5, sticky="w")

    self._end_time_lbl: ctk.CTkLabel = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._end_time_lbl.grid(row=0, column=5, padx=(5, 10), pady=5, sticky="nswe")

    ctk.CTkLabel(self._time_panel, text="Duration:").grid(row=0, column=6,padx=(10, 5), pady=5, sticky="w")

    self._duration_lbl: ctk.CTkLabel = ctk.CTkLabel(self._time_panel, text="00:00:00.000")
    self._duration_lbl.grid(row=0, column=7, padx=(5, 10), pady=5, sticky="nswe")

  def _play_pause(self) -> None:
    state = self._media_player.get_state()

    if state == vlc.State.Ended:
      self._restart_media(int(self._start_time.get()))
      return

    if self._media_player.is_playing():
      self._media_player.pause()
      self._play_pause_btn.configure(image=self._play_photo)
      self._screenshot_btn.configure(state="normal")

    else:
      current_ms = self._media_player.get_time()
      end_ms = int(self._end_time.get())
      self._screenshot_btn.configure(state="disabled")

      if current_ms >= end_ms:
        start_ms = int(self._start_time.get())
        self._media_player.set_time(start_ms)
        self._current_time.set(start_ms)
        self._curtime_lbl.configure(text=self._ms_text_converter(start_ms))

      self._media_player.play()
      self._play_pause_btn.configure(image=self._pause_photo)

  def _update_progress(self):
    try:
      state = self._media_player.get_state()
      
      # Break out of update progress loop if VLC enters an Error state
      if state == vlc.State.Error:
        logger.exception("VLC Error")
        return

      if state == vlc.State.Playing and not self._is_seeking:
        current_time_ms = self._media_player.get_time()
        end_time_ms = int(self._end_time.get())

        if current_time_ms >= end_time_ms:
          self._media_player.pause()
          self._media_player.set_time(end_time_ms)
          self._play_pause_btn.configure(image=self._play_photo)
          current_time_ms = end_time_ms
          self._screenshot_btn.configure(state="normal")

        self._current_time.set(current_time_ms)
        self._curtime_lbl.configure(text=self._ms_text_converter(current_time_ms))

      elif state == vlc.State.Ended:
        end_time_ms = int(self._end_time.get())
        self._current_time.set(end_time_ms)
        self._curtime_lbl.configure(text=self._ms_text_converter(end_time_ms))
        self._play_pause_btn.configure(image=self._play_photo)
        self._screenshot_btn.configure(state="normal")
    
    except Exception:
      logger.exception("VLC Error")
      return

    self._update_id = self.after(33, self._update_progress)
  
  def _seek(self, value):
    self._is_seeking = True
    target = int(value)

    state = self._media_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)
    else:
      self._media_player.set_time(target)

    self._curtime_lbl.configure(text=self._ms_text_converter(target))
    self._schedule_seek_reset()
  
  def _set_start_time(self, value):
    self._is_seeking = True
    target = int(value)
    self._current_time.set(target)

    state = self._media_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)
    else:
      self._media_player.set_time(target)

    self._curtime_lbl.configure(text=self._ms_text_converter(target))
    self._schedule_seek_reset()

    new_duration = int(self._end_time.get()) - target
    self._current_duration_lbl.configure(text=self._ms_text_converter(new_duration))
    self._start_time_lbl.configure(text=self._ms_text_converter(target))

  def _set_end_time(self, value):
    self._is_seeking = True
    target = int(value)
    self._current_time.set(target)

    state = self._media_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)
    else:
      self._media_player.set_time(target)
    
    self._curtime_lbl.configure(text=self._ms_text_converter(target))
    self._schedule_seek_reset()

    new_duration = target - int(self._start_time.get())
    self._current_duration_lbl.configure(text=self._ms_text_converter(new_duration))
    self._end_time_lbl.configure(text=self._ms_text_converter(target))
  
  def _schedule_seek_reset(self) -> None:
    if self._seek_reset_id is not None:
      self.after_cancel(self._seek_reset_id)
    self._seek_reset_id = self.after(150, self._reset_seeking)

  def _reset_seeking(self) -> None:
    self._is_seeking = False
    self._seek_reset_id = None
  
  def _reverse_10_seconds(self) -> None:
    current_time = self._media_player.get_time()

    target = current_time - 10000
    if target < self._start_time.get():
      target = self._start_time.get()
    
    self._trim_slider.set("center_value", target)
    self._seek(target)
  
  def _forward_10_seconds(self) -> None:
    current_time = self._media_player.get_time()

    target = current_time + 10000
    if target > self._end_time.get():
      target = self._end_time.get()
    
    self._trim_slider.set("center_value", target)
    self._seek(target)

  def set_vid_values(self, duration: float) -> None:
    original_duration = int(duration * 1000)
    self._trim_slider.configure(require_redraw=True, 
                                to=original_duration, 
                                number_of_steps=original_duration, 
                                state="disabled")

    self._start_time.set(0)
    self._current_time.set(0)
    self._end_time.set(original_duration)

    self._current_duration_lbl.configure(text=self._ms_text_converter(original_duration))
    self._duration_lbl.configure(text=self._ms_text_converter(original_duration))

    self._start_time_lbl.configure(text=self._ms_text_converter(0))
    self._end_time_lbl.configure(text=self._ms_text_converter(original_duration))

  # VLC enters error state sometimes on loading new media
  # Need to unload previous videos, and load new videos on separate threads
  # Need to check for error states and destroy VLC instances and load new instances 
  def load_media(self, vid_file: os.PathLike | str) -> None:
    self._ensure_vlc_initialized()

    if self._update_id is not None:
      self.after_cancel(self._update_id)
      self._update_id = None

    self._is_loading = True
    self._load_request +=1
    request = self._load_request

    Thread(target=self._stop_and_load_media, args=(vid_file, request,), daemon=True).start()
  
  def _stop_and_load_media(self, vid_file: os.PathLike | str, request: int) -> None:
    try:
      self._media_player.stop()

      # VLC state doesn't immediately update so need to wait and check if it stops
      # If no media is loaded, state should be NothingSpecial
      for _ in range(50):
        state = self._media_player.get_state()
        if state in (vlc.State.Stopped, vlc.State.Ended, vlc.State.NothingSpecial):
          break

        Event().wait(timeout=0.05)
      
      else:
        self.after(0, self._reset_vlc, vid_file)
        return
      
      # Don't load media if another request to load media occurs while waiting for video to load
      if request != self._load_request:
        return
      
      # Need to check if there is already media loaded
      current_media = self._media
      self._media = self._instance.media_new(vid_file)
      self._media_player.set_media(self._media)

      if current_media is not None:
        current_media.release()
      
      self.after(0, self._finish_loading, request)
    
    except Exception as e:
      raise vlc.VLCException("Error occuring") from e


  def _finish_loading(self, request: int) -> None:
    if request != self._load_request:
      return

    self._is_loading = False
    self._display_video()

    self._set_volume(100)
    self._is_muted = False
    self._media_player.audio_set_mute(self._is_muted)

    self._play_pause_btn.configure(state="normal")
    self._volume_btn.configure(state="normal")
    self._volume_slider.configure(state="normal")
    self._trim_slider.configure(state="normal")
    self._reverse_10s_btn.configure(state="normal")
    self._forward_10s_btn.configure(state="normal")

    self._media_player.play()
    self._play_pause_btn.configure(image=self._pause_photo)
    self.after(200, self._pause_initial_frame)

    self._update_progress()

  def _display_video(self) -> None:
    if self._device_os == "Linux":
      self._media_player.set_xwindow(self._media_viewer.winfo_id())
    elif self._device_os == "Windows":
      self._media_player.set_hwnd(self._media_viewer.winfo_id())
  
  def _reset_vlc(self, reload_file: os.PathLike | str | None = None) -> None:
    if self._update_id is not None:
      self.after_cancel(self._update_id)
      self._update_id = None
    
    self._is_loading = True

    def _teardown_vlc():
      try:
        self._media_player.stop()
        self._media_player.release()
      except Exception:
        pass
      
      try:
        self._instance.release()
      except Exception:
        pass

      self.after(0, self._rebuild_instance, reload_file)
    
    # Putting on separate thread to keep VLC from blocking main thread if error occurs
    Thread(target=_teardown_vlc, daemon=True).start()
  
  def _rebuild_instance(self, reload_file: os.PathLike | str | None = None) -> None:
    self._media = None
    self._instance = self._platform_specific_inst()
    self._media_player = self._instance.media_player_new()

    self._is_loading = False

    self._play_pause_btn.configure(image=self._play_photo, state="disabled")
    self._volume_btn.configure(state="disabled")
    self._volume_slider.configure(state="disabled")

    if reload_file is not None:
      self.load_media(reload_file)

  def _pause_initial_frame(self) -> None:
    if self._media_player.is_playing():
      self._media_player.pause()
      self._media_player.set_time(0)
      self._play_pause_btn.configure(image=self._play_photo)
      self._current_time.set(0)
      self._curtime_lbl.configure(text="00:00:00.000")
      self._screenshot_btn.configure(state="normal")

  def _restart_media(self, seek_ms: int, paused: bool = False) -> None:
    self._media_player.set_media(self._media)
    self._display_video()
    self._media_player.play()
    if paused:
      self.after(100, lambda: self._seek_and_pause(seek_ms))
    else:
      self.after(100, lambda: self._media_player.set_time(seek_ms))
      self._play_pause_btn.configure(text=' ||')

  def _seek_and_pause(self, seek_ms: int, retries: int = 10) -> None:
    state = self._media_player.get_state()
    if state not in (vlc.State.Playing, vlc.State.Paused):
      if retries > 0:
        self.after(50, lambda: self._seek_and_pause(seek_ms, retries - 1))
      return
    self._media_player.set_time(seek_ms)
    self._media_player.pause()
    self._play_pause_btn.configure(image=self._play_photo)
    self._current_time.set(seek_ms)
    self._curtime_lbl.configure(text=self._ms_text_converter(seek_ms))

  def _toggle_mute(self) -> None:
    self._is_muted = not self._is_muted
    self._media_player.audio_set_mute(self._is_muted)

    if self._is_muted:
      self._volume_btn.configure(image=self._mute_photo)
      self._volume_slider.set(0)
    else:
      self._volume_btn.configure(image=self._unmute_photo)
      if self._volume != 0:
        self._volume_slider.set(self._volume)
        self._set_volume(self._volume)
      else:
        self._volume_slider.set(10)
        self._set_volume(10)

  def _set_volume(self, value: int) -> None:
    self._volume = int(value)
    self._media_player.audio_set_volume(self._volume)

    if self._volume == 0 and not self._is_muted:
      self._is_muted = True
      self._media_player.audio_set_mute(True)
      self._volume_btn.configure(image=self._mute_photo)
    elif self._volume > 0 and self._is_muted:
      self._is_muted = False
      self._media_player.audio_set_mute(False)
      self._volume_btn.configure(image=self._unmute_photo)

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
  
  def _take_screenshot(self) -> None:
    state = self._media_player.get_state()
    if state not in [vlc.State.Paused, vlc.State.Ended]:
      return
    
    file  = filedialog.asksaveasfilename(title="Save As",
                                        initialdir=os.path.expanduser("~"),
                                        initialfile="screenshot",
                                        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
                                        confirmoverwrite=True)
    
    if file == "":
      return
    
    _, ext = os.path.splitext(file)

    if ext not in (".png", ".jpg", ".jpeg"):
      CTkMessagebox(master=self,
                    title="Incompatible file type",
                    message=f"Screenshot cannot be saved as {ext}!",
                    icon="cancel")
      return
    
    x =  self._media_player.video_take_snapshot(0, file, 0, 0)
    if x != 0:
      CTkMessagebox(master=self,
                    title="Screenshot Error",
                    message="Failed to Take screenshot",
                    icon="cancel")
    else:
      CTkMessagebox(master=self,
                    title="Screenshot Successful",
                    message=f"Screenshot taken!\n{file}",
                    icon="info")

  def release(self) -> None:
    if self._update_id is not None:
      self.after_cancel(self._update_id)
      self._update_id = None

    if self._seek_reset_id is not None:
      self.after_cancel(self._seek_reset_id)
      self._seek_reset_id = None

    if self._media_player is not None:
      self._media_player.stop()
      self._media_player.release()

    if self._instance is not None:
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