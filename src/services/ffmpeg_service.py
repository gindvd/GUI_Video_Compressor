import os
import shutil
import signal
import subprocess
import sys

from pathlib import Path
from typing import Any

from models.app_state import AppState

from utils.log_utils import logger

from services.exit_status import ExitStatus

from rules.optimization_command_rules import (
    hwaccel_args_for,
    quality_args_for,
    scale_args_for,
    get_audio_args,
    quality_converter
)


class FFmpegService:
    """Handler class for running FFmpeg and yt-dlp processes"""

    def __init__(self, ffmpeg_path: str, ytdlp_path: list[str]) -> None:
        self._ffmpeg_path: str = ffmpeg_path
        self._ytdlp_path: list[str] = ytdlp_path

        self._proc: subprocess.Popen | None = None
        self._terminated: bool = False

        self._flags: dict[str, Any] = {}

        # Flags to hide console window and create a process group
        if sys.platform.startswith("win"):
            self._flags["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            )

            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self._flags["startupinfo"] = si

        else:
            # Create process that can be terminated on Linux / MacOS
            self._flags["start_new_session"] = True
    
    def extract_frame(self, input_file: str, timestamp: str) -> bytes | None:
        """Extracts frame of media file at the given timestamp"""

        cmd = [
            self._ffmpeg_path,
            "-ss",
            timestamp,
            "-i",
            input_file,
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-loglevel",
            "error",
            "pipe:1",
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                shell=False,
                check=True,
                timeout=10,
                **self._flags,
            )

        except subprocess.CalledProcessError as e:
            logger.exception(f"FFmpeg frame extraction failed: {str(e)}")
            return None

        except subprocess.TimeoutExpired:
            logger.exception("FFmpeg frame extraction timed out")
            return None

        except Exception as e:
            logger.exception(f"Frame extraction error: {str(e)}")
            return None

        else:
            return proc.stdout

    def download_video(self, url: str, ext: str, output_file: str) -> ExitStatus:
        """Downloads a video using yt-dlp"""

        if self._proc:
            return ExitStatus.BUSY
        
        output_path = Path(output_file)

        # Let yt-dlp control the extension during postprocessing
        output_template = str(output_path.with_suffix("")) + ".%(ext)s"

        cmd = [
            *self._ytdlp_path,
            "--no-keep-fragments",
            "--no-playlist",
            "--format",
            "bestvideo+bestaudio/best",
            # Convert the merged result to the format selected in DownloaderView
            "--recode-video",
            ext,
            "--output",
            output_template,
            "--ffmpeg-location",
            self._ffmpeg_path,
            url,
        ]

        return self._run_command(cmd)

    def create_gif(self, app_state: AppState) -> ExitStatus:
        """Converts video file to GIF"""

        width, _ = app_state.gif_settings.resolution.split("x")

        filter_complex = (
            f"fps={app_state.gif_settings.fps},"
            f"scale={width}:-1:flags=lanczos,"
            "split[s0][s1];"
            "[s0]palettegen=stats_mode=diff[p];"
            "[s1][p]paletteuse=dither=sierra2_4a"
        )

        cmd = [
            self._ffmpeg_path,
            "-ss",
            app_state.timestamps.start_time,
            "-t",
            app_state.timestamps.duration,
            "-i",
            app_state.media.input_file,
            "-filter_complex",
            filter_complex,
            "-loop",
            app_state.gif_settings.loops,
            app_state.gif_settings.output_file,
        ]

        return self._run_command(cmd)

    def optimize(self, app_state: AppState) -> ExitStatus:
        """Creates FFmpeg command and executes it"""

        width, height = app_state.settings.resolution.split("x")
        crf: str = quality_converter(app_state.settings.quality)

        aud_opts: list[str] = get_audio_args(
            app_state.settings.include_audio, 
            app_state.settings.audio_codec, 
            app_state.settings.audio_bitrate
        )

        hwaccel_args: list[str] | None = hwaccel_args_for(
            app_state.settings.video_codec
        )

        scale_args: list[str] = scale_args_for(
            app_state.settings.video_codec, 
            app_state.settings.frame_rate, 
            width, 
            height
        )

        quality_args: list[str] = quality_args_for(
            app_state.settings.video_codec, crf
        )

        cmd: list[str] = [
            self._ffmpeg_path,
        ]

        if hwaccel_args is not None:
            cmd.extend(hwaccel_args)

        cmd.extend([
            "-ss",
            app_state.timestamps.start_time,
            "-t",
            app_state.timestamps.duration,
            "-i",
            app_state.media.input_file,
            "-c:v",
            app_state.settings.video_codec,
            *scale_args,
        ])

        if app_state.settings.preset:
            cmd.extend([
                "-preset",
                app_state.settings.preset,
            ])

        cmd.extend([
            *quality_args,
            *aud_opts,
            app_state.media.output_file,
        ])

        return self._run_command(cmd)

    def _run_command(self, cmd: list[str]) -> ExitStatus:
        """Runs an external process and waits for it to finish"""

        if self._proc:
            return ExitStatus.BUSY

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                text=True,
                **self._flags,
            )

            out = self._proc.communicate()
            rc = self._proc.returncode

        except AttributeError:
            # Can occur during cancellation if another thread has
            # already cleared/replaced the process reference.
            return ExitStatus.TERMINATED

        except FileNotFoundError as e:
            logger.exception(str(e))
            return ExitStatus.ERROR

        except PermissionError as e:
            logger.exception(str(e))
            return ExitStatus.ERROR

        except subprocess.SubprocessError as e:
            logger.exception(str(e))
            return ExitStatus.ERROR

        except OSError as e:
            logger.exception(str(e))
            return ExitStatus.ERROR

        else:
            # Log / display error when return code is non-zero
            # and process was not terminated by user
            if rc != 0 and not self._terminated:
                logger.error(
                    "Process failed with exit code %d\n\n"
                    "Command: %s\n\n"
                    "Output:\n%s",
                    rc,
                    " ".join(str(arg) for arg in cmd),
                    out,
                )

                return ExitStatus.ERROR
            
            elif rc != 0 and self._terminated:
                return ExitStatus.TERMINATED

            else:
                return ExitStatus.SUCCESS

        finally:
            # Resets values
            self._proc = None
            self._terminated = False

    def terminate_process(self) -> None:
        """Terminates the current process and its child processes"""

        proc = self._proc

        if proc is None or proc.poll() is not None:
            return

        self._terminated = True

        try:
            if sys.platform.startswith("win"):
                proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._terminate_unix_process_group(proc)

            proc.wait(timeout=5)

        except subprocess.TimeoutExpired:

            try:
                if sys.platform.startswith("win"):
                    proc.kill()
                else:
                    self._kill_unix_process_group(proc)

            except ProcessLookupError:
                pass

        except ProcessLookupError:
            pass

        except OSError as e:
            logger.exception(
                "Failed to terminate process: %s",
                e,
            )
    
    @staticmethod
    def _terminate_unix_process_group(
        proc: subprocess.Popen,
    ) -> None:
        """Send terminate signal to parent and child processes on Linux/MacOS"""

        os.killpg(
            os.getpgid(proc.pid),
            signal.SIGTERM,
        )

    @staticmethod
    def _kill_unix_process_group(
        proc: subprocess.Popen,
    ) -> None:
        """Send kill signal to parent and child processes on Linux/MacOS"""

        os.killpg(
            os.getpgid(proc.pid),
            signal.SIGKILL,
        )
 