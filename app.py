import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import os

import GPUinfo as GPU

class App(tk.Tk):
	def __init__(self):
		super().__init__()

		self.title("Video Compressor")
		self.resizable(False, False)

		""" FFmpeg options to compress video """
		self.input_file = ""
		self.format = "mp4"
		self.resolution = "1920x1080"
		self.codec = "libx264"
		self.fps = "30"
		self.quality = 90
		self.remove_audio = False

		""" Creates menu bar at top of window with dropddown menus """
		self.create_menu()
		self.create_main()

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
		helpmenu.add_cascade(label="About", command=self.show_about)

	def create_main(self):  
		tk.Label(self, text="Input File:",).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W,)
		self.file_entry = ttk.Entry(self)
		self.file_entry.bind("<Return>", self.file_entered)
		self.file_entry.grid(row=0, column=1, columnspan=3, padx=5, pady=5,sticky=tk.N+tk.S+tk.E+tk.W,)

		self.browse = ttk.Button(self, text="Browse", command=self.browse_files)
		self.browse.grid(row=0, column=4, padx=5, pady=5,)

		tk.Label(self, text="Video Format:",).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W,)
		self.format_combobox = ttk.Combobox(self, values=["mp4", "mov", "mkv", "avi"], state="readonly",)
		self.format_combobox.set("mp4")
		self.format_combobox.bind("<<ComboboxSelected>>", self.select_format)
		self.format_combobox.grid(row=1, column=1, padx=5, pady=5,)

		tk.Label(self, text="Resolution:",).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W,)
		self.res_combobox = ttk.Combobox(self, values=self.resolution_values(), state="readonly",)
		self.res_combobox.set("1920x1080")
		self.res_combobox.bind("<<ComboboxSelected>>", self.select_resolution)
		self.res_combobox.grid(row=1, column=3, padx=5, pady=5,)

		tk.Label(self, text="Codec:",).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W,)
		self.codec_combobox = ttk.Combobox(self, values=self.codec_values(), state="readonly",)
		self.codec_combobox.set("libx264")
		self.codec_combobox.bind("<<ComboboxSelected>>", self.select_codec)
		self.codec_combobox.grid(row=2, column=1, padx=5, pady=5,)

		tk.Label(self, text="FPS:",).grid(row=2, column=2, padx=5, pady=5, sticky=tk.W,)
		self.fps_combobox = ttk.Combobox(self, values=["60", "50", "30", "24", "15"], state="readonly",)
		self.fps_combobox.set("30")
		self.fps_combobox.bind("<<ComboboxSelected>>", self.select_fps)
		self.fps_combobox.grid(row=2, column=3, padx=5, pady=5,)

		tk.Label(self, text="Video Quality:",).grid(row=3, column=0, padx=5, pady=5, sticky=tk.SW,)
		self.quality_slider = tk.Scale(self, from_=0, to=100, orient="horizontal")
		self.quality_slider.set(90)
		self.quality_slider.bind("<Motion>", self.change_quality)
		self.quality_slider.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky=tk.N+tk.S+tk.E+tk.W,)

		self.var = tk.IntVar()
		self.audio_chkbox = tk.Checkbutton(self, text="Remove Audio", variable=self.var,)
		self.audio_chkbox.config(command=self.set_audio_opt)
		self.audio_chkbox.grid(row=4, column=0, padx=5, pady=5,)

		self.compress = ttk.Button(self, text="Compress", command=self.compress_video)
		self.compress.grid(row=4, column=4, padx=5, pady=5,)

	def show_guide(self):
		pass
    
	def show_about(self):
		pass
  
	def browse_files(self):
		item = filedialog.askopenfilename(filetypes=({("Video Files",  "*.mp4;*.mov;*.mkv;*.avi;*.webm"),
																									("All Files", "*.*")}))
    
		if not self.compatible_file(item):
			return

		self.file_entry = item
		self.file_entry.insert(0, self.input_file)
    
	def file_entered(self, event):
		item = event.widget.get()

		if not self.compatible_file(item):
			return

		self.input_file = item

	""" Returns false if item is not a file or suported video file """
	def compatible_file(item):
		if item == "":
			return False

		""" Checks if typed path is a file that exists """
		if not os.path.isfile(item):
			messagebox.showwarning("File Warning", "Warning!\nFile does not exist!")
			return False

		""" Splits file extension from file path """     
		_, extension = os.path.splitext(item)   

		if extension not in [".mp4", ".mov", ".mkv", ".avi", ".webm"]:
			messagebox.showwarning("Video File Warning", "Warning!\nFile is not supperted video file!")
			return False

		return True

	def select_format(self, event):
		self.format = event.widget.get()
    
	def select_resolution(self, event):
		self.resolution = event.widget.get()
    
	def select_codec(self, event):
		self.codec = event.widget.get()

	def select_fps(self, event):
		self.fps = event.widget.get()

	def change_quality(self, event):
		self.quality = event.widget.get()

	def set_audio_opt(self):
		self.remove_audio = True if self.var.get() else False

	def compress_video(self):
		pass

	def resolution_values(self):
		""" Will update to get input files resolution, and use it to update the resolution list """ 

		resolutions = ["3840x2160", "2560x1440", "1920x1080", 
									 "1280x720", "854x480", "640x360"]

		return resolutions

	def codec_values(self):
		codec_values = ["libx264", "libx265", "libvtav1", "libvpx-vp9"]

		""" 
		Gets list of GPU Manufacturer names to update list of codec with codecs
		only compatible with the GPU brand
		"""
		for name in GPU.manufacturer():
			match name:
				case "NVIDIA":
					codec_values.extend(["h264_nvemc", "hevc_nvenc"])
				case "AMD":
					codec_values.extend(["h264_amf", "hevc_amf"])
				case "Intel":
					codec_values.extend(["h264_qsv", "hevc_qsv"])
				case _:
					continue
					
		return codec_values

if __name__ == "__main__":
	clip_optimization_app = App()
	clip_optimization_app.mainloop()