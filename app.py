import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

class App(tk.Tk):
  def __init__(self):
    super().__init__()

    self.title("Video Compressor")
    self.geometry('800x400')
    self.resizable(False, False)

if __name__ == "__main__":
  clip_optimization_app = App()
  clip_optimization_app.mainloop()