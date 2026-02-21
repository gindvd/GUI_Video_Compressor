import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

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

    """ Creates menu bar at top of window with dropddown menus """
    self.create_menu()

  def create_menu(self):
    menubar = tk.Menu(self)
    self.config(menu=menubar)
    
    filemenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=filemenu)
    filemenu.add_command(label="Open", command=self.browse_files())
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=self.quit)
    
    helpmenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=helpmenu)
    helpmenu.add_command(label="Guide", command=self.show_guide())
    helpmenu.add_cascade(label="About", command=self.show_about())

  def show_guide(self):
    pass
    
  def show_about(self):
    pass
  
  def browse_files(self):
    pass

if __name__ == "__main__":
  clip_optimization_app = App()
  clip_optimization_app.mainloop()