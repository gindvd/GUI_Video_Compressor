import vlc

from sys import platform
from threading import Event, RLock, Thread
from collections.abc import Callable

from utils.log_utils import logger


class VLCService:
    _PLAYING = vlc.State.Playing
    _PAUSED = vlc.State.Paused
    _ENDED = vlc.State.Ended
    _STOPPED = vlc.State.Stopped
    _IDLE = vlc.State.NothingSpecial
    _ERROR = vlc.State.Error

    def __init__(self, path: str) -> None:
        self._vlc_path: str = path

        self._vlc_media: vlc.Media | None = None
        self._vlc_instance: vlc.Instance | None = None
        self._vlc_media_player: vlc.MediaPlayer | None = None

        self._instance_loading: bool = False
        self._is_loading: bool = False
        self._load_request: int = 0
        self._lock = RLock()

        self._teardown_thread: Thread | None = None

    # Threaded functions to create VLC instance and media player
    def create_vlc_instance_async(
        self,
        on_created: Callable[[], None] | None = None,
        on_error: Callable[[], None] | None = None,
    ) -> None:
        """Creates the VLC instance on a worker thread"""

        Thread(
            target=self._create_vlc_instance_worker,
            args=(on_created, on_error),
            daemon=True,
        ).start()

    def _create_vlc_instance_worker(
        self,
        on_created: Callable[[], None] | None,
        on_error: Callable[[], None] | None,
    ) -> None:
        """Threaded function to create new instance and handled errors"""
        try:
            self._create_vlc_instance()
            if on_created is not None:
                on_created()

        except Exception as e:
            logger.exception(str(e))

            if on_error is not None:
                on_error()

    def _create_vlc_instance(self) -> None:
        """Creates the VLC instance and media player if they do not exist"""
        with self._lock:
            if self._instance_loading:
                return

            self._instance_loading = True

            try:
                if self._vlc_instance is None:
                    self._vlc_instance = self._platform_specific_instance()
                    self._vlc_instance.log_unset()  # Suppresses VLC logs

                if self._vlc_media_player is None:
                    self._vlc_media_player = self._vlc_instance.media_player_new()

            finally:
                self._instance_loading = False

    def _platform_specific_instance(self) -> vlc.Instance:
        """Initializes the VLC instance with platform-specific settings"""
        if platform.startswith("win"):
            return vlc.Instance(
                [
                    "--quiet",
                    "--verbose=0",
                    "--aout=directsound",
                    "--avcodec-skiploopfilter=0",
                    "--avcodec-hw=any",
                    f"--plugin-path={self._vlc_path}",
                ]
            )
        return vlc.Instance(["--quiet", "--verbose=0", "--aout=pulse", "--no-xlib"])

    # Threaded Functions to unload old media before load ingnew media
    def load_media_async(
        self,
        media_file: str,
        on_loaded: Callable[[], None] | None = None,
        on_error: Callable[[], None] | None = None,
    ) -> None:
        """
        Loads media on a worker thread

        The worker serializes the VLC lifecycle so media is not loaded until:
        1. A VLC instance and media player exist
        2. Current media has been stopped/unloaded
        3. The request is still the newest load request
        """
        with self._lock:
            self._load_request += 1
            request_id = self._load_request

        Thread(
            target=self._load_media_worker,
            args=(media_file, request_id, on_loaded, on_error),
            daemon=True,
        ).start()

    def _load_media_worker(
        self,
        media_file: str,
        request_id: int,
        on_loaded: Callable[[], None] | None,
        on_error: Callable[[], None] | None,
    ) -> None:
        """Threaded worker to stop any loaded  media before loading new media"""
        try:
            with self._lock:
                if request_id != self._load_request:
                    return

                self._create_vlc_instance()

                if request_id != self._load_request:
                    return

                self.stop_media()

                # Tearsdown and creates new instance if media gets stuck stopping
                if not self._wait_until_media_unloaded():
                    self._teardown_instance()
                    self._create_vlc_instance()

                if request_id != self._load_request:
                    return

                self._release_media()
                self._load_media(media_file)

            if on_loaded is not None:
                on_loaded()

        except Exception as e:
            logger.exception(str(e))
            self._is_loading = False

            if on_error is not None:
                on_error()

    def _wait_until_media_unloaded(self) -> bool:
        """
        Time loop to wait for certain amount of time for media to stop

        Returns False if media hasn't stopped in given time frame
        """
        for _ in range(50):
            if self._check_media_unloaded():
                return True
            Event().wait(timeout=0.05)

        return False

    def _check_media_unloaded(self) -> bool:
        """Checks if media is a stopped state"""
        if self._vlc_media_player is None:
            return True

        state = self._vlc_media_player.get_state()
        return state in (
            self._STOPPED,
            self._IDLE,  # State when media is stopped or no media is currently loaded
        )

    def _load_media(self, media_file: str) -> None:
        """Loads new media into the existing VLC media player"""
        if self._vlc_instance is None or self._vlc_media_player is None:
            return

        self._is_loading = True
        try:
            self._vlc_media = self._vlc_instance.media_new(media_file)
            self._vlc_media_player.set_media(self._vlc_media)

        finally:
            self._is_loading = False

    # Threaded teardown functions to stop loaded media and release VLC instance / Media
    def teardown_instance_async(
        self,
        on_complete: Callable[[], None] | None = None,
        on_error: Callable[[], None] | None = None,
    ) -> None:
        """Tears down the VLC instance on a worker thread."""
        self._teardown_thread = Thread(
            target=self._teardown_instance_worker,
            args=(on_complete, on_error),
            daemon=True,
        )
        self._teardown_thread.start()

    def _teardown_instance_worker(
        self,
        on_complete: Callable[[], None] | None,
        on_error: Callable[[], None] | None,
    ) -> None:
        """Worker to teardown vlc instance"""
        try:
            self._teardown_instance()
            if on_complete is not None:
                on_complete()

        except Exception as e:
            logger.exception(str(e))

            if on_error is not None:
                on_error()

        finally:
            self._teardown_thread = None

    def _teardown_instance(self) -> None:
        """Releases VLC media, media player, and instance"""
        with self._lock:
            if self._vlc_media_player is not None:
                self._vlc_media_player.stop()
                self._vlc_media_player.release()
                self._vlc_media_player = None

            self._release_media()

            if self._vlc_instance is not None:
                self._vlc_instance.release()
                self._vlc_instance = None

    def _release_media(self) -> None:
        """Quickly release of the VLC media"""
        if self._vlc_media is not None:
            self._vlc_media.release()
            self._vlc_media = None

    def display_media(self, media_frame_id) -> None:
        """Creates the media viewer inside a canvas"""
        if self._vlc_media_player is None:
            return

        if platform.startswith("linux"):
            self._vlc_media_player.set_xwindow(media_frame_id)
        elif platform.startswith("win"):
            self._vlc_media_player.set_hwnd(media_frame_id)

    def stop_media(self) -> None:
        if self._vlc_media_player is not None:
            self._vlc_media_player.stop()

    def play_media(self) -> None:
        if self._vlc_media_player is not None:
            self._vlc_media_player.play()

    def pause_media(self) -> None:
        """Idempotently place the player in the paused state."""
        if self._vlc_media_player is not None:
            self._vlc_media_player.set_pause(1)

    def set_volume(self, volume: int) -> None:
        if self._vlc_media_player is None:
            return

        clamped = max(0, min(volume, 100))
        self._vlc_media_player.audio_set_volume(clamped)

    def mute(self, muted: bool) -> None:
        if self._vlc_media_player is not None:
            self._vlc_media_player.audio_set_mute(muted)

    def reset_media(self) -> None:
        """Quickly resets loaded media when media reaches ended state"""
        if self._vlc_media is not None and self._vlc_media_player is not None:
            self._vlc_media_player.set_media(self._vlc_media)

    def seek_to(self, target_ms: int) -> None:
        """Helper function to set time"""
        self.current_time = target_ms

    def take_snapshot(self, filename: str) -> int:
        """
        Takes snapshot when media is paused.

        Returns 0 on success, -1 on error.
        """
        if self._vlc_media_player is None:
            return -1

        state = self._vlc_media_player.get_state()
        if state not in [self._PAUSED, self._ENDED]:
            return -1

        return self._vlc_media_player.video_take_snapshot(0, filename, 0, 0)

    def shutdown(self) -> None:
        """Release VLC resources and wait briefly for teardown to finish."""
        if self._teardown_thread is None or not self._teardown_thread.is_alive():
            self.teardown_instance_async(
                on_complete=None,
                on_error=None,
            )

        if self._teardown_thread is not None:
            self._teardown_thread.join(timeout=1)

    @property
    def current_time(self) -> int:
        if self._vlc_media_player is None:
            return 0
        return self._vlc_media_player.get_time()

    @current_time.setter
    def current_time(self, target_ms: int) -> None:
        if self._vlc_media_player is not None:
            self._vlc_media_player.set_time(target_ms)

    # VLC state getters
    def is_instance_loading(self) -> bool:
        return self._instance_loading

    def is_media_loading(self) -> bool:
        return self._is_loading

    def load_request(self) -> int:
        return self._load_request

    def media_exists(self) -> bool:
        return self._vlc_media is not None

    def media_player_exists(self) -> bool:
        return self._vlc_media_player is not None

    def instance_exists(self) -> bool:
        return self._vlc_instance is not None

    def is_media_player_playing(self) -> bool:
        return self._get_media_player_state() == self._PLAYING

    def is_media_player_paused(self) -> bool:
        return self._get_media_player_state() == self._PAUSED

    def is_media_player_stopped(self) -> bool:
        return self._get_media_player_state() == self._STOPPED

    def is_media_player_idle(self) -> bool:
        return self._get_media_player_state() == self._IDLE

    def is_media_player_ended(self) -> bool:
        return self._get_media_player_state() == self._ENDED

    def is_media_player_errored(self) -> bool:
        return self._get_media_player_state() == self._ERROR

    def _get_media_player_state(self):
        if self._vlc_media_player is None:
            return None
        return self._vlc_media_player.get_state()
