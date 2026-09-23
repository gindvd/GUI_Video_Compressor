import customtkinter as ctk
from tkinter import Event

from collections.abc import Callable
from typing import Any

from PIL import ImageTk


class FrameViewer(ctk.CTkToplevel):
    def __init__(self, master: Any, **kwargs) -> None:
        super().__init__(master=master, **kwargs)

        self.title("Frame Viewer")
        self.minsize(750, 500)
        self.resizable(True, True)

        self.on_previous_frame_change: Callable[..., Any] | None = None
        self.on_next_frame_change: Callable[..., Any] | None = None
        self.on_slider_move: Callable[..., Any] | None = None
        self.on_save_frame: Callable[..., Any] | None = None
        self.on_canvas_resize: Callable[..., Any] | None = None

        self._current_time_ms: ctk.DoubleVar = ctk.DoubleVar(self, value=0)
        self._current_timestamp: ctk.StringVar = ctk.StringVar(
            self, value="00:00:00.000"
        )
        self._frame_rate: ctk.StringVar = ctk.StringVar(self, value="--")
        self._frame_per_total: ctk.StringVar = ctk.StringVar(self, value="0 / 0")

        self._build_ui()

    def _build_ui(self) -> None:
        """Builds and places all widgets and UI elements"""
        fg_color = ("gray75", "gray25")
        font = ctk.CTkFont(size=20)

        self._container = ctk.CTkFrame(
            self, fg_color="black", corner_radius=10,
        )
        self._container.pack(padx=10, pady=(10, 5), fill="both", expand=True)

        # Image canvas
        self._frame_canvas = ctk.CTkCanvas(
            self._container, bg="black", highlightthickness=0, borderwidth=0
        )

        self._frame_canvas.pack(padx=10, pady=10, fill="both", expand=True)

        # Resize the fame image when the window is resized
        self._frame_canvas.bind("<Configure>", self._handle_canvas_resize)

        self._image_id: int | None = None
        self._text_id: int | None = self._frame_canvas.create_text(
            0, 0, text="No media loaded", fill="white", anchor="center"
        )

        # Control frame: controls for fingding frames
        control_frame = ctk.CTkFrame(self, fg_color=fg_color, corner_radius=6)
        control_frame.pack(padx=10, pady=5, fill="x")
        control_frame.columnconfigure(1, weight=1)

        self._previous_btn = ctk.CTkButton(
            control_frame,
            text="<",
            width=35,
            height=30,
            font=font,
            state="disabled",
            command=self._handle_previous_frame_change,
        )
        self._previous_btn.grid(row=0, column=0, padx=(10, 5), pady=5)

        self._frame_slider = ctk.CTkSlider(
            control_frame,
            button_corner_radius=4,
            from_=0,
            to=1,
            number_of_steps=1,
            state="disabled",
            variable=self._current_time_ms,
            command=self._handle_slider_move,
        )
        self._frame_slider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self._next_btn = ctk.CTkButton(
            control_frame,
            text=">",
            width=35,
            height=30,
            font=font,
            state="disabled",
            command=self._handle_next_frame_change,
        )
        self._next_btn.grid(row=0, column=2, padx=(5, 10), pady=5)

        # Info Frame: Displays frame number, timestamp, and other media info
        info_frame = ctk.CTkFrame(self, fg_color=fg_color, corner_radius=6)
        info_frame.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(info_frame, text="Time:").grid(
            row=0, column=0, padx=(10, 5), pady=5, sticky="w"
        )
        self._time_lbl = ctk.CTkLabel(info_frame, textvariable=self._current_timestamp)
        self._time_lbl.grid(row=0, column=1, padx=(0, 15), pady=5, sticky="w")

        ctk.CTkLabel(info_frame, text="Frame:").grid(
            row=0, column=2, padx=(10, 5), pady=5, sticky="w"
        )
        self._frame_lbl = ctk.CTkLabel(info_frame, textvariable=self._frame_per_total)
        self._frame_lbl.grid(row=0, column=3, padx=(0, 15), pady=5, sticky="w")

        ctk.CTkLabel(info_frame, text="FPS:").grid(
            row=0, column=4, padx=(10, 5), pady=5, sticky="w"
        )
        self._fps_lbl = ctk.CTkLabel(info_frame, textvariable=self._frame_rate)
        self._fps_lbl.grid(row=0, column=5, padx=(0, 10), pady=5, sticky="w")

        # Save button
        info_frame.columnconfigure(6, weight=1)
        self._save_button = ctk.CTkButton(
            info_frame,
            text="Save",
            state="disabled",
            command=self._handle_save_frame,
        )
        self._save_button.grid(row=0, column=6, padx=10, pady=5, sticky="e")

    # Handlers
    def _handle_previous_frame_change(self, event: Event | None = None) -> None:
        if self.on_previous_frame_change:
            self.on_previous_frame_change()

    def _handle_next_frame_change(self, event: Event | None = None) -> None:
        if self.on_next_frame_change:
            self.on_next_frame_change()

    def _handle_slider_move(self, value: float) -> None:
        if self.on_slider_move:
            self.on_slider_move(int(value))

    def _handle_save_frame(self, event: Event | None = None) -> None:
        if self.on_save_frame:
            self.on_save_frame()

    def _handle_canvas_resize(self, event: Event | None = None) -> None:
        if self.on_canvas_resize:
            self.on_canvas_resize()

    @property
    def timestamp(self) -> str:
        return self._current_timestamp.get()

    @timestamp.setter
    def timestamp(self, time: str) -> None:
        self._current_timestamp.set(time)

    @property
    def frame_rate(self) -> str:
        return self._frame_rate.get()

    @frame_rate.setter
    def frame_rate(self, fps: str) -> None:
        self._frame_rate.set(fps)

    @property
    def total_frames(self) -> str:
        _, total = self._frame_per_total.get().split("/")

        return total.strip()

    @total_frames.setter
    def total_frames(self, total: str) -> None:
        frame, _ = self._frame_per_total.get().split("/")

        self._frame_per_total.set(f"{frame.strip()} / {total}")

    @property
    def current_frame(self) -> str:
        frame, _ = self._frame_per_total.get().split("/")

        return frame.strip()

    @current_frame.setter
    def current_frame(self, frame: str) -> None:
        _, total = self._frame_per_total.get().split("/")

        self._frame_per_total.set(f"{frame} / {total.strip()}")

    @property
    def current_time_ms(self) -> int:
        return int(self._current_time_ms.get())

    @current_time_ms.setter
    def current_time_ms(self, value: int) -> None:
        self._current_time_ms.set(value)

    @property
    def save_button_state(self) -> str:
        return self._save_button.cget("state")

    @save_button_state.setter
    def save_button_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._save_button.configure(state=state)

    @property
    def next_btn_state(self) -> str:
        return self._next_btn.cget("state")

    @next_btn_state.setter
    def next_btn_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._next_btn.configure(state=state)

    @property
    def previous_btn_state(self) -> str:
        return self._previous_btn.cget("state")

    @previous_btn_state.setter
    def previous_btn_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._previous_btn.configure(state=state)

    @property
    def frame_slider_state(self) -> str:
        return self._frame_slider.cget("state")

    @frame_slider_state.setter
    def frame_slider_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return

        self._frame_slider.configure(state=state)

    @property
    def frame_canvas(self) -> ctk.CTkCanvas:
        return self._frame_canvas

    @property
    def image_id(self) -> int | None:
        return self._image_id

    @property
    def text_id(self) -> int | None:
        return self._text_id

    def display_frame(self, x: float, y: float, frame: ImageTk.PhotoImage) -> None:
        if self._image_id is None:
            self._image_id = self._frame_canvas.create_image(
                x, y, image=frame, anchor="center"
            )

        else:
            self._frame_canvas.coords(self._image_id, x, y)
            self._frame_canvas.itemconfigure(self._image_id, image=frame)

        if self._text_id is not None:
            self._frame_canvas.delete(self._text_id)
            self._text_id = None

    def display_error(self) -> None:
        self._frame_canvas.delete("all")

        self._image_id = None

        self._text_id = self._frame_canvas.create_text(
            self._frame_canvas.winfo_width() // 2,
            self._frame_canvas.winfo_height() // 2,
            text="Frame extraction failed",
            fill="white",
        )

    def configure_frame_slider(self, to: int, number_of_steps: int) -> None:
        self._frame_slider.configure(to=to, number_of_steps=number_of_steps)
