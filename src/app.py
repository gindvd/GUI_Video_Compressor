"""
Media Conversion Tool
GUI tool for editing, compressing, and converting media files.
Author: David Gingerich
Version: 2.0.0
"""

import customtkinter  as ctk

from CTkMenuBar    import CTkMenuBar, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from customtkinter import filedialog
from tkinter       import PhotoImage, IntVar

import os
from threading import Thread
from platform  import system

from utils.log_utils        import logger
from utils.resolution_utils import get_list_of_smaller_res
from utils.path_utils       import *

from processors.ffmpeg_processor  import FFmpegProcessor
from processors.ffprobe_processor import FFprobeProcessor

from components.progressbar_popup import ProgressbarPopup
from components.video_trimmer      import VideoTrimmer

class App(ctk.CTk):
  HW_CODEC_OPTS: dict = \
  {
    "NVIDIA" :  \
    {
      "Windows" : ["h264_nvenc", "hevc_nvenc"],
      "Linux" : ["h264_nvenc", "hevc_nvenc"],
    },
    "AMD" : \
    {
      "Windows" : ["h264_amf", "hevc_amf"],
      "Linux" : ["h264_amf", "hevc_amf"],
    },
    "Intel" : \
    {
      "Windows" : ["h264_qsv", "hevc_qsv"],
      "Linux" : ["h264_vaapi", "hevc_vaapi"],
    },
  }

  def __init__(self) -> None:
    super().__init__()
    self._device_os: str = system()
    self._external_procs: list = get_external_procs(self._device_os)

    self._check_procs_exist()
    
    self._ffmpeg: FFmpegProcessor   = FFmpegProcessor(self._external_procs[0], self._device_os)
    self._ffprobe: FFprobeProcessor = FFprobeProcessor(self._external_procs[1], self._device_os)

    self._input_file: os.PathLike | str = ""

    self._target_format: str = "mp4"
    self._target_res:    str = "1920x1080"
    self._codec:         str = "libx264"
    self._target_fps:    str = "30"
    self._preset:        str | None = "medium"
    self._quality:       int = 90
    self._audio:         bool = True
    self._audio_codec:   str = "aac"
    self._audio_bitrate: str = "128k"

    self.title("Media Conversion Tool")
    self.minsize(1040, 675)
    self.resizable(True, True)
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._set_icon()

    self._create_menubar()
    self._build_ui()

    self._bind_keys()

  def _check_procs_exist(self) -> None:
    for proc in self._external_procs:
      if proc is None:
        CTkMessagebox(master=self,
                      title="Missing Dependency", 
                      message=f"Missing External Processor:\n {proc}!", 
                      icon="cancel")
        
        self.destroy()
        raise SystemExit(f"Missing dependency: {proc}")
  
  def _set_icon(self) -> None:
    icon_path = get_icon()
    ico_path = get_ico()
    
    if icon_path is None or ico_path is None:
      CTkMessagebox(master=self,
                    title="Missing icon",
                    message="Icon missing from assets folder",
                    icon="warning")
      return
    
    else:

      if self._device_os == "Windows":
        self.iconbitmap(ico_path)
      # using png since cross platform 
      icon = PhotoImage(file=icon_path)
      self.iconphoto(True, icon)
	
  def _create_menubar(self) -> None:
    menubar = CTkMenuBar(self)
    
    file_btn = menubar.add_cascade("File")
    help_btn = menubar.add_cascade("Help")
    
    file_drop = CustomDropdownMenu(widget=file_btn)
    file_drop.add_option(option="Open    Ctrl+O", command=self._browse_files)
    file_drop.add_separator()
    file_drop.add_option(option="Exit    Ctrl+Q", command=self.on_quit)
    
    help_drop = CustomDropdownMenu(widget=help_btn)
    help_drop.add_option(option="About    Ctrl+A", command=self._show_about)

  def _build_ui(self) -> None: 
    self._main_frame = ctk.CTkFrame(self, corner_radius=0)
    self._main_frame.pack(fill='both', expand=True)
    self._main_frame.columnconfigure(0, weight=1)
    self._main_frame.rowconfigure(1, weight=1)

    # File Selection Bar
    self._file_frame = ctk.CTkFrame(self._main_frame, corner_radius=0, fg_color=("gray78", "gray22"))
    self._file_frame.grid(row=0, column=0,padx=0, pady=(0, 10), sticky="ew")
    self._file_frame.columnconfigure(0, weight=1)

    self._file_entry = ctk.CTkEntry(self._file_frame, height=30)
    self._file_entry.bind("<Return>", self._file_entered)
    self._file_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    self._browse_btn = ctk.CTkButton(self._file_frame, 
                                     text="Browse",
                                     command=self._browse_files)
    self._browse_btn.grid(row=0, column=1, padx=(10, 5), pady=5)

    # Content Area - Video Preview left, Settings right
    self._content_frame = ctk.CTkFrame(self._main_frame, corner_radius=0, fg_color="transparent")
    self._content_frame.grid(row=1, column=0, padx=5, pady=0, sticky="nsew")
    self._content_frame.columnconfigure(0, weight=1)
    self._content_frame.rowconfigure(0, weight=1)

    # Left: Video Trimmer
    self._video_trimmer = VideoTrimmer(self._content_frame,
                                       self._external_procs[2], 
                                      self._device_os,
                                      corner_radius=0,
                                      fg_color="transparent")
    self._video_trimmer.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")

    # Right: Settings Panel
    self._settings_panel = ctk.CTkFrame(self._content_frame, width=320, corner_radius=8, fg_color="transparent")
    self._settings_panel.grid(row=0, column=1, padx=0, pady=10, sticky="ns")

    self._build_settings_panel()

    # Bottom: Compress Button
    self._compress_btn_frame = ctk.CTkFrame(self._main_frame, corner_radius=0, fg_color=("gray78", "gray22"))
    self._compress_btn_frame.grid(row=2, column=0,padx=0, pady=(10, 0), sticky="ew")

    self._compress_btn = ctk.CTkButton(self._compress_btn_frame,
                                       width=150,
                                       height=35,
                                       text="Compress",
                                       state="disabled",
                                       command=self._compress_video)
    self._compress_btn.pack(padx=10, pady=10)
  
  def _build_settings_panel(self) -> None:
    section_color = ("gray75", "gray25")

    # Video Settings Section 
    video_section = ctk.CTkFrame(self._settings_panel, fg_color=section_color, corner_radius=8)
    video_section.pack(fill="x", padx=8, pady=(0, 4))
    video_section.columnconfigure(1, weight=1)

    ctk.CTkLabel(video_section, text="Video Settings",
                 font=ctk.CTkFont(size=14, weight="bold")).grid(
                   row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

    ctk.CTkLabel(video_section, text="Codec:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
    self._codec_drpdwn = ctk.CTkComboBox(video_section, 
                                        values=self._codec_values(),
                                        state='readonly',
                                        command=self._codec_choice)
    self._codec_drpdwn.set("libx264")
    self._codec_drpdwn.grid(row=1, column=1, padx=10, pady=6, sticky="ew")

    ctk.CTkLabel(video_section, text="Format:").grid(row=2, column=0, padx=10, pady=6, sticky="w")
    self._containers_drpdwn = ctk.CTkComboBox(video_section, 
                                              values=["mp4", "mkv", "mov"],
                                              state='readonly',
                                              command=self._container_choice)
    self._containers_drpdwn.set("mp4")
    self._containers_drpdwn.grid(row=2, column=1, padx=10, pady=6, sticky="ew")

    ctk.CTkLabel(video_section, text="Resolution:").grid(row=3, column=0, padx=10, pady=6, sticky="w")
    self._resolutions_drpdwn = ctk.CTkComboBox(video_section, 
                                              values=["3840x2160", "2560x1440", "1920x1080", 
                                                      "1280x720", "854x480", "640x360"],
                                              state='readonly',
                                              command=self._resolution_choice)
    self._resolutions_drpdwn.set("1920x1080")
    self._resolutions_drpdwn.grid(row=3, column=1, padx=10, pady=6, sticky="ew")

    ctk.CTkLabel(video_section, text="FPS:").grid(row=4, column=0, padx=10, pady=6, sticky="w")
    self._frames_drpdwn = ctk.CTkComboBox(video_section, 
                                          values=["60", "30", "24", "15"],
                                          state='readonly',
                                          command=self._fps_choice)
    self._frames_drpdwn.set("60")
    self._frames_drpdwn.grid(row=4, column=1, padx=10, pady=6, sticky="ew")

    quality_row = ctk.CTkFrame(video_section, fg_color="transparent")
    quality_row.grid(row=5, column=0, columnspan=2, padx=10, pady=(6, 10), sticky="ew")
    quality_row.columnconfigure(1, weight=1)

    ctk.CTkLabel(quality_row, text="Quality:").grid(row=0, column=0, padx=(0, 8), sticky="w")
    self._quality_slider = ctk.CTkSlider(quality_row, 
                                        button_corner_radius=4,
                                        from_=0,
                                        to=100,
                                        number_of_steps=100, 
                                        command=self._quality_choice)
    self._quality_slider.set(90)
    self._quality_slider.grid(row=0, column=1, padx=(0, 8), sticky="ew")
    self._quality_perc_lbl = ctk.CTkLabel(quality_row, text="90%", width=40)
    self._quality_perc_lbl.grid(row=0, column=2, sticky="e")

    # Audio Settings Section 
    audio_section = ctk.CTkFrame(self._settings_panel, fg_color=section_color, corner_radius=8)
    audio_section.pack(fill="x", padx=8, pady=4)
    audio_section.columnconfigure(1, weight=1)

    ctk.CTkLabel(audio_section, text="Audio Settings",
                font=ctk.CTkFont(size=14, weight="bold")).grid(
                   row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

    ctk.CTkLabel(audio_section, text="Codec:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
    self._audio_codec_drpdwn = ctk.CTkComboBox(audio_section, 
                                              values=["aac", "mp3", "libopus"],
                                              state='readonly',
                                              command=self._aud_codec_choice)
    self._audio_codec_drpdwn.set("aac")
    self._audio_codec_drpdwn.grid(row=1, column=1, padx=10, pady=6, sticky="ew")

    ctk.CTkLabel(audio_section, text="Bitrate:").grid(row=2, column=0, padx=10, pady=6, sticky="w")
    self._audio_bitrate_drpdwn = ctk.CTkComboBox(audio_section, 
                                                values=["96k", "128k", "192k", "256k"],
                                                state='readonly',
                                                command=self._bitrate_choice)
    self._audio_bitrate_drpdwn.set("128k")
    self._audio_bitrate_drpdwn.grid(row=2, column=1, padx=10, pady=6, sticky="ew")

    self._aud_on_off: IntVar = ctk.IntVar()
    self._rm_aud_chkbox = ctk.CTkCheckBox(audio_section, 
                                          text="Remove Audio",
                                          variable=self._aud_on_off,
                                          command=self._remove_audio)
    self._rm_aud_chkbox.grid(row=3, column=0, columnspan=2, padx=10, pady=(6, 10), sticky="w")

    # Compression Settings Section 
    compression_section = ctk.CTkFrame(self._settings_panel, fg_color=section_color, corner_radius=8)
    compression_section.pack(fill="x", padx=8, pady=(4,0))
    compression_section.columnconfigure(1, weight=1)

    ctk.CTkLabel(compression_section, text="Compression Settings",
                 font=ctk.CTkFont(size=14, weight="bold")).grid(
                   row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w")

    ctk.CTkLabel(compression_section, text="Speed:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
    self._preset_speed_drpdwn = ctk.CTkComboBox(compression_section, 
                                                values=["Veryfast", "Faster", "Fast", 
                                                        "Medium", "Slow", "Slower", "Veryslow"],
                                                state='readonly',
                                                command=self._preset_choice)
    self._preset_speed_drpdwn.set("Medium")
    self._preset_speed_drpdwn.grid(row=1, column=1, padx=10, pady=(6, 10), sticky="ew")

  def _show_about(self) -> None:
    about_file = resource_path(os.path.join("assets", "about.txt"))
    with open(about_file, "r") as f:
      about_msg = f.read()

    CTkMessagebox(master=self,
                  title="About",
                  width=500,
                  message=about_msg, 
                  icon="info")
  
  def _browse_files(self):
    item = filedialog.askopenfilename(initialdir = os.path.expanduser("~"),
                                      filetypes=({("Video Files",  "*.mp4 *.mov *.mkv *.avi *.webm"),
                                                  ("All Files", "*.*")}))

    if not self._compatible_file(item):
      return
    self._file_entry.delete(0, "end")

    self._input_file = item
    self._file_entry.insert(0, self._input_file)
    
    self._update_gui()
 
  def _file_entered(self, event) -> None:
    item = event.widget.get()

    if not self._compatible_file(item):
      return

    self._input_file = item
    
    self._update_gui()
  
  def _compatible_file(self, item: os.PathLike | str) -> bool:
    if item == "" or item == ():
      return False

    if not os.path.isfile(item):
      CTkMessagebox(master=self,
                    title="File Warning", 
                    message="Warning!\nFile does not exist!", 
                    icon='warning')
     
      return False

    _, ext = os.path.splitext(item)   

    if ext not in [".mp4", ".mov", ".mkv", ".avi", ".webm"]:
      CTkMessagebox(master=self,
                    title="Video File Warning", 
                    message="Warning!\nFile is not supported video file!", 
                    icon='warning')
      
      return False

    return True
  
  def _update_gui(self) -> None:
    self._browse_btn.configure(state="disabled")
    self._compress_btn.configure(state="disabled")

    # threading to keep ffprobe call from blocking UI updates
    Thread(target=self._extract_video_attrs, daemon=True).start()

  def _extract_video_attrs(self) -> None:
    completed, attributions, err_msg = self._ffprobe.get_video_attributions(self._input_file)

    if not completed:
      self.after(0, self._display_ffprobe_error, err_msg)
      return
   
    self.after(0, self._set_attr_values, attributions)
    
  def _display_ffprobe_error(self, err_msg: str) -> None:
    CTkMessagebox(master=self,
                  title="FFprobe Error", 
                  message=f"Error getting video file info!\n{err_msg}", 
                  icon='cancel')
    
    self._browse_btn.configure(state="normal")

  def _set_attr_values(self, attr_vals: list[str]) -> None:
    # Update combo box with list of resolution options lower than video's current resolution
    vid_res = attr_vals[0]
    
    res_list = get_list_of_smaller_res(vid_res)

    self._resolutions_drpdwn.configure(values=res_list)
    self._resolutions_drpdwn.set(res_list[0])
    self._target_res = res_list[0]
    
    # Update combo box with list of FPS options lower than video's current FPS
    vid_fps = attr_vals[1]
    
    numer, denom = vid_fps.split("/")
    if int(denom) == 0:
      CTkMessagebox(master=self,
                    title="FFprobe Error",
                    message="Error getting video file's fps!\nInvalid frame rate data.",
                    icon='cancel')
      return
    
    fps = round(int(numer) / int(denom))
    
    fps_list = [120, 60, 30, 24, 15]
    upd_fps = []
    
    if fps < fps_list[-1]:
      self._frames_drpdwn.configure(values=str(fps))
      upd_fps.extend([str(fps)])
    
    else:
      for i in fps_list:
        if i <= fps:
          upd_fps.extend([str(i)])

    self._frames_drpdwn.configure(values=upd_fps)
    self._frames_drpdwn.set(upd_fps[0])
    self._target_fps = upd_fps[0]

    # Update label with the videos current duration
    vid_dur = float(attr_vals[2])
    
    self._video_trimmer.set_vid_values(vid_dur)
    self._video_trimmer.load_media(self._input_file)

    # Enable compression button and display the video file
    self._browse_btn.configure(state="normal")
    self._compress_btn.configure(state="normal")

  def _codec_choice(self, choice) -> None:
    self._codec = choice

    if choice in ["libsvtav1", "libvpx-vp9"]:
      self._containers_drpdwn.configure(values=[ "mkv", "webm", "mp4"])
      self._containers_drpdwn.set("mkv")
      self._target_format = "mkv"
    
    else:
      self._containers_drpdwn.configure(values=["mp4", "mkv", "mov"])
      self._containers_drpdwn.set("mp4")
      self._target_format = "mp4"

    if choice in ["h264_amf", "hevc_amf", "h264_vaapi", "hevc_vaapi", "libsvtav1"]:
      self._preset_speed_drpdwn.configure(state="disabled")
      self._preset = None
    
    else:
      self._preset_speed_drpdwn.configure(state="normal")
      self._preset = self._preset_speed_drpdwn.get().lower()
  
  def _container_choice(self, choice) -> None:
    self._target_format = choice

    if choice == "mkv":
      self._audio_codec_drpdwn.configure(values=("aac", "mp3", "libopus", "libvorbis"))
      self._audio_codec_drpdwn.set("aac")
      self._audio_codec = "aac"
      
    elif choice == "mp4":
      self._audio_codec_drpdwn.configure(values=("aac", "mp3", "libopus"))
      self._audio_codec_drpdwn.set("aac")
      self._audio_codec = "aac"

    elif choice == "webm":
      self._audio_codec_drpdwn.configure(values=("libopus", "libvorbis"))
      self._audio_codec_drpdwn.set("libopus")
      self._audio_codec = "libopus"

    elif choice == "mov":
      self._audio_codec_drpdwn.configure(values=("aac", "mp3"))
      self._audio_codec_drpdwn.set("aac")
      self._audio_codec = "aac"

  def _resolution_choice(self, choice) -> None:
    self._target_res = choice

  def _fps_choice(self, choice) -> None:
    self._target_fps = choice
  
  def _preset_choice(self, choice) -> None:
    self._preset = choice.lower()

  def _quality_choice(self, value) -> None:
    self._quality = int(value)
    self._quality_perc_lbl.configure(text=f"{int(value)}%")

  def _remove_audio(self) -> None:
    self._audio = False if self._aud_on_off.get() else True

    if not self._audio:
      self._audio_codec_drpdwn.configure(state="disabled")
      self._audio_bitrate_drpdwn.configure(state="disabled")
    else:
      self._audio_codec_drpdwn.configure(state="normal")
      self._audio_bitrate_drpdwn.configure(state="normal")

  def _aud_codec_choice(self, value) -> None:
    self._audio_codec = value
  
  def _bitrate_choice(self, value) -> None:
    self._audio_bitrate = value

  def _codec_values(self) -> list[str]:
    codecs = ["libx264", "libx265", "libsvtav1", "libvpx-vp9"]

    try:
      from utils.gpu_utils import manufacturers
      connected_gpus = manufacturers()
    except Exception as e:
      logger.exception(str(e))

      CTkMessagebox(master=self,
                    title="System GPU Command Error",
                    message="Error getting connected GPU info!\nCheck logs for details!",
                    icon="warning")

      return codecs

    for name in connected_gpus:
      if name is None:
        continue

      hw_codecs = self.HW_CODEC_OPTS.get(name, {}).get(self._device_os)
      if hw_codecs is not None:
        codecs.extend(hw_codecs)
  
    return codecs

  def _compress_video(self) -> None:
    self._compress_btn.configure(state="disabled")
    self._browse_btn.configure(state="disabled")
    
    self._progressbar_popup: ProgressbarPopup = ProgressbarPopup(self, cmd=self.cancel_compression)
    self._progressbar_popup.run_progressbar()

    # Run FFmpeg executable/binary in separate thread 
    # Keeps the process from blocking progress bar animation from rendering
 
    Thread(target=self._run_compression_cmd, daemon=True).start()

  def _run_compression_cmd(self) -> None:
    start_time: str = self._video_trimmer.get_start_time()
    duration: str = self._video_trimmer.get_duration()

    completed, err_msg = self._ffmpeg.compress(self._input_file, 
                                               self._target_format, 
                                               self._target_res,
                                               self._codec,
                                               self._target_fps,
                                               self._preset,
                                               self._quality,
                                               self._audio,
                                               self._audio_codec,
                                               self._audio_bitrate,
                                               start_time,
                                               duration)

    self.after(0, self._compression_finished, completed, err_msg)
  
  def _compression_finished(self, completed: bool, err_msg: str) -> None:
    self._progressbar_popup.destroy_window()
    self._compress_btn.configure(state="normal")
    self._browse_btn.configure(state="normal")

    if completed:
      CTkMessagebox(master=self,
                    title="Video Compression Completed", 
                    message="Success!\nVideo compressed!", 
                    icon='info')

    if not completed and err_msg is not None:
      CTkMessagebox(master=self,
                    title="Video Compression Error", 
                    message=f"ERROR\n{err_msg}", 
                    icon='cancel')
  
  def cancel_compression(self) -> None:
    killed, msg = self._ffmpeg.terminate_compression()

    if not killed:
      return
      
    elif killed:
      self._compress_btn.configure(state="normal")
      self._browse_btn.configure(state="normal")

      CTkMessagebox(master=self,
                    title="Video Compression Terminated", 
                    message=f"{msg}!", 
                    icon="info")

  def on_quit(self) -> None:
    self.cancel_compression()
    self._video_trimmer.release()
    self.quit()
  
  def _bind_keys(self) -> None:
    self.bind("<Control-o>", self._browse_files)
    self.bind("<Control-q>", self.on_quit)
    self.bind("<Control-a>", self._show_about)
    self.bind("<space>", self._video_trimmer._play_pause)
    self.bind("k", self._video_trimmer._play_pause)
    self.bind("j", self._video_trimmer._reverse_10_seconds)
    self.bind("l", self._video_trimmer._forward_10_seconds)