import customtkinter as ctk
import tkinter as tk

from tkinter import ttk, DoubleVar
from customtkinter import filedialog
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageTk

import subprocess
import io
import os

from utils.log_utils import logger

class FrameViewer(ctk.CTkToplevel):
  def __init__(self, master, ffmpeg_path: os.PathLike | str, device_os: str, **kwargs) -> None:
    super().__init__(master=master, **kwargs)

    self.title("Frame Viewer")
    self.minsize(850, 600)
    self.geometry("960x640")

    self._ffmpeg_path: os.PathLike | str = ffmpeg_path
    self._device_os: str = device_os

    self._file_path: os.PathLike | str | None = None
    self._duration_ms: int = 0
    self._fps: float = 30.0
    self._frame_duration_ms: float = 33.33
    self._current_ms: float = 0.0
    self._current_frame: int = 0

    self._current_time: DoubleVar = DoubleVar(self, value=0)
    self._img: Image.Image | None = None
    self._photo: ImageTk.PhotoImage | None = None
    self._seek_id: str | None = None

    self._create_ui()

  def _create_ui(self) -> None:
    self._canvas = tk.Canvas(self,
                             bg="black",
                             highlightthickness=0,
                             borderwidth=0)

    self._canvas.pack(padx=10,
                      pady=(10, 5),
                      fill="both",
                      expand=True)
    
    self._canvas.bind("<Configure>", self._on_canvas_resize)
    
    self._image_id = None
    self._text_id = self._canvas.create_text(0, 0,
                                             text="No media loaded",
                                             fill="white",
                                             anchor="center")

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
    
    info_frame.columnconfigure(6, weight=1)
    self._save_button = ctk.CTkButton(info_frame, text="Save", command=self._save_frame)
    self._save_button.grid(row=0, column=6, padx=10, pady=5, sticky="e")

  def load_media(self, file_path: os.PathLike | str, duration_s: float, fps_str: str) -> None:
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

  def _on_slider_move(self, value) -> None:
    if self._seek_id is not None:
      self.after_cancel(self._seek_id)
    self._seek_id = self.after(50, lambda: self._seek_to(float(value)))

  def _seek_to(self, ms: float) -> None:
    self._seek_id = None
    self._current_ms = max(0.0, min(ms, self._duration_ms))
    self._current_time.set(self._current_ms)
    self._update_info_labels()
    self._extract_and_display(self._current_ms)

  def _prev_frame(self) -> None:
    target = self._current_ms - self._frame_duration_ms
    target = max(0.0, target)
    self._current_time.set(target)
    self._seek_to(target)

  def _next_frame(self) -> None:
    target = self._current_ms + self._frame_duration_ms
    target = min(target, self._duration_ms)
    self._current_time.set(target)
    self._seek_to(target)

  def _extract_and_display(self, ms: float) -> None:
    """
    Extracts exact frames using FFmpeg and
    displays in a tkinter canvas
    """
    if self._file_path is None:
      return

    seconds = ms / 1000.0
    timestamp = self._seconds_to_timestamp(seconds)

    cmd = [
      str(self._ffmpeg_path),
      "-ss", timestamp,
      "-i", str(self._file_path),
      "-frames:v", "1",
      "-f", "image2pipe",
      "-vcodec", "png",
      "-loglevel", "error",
      "pipe:1"
    ]

    startupinfo = None
    creation_flags = 0

    if self._device_os == "Windows":
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      creation_flags = subprocess.CREATE_NO_WINDOW

    try:
      proc = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            startupinfo=startupinfo,
                            creationflags=creation_flags,
                            timeout=10)

      if proc.returncode != 0 or not proc.stdout:
        raise subprocess.CalledProcessError

      self._img = Image.open(io.BytesIO(proc.stdout))
    
    except subprocess.CalledProcessError:
      logger.exception(f"ffmpeg frame extraction failed: {proc.stderr.decode(errors='replace')}")
      self._display_error()

    except subprocess.TimeoutExpired:
      logger.exception("ffmpeg frame extraction timed out")
      self._display_error()

    except Exception as e:
      logger.exception(f"Frame extraction error: {e}")
      self._display_error()
    
    else:
      # Store the full-resolution frame and display a scaled copy.
      self._img = self._img.convert("RGB")
      self._display_image()

  def _display_error(self) -> None:
    self._canvas.delete("all")

    self._image_id = None

    self._text_id = self._canvas.create_text(self._canvas.winfo_width() // 2,
                                             self._canvas.winfo_height() // 2,
                                             text="Frame extraction failed",
                                             fill="white")

  def _display_image(self) -> None:
    if self._img is None:
      return

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

  def _on_canvas_resize(self, event):
    if self._img is not None:
        self._display_image()

    elif self._text_id is not None:
        self._canvas.coords(self._text_id,
                            event.width // 2,
                            event.height // 2)

  def _update_info_labels(self) -> None:
    self._time_lbl.configure(text=self._ms_text_converter(int(self._current_ms)))

    self._current_frame = int(self._current_ms / self._frame_duration_ms) if self._frame_duration_ms > 0 else 0
    total_frames = int(self._duration_ms / self._frame_duration_ms) if self._frame_duration_ms > 0 else 0
    self._frame_lbl.configure(text=f"{self._current_frame} / {total_frames}")
  
  def _save_frame(self, event=None) -> None:
    if self._img is None:
      return
    
    fullname, ext = os.path.splitext(self._file_path)
    name = os.path.basename(fullname)

    file  = filedialog.asksaveasfilename(title="Save As",
                                        initialdir=os.path.expanduser("~"),
                                        initialfile=f"{name}_frame_{self._current_frame}",
                                        defaultextension=".png",
                                        filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
                                        confirmoverwrite=True)
    
    if file == "":
      return
    
    _, ext = os.path.splitext(file)

    if ext not in (".png", ".jpg", ".jpeg"):
      CTkMessagebox(master=self,
                    title="Incompatible file type",
                    message=f"Screenshot cannot be saved as {ext}!",
                    icon="warning")
      return
  
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

  @staticmethod
  def _seconds_to_timestamp(s: float) -> str:
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    secs = s % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

  @staticmethod
  def _ms_text_converter(ms: int) -> str:
    s = ms // 1000
    ms_remainder = ms % 1000

    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)

    return f"{h:02d}:{m:02d}:{sec:02d}.{ms_remainder:03d}"
