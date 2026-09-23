import subprocess

from typing import Any

from utils.log_utils import logger


class FFprobeService:
    """Handler class for running FFprobe to retrieve media stream information"""

    def __init__(self, path: str) -> None:
        self._path: str = path

        self._flags: dict[str, Any] = {}

        # flags to hide console window
        from sys import platform

        if platform.startswith("win"):
            self._flags["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            )
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self._flags["startupinfo"] = si
        else:
            self._flags["start_new_session"] = True

    def get_media_attrs(self, filepath: str) -> str | None:
        """Run command to have FFprobe extract file stream data"""

        cmd: list[str] = [
            self._path,
            "-v",
            "error",
            "-show_streams",
            "-show_entries",
            "stream=codec_type,width,height,avg_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            filepath,
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                shell=False,
                text=True,
                **self._flags,
            )

        except FileNotFoundError as e:
            logger.exception(str(e))
            return None

        except PermissionError as e:
            logger.exception(str(e))
            return None

        except subprocess.CalledProcessError as e:
            logger.exception(str(e))
            return None

        except subprocess.SubprocessError as e:
            logger.exception(str(e))
            return None

        except OSError as e:
            logger.exception(str(e))
            return None

        else:
            result = proc.stdout

            if result is None or "N/A" in result:
                return None

            return result
