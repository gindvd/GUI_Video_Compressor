import customtkinter as ctk
from tkinter import Event

from CTkTrimSlider import CTkTrimSlider

from PIL import Image

from typing import Any
from collections.abc import Callable

from utils.resource_paths import get_button_image_path


class MediaPlayerFrame(ctk.CTkFrame):

    def __init__(self, master: Any, **kwargs):
        super().__init__(master=master, **kwargs)

        self.on_play_pause_toggle: Callable[..., Any] | None = None
        self.on_reverse_click: Callable[..., Any] | None = None
        self.on_forward_click: Callable[..., Any] | None = None
        self.on_start_time_change: Callable[..., Any] | None = None
        self.on_current_time_change: Callable[..., Any] | None = None
        self.on_end_time_change: Callable[..., Any] | None = None
        self.on_volume_change: Callable[..., Any] | None = None
        self.on_mute_toggle: Callable[..., Any] | None = None
        self.on_screenshot_click: Callable[..., Any] | None = None

        self._start_time: ctk.DoubleVar = ctk.DoubleVar(self, value=0)
        self._current_time: ctk.DoubleVar = ctk.DoubleVar(self, value=0.5)
        self._end_time: ctk.DoubleVar = ctk.DoubleVar(self, value=1)

        self._volume: ctk.IntVar = ctk.IntVar(self, value=100)

        self._start_timestamp: ctk.StringVar = ctk.StringVar(self, value="00:00:00")
        self._current_timestamp: ctk.StringVar = ctk.StringVar(self, value="00:00:00")
        self._end_timestamp: ctk.StringVar = ctk.StringVar(self, value="00:00:00")
        self._full_duration_timestamp: ctk.StringVar = ctk.StringVar(
            self, value="00:00:00"
        )
        self._trim_duration_timestamp: ctk.StringVar = ctk.StringVar(
            self, value="00:00:00"
        )
        self._playback_range_timestamp: ctk.StringVar = ctk.StringVar(
            self, value="00:00:00 / 00:00:00"
        )

        self._volume_hide_id: str | None = None
        self._volume_popup_visible: bool = False
        self._loading_label: ctk.CTkLabel | None = None

        self._set_video_control_icons()

        self._build()

    def _set_video_control_icons(self) -> None:
        """Creates icons for the control buttons"""
        icon_size: tuple[int, int] = (20, 20)

        play_png = get_button_image_path("play_button.png")
        pause_png = get_button_image_path("pause_button.png")
        reverse_png = get_button_image_path("reverse.png")
        forward_png = get_button_image_path("forward.png")
        mute_png = get_button_image_path("muted_volume.png")
        unmute_png = get_button_image_path("unmuted_volume.png")
        camera_png = get_button_image_path("camera.png")

        self._play_icon: ctk.CTkImage = ctk.CTkImage(
            light_image=Image.open(play_png),
            dark_image=Image.open(play_png),
            size=icon_size,
        )
        self._pause_icon: ctk.CTkImage = ctk.CTkImage(
            light_image=Image.open(pause_png),
            dark_image=Image.open(pause_png),
            size=icon_size,
        )
        self._reverse_icon: ctk.CTkImage = ctk.CTkImage(
            light_image=Image.open(reverse_png),
            dark_image=Image.open(reverse_png),
            size=icon_size,
        )
        self._forward_icon: ctk.CTkImage = ctk.CTkImage(
            light_image=Image.open(forward_png),
            dark_image=Image.open(forward_png),
            size=icon_size,
        )
        self._mute_icon: ctk.CTkImage = ctk.CTkImage(
            light_image=Image.open(mute_png),
            dark_image=Image.open(mute_png),
            size=icon_size,
        )
        self._unmute_icon: ctk.CTkImage = ctk.CTkImage(
            light_image=Image.open(unmute_png),
            dark_image=Image.open(unmute_png),
            size=icon_size,
        )
        self._camera_icon: ctk.CTkImage = ctk.CTkImage(
            light_image=Image.open(camera_png),
            dark_image=Image.open(camera_png),
            size=icon_size,
        )


    def _build(self) -> None:
        # Container for the entire media player area.
        self._content_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self._content_frame.pack(
            fill="both",
            expand=True,
            padx=0,
            pady=0,
        )

        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_rowconfigure(0, weight=1)

        # Video viewer
        self.media_viewer = ctk.CTkFrame(
            self._content_frame,
            fg_color="black",
            corner_radius=0,
        )
        self.media_viewer.grid(
            row=0,
            column=0,
            padx=0,
            pady=0,
            sticky="nsew",
        )

        # Video controls background
        self._control_panel = ctk.CTkFrame(
            self._content_frame,
            height=48,
            fg_color="black",
            corner_radius=0,
        )
        self._control_panel.grid(
            row=1,
            column=0,
            padx=0,
            pady=0,
            sticky="ew",
        )

        # Timestamp viewer
        self._timestamp_viewer = ctk.CTkFrame(
            self._content_frame,
            height=48,
            fg_color=("gray75", "gray25"),
            corner_radius=10,
        )
        self._timestamp_viewer.grid(
            row=2,
            column=0,
            padx=0,
            pady=(10, 0),
            sticky="ew",
        )

        self._build_video_controls()
        self._build_timestamp_viewer()

    def _build_video_controls(self) -> None:
        self._control_panel.columnconfigure(4, weight=4)

        self._play_pause_btn = ctk.CTkButton(
            self._control_panel,
            width=36,
            height=36,
            fg_color="transparent",
            image=self._play_icon,
            text="",
            state="disabled",
            command=self._handle_play_pause_toggle,
        )
        self._play_pause_btn.grid(row=1, column=0, padx=5, pady=5)

        self._reverse_btn = ctk.CTkButton(
            self._control_panel,
            width=36,
            height=36,
            fg_color="transparent",
            image=self._reverse_icon,
            text="",
            state="disabled",
            command=self._handle_reverse_click,
        )
        self._reverse_btn.grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
        )

        self._forward_btn = ctk.CTkButton(
            self._control_panel,
            width=36,
            height=36,
            fg_color="transparent",
            image=self._forward_icon,
            text="",
            state="disabled",
            command=self._handle_forward_click,
        )
        self._forward_btn.grid(
            row=1,
            column=2,
            padx=5,
            pady=5,
        )

        self._time_range_lbl = ctk.CTkLabel(
            self._control_panel,
            textvariable=self._playback_range_timestamp,
            width=125,
        )
        self._time_range_lbl.grid(
            row=1,
            column=3,
            padx=5,
            pady=5,
        )

        self._trim_slider = CTkTrimSlider(
            self._control_panel,
            state="disabled",
            left_button_command=self._handle_start_time_change,
            right_button_command=self._handle_end_time_change,
            center_button_command=self._handle_current_time_change,
            left_button_var=self._start_time,
            right_button_var=self._end_time,
            center_button_var=self._current_time,
        )
        self._trim_slider.grid(
            row=1,
            column=4,
            padx=5,
            pady=5,
            sticky="ew",
        )

        # Volume container frame for stable hover events
        self._volume_container = ctk.CTkFrame(
            self._control_panel, fg_color="transparent"
        )
        self._volume_container.grid(row=1, column=5, padx=5, pady=5)

        self._volume_btn = ctk.CTkButton(
            self._volume_container,
            width=36,
            height=36,
            fg_color="transparent",
            image=self._unmute_icon,
            text="",
            state="disabled",
            command=self._handle_mute_toggle,
        )
        self._volume_btn.pack()

        # Convert volume popup to a CTkToplevel window to float properly over everything on Windows & Linux
        self._volume_popup = ctk.CTkToplevel(self)
        self._volume_popup.withdraw()  # Hidden by default
        self._volume_popup.overrideredirect(True)  # Remove window borders/title bar
        self._volume_popup.attributes("-topmost", True)  # Keep above main window

        self._volume_slider = ctk.CTkSlider(
            self._volume_popup,
            height=100,
            width=20,
            button_corner_radius=4,
            from_=0,
            to=100,
            number_of_steps=100,
            state="disabled",
            orientation="vertical",
            command=self._handle_volume_change,
            variable=self._volume,
        )
        self._volume_slider.set(100)
        self._volume_slider.pack(padx=6, pady=8)

        # Hover bindings
        self._volume_container.bind("<Enter>", self._show_volume_popup)
        self._volume_container.bind("<Leave>", self._schedule_hide_volume_popup)
        self._volume_btn.bind("<Enter>", self._show_volume_popup)
        self._volume_btn.bind("<Leave>", self._schedule_hide_volume_popup)
        self._volume_popup.bind("<Enter>", self._cancel_hide_volume_popup)
        self._volume_popup.bind("<Leave>", self._schedule_hide_volume_popup)
        self._volume_slider.bind("<Enter>", self._cancel_hide_volume_popup)
        self._volume_slider.bind("<Leave>", self._schedule_hide_volume_popup)

        self._screenshot_btn = ctk.CTkButton(
            self._control_panel,
            width=36,
            height=36,
            fg_color="transparent",
            image=self._camera_icon,
            text="",
            state="disabled",
            anchor="center",
            command=self._handle_screenshot_click,
        )
        self._screenshot_btn.grid(
            row=1,
            column=6,
            padx=5,
            pady=5,
        )
    
    def _build_timestamp_viewer(self) -> None:
        self._trim_info_frame = ctk.CTkFrame(
            self._timestamp_viewer,
            fg_color="transparent",
        )
        self._trim_info_frame.pack(anchor="center", expand=True)

        trim_info_font = ctk.CTkFont(size=11)
        trim_duration_font = ctk.CTkFont(size=11, weight="bold")

        self._start_time_info_lbl = ctk.CTkLabel(
            self._trim_info_frame,
            textvariable=self._start_timestamp,
            font=trim_info_font,
        )
        self._trim_duration_info_lbl = ctk.CTkLabel(
            self._trim_info_frame,
            textvariable=self._trim_duration_timestamp,
            font=trim_duration_font,
        )
        self._end_time_info_lbl = ctk.CTkLabel(
            self._trim_info_frame,
            textvariable=self._end_timestamp,
            font=trim_info_font,
        )
        
        ctk.CTkLabel(self._trim_info_frame, text="Start Time:", font=trim_info_font,).grid(
            padx=(20,5), pady=0, row=0, column=0, sticky="w"
        )
        self._start_time_info_lbl.grid(padx=(5, 20), pady=0, row=0, column=1, sticky="w")

        ctk.CTkLabel(self._trim_info_frame, text="Trim Duration:", font=trim_duration_font).grid(
            padx=(20,5), pady=0, row=0, column=2
        )
        self._trim_duration_info_lbl.grid(padx=(5, 20), pady=0, row=0, column=3)

        ctk.CTkLabel(self._trim_info_frame, text="End Time:", font=trim_info_font,).grid(
            padx=(20,5), pady=0, row=0, column=4, sticky="e"
        )
        self._end_time_info_lbl.grid(padx=(5, 20), pady=0, row=0, column=5, sticky="e")

    def _show_volume_popup(self, event: Event | None = None) -> None:
        """Displays volume slider using absolute screen coordinates via CTkToplevel"""

        if self._volume_hide_id is not None:
            self.after_cancel(self._volume_hide_id)
            self._volume_hide_id = None

        if self._volume_popup_visible:
            return

        self._volume_container.update_idletasks()
        btn_x = self._volume_container.winfo_rootx()
        btn_y = self._volume_container.winfo_rooty()
        btn_w = self._volume_container.winfo_width()

        self._volume_popup.update_idletasks()
        popup_w = self._volume_popup.winfo_reqwidth()
        popup_h = self._volume_popup.winfo_reqheight()

        x = btn_x + (btn_w - popup_w) // 2
        y = btn_y - popup_h - 4

        self._volume_popup.geometry(f"+{x}+{y}")
        self._volume_popup.deiconify()
        self._volume_popup.lift()
        self._volume_popup_visible = True

    def _schedule_hide_volume_popup(self, event: Event | None = None) -> None:
        """Waits a few milliseconds to hide volume slider"""
        if self._volume_hide_id is not None:
            self.after_cancel(self._volume_hide_id)
        self._volume_hide_id = self.after(300, self._hide_volume_popup)

    def _cancel_hide_volume_popup(self, event: Event | None = None) -> None:
        """Cancels volume slider hiding if the user starts hovering"""
        if self._volume_hide_id is not None:
            self.after_cancel(self._volume_hide_id)
            self._volume_hide_id = None

    def _hide_volume_popup(self) -> None:
        """Hides the volume slider"""
        self._volume_popup.withdraw()
        self._volume_popup_visible = False
        self._volume_hide_id = None

    def _update_playback_range_timestamp(self) -> None:
        self._playback_range_timestamp.set(
            f"{self._current_timestamp.get()} / {self._full_duration_timestamp.get()}"
        )

    # Handlers
    def _handle_play_pause_toggle(self) -> None:
        if self.on_play_pause_toggle:
            self.on_play_pause_toggle()

    def _handle_reverse_click(self) -> None:
        if self.on_reverse_click:
            self.on_reverse_click()

    def _handle_forward_click(self) -> None:
        if self.on_forward_click:
            self.on_forward_click()

    def _handle_start_time_change(self, value: float) -> None:
        if self.on_start_time_change:
            self.on_start_time_change(int(value))

    def _handle_current_time_change(self, value: float) -> None:
        if self.on_current_time_change:
            self.on_current_time_change(int(value))

    def _handle_end_time_change(self, value: float) -> None:
        if self.on_end_time_change:
            self.on_end_time_change(int(value))

    def _handle_volume_change(self, value: float) -> None:
        if self.on_volume_change:
            self.on_volume_change(int(value))

    def _handle_mute_toggle(self) -> None:
        if self.on_mute_toggle:
            self.on_mute_toggle()

    def _handle_screenshot_click(self) -> None:
        if self.on_screenshot_click:
            self.on_screenshot_click()

    # Getters and setters
    @property
    def start_time(self) -> int:
        return int(self._start_time.get())

    @start_time.setter
    def start_time(self, value: int) -> None:
        self._start_time.set(value)

    @property
    def current_time(self) -> int:
        return int(self._current_time.get())

    @current_time.setter
    def current_time(self, value: int) -> None:
        self._current_time.set(value)

    @property
    def end_time(self) -> int:
        return int(self._end_time.get())

    @end_time.setter
    def end_time(self, value: int) -> None:
        self._end_time.set(value)

    @property
    def volume(self) -> int:
        return self._volume.get()

    @volume.setter
    def volume(self, value: int) -> None:
        clamped_value = max(0, min(100, value))
        self._volume.set(clamped_value)

    @property
    def start_timestamp(self) -> str:
        return self._start_timestamp.get()

    @start_timestamp.setter
    def start_timestamp(self, timestamp: str) -> None:
        self._start_timestamp.set(timestamp)

    @property
    def end_timestamp(self) -> str:
        return self._end_timestamp.get()

    @end_timestamp.setter
    def end_timestamp(self, timestamp: str) -> None:
        self._end_timestamp.set(timestamp)

    @property
    def current_timestamp(self) -> str:
        return self._current_timestamp.get()

    @current_timestamp.setter
    def current_timestamp(self, timestamp: str) -> None:
        self._current_timestamp.set(timestamp)
        self._update_playback_range_timestamp()

    @property
    def full_duration_timestamp(self) -> str:
        return self._full_duration_timestamp.get()

    @full_duration_timestamp.setter
    def full_duration_timestamp(self, timestamp: str) -> None:
        self._full_duration_timestamp.set(timestamp)
        self._update_playback_range_timestamp()

    @property
    def trim_duration_timestamp(self) -> str:
        return self._trim_duration_timestamp.get()

    @trim_duration_timestamp.setter
    def trim_duration_timestamp(self, timestamp: str) -> None:
        self._trim_duration_timestamp.set(timestamp)

    @property
    def screenshot_state(self) -> str:
        return self._screenshot_btn.cget("state")

    @screenshot_state.setter
    def screenshot_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return
        self._screenshot_btn.configure(state=state)

    @property
    def volume_btn_state(self) -> str:
        return self._volume_btn.cget("state")

    @volume_btn_state.setter
    def volume_btn_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return
        self._volume_btn.configure(state=state)

    @property
    def volume_slider_state(self) -> str:
        return self._volume_slider.cget("state")

    @volume_slider_state.setter
    def volume_slider_state(self, state: str) -> None:
        if state not in ("normal", "disabled"):
            return
        self._volume_slider.configure(state=state)

    # State Setters
    def set_initial_states(self, state: str) -> None:
        """Enables or disables all user interaction controls."""
        if state not in ("normal", "disabled"):
            return

        self._play_pause_btn.configure(state=state)
        self._reverse_btn.configure(state=state)
        self._forward_btn.configure(state=state)
        self._trim_slider.configure(state=state)
        self._volume_btn.configure(state=state)
        self._volume_slider.configure(state=state)
        self._screenshot_btn.configure(state=state)

    def set_play_icon(self, is_playing: bool) -> None:
        self._play_pause_btn.configure(
            image=self._pause_icon if is_playing else self._play_icon
        )

    def set_mute_icon(self, muted: bool) -> None:
        self._volume_btn.configure(
            image=self._mute_icon if muted else self._unmute_icon
        )

    def configure_trim_slider(self, to: int, steps: int) -> None:
        self._trim_slider.configure(
            require_redraw=True,
            to=to,
            number_of_steps=steps,
        )

        self._trim_slider.set("left_value", 0)
        self._trim_slider.set("center_value", 0)
        self._trim_slider.set("right_value", to)
    
    def show_loading(self) -> None: 
        """Displays a loading indicator over the video viewer""" 
        if self._loading_label is not None: 
            return 
        
        self._loading_label = ctk.CTkLabel( self.media_viewer, text="Loading...", font=ctk.CTkFont(size=16), ) 
        self._loading_label.place( relx=0.5, rely=0.5, anchor="center", )

        self._loading_label.lift() 
        self.update_idletasks() 
    
    def hide_loading(self) -> None: 
        """Removes the loading indicator from the video viewer""" 
        if self._loading_label is None: 
            return 
        
        self._loading_label.destroy()
        self._loading_label = None