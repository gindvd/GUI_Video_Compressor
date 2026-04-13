import tkinter as tk
import customtkinter  as ctk

from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkMessagebox import CTkMessagebox
from customtkinter import filedialog

import os
import threading

from utils import *

import modules.gpu_utils as gpu
from modules.resolution_utils import get_list_of_smaller_res

from processors.ffmpeg_processor import FFmpegProcessor
from processors.ffprobe_processor import FFprobeProcessor

from components.progressbar_popup import ProgressbarPopup
from components.video_trimmer import VideoTrimmer

class App(ctk.CTk):
  HW_CODEC_OPTS: dict = {
    "NVIDIA" :  {
      "Windows" : ["h264_nvenc", "hevc_nvenc"],
      "Linux" : ["h264_nvenc", "hevc_nvenc"],
    },
    "AMD" : {
      "Windows" : ["h264_amf", "hevc_amf"],
      "Linux" : ["h264_amf", "hevc_amf"],
    },
    "Intel" : {
      "Windows" : ["h264_qsv", "hevc_qsv"],
      "Linux" : ["h264_vaapi", "hevc_vaapi"],
    },
  }

  VIDEO_ATTR: tuple = ("resolution", "fps", "duration")

  def __init__(self) -> None:
    super().__init__()
    self._external_procs: list = get_external_procs()
    assert len(self._external_procs) == 3, "Not enough external processors for app to function"

    self._check_procs_exist()
    
    self._ffmpeg: FFmpegProcessor = FFmpegProcessor(self._external_procs[0])
    self._ffprobe: FFprobeProcessor = FFprobeProcessor(self._external_procs[1])

    self._input_file: os.PathLike | str = ""
    self._target_format: str = "mp4"
    self._target_res: str = "1920x1080"
    self._codec: str = "libx264"
    self._target_fps: str = "30"
    self._preset: str | None = "medium"
    self._quality: int = 90
    self._audio: bool = True

    self.title("Video Compression Tool")
    self.resizable(False, False)
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._create_menubar()
    self._main_frame = ctk.CTkFrame(self)
    self._build_gui()  
    self._main_frame.pack(fill='both')

  def _check_procs_exist(self) -> None:
    for idx, proc in enumerate(self._external_procs):
      if proc is None:
        CTkMessagebox(title="Missing Dependency", 
                      message=f"Missing External Processor:\n {EXTERNAL_PROCS[idx]}!", 
                      icon="cancel",
                      option_1="Ok")
        
        self.destroy()
        raise SystemExit(f"Missing dependency: {EXTERNAL_PROCS[idx]}")
	
  def _create_menubar(self) -> None:
    menubar = CTkMenuBar(self)
    
    file_btn = menubar.add_cascade("File")
    help_btn = menubar.add_cascade("Help")
    
    file_drop = CustomDropdownMenu(widget=file_btn)
    file_drop.add_option(option="Open", command=self._browse_files)
    file_drop.add_separator()
    file_drop.add_option(option="Exit", command=self.on_quit)
    
    help_drop = CustomDropdownMenu(widget=help_btn)
    help_drop.add_option(option="About", command=self._show_about)

  def _build_gui(self) -> None: 
    # file frame
    self._file_frame = ctk.CTkFrame(self._main_frame)
    
    self._browse_btn = ctk.CTkButton(self._file_frame, 
                                     text="Browse",
                                     command=self._browse_files)
    
    self._browse_btn.grid(row=0, column=0, padx=5, pady=5)

    self._file_entry = ctk.CTkEntry(self._file_frame, width=700, height=35)
    self._file_entry.bind("<Return>", self._file_entered)
    self._file_entry.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

    self._file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
 
    # media frame
    self._media_frame = ctk.CTkFrame(self._main_frame)
    
    self._vid_trimmer: VideoTrimmer = VideoTrimmer(self._media_frame, self._external_procs[2])
    self._vid_trimmer.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    self._media_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    # quality frame
    self._quality_frame = ctk.CTkFrame(self._main_frame)

    ctk.CTkLabel(self._quality_frame, text="Video Quality:").grid(row=0, column=0, padx=5, pady=5, sticky="sw")

    self._quality_slider = ctk.CTkSlider(self._quality_frame, 
                                         width=700, 
                                         height=25,
                                         from_=0, 
                                         to=100,
                                         number_of_steps=100, 
                                         command=self._quality_choice)

    self._quality_slider.set(90)
    self._quality_slider.grid(row=0, column=1,  padx=5, pady=5, sticky="nsew")

    self._quality_perc_lbl = ctk.CTkLabel(self._quality_frame, text=f"{int(self._quality_slider.get())}%")
    self._quality_perc_lbl.grid(row=0, column=2, padx=5, pady=5, sticky="w")

    self._quality_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    # options frame
    self._options_frame = ctk.CTkFrame(self._main_frame)
  
    ctk.CTkLabel(self._options_frame, text="Codec:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

    self._codec_drpdwn = ctk.CTkComboBox(self._options_frame, 
                                         values=self._codec_values(),
                                         state='readonly',
                                         command=self._codec_choice)

    self._codec_drpdwn.set("libx264")
    self._codec_drpdwn.grid(row=0, column=1, padx=5, pady=5)

    ctk.CTkLabel(self._options_frame, text="Resolution:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

    self._target_res_drpdwn = ctk.CTkComboBox(self._options_frame, 
                                              values=["3840x2160", "2560x1440", "1920x1080", 
                                                      "1280x720", "854x480", "640x360"],
                                              state='readonly',
                                              command=self._res_choice)

    self._target_res_drpdwn.set("1920x1080")
    self._target_res_drpdwn.grid(row=1, column=1, padx=5, pady=5)
    
    ctk.CTkLabel(self._options_frame, text="Video Format:").grid(row=2, column=0, padx=5, pady=5, sticky="w")

    self._target_ext_drpdwn = ctk.CTkComboBox(self._options_frame, 
                                              values=["mp4", "mkv", "mov"],
                                              state='readonly',
                                              command=self._format_choice)

    self._target_ext_drpdwn.grid(row=2, column=1, padx=5, pady=5)
    self._target_ext_drpdwn.set("mp4")

    ctk.CTkLabel(self._options_frame, text="FPS:").grid(row=3, column=0, padx=5, pady=5, sticky="w")

    self._target_fps_drpdwn = ctk.CTkComboBox(self._options_frame, 
                                              values=["60", "30", "24", "15"],
                                              state='readonly',
                                              command=self._fps_choice)

    self._target_fps_drpdwn.set("60")
    self._target_fps_drpdwn.grid(row=3, column=1, padx=5, pady=5)

    ctk.CTkLabel(self._options_frame, text="Speed:").grid(row=4,column=0, padx=5, pady=5, sticky="w")

    self._preset_speed_drpdwn = ctk.CTkComboBox(self._options_frame, 
                                              values=["Veryfast", "Faster", "Fast", 
                                                      "Medium", "Slow", "Slower", "Veryslow"],
                                              state='readonly',
                                              command=self._preset_choice)

    self._preset_speed_drpdwn.set("Medium")
    self._preset_speed_drpdwn.grid(row=4, column=1, padx=5, pady=5)

    self._aud_on_off: tk.IntVar = ctk.IntVar()
    self._rm_aud_chkbox = ctk.CTkCheckBox(self._options_frame, 
                                          text="Remove Audio",
                                          variable=self._aud_on_off,
                                          command=self._remove_audio)

    self._rm_aud_chkbox.grid(row=5, column=0, columnspan=2, padx=5, pady=15, sticky="sw")

    self._options_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

    # compresion button
    self._compress_btn = ctk.CTkButton(self._main_frame, 
                                       text="Compress",
                                       font=(ctk.CTkFont(size=20)),
                                       state="disabled",
                                       command=self._compress_video)
    
    self._compress_btn.grid(row=2, column=1, padx=10, pady=10, sticky="nswe")

  def _show_about(self) -> None:
    about_file = ROOT_DIR / Path("assets/about.txt")
    with open(about_file, "r") as f:
      about_msg = f.read()

    CTkMessagebox(title="About",
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
      CTkMessagebox(title="File Warning", 
                    message="Warning!\nFile does not exist!", 
                    icon='warning')
     
      return False

    _, ext = os.path.splitext(item)   

    if ext not in [".mp4", ".mov", ".mkv", ".avi", ".webm"]:
      CTkMessagebox(title="Video File Warning", 
                    message="Warning!\nFile is not supported video file!", 
                    icon='warning')
      
      return False

    return True
  
  def _update_gui(self) -> None:
    attr_vals = []
    
    for attr in self.VIDEO_ATTR:
      completed, val, err_msg = self._ffprobe.get_video_attr_value(attr, self._input_file)
    
      if not completed:
        CTkMessagebox(title="FFprobe Error", 
                      message=f"Error getting video file's {attr}!\n{err_msg}", 
                      icon='cancel')
      
        return
      
      assert val is not None, "Video attribute value can't be None" 
      attr_vals.append(val)
    
    # Update combo box with list of resolution options lower than video's current resolution
    vid_res = attr_vals[0]
    
    res_list = get_list_of_smaller_res(vid_res)

    self._target_res_drpdwn.configure(values=res_list)
    self._target_res_drpdwn.set(res_list[0])
    self._target_res = res_list[0]
    
    # Update combo box with list of FPS options lower than video's current FPS
    vid_fps = attr_vals[1]
    
    numer, denom = vid_fps.split("/")
    if int(denom) == 0:
      CTkMessagebox(title="FFprobe Error",
                    message="Error getting video file's fps!\nInvalid frame rate data.",
                    icon='cancel')
      return
    fps = round(int(numer) / int(denom))
    
    fps_list = [120, 60, 30, 24, 15]
    upd_fps = []
    
    if fps < fps_list[-1]:
      self._target_fps_drpdwn.configure(values=str(fps))
      upd_fps.append(str(fps))
    
    else:
      for i in fps_list:
        if i <= fps:
          upd_fps.extend([str(i)])

    self._target_fps_drpdwn.configure(values=upd_fps)
    self._target_fps_drpdwn.set(upd_fps[0])
    self._target_fps = upd_fps[0]

    # Update label with the videos current duration
    vid_dur = float(attr_vals[2])
    
    self._vid_trimmer.set_vid_values(vid_dur)

    # Enable compression button and display the video file
    self._compress_btn.configure(state="normal")
    self._vid_trimmer.set_video(self._input_file)

  def _codec_choice(self, choice) -> None:
    self._codec = choice

    if choice in ["libsvtav1", "libvpx-vp9"]:
      self._target_ext_drpdwn.configure(values=[ "mkv", "webm", "mp4"])
      self._target_ext_drpdwn.set("mkv")
      self._target_format = "mkv"
    
    else:
      self._target_ext_drpdwn.configure(values=["mp4", "mkv", "mov"])
      self._target_ext_drpdwn.set("mp4")
      self._target_format = "mp4"

    if choice in ["h264_amf", "hevc_amf", "h264_vaapi", "hevc_vaapi", "libvpx-vp9"]:
      self._preset_speed_drpdwn.configure(state="disabled")
      self._preset = None
    
    else:
      self._preset_speed_drpdwn.configure(state="normal")
      self._preset = self._preset_speed_drpdwn.get().lower()
  
  def _format_choice(self, choice) -> None:
    self._target_format = choice

  def _res_choice(self, choice) -> None:
    self._target_res = choice

  def _fps_choice(self, choice) -> None:
    self._target_fps = choice
  
  def _preset_choice(self, choice) -> None:
    self._preset = choice.lower()

  def _quality_choice(self, value) -> None:
    self._quality = int(value)
    self._quality_perc_lbl.configure(text=f"{value}%")

  def _remove_audio(self) -> None:
    self._audio = False if self._aud_on_off.get() else True

  def _codec_values(self) -> list[str]:
    codecs = ["libx264", "libx265", "libsvtav1", "libvpx-vp9"]

    connected_gpus = gpu.manufacturer()

    if connected_gpus is None:
      CTkMessagebox(title="System GPU Command Error",
                    message="Error getting connected GPU info!\nCheck logs for details!",
                    icon="warning")

      return codecs

    for name in connected_gpus:
      if name is None:
        continue

      hw_codecs = self.HW_CODEC_OPTS.get(name, {}).get(DEVICE_OS)
      if hw_codecs is not None:
        codecs.extend(hw_codecs)
  
    return codecs

  def _compress_video(self) -> None:
    self._compress_btn.configure(state="disabled")
    
    self._progressbar_popup: ProgressbarPopup = ProgressbarPopup(self)
    self._progressbar_popup.run_progressbar()

    # Run FFmpeg executable/binary in separate thread 
    # Keeps the process from blocking progress bar animation from rendering
 
    threading.Thread(target=self._run_compression_cmd, daemon=True).start()

  def _run_compression_cmd(self) -> None:
    start_time: str = self._vid_trimmer.get_start_time()
    duration: str = self._vid_trimmer.get_duration()

    completed, err_msg = self._ffmpeg.compress(self._input_file, 
                                               self._target_format, 
                                               self._target_res,
                                               self._codec,
                                               self._target_fps,
                                               self._preset,
                                               self._quality,
                                               self._audio,
                                               start_time,
                                               duration)

    self.after(0, self._compression_finished, completed, err_msg)
  
  def _compression_finished(self, completed: bool, err_msg: str) -> None:
    self._progressbar_popup.destroy_window()
    self._compress_btn.configure(state="normal")

    if completed:
      CTkMessagebox(title="Video Compression Completed", 
                    message="Success!\nVideo has been successfully compressed!", 
                    icon='info')

    if not completed and err_msg is not None:
      CTkMessagebox(title="Video Compression Error", 
                    message=f"ERROR\n{err_msg}", 
                    icon='cancel')
  
  def cancel_compression(self) -> None:
    killed, msg = self._ffmpeg.terminate_compression()

    if not killed:
      return
      
    elif killed:
      close = CTkMessagebox(title="Video Compression Terminated", 
                            message=f"{msg}!", 
                            icon="info",
                            option_1="Ok")
        
      if close.get() == "Ok":
        return
      
      return
  
  def on_quit(self) -> None:
    self.cancel_compression()
    self._vid_trimmer.release()
    self.quit()

if __name__ == "__main__":
  vid_compress_app = App()
  vid_compress_app.protocol("WM_DELETE_WINDOW", vid_compress_app.on_quit)
  vid_compress_app.mainloop()