import customtkinter as ctk
from tkinter import DoubleVar, Event
from CTkMessagebox import CTkMessagebox
from CTkTrimSlider import CTkTrimSlider
from customtkinter import filedialog

import vlc
import os
from threading import Thread, Event as ThreadEvent
from typing import Any
from PIL import Image

from utils.log_utils import logger
from utils.timestamp_untils import ms_text_converter
from resource_paths import get_button_image_path

class VideoTrimmer(ctk.CTkFrame):
  """ Frame widget for video playback and trimming """

  def __init__(self, master: Any, vlc_cmd: str, device_os: str, **kwargs: Any) -> None:
    super().__init__(master=master, **kwargs)
    self._vlc_cmd: str = vlc_cmd
    self._device_os: str = device_os

    self._media: vlc.Media | None = None
    self._media_file: str | None = None

    self._is_loading: bool = False
    self._load_request: int = 0

    self._update_id: str | None = None
    self._is_seeking: bool = False
    self._seek_reset_id: str | None = None
    
    # Specifies new start time where video is trimmed and where playback will begin
    self._start_time: DoubleVar = DoubleVar(self, value=0)
    # Specifies new end time where video is trimmed to and where playback will end
    self._end_time: DoubleVar = DoubleVar(self, value=1)
    # Specifies the videos current time
    self._current_time: DoubleVar = DoubleVar(self, value=0.5)

    # Video playback volume 
    self._vol_hide_id: str | None = None
    self._vol_popup_visible: bool = False
    self._is_muted: bool = False
    self._volume: int = 0

    self._instance: vlc.Instance | None = None
    self._media_player: vlc.MediaPlayer | None = None

    self._set_video_control_icons()
    self._build_ui_widgets()

  def _ensure_vlc_initialized(self) -> None:
    """ Creates a VLC instance if none instance exists """
    if self._instance is not None:
      return

    self._instance = self._platform_specific_instance()
    self._instance.log_unset() # Supresses VLC logs
    self._media_player = self._instance.media_player_new()
  
  def _set_video_control_icons(self) -> None:
    """ Creates icons for the control buttons """
    self._play_btn_icon: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("play_button.png")),
                                                  dark_image=Image.open(get_button_image_path("play_button.png")))
    self._pause_btn_icon: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("pause_button.png")),
                                                   dark_image=Image.open(get_button_image_path("pause_button.png")))
    self._reverse_btn_icon: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("reverse.png")),
                                                     dark_image=Image.open(get_button_image_path("reverse.png")))
    self._forward_btn_icon: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("forward.png")),
                                                     dark_image=Image.open(get_button_image_path("forward.png")))
    self._mute_btn_icon: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("muted_volume.png")),
                                                  dark_image=Image.open(get_button_image_path("muted_volume.png")))
    self._unmute_btn_icon: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("unmuted_volume.png")),
                                                    dark_image=Image.open(get_button_image_path("unmuted_volume.png")))
    self._camera_btn_icon: ctk.CTkImage = ctk.CTkImage(light_image=Image.open(get_button_image_path("camera.png")),
                                                    dark_image=Image.open(get_button_image_path("camera.png")))

  def _platform_specific_instance(self) -> vlc.Instance:
    """ Initializes the VLC instance with platform specific settings """
    if self._device_os == "Windows":
        return vlc.Instance(["--quiet",
                             "--verbose=0", 
                             "--aout=directsound",
                             "--avcodec-skiploopfilter=0",
                             "--avcodec-hw=any",
                             f"--plugin-path={self._vlc_cmd}"])

    return vlc.Instance(["--quiet",
                        "--verbose=0", 
                        "--aout=pulse", 
                        "--no-xlib"])
  
  def _build_ui_widgets(self) -> None:
    """ Builds the main widgets in the video trimmer parent widget """
    # Media playback frame
    self._media_viewer = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
    self._media_viewer.pack(padx=(10, 5), pady=10, fill='both', expand=True)

    # Control panel: Media playback / trimming controls
    self._control_panel = ctk.CTkFrame(self, width=750, height=40, fg_color=("gray75", "gray25"), corner_radius=10)
    self._control_panel.pack(padx=(10, 5), pady=0, fill='x')
    self._control_panel.grid_propagate(False)
    self._build_video_controls()
    
    # Timestamp panels: Displays timestamps
    self._time_panel = ctk.CTkFrame(self, width=750, fg_color=("gray75", "gray25"), corner_radius=10)
    self._time_panel.pack(padx=(10, 5), pady=10, fill='x')
    self._build_time_labels()
  
  def _build_video_controls(self) -> None:
    """ Builds the controller buttons for video playback and trimming """
    self._control_panel.columnconfigure(3, weight=3)

    self._play_pause_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=35,
                                                        height=30,
                                                        fg_color="transparent",
                                                        image=self._play_btn_icon,
                                                        text="",
                                                        state="disabled",
                                                        command=self._play_pause)

    self._play_pause_btn.grid(row=0, column=0, padx=(10, 5), pady=5)

    self._reverse_10s_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=35,
                                                        height=30,
                                                        fg_color="transparent",
                                                        image=self._reverse_btn_icon,
                                                        text="",
                                                        state="disabled",
                                                        command=self._reverse_10_seconds)

    self._reverse_10s_btn.grid(row=0, column=1, padx=5, pady=5)

    self._forward_10s_btn: ctk.CTkButton = ctk.CTkButton(self._control_panel,
                                                        width=30,
                                                        height=35,
                                                        fg_color="transparent",
                                                        image=self._forward_btn_icon,
                                                        text="",
                                                        state="disabled",
                                                        command=self._forward_10_seconds)

    self._forward_10s_btn.grid(row=0, column=2, padx=5, pady=5)
    
    """
    Trim slider for adjusting start and end time values so FFmpeg has trim video
    Left handle adjust the start time, right handle adjusts the end time
    The center handle adjusts the current time, and moves as the video plays
    """
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
                                                    width=35,
                                                    height=30,
                                                    fg_color="transparent",
                                                    image=self._unmute_btn_icon,
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

    # Shows and hides the volume slider depending on mouse location
    self._volume_btn.bind("<Enter>", self._show_vol_popup)
    self._volume_btn.bind("<Leave>", self._schedule_hide_vol_popup)
    self._vol_popup.bind("<Enter>", self._cancel_hide_vol_popup)
    self._vol_popup.bind("<Leave>", self._schedule_hide_vol_popup)
    self._volume_slider.bind("<Enter>", self._cancel_hide_vol_popup)
    self._volume_slider.bind("<Leave>", self._schedule_hide_vol_popup)

    self._screenshot_btn = ctk.CTkButton(self._control_panel,
                                         width=30,
                                         height=35,
                                         fg_color="transparent",
                                         image=self._camera_btn_icon,
                                         text="",
                                         state="disabled",
                                         anchor="center",
                                         command=self._take_screenshot)
    
    self._screenshot_btn.grid(row=0, column=6, padx=(5, 10), pady=5, sticky="nswe")

  def _build_time_labels(self) -> None:
    """ Creates and places timestamp labels """
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

  def _play_pause(self, event: Event | None = None) -> None:
    """ Toggles between play and pause states depending on the current state """
    state = self._media_player.get_state()
    
    # If instance is in ended state, reloads the media
    if state == vlc.State.Ended:
        self._restart_media(int(self._start_time.get()))
        return

    # Pauses video
    if self._media_player.is_playing():
        self._media_player.pause()
        self._play_pause_btn.configure(image=self._play_btn_icon)
        self._screenshot_btn.configure(state="normal")
    
    # Plays video
    else:
        current_ms = self._media_player.get_time()
        end_ms = int(self._end_time.get())

        self._screenshot_btn.configure(state="disabled")
        
        # Changes the current time to the start time if media has reached the end time
        if current_ms >= end_ms:
            start_ms = int(self._start_time.get())
            self._media_player.set_time(start_ms)
            self._current_time.set(start_ms)
            self._curtime_lbl.configure(text=ms_text_converter(start_ms))

        self._media_player.play()

        self._play_pause_btn.configure(image=self._pause_btn_icon)

    self._start_update_loop()
    
  def _start_update_loop(self) -> None:
    """ Only calls update progress if media player is not being updated """
    if self._update_id is None:
        self._update_progress()

  def _update_progress(self) -> None:
    """ Updates labels and slider as video plays """
    self._update_id = None

    try:
      state = self._media_player.get_state()
      
      # Breaks loop if an error occurs
      if state == vlc.State.Error:
          logger.exception("VLC Error")
          return
      
      # Updates current time if media reaches EOF and VLC enters Ended state
      elif state == vlc.State.Ended:
        end_time_ms = int(self._end_time.get())
        self._current_time.set(end_time_ms)
        self._curtime_lbl.configure(text=ms_text_converter(end_time_ms))
        self._play_pause_btn.configure(image=self._play_btn_icon)
        self._screenshot_btn.configure(state="normal")
      
      # Updates time labels if video is playing, and user isn't seeking
      elif state == vlc.State.Playing and not self._is_seeking:
        current_time_ms = self._media_player.get_time()
        end_time_ms = int(self._end_time.get())
        
        # Pauses the video, if current time reaches the updated end time
        if current_time_ms >= end_time_ms:
          self._media_player.pause()
          self._media_player.set_time(end_time_ms)

          current_time_ms = end_time_ms

          self._play_pause_btn.configure(image=self._play_btn_icon)
          self._screenshot_btn.configure(state="normal")

        self._current_time.set(current_time_ms)

        self._curtime_lbl.configure(text=ms_text_converter(current_time_ms))

      elif state == vlc.State.Paused:
        self._play_pause_btn.configure(image=self._play_btn_icon)

    except Exception:
      logger.exception("VLC Error")
      return
    
    # Loops the function after 33 ms to not block the main thread
    self._update_id = self.after(33, self._update_progress)
  
  def _seek(self, value: float) -> None:
    """ Changes current time to user desired location """
    self._is_seeking = True

    target = int(value)

    state = self._media_player.get_state()
    
    # Resarts media if in end state 
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)

    else:
      self._media_player.set_time(target)

      # Helps force paused-frame refresh on some VLC backends
      if state == vlc.State.Paused:
          self.after(1, self._media_player.set_pause, 1)

    self._current_time.set(target)
    self._curtime_lbl.configure(text=ms_text_converter(target))

    self._schedule_seek_reset()
    self._start_update_loop()
  
  def _set_start_time(self, value: float) -> None:
    """ Changes start time to user desired time """
    self._is_seeking = True
    
    # Target is integer representing milliseconds
    target = int(value)
    self._current_time.set(target)

    state = self._media_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)

    else:
      self._media_player.set_time(target)
      
      # Pauses the video when start time is changed
      if state == vlc.State.Paused:
        self.after(1,  self._media_player.set_pause, 1)

    self._curtime_lbl.configure(text=ms_text_converter(target))
    self._schedule_seek_reset()
    
    # Updates labels
    new_duration = int(self._end_time.get()) - target
    self._current_duration_lbl.configure(text=ms_text_converter(new_duration))
    self._start_time_lbl.configure(text=ms_text_converter(target))

    self._start_update_loop()

  def _set_end_time(self, value: float) -> None:
    """ Changes end time to user desired time """
    self._is_seeking = True
    
    # Target is integer representing milliseconds
    target = int(value)
    self._current_time.set(target)

    if self._media_player.is_playing():
      self._media_player.pause()
      self._play_pause_btn.configure(image=self._play_btn_icon)
      self._screenshot_btn.configure(state="normal")

    state = self._media_player.get_state()
    if state == vlc.State.Ended:
      self._restart_media(target, paused=True)

    else:
      self._media_player.set_time(target)

      # Pauses the video when end time is changed
      if state == vlc.State.Paused:
        self.after(1, self._media_player.set_pause, 1)

    self._curtime_lbl.configure(text=ms_text_converter(target))

    self._schedule_seek_reset()

    new_duration = (target - int(self._start_time.get()))
    self._current_duration_lbl.configure(text=ms_text_converter(new_duration))
    self._end_time_lbl.configure(text=ms_text_converter(target))

    self._start_update_loop()
  
  def _schedule_seek_reset(self) -> None:
    """ Keeps multiple seek resets from occuring at once """
    if self._seek_reset_id is not None:
      self.after_cancel(self._seek_reset_id)
    self._seek_reset_id = self.after(50, self._reset_seeking)

  def _reset_seeking(self) -> None:
    """ Resets seeking and id values """
    self._is_seeking = False
    self._seek_reset_id = None
  
  def _reverse_10_seconds(self, event: Event | None = None) -> None:
    """ Skips 10 seconds backwards """
    current_time = self._media_player.get_time()

    target = current_time - 10000

    # Sets current time to start time if targeted current time will be less than start time
    if target < self._start_time.get():
      target = self._start_time.get()
    
    self._trim_slider.set("center_value", target)

    # Calls seek function after updating labels
    self._seek(target)
  
  def _forward_10_seconds(self, event: Event | None = None) -> None:
    """ Skips 10 seconds forward """
    current_time = self._media_player.get_time()

    target = current_time + 10000

    # Sets current time to end time if targeted current time will be grater than end time
    if target > self._end_time.get():
      target = self._end_time.get()
    
    self._trim_slider.set("center_value", target)

    # Calls seek function after updating labels
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

    self._current_duration_lbl.configure(text=ms_text_converter(original_duration))
    self._duration_lbl.configure(text=ms_text_converter(original_duration))

    self._start_time_lbl.configure(text=ms_text_converter(0))
    self._end_time_lbl.configure(text=ms_text_converter(original_duration))

  
  def load_media(self, vid_file: str) -> None:
    """ Loads new media in to VLC instance to allow playback and trimming """

    # Creates a VLC instance if one doesn't exist
    self._ensure_vlc_initialized()
    self._media_file = vid_file

    if self._update_id is not None:
      self.after_cancel(self._update_id)
      self._update_id = None

    self._is_loading = True
    self._load_request +=1
    request = self._load_request
    
    # Runs stop and load function in new thread to keep VLC from blocking main thread and causing app to stop responding
    Thread(target=self._stop_and_load_media, args=(vid_file, request,), daemon=True).start()
  
  def _stop_and_load_media(self, vid_file: str, request: int) -> None:
    """ Stops already loaded meia, before loading new media"""
    try:
      self._media_player.stop()

      # VLC state doesn't immediately update so need to wait and check if it stops
      # If no media is loaded, state should be NothingSpecial
      # Loop will break if in one of the 3 specified states
      for _ in range(50):
        state = self._media_player.get_state()
        if state in (vlc.State.Stopped, vlc.State.Ended, vlc.State.NothingSpecial):
          break
        
        # Causes thread to sleep for .05 seconds before starting next loop
        ThreadEvent().wait(timeout=0.05)
      
      # Destroys old VLC instance and creates a new one if video hasn't stopped in specified time
      else:
        self.after(0, self._reset_vlc, vid_file)
        return
      
      # Don't load media if another request to load media occurs while waiting for video to load
      if request != self._load_request:
        return
      
      # Current media gets set to previous media before setting new media
      current_media = self._media
      self._media = self._instance.media_new(vid_file)
      self._media_player.set_media(self._media)
      
      # Releases and closes previously loaded media file
      if current_media is not None:
        current_media.release()
      
      self.after(0, self._finish_loading, request)
    
    except Exception as e:
      raise vlc.VLCException("Error occuring") from e


  def _finish_loading(self, request: int) -> None:
    """ Updates GUI after old media is unlodaed and new media set"""
    # Checks again if another request to load new media was sent before media could finish loading
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
    self._play_pause_btn.configure(image=self._pause_btn_icon)
    self.after(200, self._pause_initial_frame)

    self._update_progress()

  def _display_video(self) -> None:
    """ Creates the media viewer inside a canvas """
    if self._device_os == "Linux":
      self._media_player.set_xwindow(self._media_viewer.winfo_id())
    elif self._device_os == "Windows":
      self._media_player.set_hwnd(self._media_viewer.winfo_id())
  
  def _reset_vlc(self, reload_file: None = None) -> None:
    """ Destroys old instance if stuck and resets variables """
    if self._update_id is not None:
      self.after_cancel(self._update_id)
      self._update_id = None
    
    self._is_loading = True

    def _teardown_vlc():
      # Releases VLC media player and instance, waits for them to be destroyed
      try:
        self._media_player.stop()
        self._media_player.release()
      except Exception:
        pass
      
      try:
        self._instance.release()
      except Exception:
        pass
      
      # Rebuilds VLC instance after old instance is torndown
      self.after(0, self._rebuild_instance, reload_file)
    
    # Stopping and releasing media and instance is not instant, put on new thread to keep from blocking main thread
    Thread(target=_teardown_vlc, daemon=True).start()
  
  def _rebuild_instance(self, reload_file: str | None = None) -> None:
    """ Rebuilds VLC instance and media player if previous instance and player were released """
    self._media = None
    self._instance = self._platform_specific_instance()
    self._media_player = self._instance.media_player_new()

    self._is_loading = False

    self._play_pause_btn.configure(image=self._play_btn_icon, state="disabled")
    self._volume_btn.configure(state="disabled")
    self._volume_slider.configure(state="disabled")
    
    # Loads new media if instance got stuck and was rebuilt
    if reload_file is not None:
      self.load_media(reload_file)

  def _pause_initial_frame(self) -> None:
    """ Shows initial frame as thumbnail when video is loaded"""
    if self._media_player.is_playing():
      self._media_player.pause()
      self._media_player.set_time(0)
      self._play_pause_btn.configure(image=self._play_btn_icon)
      self._current_time.set(0)
      self._curtime_lbl.configure(text="00:00:00.000")
      self._screenshot_btn.configure(state="normal")

  def _restart_media(self, seek_ms: int, paused: bool = False) -> None:
    """ Restarts media player if EOF is reached and VLC is in ENDED state"""
    self._media_player.set_media(self._media)
    self._display_video()
    self._media_player.play()
    
    # Keeps media paused when restarting
    if paused:
      self.after(100, self._seek_and_pause, seek_ms)

    else:
      self.after(100, self._media_player.set_time, seek_ms)
      self._play_pause_btn.configure(image=self._pause_btn_icon)

    self._start_update_loop()

  def _seek_and_pause(self, seek_ms: int, retries: int = 10) -> None:
    """ Seek to specified timestamp before pausing media player """
    state = self._media_player.get_state()
    
    # Loop until VLC in playing or paused states or max retries reached
    if state not in (vlc.State.Playing, vlc.State.Paused):
      if retries > 0:
        self.after(50, lambda: self._seek_and_pause(seek_ms, retries - 1))
      return
    
    # Seek and update time timestamps
    self._media_player.set_time(seek_ms)
    self._media_player.pause()
    self._play_pause_btn.configure(image=self._play_btn_icon)
    self._current_time.set(seek_ms)
    self._curtime_lbl.configure(text=ms_text_converter(seek_ms))

  def _toggle_mute(self) -> None:
    """ Toggles mute """
    self._is_muted = not self._is_muted
    self._media_player.audio_set_mute(self._is_muted)

    # mutes audio         
    if self._is_muted:
      self._volume_btn.configure(image=self._mute_btn_icon)
      self._volume_slider.set(0)

    else:
      self._volume_btn.configure(image=self._unmute_btn_icon)

      # Unmutes audio and sets volume to volume level before muting
      if self._volume != 0:
        self._volume_slider.set(self._volume)
        self._set_volume(self._volume)
      
      # Unmutes, sets volume level to 10 if volume before toggling mute was already 0
      else:
        self._volume_slider.set(10)
        self._set_volume(10)

  def _set_volume(self, value: float) -> None:
    """ Change volume to user specified level """
    self._volume = int(value)
    self._media_player.audio_set_volume(self._volume)

    if self._volume == 0 and not self._is_muted:
      self._is_muted = True
      self._media_player.audio_set_mute(True)
      self._volume_btn.configure(image=self._mute_btn_icon)
    elif self._volume > 0 and self._is_muted:
      self._is_muted = False
      self._media_player.audio_set_mute(False)
      self._volume_btn.configure(image=self._unmute_btn_icon)

  def _show_vol_popup(self, event: Event | None = None) -> None:
    """ Displays volume slider while volume button, or slider are being hovered over """

    if self._vol_hide_id is not None:
      self.after_cancel(self._vol_hide_id)
      self._vol_hide_id = None

    if self._vol_popup_visible:
      return
    
    # Aligns volume slider with the volume button
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

  def _schedule_hide_vol_popup(self, event: Event | None = None) -> None:
    """ Waits a few milliseconds to hide volume slider when user is no loger hovering over volume slider / button"""
    if self._vol_hide_id is not None:
      self.after_cancel(self._vol_hide_id)
    self._vol_hide_id = self.after(300, self._hide_vol_popup)

  def _cancel_hide_vol_popup(self, event: Event | None = None) -> None:
    """ Cancels volume slider hiding if the usre starts hovering over volume button / slider again"""
    if self._vol_hide_id is not None:
      self.after_cancel(self._vol_hide_id)
      self._vol_hide_id = None

  def _hide_vol_popup(self) -> None:
    """ Hides the volume slider """
    self._vol_popup.place_forget()
    self._vol_popup_visible = False
    self._vol_hide_id = None
  
  def _take_screenshot(self, event: Event | None = None) -> None:
    """ Takes a snapshot of the video at the current time and save it as a PNG or JPEG """

    state = self._media_player.get_state()

    # Keeps snapshot from being taken when media player is not paused
    if state not in [vlc.State.Paused, vlc.State.Ended]:
      return
    
    if self._media_file is None: 
      return
    
    basename, _ = os.path.basename(self._file_path)
    name, _ = basename.split(".")
    
    # Open file dialog to let user specify file name and location
    file  = filedialog.asksaveasfilename(title="Save As",
                                        initialdir=os.path.expanduser("~"),
                                        initialfile=f"{name}_screenshot",
                                        defaultextension=".png",
                                        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
                                        confirmoverwrite=True)
    
    if file == "":
      return
    
    _, ext = os.path.splitext(file)
    
    # Ensures user didn't change the file extension to unsupported type
    if ext not in (".png", ".jpg", ".jpeg"):
      CTkMessagebox(master=self,
                    title="Incompatible file type",
                    message=f"Screenshot cannot be saved as {ext}!",
                    icon="warning")
      return
    
    # Take snapshot and get return code
    x =  self._media_player.video_take_snapshot(0, file, 0, 0)

    # Displays error message if return code is 0
    if x != 0:
      CTkMessagebox(master=self,
                    title="Screenshot Error",
                    message="Failed to Take screenshot",
                    icon="cancel")
    
    # Displays sucess message if return code is 0
    else:
      CTkMessagebox(master=self,
                    title="Screenshot Successful",
                    message=f"Screenshot taken!\n{file}",
                    icon="check")

  def release(self) -> None:
    """ Releases media player and instance when app is closed """
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
    return ms_text_converter(self.start_time_ms)
  
  def get_duration(self) -> str:
    return ms_text_converter(self.duration_ms)