import customtkinter  as ctk
from CTkMessagebox import CTkMessagebox
import tkinter as tk
from tkinter import filedialog

import os
import platform
import shutil

import GPUinfo as GPU
from ffmpeg_processor import FFmpegProcessor
from ffprobe_processor import FFprobeProcessor

class App(ctk.CTk):
  def __init__(self):
    super().__init__()
     
    self.ffmpeg_cmd, self.ffprobe_cmd = self.exe_paths()
    self.ffmpeg = FFmpegProcessor(self.ffmpeg_cmd)
    self.ffprobe = FFprobeProcessor(self.ffprobe_cmd)

    print(self.ffmpeg)
    print(self.ffprobe)

    """ FFmpeg options to compress video """
    self.input_file = ""
    self.format = "mp4"
    self.resolution = "1920x1080"
    self.codec = "libx264"
    self.fps = "30"
    self.quality = 90
    self.audio = True
        
    self.title("Video Compression Tool")
    self.resizable(False, False)
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    """ Creates menu bar at top of window with dropddown menus """
    self.create_menu()
    self.create_main()
	
  def exe_paths(self):
    if platform.system() == "Windows":
      basepath = os.getcwd()
      ffmpeg_path = "/lib/ffmpeg.exe"
      ffprobe_path = "/lib/ffprobe.exe" 

      return os.path.join(basepath, ffmpeg_path), os.path.join(basepath, ffprobe_path)
    
    if platform.system() == "Linux":

      if not shutil.which("ffmpeg"):
        CTkMessagebox(title="Missing FFmpeg", message="ERROR!\nMissing FFmpeg binaries!\nInstall to use program!", icon="error")
        self.quit()
        
      if not shutil.which("ffprobe"):
        CTkMessagebox(title="Missing FFprobe", message="ERROR!\nMissing FFprobe binaries!\nInstall to use program!", icon="error")
        self.quit()
        
      return "ffmpeg", "ffprobe"


  def create_menu(self):
    menubar = tk.Menu(self)
    self.config(menu=menubar)

    filemenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open", command=self.browse_files)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=self.quit)

    helpmenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=helpmenu)
    helpmenu.add_command(label="Guide", command=self.show_guide)
    helpmenu.add_command(label="About", command=self.show_about)

  def create_main(self):  
    ctk.CTkLabel(self, text="Input File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

    self.file_entry = ctk.CTkEntry(self)
    self.file_entry.bind("<Return>", self.file_entered)
    self.file_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="nsew")

    self.browse = ctk.CTkButton(self, text="Browse", command=self.browse_files)
    self.browse.grid(row=0, column=4, padx=5, pady=5)

    ctk.CTkLabel(self, text="Video Format:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

    self.format_combobox = ctk.CTkComboBox(self, values=["mp4", "mov", "mkv", "avi"],
		                                       state='readonly',
                                           command=self.select_format)

    self.format_combobox.set("mp4")
    self.format_combobox.grid(row=1, column=1, padx=5, pady=5)

    ctk.CTkLabel(self, text="Resolution:").grid(row=1, column=2, padx=5, pady=5, sticky="w")

    self.res_combobox = ctk.CTkComboBox(self, values=self.default_resolutions(),
		                                    state='readonly',
                                        command=self.select_resolution)

    self.res_combobox.set("1920x1080")
    self.res_combobox.grid(row=1, column=3, padx=5, pady=5)

    ctk.CTkLabel(self, text="Codec:").grid(row=2, column=0, padx=5, pady=5, sticky="w")

    self.codec_combobox = ctk.CTkComboBox(self, values=self.codec_values(),
		                                      state='readonly',
                                          command = self.select_codec)

    self.codec_combobox.set("libx264")
    self.codec_combobox.grid(row=2, column=1, padx=5, pady=5)

    ctk.CTkLabel(self, text="FPS:").grid(row=2, column=2, padx=5, pady=5, sticky="w")

    self.fps_combobox = ctk.CTkComboBox(self, values=["60", "50", "30", "24", "15"],
		                                    state='readonly',
                                        command=self.select_fps)

    self.fps_combobox.set("30")
    self.fps_combobox.grid(row=2, column=3, padx=5, pady=5)

    ctk.CTkLabel(self, text="Video Quality:").grid(row=3, column=0, padx=5, pady=5, sticky="sw")

    self.quality_slider = ctk.CTkSlider(self, from_=0, to=100, 
                                        command=self.change_quality,
                                        )
    self.quality_slider.set(90)
    self.quality_slider.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="nsew")

    self.var = ctk.IntVar()
    self.audio_chkbox = ctk.CTkCheckBox(self, text="Remove Audio",
                                        variable=self.var,
                                        command=self.remove_audio)

    self.audio_chkbox.grid(row=4, column=0, padx=5, pady=5)

    self.compress = ctk.CTkButton(self, text="Compress", command=self.compress_video)
    self.compress.grid(row=4, column=4, padx=5, pady=5)

  def show_guide(self):
    pass

  def show_about(self):
    CTkMessagebox(title="About", message="""GUI Video Compression Tool\n""", icon="info")
  
  def browse_files(self):
    item = filedialog.askopenfilename(filetypes=({("Video Files",  "*.mp4 *.mov *.mkv *.avi *.webm"),
                                                  ("All Files", "*.*")}))

    if not self.compatible_file(item):
      return

    self.input_file = item
    self.file_entry.insert(0, self.input_file)
    
    """
    Updates combox with list of smaller resolutions with same 
    aspect ratio as the inputted video file
    """
    updated_resolutions = self.ffprobe.get_resolutions(self.input_file)
    self.res_combobox.configure(values=updated_resolutions)
    self.res_combobox.set(updated_resolutions[0])

  def file_entered(self, event):
    item = event.widget.get()

    if not self.compatible_file(item):
      return

    self.input_file = item
    
    """
    Updates combox with list of smaller resolutions with same 
    aspect ratio as the inputted video file
    """
    updated_resolutions = self.ffprobe.get_resolutions(self.input_file)
    self.res_combobox.configure(values=updated_resolutions)
    self.res_combobox.set(updated_resolutions[0])

  """ Returns false if item is not a file or suported video file """
  def compatible_file(self, item):
    if item == "" or item == ():
      return False

    """ Checks if typed path is a file that exists """
    if not os.path.isfile(item):
      CTkMessagebox(title="File Warning", message="Warning!\nFile does not exist!", icon='warning')
      return False

    """ Splits file extension from file path """     
    _, extension = os.path.splitext(item)   

    if extension not in [".mp4", ".mov", ".mkv", ".avi", ".webm"]:
      CTkMessagebox(title="Video File Warning", message="Warning!\nFile is not supperted video file!", icon='warning')
      return False

    return True

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

  def compress_video(self):
    pass

  def default_resolutions(self):
    return ["3840x2160", "2560x1440", "1920x1080", 
            "1280x720", "854x480", "640x360"]

  def codec_values(self):
    codecs = ["libx264", "libx265", "libvtav1", "libvpx-vp9"]

    """ 
    Gets list of GPU Manufacturer names to update list of codec with codecs
    only compatible with the GPU brand
    """
    for name in GPU.manufacturer():
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

if __name__ == "__main__":
  video_compression_tool = App()
  video_compression_tool.mainloop()