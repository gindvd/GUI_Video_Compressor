import subprocess
from os import PathLike

from utils import create_logs, DEVICE_OS

class FFprobeProcessor():
  _CMD_ARGS: dict = {
    "duration" : {
      "entry" : "format=duration",
      "-of_arg" : "default=noprint_wrappers=1:nokey=1"
    },
    "resolution" : {
      "entry" : "stream=width,height",
      "-of_arg" : "csv=s=x:p=0"
    },
    "fps" : {
      "entry" : "stream=avg_frame_rate",
      "-of_arg" : "default=noprint_wrappers=1:nokey=1"
    },
  }

  def __init__(self, ffprobe: PathLike | str) -> None:
    self._ffprobe: PathLike | str = ffprobe
    
  def get_video_attr_value(self, vid_attr: str, filepath: PathLike | str) -> tuple[bool, str | None, str | None]:

    entries_arg = self._CMD_ARGS.get(vid_attr, {}).get("entry")
    of_arg = self._CMD_ARGS.get(vid_attr, {}).get("-of_arg")
    
    cmd = [self._ffprobe, 
           "-v", 
           "error",
           "-select_streams",
           "v:0",
           "-show_entries",
           entries_arg,
           "-of", 
           of_arg,
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

      return True, result.strip(), None