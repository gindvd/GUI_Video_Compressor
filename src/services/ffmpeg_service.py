import os
import shutil
import signal
import subprocess
import sys

from pathlib import Path
from typing import Any

from utils.log_utils import logger
from services.exit_status import ExitStatus


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
                subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.CREATE_NO_WINDOW
            )

            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self._flags["startupinfo"] = si

        else:
            # Create process that can be terminated on Linux / MacOS
            self._flags["start_new_session"] = True

    def download_video(
        self,
        url: str,
        ext: str,
        output_folder: str,
    ) -> ExitStatus:
        """Downloads a video using yt-dlp"""

        if self._proc:
            return ExitStatus.BUSY

        cmd = [
            *self._ytdlp_path,
            "--format",
            "bestvideo+bestaudio/best",
            "--merge-output-format",
            ext,
            "--output",
            os.path.join(output_folder, "%(title)s.%(ext)s"),
            "--no-playlist",
            "--ffmpeg-location",
            self._ffmpeg_path,
            url,
        ]

        return self._run_command(cmd)

    def extract_frame(
        self,
        input_file: str,
        timestamp: str,
    ) -> bytes | None:
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

    def create_gif(
        self,
        input_file: str,
        output_file: str,
        start_time: str,
        duration: str,
        fps: str,
        resolution: str,
        loops: int,
    ) -> ExitStatus:
        """Converts video file to GIF"""

        width, _ = resolution.split("x")

        filter_complex = (
            f"fps={fps},"
            f"scale={width}:-1:flags=lanczos,"
            "split[s0][s1];"
            "[s0]palettegen=stats_mode=diff[p];"
            "[s1][p]paletteuse=dither=sierra2_4a"
        )

        cmd = [
            self._ffmpeg_path,
            "-ss",
            start_time,
            "-t",
            duration,
            "-i",
            input_file,
            "-filter_complex",
            filter_complex,
            "-loop",
            str(loops),
            output_file,
        ]

        return self._run_command(cmd)

    def optimize(
        self,
        input_file: str,
        file_format: str,
        resolution: str,
        codec: str,
        fps: str,
        preset: str | None,
        quality: int,
        include_audio: bool,
        audio_codec: str | None,
        audio_bitrate: str | None,
        start_time: str,
        duration: str,
        output_file: str,
    ) -> ExitStatus:
        """Creates FFmpeg command and executes it"""

        width, height = resolution.split("x")

        crf = self._quality_converter(quality)

        if (
            include_audio is None
            or audio_codec is None
            or audio_bitrate is None
        ):
            aud_opts = ["-an"]

        else:
            aud_opts = [
                "-c:a",
                audio_codec,
                "-b:a",
                audio_bitrate,
            ]

        hwaccel_args = None
        scale_args = [
            "-vf",
            f"scale={width}:{height},fps={fps}",
        ]

        # Splits codec to check for hardware specific args
        _, __, hw_id = codec.partition("_")

        if hw_id == "nvenc":
            quality_args = [
                "-rc",
                "vbr",
                "-cq",
                str(crf),
                "-b:v",
                "0",
            ]

        elif hw_id == "amf":
            quality_args = [
                "-rc",
                "qvbr",
                "-qvbr_quality_level",
                str(crf),
            ]

        elif hw_id == "qsv":
            hwaccel_args = [
                "-init_hw_device",
                "qsv=hw",
                "-filter_hw_device",
                "hw",
            ]

            quality_args = [
                "-global_quality",
                str(crf),
                "-look_ahead",
                "1",
            ]

        elif hw_id == "vaapi":
            hwaccel_args = [
                "-vaapi_device",
                "/dev/dri/renderD128",
            ]

            scale_args = [
                "-vf",
                (
                    f"format=nv12,fps={fps},hwupload,"
                    f"scale_vaapi=w={width}:h={height}"
                ),
            ]

            quality_args = [
                "-qp",
                str(crf),
            ]

        else:
            quality_args = [
                "-crf",
                str(crf),
            ]

        if codec == "libvpx-vp9":
            quality_args.extend([
                "-b:v",
                "0",
            ])

        cmd: list[str] = [
            self._ffmpeg_path,
        ]

        if hwaccel_args is not None:
            cmd.extend(hwaccel_args)

        cmd.extend([
            "-ss",
            start_time,
            "-t",
            duration,
            "-i",
            input_file,
            "-c:v",
            codec,
            *scale_args,
        ])

        if preset:
            cmd.extend([
                "-preset",
                preset,
            ])

        cmd.extend([
            *quality_args,
            *aud_opts,
            output_file,
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
        """Terminates the current process and its child processes."""

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

    @staticmethod
    def _quality_converter(quality: int) -> int:
        """Converts quality percentage into inverted CRF number"""
        quality_inverted = abs(quality / 100 - 1)
        crf = quality_inverted * 33 + 18 # Range 18 to 51

        return int(crf)