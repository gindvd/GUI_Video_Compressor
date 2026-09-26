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

        self._initial_frame_id: str | None = None

        self._bind_player_view()

    def on_play_pause_toggle(self) -> None:
        """Checks state to toggle between play and pause"""
        if self._vlc_service.is_media_player_ended():
            self._restart_media_player(
                paused=False,
                target_ms=self._player_view.start_time,
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
        """Updates the player volume from the volume slider"""
        self._change_volume(value)

    def on_mute_toggle(self) -> None:
        """Toggles mute while preserving the selected volume"""
        self._change_mute(muted=not self._is_muted)

    def _change_volume(self, volume: int) -> None:
        """Updates VLC and mute state when the volume changes"""
        volume = max(0, min(100, volume))

        self._player_view.volume = volume
        self._vlc_service.set_volume(volume)

        if volume == 0:
            self._change_mute(muted=True)

        elif self._is_muted:
            self._change_mute(muted=False)

    def _change_mute(self, muted: bool) -> None:
        """Updates VLC and UI mute state"""
        self._is_muted = muted

        self._player_view.set_mute_icon(muted=muted)
        self._vlc_service.mute(muted=muted)

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

        return_code = self._vlc_service.take_snapshot(
            screenshot_filename
        )

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

    def load_media(self, media_file: str | None) -> None:
        """
        Asynchronously loads media into VLC.

        The UI remains in its loading state until VLC has loaded the
        media and rendered its initial video frame.
        """
        if media_file is None or not path.isfile(media_file):
            return

        self._currently_loaded_media = media_file

        # Cancel any pending initial-frame check from a previous load.
        self._cancel_initial_frame_wait()

        # Disable player controls while VLC initializes.
        self._player_view.set_initial_states(state="disabled")

        # Tell the view that media loading has started.
        #
        # This method should display an indeterminate progress bar
        # and/or loading message.
        self._player_view.show_loading()

        self._vlc_service.load_media_async(
            media_file,
            on_loaded=lambda: self._player_view.after(
                0,
                self._finish_loading,
                media_file,
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

        self._cancel_initial_frame_wait()

        self._player_view.hide_loading()
        self._player_view.set_initial_states(state="disabled")

        dialogs.show_error(
            master=self._player_view,
            title="Media Load Error",
            message="Failed to load media.",
        )

    def _reset_vlc(self, media_file: str) -> None:
        """Destroys and rebuilds the VLC Instance if an error occurs"""
        self._cancel_initial_frame_wait()

        self._vlc_service.teardown_instance_async(
            on_complete=lambda: self._player_view.after(
                0,
                self.load_media,
                media_file,
            ),
            on_error=lambda: self._player_view.after(
                0,
                self._handle_load_error,
                media_file,
            ),
        )

    def _finish_loading(self, media_file: str) -> None:
        """
        Finishes setting up after media has been loaded into VLC.

        VLC has accepted the media at this point, but it may not have
        rendered a video frame yet. The controls therefore remain
        disabled until the initial frame is available.
        """
        if self._currently_loaded_media != media_file:
            return

        self._vlc_service.display_media(
            self._player_view.media_viewer.winfo_id()
        )

        self._initialize_audio()
        self._initialize_times()

        self._player_view.set_play_icon(is_playing=False)

        # Start VLC and wait until it has actually entered a playable
        # state before pausing on the initial frame.
        self._show_initial_frame()

    def _show_initial_frame(self) -> None:
        """
        Starts VLC so that the first video frame can be rendered.

        VLC's play() call is asynchronous, so we cannot immediately
        pause the player and expect a frame to have been displayed.
        """
        if self._currently_loaded_media is None:
            return

        self._vlc_service.play_media()

        self._initial_frame_id = self._player_view.after(
            50,
            self._wait_for_initial_frame,
            0,
        )

    def _wait_for_initial_frame(self, attempt: int) -> None:
        """
        Waits for VLC to enter Playing/Paused before allowing the
        initial frame to be displayed.

        A maximum of 20 attempts are made at 50 ms intervals.
        """
        self._initial_frame_id = None

        if self._currently_loaded_media is None:
            return

        if self._vlc_service.is_media_player_errored():
            media_file = self._currently_loaded_media
            self._handle_load_error(media_file)
            return

        ready = (
            self._vlc_service.is_media_player_playing()
            or self._vlc_service.is_media_player_paused()
        )

        if ready:
            # VLC has transitioned into a usable playback state.
            #
            # Give the video output another short interval to actually
            # decode/render the first frame before pausing.
            self._initial_frame_id = self._player_view.after(
                100,
                self._finish_initial_frame,
            )
            return

        # Retry for up to approximately one second.
        if attempt < 20:
            self._initial_frame_id = self._player_view.after(
                50,
                self._wait_for_initial_frame,
                attempt + 1,
            )
            return

        # VLC did not report a usable state within the timeout.
        # Still finish the UI transition rather than leaving the
        # application permanently disabled.
        self._finish_initial_frame()

    def _finish_initial_frame(self) -> None:
        """
        Pauses VLC after the first frame has had time to render and
        transitions the UI from loading to ready.
        """
        self._initial_frame_id = None

        if self._currently_loaded_media is None:
            return

        if self._vlc_service.is_media_player_errored():
            self._handle_load_error(self._currently_loaded_media)
            return

        self._vlc_service.pause_media()

        self._player_view.set_play_icon(is_playing=False)

        # The initial frame is now displayed, so the player is ready.
        self._player_view.hide_loading()
        self._player_view.set_initial_states(state="normal")

    def _cancel_initial_frame_wait(self) -> None:
        """Cancels any pending initial-frame polling callbacks"""
        if self._initial_frame_id is not None:
            try:
                self._player_view.after_cancel(self._initial_frame_id)
            except Exception:
                # The widget may already be in the process of being
                # destroyed during application shutdown.
                pass

            self._initial_frame_id = None

    def _initialize_audio(self) -> None:
        """Initializes audio controls after media has loaded"""

        if self._media_attrs.has_audio:
            self._player_view.volume_btn_state = "normal"
            self._player_view.volume_slider_state = "normal"

            self._player_view.volume = 100
            self._is_muted = False
            self._player_view.set_mute_icon(muted=False)

            self._vlc_service.set_volume(100)
            self._vlc_service.mute(muted=False)

        else:
            self._player_view.volume_btn_state = "disabled"
            self._player_view.volume_slider_state = "disabled"

            self._player_view.volume = 0
            self._is_muted = True
            self._player_view.set_mute_icon(muted=True)

            self._vlc_service.set_volume(0)
            self._vlc_service.mute(muted=True)

    def _initialize_times(self) -> None:
        """Initializes time related UI elements after media is loaded"""
        self._player_view.start_time = 0

        start_timestamp = ms_to_player_timestamp(0)
        self._player_view.start_timestamp = start_timestamp

        self._player_view.current_time = 0

        current_timestamp = ms_to_player_timestamp(0)
        self._player_view.current_timestamp = current_timestamp

        duration = self._media_attrs.full_duration_ms

        self._player_view.configure_trim_slider(
            to=duration,
            steps=duration,
        )

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
        Checks the players state every 33 ms before updating UI.

        Loop will only be run while media is playing.
        Exits loop if player has paused, stopped, or ended.
        Rebuilds player if error occurs.
        """
        self._update_id = None

        if self._currently_loaded_media is None:
            return

        # Rebuild VLC player if an error occurs during playback.
        if self._vlc_service.is_media_player_errored():
            self._reset_vlc(self._currently_loaded_media)
            return

        # Don't do anything for stopped media.
        # Player will either be destroyed or rebuilt.
        elif (
            self._vlc_service.is_media_player_stopped()
            or self._vlc_service.is_media_player_idle()
        ):
            return

        # Updates UI before exiting loop when media has reached EOF.
        elif self._vlc_service.is_media_player_ended():
            self._update_state_ended()

            current_time_ms = self._player_view.end_time
            timestamp = ms_to_player_timestamp(current_time_ms)
            self._player_view.current_timestamp = timestamp

            self._restart_media_player(
                paused=True,
                target_ms=current_time_ms,
            )

            return

        # Updates UI and exits if media is paused.
        elif self._vlc_service.is_media_player_paused():
            current_time_ms = max(
                0,
                self._vlc_service.current_time,
            )

            timestamp = ms_to_player_timestamp(current_time_ms)
            self._player_view.current_timestamp = timestamp

            return

        # Updates UI while media is playing and not seeking.
        # UI is not updated when media is seeking.
        elif (
            self._vlc_service.is_media_player_playing()
            and not self._is_seeking
        ):
            current_time_ms = self._vlc_service.current_time
            self._player_view.current_time = current_time_ms

            end_time = self._player_view.end_time

            # Pause media if it has reached the changed end time.
            if current_time_ms >= end_time:
                self._player_view.current_time = end_time

                timestamp = ms_to_player_timestamp(end_time)
                self._player_view.current_timestamp = timestamp

                self._update_state_pause()
                return

            timestamp = ms_to_player_timestamp(current_time_ms)
            self._player_view.current_timestamp = timestamp

        self._update_id = self._player_view.after(
            33,
            self._update_view,
        )

    def _restart_media_player(
        self,
        paused: bool,
        target_ms: int,
    ) -> None:
        """Reset ended media, seek after VLC starts, then restore intent"""
        self._vlc_service.reset_media()

        self._vlc_service.display_media(
            self._player_view.media_viewer.winfo_id()
        )

        self._vlc_service.play_media()

        self._player_view.current_time = target_ms

        self._player_view.after(
            100,
            self._complete_restart,
            paused,
            target_ms,
            0,
        )

    def _complete_restart(
        self,
        paused: bool,
        target_ms: int,
        attempt: int,
    ) -> None:
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
                50,
                self._complete_restart,
                paused,
                target_ms,
                attempt + 1,
            )
            return

        self._vlc_service.seek_to(target_ms)

        self._player_view.current_time = target_ms
        self._player_view.current_timestamp = (
            ms_to_player_timestamp(target_ms)
        )

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
        Updates UI when media has started playing.

        Restarts update loop if it has stopped.
        """
        self._vlc_service.play_media()

        self._player_view.set_play_icon(is_playing=True)
        self._player_view.screenshot_state = "disabled"

        self._start_progress_update_loop()

    def _seek(self, target_ms: int) -> None:
        """Seek without changing the user's playback intent"""
        if self._currently_loaded_media is None:
            return

        self._is_seeking = True

        try:
            start_time = self._player_view.start_time
            end_time = self._player_view.end_time

            clamped_target = max(
                start_time,
                min(target_ms, end_time),
            )

            was_playing = (
                self._vlc_service.is_media_player_playing()
            )

            self._player_view.current_time = clamped_target
            self._player_view.current_timestamp = (
                ms_to_player_timestamp(clamped_target)
            )

            if self._vlc_service.is_media_player_ended():
                self._restart_media_player(
                    paused=True,
                    target_ms=clamped_target,
                )
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

    def _bind_player_view(self) -> None:
        self._player_view.on_play_pause_toggle = (
            self.on_play_pause_toggle
        )

        self._player_view.on_reverse_click = self.on_reverse_click
        self._player_view.on_forward_click = self.on_forward_click

        self._player_view.on_start_time_change = (
            self.on_start_time_change
        )

        self._player_view.on_current_time_change = (
            self.on_current_time_change
        )

        self._player_view.on_end_time_change = (
            self.on_end_time_change
        )

        self._player_view.on_volume_change = (
            self.on_volume_change
        )

        self._player_view.on_mute_toggle = self.on_mute_toggle

        self._player_view.on_screenshot_click = (
            self.on_screenshot_click
        )
