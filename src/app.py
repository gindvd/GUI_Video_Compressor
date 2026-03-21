import customtkinter  as ctk

from CTkMenuBar import *
from CTkMessagebox import CTkMessagebox
from customtkinter import filedialog

import os
import threading

from utils import get_ffmpeg_cmd, get_ffprboe_cmd

import modules.GPUinfo as gpu

from processors.ffmpeg_processor import FFmpegProcessor
from processors.ffprobe_processor import FFprobeProcessor

from components.progressbar_popup import ProgressbarPopup
from components.video_trimmer import VideoTrimmer

class App(ctk.CTk):
  def __init__(self):
    super().__init__()
    ffmpeg_cmd = get_ffmpeg_cmd()
    ffprobe_cmd = get_ffprboe_cmd()
    
    if ffmpeg_cmd is None:
      close = CTkMessagebox(title="Missing FFmpeg", 
                      message="FFmpeg command missing!", 
                      icon="cancel",
                      option_1="Ok")
        
      if close.get() == "Ok":
        self.quit()
    
    if ffprobe_cmd is None:
      close = CTkMessagebox(title="Missing FFprobe", 
                      message="FFprobe command missing!", 
                      icon="cancel",
                      option_1="Ok")
        
      if close.get() == "Ok":
        self.quit()
    
    self._ffmpeg = FFmpegProcessor(ffmpeg_cmd)
    self._ffprobe = FFprobeProcessor(ffprobe_cmd)

    self._input_file = ""
    self._target_format = "mp4"
    self._target_res = "1920x1080"
    self._codec = "libx264"
    self._target_fps = "30"
    self._quality = 90
    self._audio = True
        
    self.title("Video Compression Tool")
    self.resizable(False, False)
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._create_menubar()
    self._central_frame = ctk.CTkFrame(self, corner_radius=0)
    self._populate_central_frame()
    self._central_frame.pack()

    self._vid_trimmer = VideoTrimmer(self)
    self._vid_trimmer.pack(fill='x')
	
  def _create_menubar(self):
    menubar = CTkMenuBar(self)
    
    file_btn = menubar.add_cascade("File")
    help_btn = menubar.add_cascade("Help")
    
    file_drop = CustomDropdownMenu(widget=file_btn)
    file_drop.add_option(option="Open", command=self._browse_files)
    file_drop.add_separator()
    file_drop.add_option(option="Exit", command=self.on_quit)
    
    help_drop = CustomDropdownMenu(widget=help_btn)
    help_drop.add_option(option="About", command=self._show_about)

  def _populate_central_frame(self):  
    ctk.CTkLabel(self._central_frame, text="Input File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

    self._file_entry = ctk.CTkEntry(self._central_frame)
    self._file_entry.bind("<Return>", self._file_entered)
    self._file_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="nsew")

    self._browse_btn = ctk.CTkButton(self._central_frame, 
                                     text="Browse", 
                                     command=self._browse_files)
    
    self._browse_btn.grid(row=0, column=4, padx=5, pady=5)

    ctk.CTkLabel(self._central_frame, text="Codec:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

    self._codec_drpdwn = ctk.CTkComboBox(self._central_frame, 
                                         values=self._codec_values(),
		                                     state='readonly',
                                         command=self._codec_choice)

    self._codec_drpdwn.set("libx264")
    self._codec_drpdwn.grid(row=1, column=1, padx=5, pady=5)

    ctk.CTkLabel(self._central_frame, text="Resolution:").grid(row=1, column=2, padx=5, pady=5, sticky="w")

    self._target_res_drpdwn = ctk.CTkComboBox(self._central_frame, 
                                              values=["3840x2160", "2560x1440", "1920x1080", 
                                                      "1280x720", "854x480", "640x360"],
		                                          state='readonly',
                                              command=self._res_choice)

    self._target_res_drpdwn.set("1920x1080")
    self._target_res_drpdwn.grid(row=1, column=3, padx=5, pady=5)

    ctk.CTkLabel(self._central_frame, text="Video Format:").grid(row=2, column=0, padx=5, pady=5, sticky="w")

    self._target_ext_drpdwn = ctk.CTkComboBox(self._central_frame, 
                                              values=["mp4", "mkv", "mov"],
		                                          state='readonly',
                                              command=self._ext_choice)

    self._target_ext_drpdwn.grid(row=2, column=1, padx=5, pady=5)
    self._target_ext_drpdwn.set("mp4")

    ctk.CTkLabel(self._central_frame, text="FPS:").grid(row=2, column=2, padx=5, pady=5, sticky="w")

    self._target_fps_drpdwn = ctk.CTkComboBox(self._central_frame, 
                                              values=["60", "30", "24", "15"],
		                                          state='readonly',
                                              command=self._fps_choice)

    self._target_fps_drpdwn.set("60")
    self._target_fps_drpdwn.grid(row=2, column=3, padx=5, pady=5)

    ctk.CTkLabel(self._central_frame, text="Video Quality:").grid(row=3, column=0, padx=5, pady=5, sticky="sw")

    self._quality_slider = ctk.CTkSlider(self._central_frame, 
                                         from_=0, 
                                         to=100,
                                         number_of_steps=100, 
                                         command=self._quality_choice)

    self._quality_slider.set(90)
    self._quality_slider.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="nsew")

    self._quality_perc_lbl = ctk.CTkLabel(self._central_frame, text=f"{self._quality_slider.get()}%")
    self._quality_perc_lbl.grid(row=3, column=4, padx=5, pady=5, sticky="w")

    self._aud_on_off = ctk.IntVar()
    self._rm_aud_chkbox = ctk.CTkCheckBox(self._central_frame, 
                                          text="Remove Audio",
                                          variable=self._aud_on_off,
                                          command=self._remove_audio)

    self._rm_aud_chkbox.grid(row=4, column=0, padx=5, pady=5)

    self._compress_btn = ctk.CTkButton(self._central_frame, 
                                       text="Compress",
                                       state="disabled",
                                       command=self._compress_video)
    
    self._compress_btn.grid(row=4, column=4, padx=5, pady=5)

  def _show_about(self):
    CTkMessagebox(title="About", 
                  message="""GUI Video Compression Tool\n""", 
                  icon="info")
  
  def _browse_files(self):
    self._file_entry.insert(0, "")
    item = filedialog.askopenfilename(initialdir = os.path.expanduser("~"),
                                      filetypes=({("Video Files",  "*.mp4 *.mov *.mkv *.avi *.webm"),
                                                  ("All Files", "*.*")}))

    if not self._compatible_file(item):
      return

    self._input_file = item
    self._file_entry.insert(0, self._input_file)
    
    self._update_gui()
 
  def _file_entered(self, event):
    item = event.widget.get()

    if not self._compatible_file(item):
      return

    self.input_file = item
    
    self._update_gui()
    
  def _update_gui(self):
    self._compress_btn.configure(state="normal")

    # ffprobe.get_resolutions will return list of common resolutions 
    # smaller that the videos current resolution that maintain the same aspect ratio
    completed, res_list, err_msg = self._ffprobe.get_resolutions(self._input_file)
    
    if not completed:
      CTkMessagebox(title="FFprobe Error", 
                    message=f"Error getting video file's resolution!\n{err_msg}", 
                    icon='cancel')
      
      return

    elif completed:    
      self._target_res_drpdwn.configure(values=res_list)
      self._target_res_drpdwn.set(res_list[0])

      self._vid_trimmer.set_video(self._input_file)
    
    completed, vid_fps, err_msg = self._ffprobe.get_fps(self._input_file)

    if not completed:
      CTkMessagebox(title="FFprobe Error", 
                    message=f"Error getting video file's FPS!\n{err_msg}", 
                    icon='cancel')
    
    elif completed:
      upd_fps = []
      fps_list = [120, 60, 30, 24, 15]

      for i in fps_list:
        if i <= vid_fps:
          upd_fps.extend([str(i)])

      self._target_fps_drpdwn.configure(values=upd_fps)
      self._target_fps_drpdwn.set(upd_fps[0])

    completed, duration, err_msg = self._ffprobe.get_duration(self._input_file)

    if not completed:
      CTkMessagebox(title="FFprobe Error", 
                    message=f"{err_msg}", 
                    icon='cancel')
      
      return
    
    elif completed:
      self._vid_trimmer.set_duration(duration)


  def _compatible_file(self, item):
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

  def _codec_choice(self, choice):
    self._codec = choice

    if choice == "libsvtav1":
      self._target_ext_drpdwn.configure(values=["mkv", "mov", "mp4"])
      self._target_ext_drpdwn.set("mkv")
    elif choice == "libvpx-vp9":
      self._target_ext_drpdwn.configure(values=["webm", "mkv"])
      self._target_ext_drpdwn.set("mebm")
    else:
      self._target_ext_drpdwn.configure(values=["mp4", "mkv", "mov"])
      self._target_ext_drpdwn.set("mp4")
  
  def _ext_choice(self, choice):
    self._target_format = choice

  def _res_choice(self, choice):
    self._target_res = choice

  def _fps_choice(self, choice):
    self._target_fps = choice
  
  def _quality_choice(self, value):
    self._quality = value
    self._quality_perc_lbl.configure(text="{}%".format(value))

  def _remove_audio(self):
    self._audio = False if self._aud_on_off.get() else True

  def _codec_values(self):
    codecs = ["libx264", "libx265", "libsvtav1", "libvpx-vp9"]

    for name in gpu.manufacturer():
      match name:
        case "NVIDIA":
          codecs.extend(["h264_nvenc", "hevc_nvenc"])
        case "AMD":
          codecs.extend(["h264_amf", "hevc_amf"])
        case "Intel":
          codecs.extend(["h264_qsv", "hevc_qsv"])
        case _:
          continue
  
    return codecs

  def _compress_video(self):
    self._compress_btn.configure(state="disabled")
    
    self._progressbar_popup = ProgressbarPopup(self)
    self._progressbar_popup.run_progressbar()

    # Run FFmpeg executable/binary in separate thread 
    # Keeps the process from blocking progress bar animation from rendering
 
    threading.Thread(target=self._run_compression_cmd, daemon=True).start()

  def _run_compression_cmd(self): 
    completed, err_msg = self._ffmpeg.compress(self._input_file, 
                                               self._target_format, 
                                               self._target_res,
                                               self._codec,
                                               self._target_fps,
                                               self._quality,
                                               self._audio)

    self.after(0, self._compression_finished, completed, err_msg)
  
  def _compression_finished(self, completed, err_msg):
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
  
  def cancel_compression(self):
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
  
  def on_quit(self):
    self.cancel_compression()
    
    self.quit()

if __name__ == "__main__":
  vid_compress_app = App()
  vid_compress_app.protocol("WM_DELETE_WINDOW", vid_compress_app.on_quit)
  vid_compress_app.mainloop()