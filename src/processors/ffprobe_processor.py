import json
from pathlib import Path
from typing import Any

from utils.log_utils import logger

class FFprobeProcessHandler():
  """ Handler class for running FFprobe to retrieve media stream information """

  def __init__(self, ffprobe: Path, device_os: str) -> None:
    self._ffprobe: Path = ffprobe
    self._device_os: str = device_os
    
  def get_video_attributions(self, filepath: Path) -> tuple[bool, list[str] | None, str | None]:
    """ Run command to have FFprobe extract file stream data """
    import subprocess

    # Returns json formatted stream with mdia file's resolution, frame rate, and duration
    cmd = [self._ffprobe,
           "-v",
           "error",
           "-select_streams",
           "v:0",
           "-show_entries",
           "stream=width,height,avg_frame_rate",
           "-show_entries",
           "format=duration",
           "-of",
           "json",
           filepath]

    flags: dict[str, Any] = {}
    
    # flags to hide console window
    if self._device_os == "Windows":
      flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
      si = subprocess.STARTUPINFO()
      si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      flags["startupinfo"] = si

    else:
      flags["start_new_session"] = True

    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False, 
                            text=True,
                            **flags)
    
    try: 
      result, err = proc.communicate()
      rc = proc.returncode
    
    except FileNotFoundError:
      return False, None, "FFprobe not found!"

    except PermissionError as e:
      logger.exception(str(e))
      return False, None, "Permission Error Occured!\nCheck logs for details!"

    except subprocess.SubprocessError as e:
      logger.exception(str(e))
      return False, None, "Subprocess Error Occured!\nCheck logs for details!"

    except OSError as e:
      logger.exception(str(e))
      return False, None, "OS Error Occured!\nCheck logs for details!"
    
    else:
      # Log error when return code is non-zero, return error message
      if rc != 0:
        logger.error("FFmpeg failed with exit code %d\n"
                     "Command: %s\n"
                     "Output:\n%s",
                     rc,
                     " ".join(str(arg) for arg in cmd),
                     err,)
      
        return False, None, "Called Process Error Occured!\nCheck logs for details!"
      
      if result is None or "N/A" in result:
        return False, None, "Issue getting info from file headers."
      
      return self._parse_attributes(result)
      
  @staticmethod
  def _parse_attributes(result: str) -> tuple[bool, list[str] | None, str | None]:
    """ Parses through returned JSON and gets clean values for video frame rate, resolution, and duration """
    import json

    try:
      data = json.loads(result)
    except json.JSONDecodeError as e:
      logger.exception(str(e))
      return False, None, "Issue getting info from file headers."

    streams = data.get("streams", [])
    fmt = data.get("format", {})

    if not streams:
      return False, None, "No video stream found."

    s = streams[0]
    width: int | None = s.get("width")
    height: int | None = s.get("height")
    avg_frame_rate: str | None = s.get("avg_frame_rate")
    duration: str | None = fmt.get("duration")

    if None in (width, height, avg_frame_rate, duration):
      return False, None, "Issue getting info from file headers."

    if "N/A" in str(avg_frame_rate) or "N/A" in str(duration):
      return False, None, "Issue getting info from file headers."

    attrs = [f"{width}x{height}", str(avg_frame_rate), str(duration)]

    return True, attrs, None