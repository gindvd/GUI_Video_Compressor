import json
from os import PathLike
from utils import create_logs, DEVICE_OS

class FFprobeProcessor():

  def __init__(self, ffprobe: PathLike | str) -> None:
    self._ffprobe: PathLike | str = ffprobe
    
  def get_video_attributions(self, filepath: PathLike | str) -> tuple[bool, list[str] | None, str | None]:
    import subprocess
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

    startupinfo = None
    creation_flags = 0

    # flags to hide console window
    if DEVICE_OS == 'Windows':
      startupinfo = subprocess.STARTUPINFO()
      startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      creation_flags = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False, 
                            text=True,
                            startupinfo=startupinfo,
                            creationflags=creation_flags)
    
    try: 
      result, err = proc.communicate()

      proc.wait()
      rc = proc.returncode
    
    except FileNotFoundError:
      return False, None, "FFprobe not found!"

    except Exception as e:
      create_logs(str(e))
      return False, None, "Error Occured!\nCheck logs for details!"
    
    else:
      if rc != 0:
        create_logs(err)
        return False, None, "Error Occured!\nCheck logs for details!"
      
      if result is None or "N/A" in result:
        return False, None, "Issue getting info from file headers."
      
      return self._parse_attributes(result)
      
  @staticmethod
  def _parse_attributes(result: json) -> tuple[bool, set[str] | None, str | None]:
    try:
      data = json.loads(result)
    except json.JSONDecodeError as e:
      create_logs(str(e))
      return False, None, "Issue getting info from file headers."

    streams = data.get("streams", [])
    fmt = data.get("format", {})

    if not streams:
      return False, None, "No video stream found."

    s = streams[0]
    width = s.get("width")
    height = s.get("height")
    avg_frame_rate = s.get("avg_frame_rate")
    duration = fmt.get("duration")

    if None in (width, height, avg_frame_rate, duration):
      return False, None, "Issue getting info from file headers."

    if "N/A" in str(avg_frame_rate) or "N/A" in str(duration):
      return False, None, "Issue getting info from file headers."

    attrs = [f"{width}x{height}", avg_frame_rate, duration]

    return True, attrs, None