import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

class App(tk.Tk):
  def __init__(self):
    super().__init__()

    self.title("Video Compressor")
    self.geometry('800x400')
    self.resizable(False, False)

    """ FFmpeg options to compress video """
    self.input_file = ""
    self.format = "mp4"
    self.resolution = "1920x1080"
    self.codec = "libx264"
    self.fps = "30"
    self.quality = 90
    self.remove_audio = False

if __name__ == "__main__":
  clip_optimization_app = App()
  clip_optimization_app.mainloop()