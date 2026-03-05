import customtkinter  as ctk
from CTkMessagebox import CTkMessagebox
import tkinter as tk
from tkinter import filedialog

import os
import platform
import shutil
import threading

import GPUinfo as gpu
from ffmpeg_processor import FFmpegProcessor
from ffprobe_processor import FFprobeProcessor
from ctk_progressbar_popup import ProgressbarPopup

class App(ctk.CTk):
  def __init__(self):
    super().__init__()
     
    self._ffmpeg_cmd, self._ffprobe_cmd = self._ffmpeg_ffprobe_sys_cmd()
    self._ffmpeg = FFmpegProcessor(self._ffmpeg_cmd)
    self._ffprobe = FFprobeProcessor(self._ffprobe_cmd)

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

    self._create_menu_gui()
    self._create_main_gui()
	
  def _ffmpeg_ffprobe_sys_cmd(self)
    # Currently only supports WIndows and Linux
    # Possibly expand this to be compatible with Mac and others    
    device_os = platform.system() 
    basepath = os.getcwd()
      ffmpeg_path = os.path.join(basepath, "/lib/ffmpeg.exe")
      ffprobe_path = os.path.join(basepath, "/lib/ffprobe.exe")
      
      if os.path.isfile(ffmpeg_path):
        CTkMessagebox(title="Missing FFmpeg Exe", 
                      message="""
                              ERROR!\n
                              FFmpeg.exe is missing from lib folder!\n
                              Please ensure FFmpeg is installed correctly!
                              """, 
                      icon="cancel")
        
        self.quit()
      
      if os.path.isfile(ffprobe_path):
        CTkMessagebox(title="Missing FFprobe Exe", 
                      message="""
                              ERROR!\n
                              FFprobe.exe is missing from lib folder!\n
                              Please ensure FFmpeg is installed correctly!
                              """, 
                      icon="cancel")
        
        self.quit()
    
    elif device_os == "Linux":

      if not shutil.which("ffmpeg"):
        CTkMessagebox(title="Missing FFmpeg", 
                      message="ERROR!\nMissing FFmpeg binaries!\nInstall to use program!", 
                      icon="cancel")
        
        self.quit()
        
      if not shutil.which("ffprobe"):
        CTkMessagebox(title="Missing FFprobe", 
                      message="ERROR!\nMissing FFprobe binaries!\nInstall to use program!", 
                      icon="cancel")
        
        self.quit()
        
      return "ffmpeg", "ffprobe"
    
    error_msg = CTkMessagebox(title="Incompatible Operating System", 
                              message="""ERROR!
                                         \nCurrent program is not currently compatible with {}!
                                         \n\nTerminating program!""".format(device_os), 
                              icon="cancel",
                              option_1='Ok')
    
    response = error_msg.get()

    if error_msg == 'OK':
      self.quit()

  def _create_menu(self):
    menubar = tk.Menu(self)
    self.config(menu=menubar)

    filemenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open", command=self._browse_files)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=self.quit)

    helpmenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=helpmenu)
    helpmenu.add_command(label="About", command=self._show_about)

  def _create_main(self):  
    ctk.CTkLabel(self, text="Input File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

    self.file_entry = ctk.CTkEntry(self)
    self.file_entry.bind("<Return>", self.file_entered)
    self.file_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="nsew")

    self.browse = ctk.CTkButton(self, 
                                text="Browse", 
                                command=self.browse_files)
    
    self.browse.grid(row=0, column=4, padx=5, pady=5)

    ctk.CTkLabel(self, text="Video Format:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

    self.format_combobox = ctk.CTkComboBox(self, 
                                           values=["mp4", "mov", "mkv", "avi"],
		                                       state='readonly',
                                           command=self.select_format)

    self.format_combobox.set("mp4")
    self.format_combobox.grid(row=1, column=1, padx=5, pady=5)

    ctk.CTkLabel(self, text="Resolution:").grid(row=1, column=2, padx=5, pady=5, sticky="w")

    self.res_combobox = ctk.CTkComboBox(self, 
                                        values=self.default_resolutions(),
		                                    state='readonly',
                                        command=self.select_resolution)

    self.res_combobox.set("1920x1080")
    self.res_combobox.grid(row=1, column=3, padx=5, pady=5)

    ctk.CTkLabel(self, text="Codec:").grid(row=2, column=0, padx=5, pady=5, sticky="w")

    self.codec_combobox = ctk.CTkComboBox(self, 
                                          values=self.codec_values(),
		                                      state='readonly',
                                          command = self.select_codec)

    self.codec_combobox.set("libx264")
    self.codec_combobox.grid(row=2, column=1, padx=5, pady=5)

    ctk.CTkLabel(self, text="FPS:").grid(row=2, column=2, padx=5, pady=5, sticky="w")

    self.fps_combobox = ctk.CTkComboBox(self, 
                                        values=["60", "50", "30", "24", "15"],
		                                    state='readonly',
                                        command=self.select_fps)

    self.fps_combobox.set("30")
    self.fps_combobox.grid(row=2, column=3, padx=5, pady=5)

    ctk.CTkLabel(self, text="Video Quality:").grid(row=3, column=0, padx=5, pady=5, sticky="sw")

    self.quality_slider = ctk.CTkSlider(self, 
                                        from_=0, 
                                        to=100, 
                                        command=self.change_quality)

    self.quality_slider.set(90)
    self.quality_slider.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="nsew")

    self.var = ctk.IntVar()
    self.audio_chkbox = ctk.CTkCheckBox(self, 
                                        text="Remove Audio",
                                        variable=self.var,
                                        command=self.remove_audio)

    self.audio_chkbox.grid(row=4, column=0, padx=5, pady=5)

    self.compress = ctk.CTkButton(self, 
                                  text="Compress", 
                                  command=self.compress_video)
    
    self.compress.grid(row=4, column=4, padx=5, pady=5)

  def _show_about(self):
    CTkMessagebox(title="About", 
                  message="""GUI Video Compression Tool\n""", 
                  icon="info")
  
 def _browse_files(self):
    self._file_entry.insert(0, "")
    item = filedialog.askopenfilename(filetypes=({("Video Files",  "*.mp4 *.mov *.mkv *.avi *.webm"),
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
    self._compress_btn.config(state=NORMAL)

    # ffprobe.get_resolutions will return list of common resolutions 
    # smaller that the videos current resolution that maintain the same aspect ratio
    completed, updated_list, err_msg = self._ffprobe.get_resolutions(self._input_file)
    
    if not completed:
      CTkMessagebox(title="FFprobe Error", 
                    message="Error getting video file's resolution!\n{}".format(err_msg), 
                    icon='cancel')
      
      return

    elif completed:    
      self._target_res_drpdwn.configure(values=updated_list)
      self._target_res_drpdwn.set(updated_resolutions[0])


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


  def select_format(self, choice):
    self.format = choice

  def select_resolution(self, choice):
    self.resolution = choice

  def select_codec(self, choice):
    self.codec = choice

  def select_fps(self, choice):
    self.fps = choice

  def change_quality(self, choice):
    self.quality = choice

  def remove_audio(self):
    self.audio = False if self.var.get() else True
    pass

  def default_resolutions(self):
    return ["3840x2160", "2560x1440", "1920x1080", 
            "1280x720", "854x480", "640x360"]

  def codec_values(self):
    codecs = ["libx264", "libx265", "libsvtav1", "libvpx-vp9"]

    """ 
    Gets list of GPU Manufacturer names to update list of codec with codecs
    only compatible with the GPU brand
    """
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

  def compress_video(self):
    """ Create progress bar to display while FFmpeg is converting video file """
    self.progressbar_popup = ProgressbarPopup(self)
    self.progressbar_popup.run_progressbar()

    """ Run FFmpeg executable/binary is separate thread """
    threading.Thread(target=self.run_command, daemon=True).start()

  def run_command(self): 
    completed, error_msg = self.ffmpeg.compress(self.input_file, 
                                                self.format, 
                                                self.resolution,
                                                self.codec,
                                                self.fps,
                                                self.quality,
                                                self.audio)

    self.after(0, lambda: self.compression_finished(completed, error_msg))
  
  def compression_finished(self, completed, error_msg):
    self.progressbar_popup.destroy_window() 

    if completed:
      CTkMessagebox(title="Video Compression Completed", 
                    message="Success!\nVideo has been successfully compressed!", 
                    icon='info')

    if not completed:
      CTkMessagebox(title="Video Compression Error", 
                    message=f"Error!\n{error_msg}", 
                    icon='cancel')

if __name__ == "__main__":
  video_compression_tool = App()
  video_compression_tool.mainloop()