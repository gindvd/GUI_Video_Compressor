import customtkinter as ctk
import tkinter as tk

from tkinter import DoubleVar, Event
from customtkinter import filedialog
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageTk

import subprocess
import os
from io import BytesIO
from typing import Any

from processors.ffmpeg_processor import FFmpegProcessHandler
from utils.timestamp_untils import ms_text_converter, seconds_to_timestamp

class FrameViewer(ctk.CTkToplevel):
  """ Toplevel window for view and extracting individual frames from a media file """

  def __init__(self, master: Any, ffmpeg_handler: FFmpegProcessHandler, **kwargs: Any) -> None:
    super().__init__(master=master, **kwargs)

    self.title("Frame Viewer")
    self.minsize(850, 600)
    self.geometry("960x640")

    self._ffmpeg_handler: FFmpegProcessHandler = ffmpeg_handler

    self._file_path: str | None = None
    self._duration_ms: int = 0
    self._fps: float = 30.0
    self._frame_duration_ms: float = 33.33
    self._current_ms: float = 0.0
    self._current_frame: int = 0

    self._current_time: DoubleVar = DoubleVar(self, value=0)
    self._img: Image.Image | None = None
    self._photo: ImageTk.PhotoImage | None = None
    self._seek_id: str | None = None

    self._build_ui()

  def _build_ui(self) -> None:
    """ Builds and places all widgets and UI elements """
    # Image canvas
    self._canvas = tk.Canvas(self,
                             bg="black",
                             highlightthickness=0,
                             borderwidth=0)

    self._canvas.pack(padx=10,
                      pady=(10, 5),
                      fill="both",
                      expand=True)
    
    # Resize the fame image when the window is resized
    self._canvas.bind("<Configure>", self._on_canvas_resize)
    
    
    self._image_id: int | None = None
    self._text_id: int | None = self._canvas.create_text(0, 0,
                                             text="No media loaded",
                                             fill="white",
                                             anchor="center")
    
    # Control frame: controls for fingding frames
    control_frame = ctk.CTkFrame(self, fg_color=("gray75", "gray25"), corner_radius=6)
    control_frame.pack(padx=10, pady=5, fill="x")
    control_frame.columnconfigure(1, weight=1)

    self._prev_btn = ctk.CTkButton(control_frame, text="<", width=35, height=30,
                                   font=ctk.CTkFont(size=20),
                                   state="disabled", command=self._prev_frame)
    self._prev_btn.grid(row=0, column=0, padx=(10, 5), pady=5)

    self._slider = ctk.CTkSlider(control_frame, 
                                 button_corner_radius=4,
                                 from_=0, 
                                 to=1,
                                 number_of_steps=1, 
                                 state="disabled",
                                 variable=self._current_time,
                                 command=self._on_slider_move)
    self._slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    self._next_btn = ctk.CTkButton(control_frame, text=">", width=35, height=30,
                                   font=ctk.CTkFont(size=20),
                                   state="disabled", command=self._next_frame)
    self._next_btn.grid(row=0, column=2, padx=(5, 10), pady=5)
    
    # Info Frame: Displays frame number, timestamp, and other media info
    info_frame = ctk.CTkFrame(self, fg_color=("gray75", "gray25"), corner_radius=6)
    info_frame.pack(padx=10, pady=(0, 10), fill="x")

    ctk.CTkLabel(info_frame, text="Time:").grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
    self._time_lbl = ctk.CTkLabel(info_frame, text="00:00:00.000")
    self._time_lbl.grid(row=0, column=1, padx=(0, 15), pady=5, sticky="w")

    ctk.CTkLabel(info_frame, text="Frame:").grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")
    self._frame_lbl = ctk.CTkLabel(info_frame, text="0 / 0")
    self._frame_lbl.grid(row=0, column=3, padx=(0, 15), pady=5, sticky="w")

    ctk.CTkLabel(info_frame, text="FPS:").grid(row=0, column=4, padx=(10, 5), pady=5, sticky="w")
    self._fps_lbl = ctk.CTkLabel(info_frame, text="--")
    self._fps_lbl.grid(row=0, column=5, padx=(0, 10), pady=5, sticky="w")
    
    # Save button
    info_frame.columnconfigure(6, weight=1)
    self._save_button = ctk.CTkButton(info_frame, text="Save", command=self._save_frame)
    self._save_button.grid(row=0, column=6, padx=10, pady=5, sticky="e")

  def load_media(self, file_path: str, duration_s: float, fps_str: str) -> None:
    """ Loads media file, and media info, then displays the displays the first frame"""

    self._file_path = file_path

    try:
      num, den = fps_str.split("/")
      self._fps = float(num) / float(den) if float(den) != 0 else 30.0
    except (ValueError, ZeroDivisionError):
      try:
        self._fps = float(fps_str)
      except ValueError:
        self._fps = 30.0

    self._frame_duration_ms = 1000.0 / self._fps
    self._duration_ms = int(duration_s * 1000)
    self._current_ms = 0.0

    total_frames = int(self._duration_ms / self._frame_duration_ms)
    steps = max(total_frames, 1)

    self._slider.configure(to=self._duration_ms, number_of_steps=steps, state="normal")
    self._current_time.set(0)
    self._prev_btn.configure(state="normal")
    self._next_btn.configure(state="normal")

    self._fps_lbl.configure(text=f"{self._fps:.2f}")
    self._update_info_labels()
    self._extract_and_display(0.0)

  def _on_slider_move(self, value: float) -> None:
    """ Finds frame when slider handle in moved """
    # Waits until previous seek is complete before starting next seek
    if self._seek_id is not None:
      self.after_cancel(self._seek_id)
    self._seek_id = self.after(50, lambda: self._seek_to(float(value)))

  def _seek_to(self, ms: float) -> None:
    """ Gets the selected tmestamp, extracts the frame, and updates information labels """
    self._seek_id = None
    self._current_ms = max(0.0, min(ms, self._duration_ms))
    self._current_time.set(self._current_ms)
    self._update_info_labels()
    self._extract_and_display(self._current_ms)

  def _prev_frame(self) -> None:
    """ Calculates timestamps to get the exact previous frame """
    target = self._current_ms - self._frame_duration_ms
    target = max(0.0, target)
    self._current_time.set(target)
    self._seek_to(target)

  def _next_frame(self) -> None:
    """ Calculates timestamps to get the exact next frame """
    target = self._current_ms + self._frame_duration_ms
    target = min(target, self._duration_ms)
    self._current_time.set(target)
    self._seek_to(target)

  def _extract_and_display(self, ms: float) -> None:
    """ Extracts exact frames using FFmpeg """
    if self._file_path is None:
      return

    seconds = ms / 1000.0
    timestamp = self.seconds_to_timestamp(seconds)

    extracted, frame_bytes  = self._ffmpeg_handler.extract_frame(self._file_path, timestamp)
    
    if extracted is False or frame_bytes is None:
      self._display_error()
      return
    
    self._img = Image.open(BytesIO(frame_bytes))

    # Store the full-resolution frame and display a scaled copy.
    self._img = self._img.convert("RGB")
    self._display_image()

  def _display_error(self) -> None:
    """ Displays an error message on the canvas if one occurs """
    self._canvas.delete("all")

    self._image_id = None

    self._text_id = self._canvas.create_text(self._canvas.winfo_width() // 2,
                                             self._canvas.winfo_height() // 2,
                                             text="Frame extraction failed",
                                             fill="white")

  def _display_image(self) -> None:
    """ Displays extracted frame in the canvas """
    if self._img is None:
      return
    
    # Sets image size to fit inside the canvas
    canvas_width = self._canvas.winfo_width()
    canvas_height = self._canvas.winfo_height()

    if canvas_width <= 1 or canvas_height <= 1:
      return

    img_width, img_height = self._img.size

    scale = min(canvas_width / img_width, canvas_height / img_height)

    # Prevent enlarging
    scale = min(scale, 1.0)

    new_width = max(1, int(img_width * scale))
    new_height = max(1, int(img_height * scale))

    resized = self._img.resize((new_width, new_height),
                               Image.Resampling.LANCZOS)

    self._photo = ImageTk.PhotoImage(resized)

    x = canvas_width // 2
    y = canvas_height // 2

    if self._image_id is None:
      self._image_id = self._canvas.create_image(x, y,
                                                image=self._photo,
                                                anchor="center")

    else:
      self._canvas.coords(self._image_id, x, y)
      self._canvas.itemconfigure(self._image_id, image=self._photo)
    
    if self._text_id is not None:
      self._canvas.delete(self._text_id)
      self._text_id = None

  def _on_canvas_resize(self, event: Event) -> None:
    """ Resizes the image to fit the canvas when the window is resized """
    if self._img is not None:
        self._display_image()

    elif self._text_id is not None:
        self._canvas.coords(self._text_id,
                            event.width // 2,
                            event.height // 2)

  def _update_info_labels(self) -> None:
    """ Update current frame and timestamp labels """
    self._time_lbl.configure(text=self.ms_text_converter(int(self._current_ms)))

    self._current_frame = int(self._current_ms / self._frame_duration_ms) if self._frame_duration_ms > 0 else 0
    total_frames = int(self._duration_ms / self._frame_duration_ms) if self._frame_duration_ms > 0 else 0
    self._frame_lbl.configure(text=f"{self._current_frame} / {total_frames}")
  
  def _save_frame(self, event: Event | None = None) -> None:
    """ Saves the current frame as a JPEG or PNG """
    if self._img is None:
      return
    
    if self._file_path is None:
      return
    
    # Gets basename of media file
    fullname, ext = os.path.splitext(self._file_path)
    name = os.path.basename(fullname)
    
    # Opens file dialog to get new file name, and save directory from a user
    file  = filedialog.asksaveasfilename(title="Save As",
                                        initialdir=os.path.expanduser("~"),
                                        initialfile=f"{name}_frame_{self._current_frame}",
                                        defaultextension=".png",
                                        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
                                        confirmoverwrite=True)
    
    if file == "" or file is None:
      return
    
    _, ext = os.path.splitext(file)
    
    # Only allows files to be saved a jpeg or png
    if ext not in (".png", ".jpg", ".jpeg"):
      CTkMessagebox(master=self,
                    title="Incompatible file type",
                    message=f"Screenshot cannot be saved as {ext}!",
                    icon="warning")
      return
    
    # Use PIL functions to save frame
    try:
      self._img.save(file)

    except Exception:
      CTkMessagebox(master=self,
                    title="Screenshot Error",
                    message="Failed to Take screenshot",
                    icon="cancel")
    else:
      CTkMessagebox(master=self,
                    title="Screenshot Successful",
                    message=f"Screenshot taken!\n{file}",
                    icon="check")