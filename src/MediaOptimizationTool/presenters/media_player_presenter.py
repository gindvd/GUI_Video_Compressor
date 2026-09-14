from os import path

from models.media_attrs import MediaAttrs
from models.media_timestamps import MediaTimestamps

from views.media_player_frame import MediaPlayerFrame
from views import dialogs

from services.vlc_playback_service import VLCService

from utils.timestamp_untils import ms_to_player_timestamp, ms_to_timestamp


class MediaPlayerPresenter:

    def __init__(
        self,
        media_attrs: MediaAttrs,
        timestamps: MediaTimestamps,
        media_player_view: MediaPlayerFrame,
        vlc_service: VLCService,
    ):
        self._media_attrs: MediaAttrs = media_attrs
        self._timestamps: MediaTimestamps = timestamps

        self._player_view: MediaPlayerFrame = media_player_view
        self._vlc_service: VLCService = vlc_service

        self._currently_loaded_media: str | None = None
        self._update_id: str | None = None
        self._is_seeking: bool = False
        self._is_muted: bool = False

        self._bind_player_view()

    def on_play_pause_toggle(self) -> None:
        """Checks state to toggle between play and pause"""
        if self._vlc_service.is_media_player_ended():
            self._restart_media_player(
                paused=False, target_ms=self._player_view.start_time
            )

        elif self._vlc_service.is_media_player_playing():
            self._update_state_pause()

        elif self._vlc_service.is_media_player_paused():

            if self._vlc_service.current_time >= self._player_view.end_time:
                start_time = self._player_view.start_time

                self._vlc_service.current_time = start_time
                self._player_view.current_time = start_time

                timestamp = ms_to_player_timestamp(start_time)
                self._player_view.current_timestamp = timestamp

            self._update_state_play()

    def on_reverse_click(self) -> None:
        """Skips 10 seconds backwards"""
        current_time = self._vlc_service.current_time
        target_ms = current_time - 10000
        self._seek(target_ms=target_ms)

    def on_forward_click(self) -> None:
        """Skips 10 seconds forwards"""
        current_time = self._vlc_service.current_time
        target_ms = current_time + 10000
        self._seek(target_ms=target_ms)

    def on_start_time_change(self, value: int) -> None:
        """Updates start time to millisecond where FFmpeg begins trim"""
        end_time = self._player_view.end_time
        clamped = max(0, min(value, end_time))

        self._timestamps.start_time = ms_to_timestamp(clamped)
        timestamp = ms_to_player_timestamp(clamped)
        self._player_view.start_timestamp = timestamp

        self._seek(target_ms=clamped)

        trim_duration = end_time - clamped
        trim_timestamp = ms_to_player_timestamp(trim_duration)
        self._player_view.trim_duration_timestamp = trim_timestamp
        self._timestamps.trimmed_duration = ms_to_timestamp(trim_duration)

    def on_end_time_change(self, value: int) -> None:
        """Updates end time to millisecond where FFmpeg ends trim"""
        start_time = self._player_view.start_time
        full_duration = self._media_attrs.full_duration_ms
        clamped = max(start_time, min(value, full_duration))

        self._timestamps.end_time = ms_to_timestamp(clamped)
        timestamp = ms_to_player_timestamp(clamped)
        self._player_view.end_timestamp = timestamp

        self._seek(target_ms=clamped)

        trim_duration = clamped - start_time
        trim_timestamp = ms_to_player_timestamp(trim_duration)
        self._player_view.trim_duration_timestamp = trim_timestamp
        self._timestamps.trimmed_duration = ms_to_timestamp(trim_duration)

    def on_current_time_change(self, value: int) -> None:
        self._seek(target_ms=value)

    def on_volume_change(self, value: int) -> None:
        self._change_volume(value)

    def on_mute_toggle(self) -> None:
        self._change_mute(muted=not self._is_muted)

        if not self._is_muted:
            self._change_volume(volume=self._player_view.volume)

    def on_screenshot_click(self) -> None:
        if self._currently_loaded_media is None:
            return

        from tkinter import filedialog

        name, _ = path.splitext(self._currently_loaded_media)
        basename = path.basename(name)

        screenshot_filename = filedialog.asksaveasfilename(
            title="Save As",
            initialdir=path.expanduser("~"),
            initialfile=f"{basename}_screenshot",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
            confirmoverwrite=True,
        )

        if (
            screenshot_filename is None
            or screenshot_filename == ""
            or screenshot_filename is None
        ):
            return

        _, ext = path.splitext(screenshot_filename)
        ext = ext.lower()
        if ext not in (".png", ".jpg", ".jpeg"):
            dialogs.show_warning(
                master=self._player_view,
                title="Incompatible file type",
                message=f"Screenshot cannot be saved as {ext}!",
            )
            return

        return_code = self._vlc_service.take_snapshot(screenshot_filename)
        if return_code != 0:
            dialogs.show_error(
                master=self._player_view,
                title="Screenshot Error",
                message="Failed to Take screenshot",
            )
        else:
            dialogs.show_success(
                master=self._player_view,
                title="Screenshot Successful",
                message=f"Screenshot taken!\n{screenshot_filename}",
            )

    def load_media(self, media_file: str) -> None:
        """Asyncly loads media into VLC player for playback and trimming on a separate thread"""
        if media_file is None or not path.isfile(media_file):
            return

        self._currently_loaded_media = media_file
        self._player_view.set_initial_states(state="disabled")

        self._vlc_service.load_media_async(
            media_file,
            on_loaded=lambda: self._player_view.after(
                0, self._finish_loading, media_file
            ),
            on_error=lambda: self._player_view.after(
                0,
                self._handle_load_error,
                media_file,
            ),
        )

    def _handle_load_error(self, media_file: str) -> None:
        """Displays an error if media could not be loaded into the player"""
        if self._currently_loaded_media != media_file:
            return

        self._player_view.set_initial_states(state="disabled")
        dialogs.show_error(
            master=self._player_view,
            title="Media Load Error",
            message=f"Failed to load media.",
        )

    def _reset_vlc(self, media_file: str) -> None:
        """Destroys and rebuilds the VLC Instance if error occurs while media is already loaded"""
        self._vlc_service.teardown_instance_async(
            on_complete=lambda: self._player_view.after(0, self.load_media, media_file),
            on_error=lambda: self._player_view.after(
                0,
                self._handle_load_error,
                media_file,
            ),
        )

    def _finish_loading(self, media_file: str) -> None:
        """Finishes setting up after media is successfully loaded into VLC player"""
        if self._currently_loaded_media != media_file:
            return

        self._vlc_service.display_media(self._player_view.media_viewer.winfo_id())
        self._player_view.set_initial_states(state="normal")
        self._player_view.set_play_icon(is_playing=False)
        self._initialize_audio()

        # Displays a frame as thumbnail
        self._vlc_service.play_media()
        self._player_view.after(100, self._vlc_service.pause_media)

        self._initialize_times()

    def _initialize_audio(self) -> None:
        """Checks if media file has audio tracks before setting audio"""
        if self._media_attrs.has_audio:
            self._player_view.volume_btn_state = "normal"
            self._player_view.volume_slider_state = "normal"
            self._change_volume(volume=100)
        else:
            self._player_view.volume_btn_state = "disabled"
            self._player_view.volume_slider_state = "disabled"
            self._change_volume(volume=0)

    def _initialize_times(self) -> None:
        """Initilizes time related UI elements after media is loaded"""
        self._player_view.start_time = 0
        start_timestamp = ms_to_player_timestamp(0)
        self._player_view.start_timestamp = start_timestamp

        self._player_view.current_time = 0
        current_timestamp = ms_to_player_timestamp(0)
        self._player_view.current_timestamp = current_timestamp

        duration = self._media_attrs.full_duration_ms

        self._player_view.configure_trim_slider(to=duration, steps=duration)
        self._player_view.end_time = duration

        duration_timestamp = ms_to_player_timestamp(duration)

        self._player_view.end_timestamp = duration_timestamp
        self._player_view.full_duration_timestamp = duration_timestamp
        self._player_view.trim_duration_timestamp = duration_timestamp

    def _start_progress_update_loop(self) -> None:
        """
        Starts loop to update current timestamp and UI elements.

        Only starts an update loop if one has not started yet.
        """
        if self._update_id is None:
            self._update_view()

    def _update_view(self) -> None:
        """
        Checks the players state every 33 ms before updating UI

        Loop will only be run while media is playing
        Exits loop if player has paused, stopped, or ended
        Rebuilds player if error occurs
        """
        self._update_id = None
        if self._currently_loaded_media is None:
            return

        # Reubuilds VLC player if an error occurs during playback
        if self._vlc_service.is_media_player_errored():
            self._reset_vlc(self._currently_loaded_media)
            return

        # Don't do anything for stopped media
        # As Player will either be destroyed or rebuilt
        elif (
            self._vlc_service.is_media_player_stopped()
            or self._vlc_service.is_media_player_idle()
        ):
            return

        # Updates UI before exiting loop when media has reach EOF
        elif self._vlc_service.is_media_player_ended():
            self._update_state_ended()

            current_time_ms = self._player_view.end_time
            timestamp = ms_to_player_timestamp(current_time_ms)
            self._player_view.current_timestamp = timestamp
            self._restart_media_player(paused=True, target_ms=current_time_ms)

            return

        # Updates UI and exits if media is paused
        elif self._vlc_service.is_media_player_paused():
            current_time_ms = max(0, self._vlc_service.current_time)
            timestamp = ms_to_player_timestamp(current_time_ms)
            self._player_view.current_timestamp = timestamp
            return

        # Updates UI while media is playing and not seeking
        # UI is not updated when media is seeking
        elif self._vlc_service.is_media_player_playing() and not self._is_seeking:
            current_time_ms = self._vlc_service.current_time
            self._player_view.current_time = current_time_ms

            end_time = self._player_view.end_time

            # Paused media and exits if media has reached the changed end time
            if current_time_ms >= end_time:
                self._player_view.current_time = end_time

                timestamp = ms_to_player_timestamp(self._player_view.end_time)
                self._player_view.current_timestamp = timestamp
                self._update_state_pause()
                return

            timestamp = ms_to_player_timestamp(current_time_ms)
            self._player_view.current_timestamp = timestamp

        self._update_id = self._player_view.after(33, self._update_view)

    def _restart_media_player(self, paused: bool, target_ms: int) -> None:
        """Reset ended media, seek after VLC starts, then restore intent."""
        self._vlc_service.reset_media()
        self._vlc_service.display_media(self._player_view.media_viewer.winfo_id())
        self._vlc_service.play_media()
        self._player_view.current_time = target_ms
        self._player_view.after(100, self._complete_restart, paused, target_ms, 0)

    def _complete_restart(self, paused: bool, target_ms: int, attempt: int) -> None:
        """Finish a restart once VLC is in a state that accepts a seek"""
        if self._currently_loaded_media is None:
            return

        if self._vlc_service.is_media_player_errored():
            self._reset_vlc(self._currently_loaded_media)
            return

        ready = (
            self._vlc_service.is_media_player_playing()
            or self._vlc_service.is_media_player_paused()
        )

        if not ready and attempt < 10:
            self._player_view.after(
                50, self._complete_restart, paused, target_ms, attempt + 1
            )
            return

        self._vlc_service.seek_to(target_ms)
        self._player_view.current_time = target_ms
        self._player_view.current_timestamp = ms_to_player_timestamp(target_ms)

        if paused:
            self._update_state_pause()
        else:
            self._update_state_play()

    def _update_state_ended(self) -> None:
        """Updates UI when media has ended"""
        self._player_view.set_play_icon(is_playing=False)
        self._player_view.screenshot_state = "normal"

    def _update_state_pause(self) -> None:
        """Updates UI when media has paused"""
        self._vlc_service.pause_media()
        self._player_view.set_play_icon(is_playing=False)
        self._player_view.screenshot_state = "normal"

    def _update_state_play(self) -> None:
        """
        Updates UI when media has started playing
        Restarts update loop if it has stopped
        """
        self._vlc_service.play_media()
        self._player_view.set_play_icon(is_playing=True)
        self._player_view.screenshot_state = "disabled"
        self._start_progress_update_loop()

    def _seek(self, target_ms: int) -> None:
        """Seek without changing the user's playback intent."""
        if self._currently_loaded_media is None:
            return

        self._is_seeking = True
        try:
            start_time = self._player_view.start_time
            end_time = self._player_view.end_time
            clamped_target = max(start_time, min(target_ms, end_time))
            was_playing = self._vlc_service.is_media_player_playing()

            self._player_view.current_time = clamped_target
            self._player_view.current_timestamp = ms_to_player_timestamp(clamped_target)

            if self._vlc_service.is_media_player_ended():
                self._restart_media_player(paused=True, target_ms=clamped_target)
                return

            if (
                self._vlc_service.is_media_player_stopped()
                or self._vlc_service.is_media_player_idle()
                or self._vlc_service.is_media_player_errored()
            ):
                return

            self._vlc_service.seek_to(clamped_target)

            if was_playing:
                self._start_progress_update_loop()

        finally:
            self._is_seeking = False

    def _change_volume(self, volume: int) -> None:
        """Updates vlc player and UI when volume is changed"""
        self._player_view.volume = volume
        self._vlc_service.set_volume(volume)
        if volume == 0:
            self._change_mute(muted=True)
            return

        # Unmutes player if volume changes when volume is not 0
        # And player is already muted
        if self._is_muted:
            self._change_mute(muted=False)

    def _change_mute(self, muted: bool) -> None:
        """Updates vlc player and UI when volume is muted or unmuted"""
        self._is_muted = muted
        self._player_view.set_mute_icon(muted=muted)
        self._vlc_service.mute(muted=muted)

    def _bind_player_view(self) -> None:
        self._player_view.on_play_pause_toggle = self.on_play_pause_toggle
        self._player_view.on_reverse_click = self.on_reverse_click
        self._player_view.on_forward_click = self.on_forward_click
        self._player_view.on_start_time_change = self.on_start_time_change
        self._player_view.on_current_time_change = self.on_current_time_change
        self._player_view.on_end_time_change = self.on_end_time_change
        self._player_view.on_volume_change = self.on_volume_change
        self._player_view.on_mute_toggle = self.on_mute_toggle
        self._player_view.on_screenshot_click = self.on_screenshot_click
