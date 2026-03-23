import subprocess
from os import PathLike

from utils import create_logs

class FFprobeProcessor():
  def __init__(self, ffprobe: PathLike | str) -> None:
    self._ffprobe: PathLike | str = ffprobe
    
  def get_duration_sexagesimal(self, filepath: PathLike | str) -> tuple[bool, str | None, str | None]:
    # Returns duration string in HH:MM:SS.MICROSECOND format
    cmd = [self._ffprobe, 
              "-v", 
              "error",
              "-select_streams",
              "v:0",
              "-show_entries",
              "stream=duration",
              "-of", 
              "default=noprint_wrappers=1:nokey=1", 
              "-sexagesimal", 
              filepath]
    
    
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False, 
                            text=True)
    
    try: 
      duration, err = proc.communicate()

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
      
      if duration is None:
        return False, None, "Error Occured!\nVideo Duration not found!"

      return True, duration, None

  def get_duration_milliseconds(self, filepath: PathLike | str) -> tuple[bool, float | None, str | None]:
    # Returns duration in milliseconds as a float
    cmd = [self._ffprobe, 
              "-v", 
              "error",
              "-select_streams",
              "v:0",
              "-show_entries",
              "stream=duration",
              "-of", 
              "default=noprint_wrappers=1:nokey=1", 
              filepath]
    
    
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False, 
                            text=True)
    
    try: 
      duration, err = proc.communicate()

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
      
      if duration is None:
        return False, None, "Error Occured!\nVideo Duration not found!"

      return True, duration, None

  def get_resolutions(self, filepath: PathLike | str) -> tuple[bool, list[str] | None, str | None]:
    cmd = [self._ffprobe, 
              "-v", 
              "error", 
              "-select_streams", 
              "v:0", 
              "-show_entries", 
              "stream=width,height", 
              "-of",
              "csv=s=x:p=0", 
              filepath]
    
    
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False, 
                            text=True)

    try: 
      vid_res, err = proc.communicate()

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
      
      if vid_res is None:
        return False, None, "Error Occured!\nVideo Resolution not found!"

      return True, self._res_opt_list(vid_res), None

  def _res_opt_list(self, vid_res: str) -> list[str]:
    dimensions = vid_res.split('x')
    
    width = int(dimensions[0])
    height = int(dimensions[1])

    aspect_ratio = width / height

    # List of some reoccuring standard pixel measurements for height and width
    # Not a comprehessive list, but enough for a list of usable target 
    # resolutions for compressing too
   
    if width >= height:
      std_width = [5120, 3840, 2560, 1920, 1600, 1280, 854, 640]
      std_height = [2880, 2160, 1440, 1080, 900, 720, 480, 360]
 
    elif width < height:
      std_width = [2880, 2160, 1440, 1080, 900, 720, 480, 360]
      std_height = [5120, 3840, 2560, 1920, 1600, 1280, 854, 640]

    temp_res = []

    for size in std_width:
      if size <= width:
        h = self._round_to_even(size / aspect_ratio)
        new = str(size) + "x" + str(h)

        temp_res.extend([new])

    for size in std_height:
      if size <= height:
        w = self._round_to_even(size * aspect_ratio)
        new = str(w) + "x" + str(size)

        temp_res.extend([new])

    # Turns list into set to remove any duplicate resolutions, then reverts back to a list
    temp_res = list(set(temp_res))
    
    # Sort the list based on width
    temp_res = sorted(temp_res, key=lambda x: int(x.split('x')[0]), reverse=True)

    resolutions = []
    
    # Resolutions with width / height of 360 are too small so will remove them
    if width >= height:
      for x in temp_res:
        h = int(x.split('x')[1])

        if h >= 360:
          resolutions.extend([x])

    elif width < height:
      for x in temp_res:
        w = int(x.split('x')[0])

        if w >= 360:
          resolutions.extend([x])
    
    # Return video resolution if it has a height or width smaller than 360
    if not resolutions:
      return [vid_res]

    return resolutions

  @staticmethod
  def _round_to_even(f: float) -> int:
    return round(f / 2.) * 2

  def get_fps(self, filepath: PathLike | str) -> tuple[bool, int | None, str | None]:
    cmd = [self._ffprobe, 
              "-v", 
              "error",
              "-select_streams",
              "v:0",
              "-show_entries",
              "stream=r_frame_rate",
              "-of",
              "default=noprint_wrappers=1:nokey=1",
              filepath]
    
    
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False, 
                            text=True)
    
    try: 
      fps, err = proc.communicate()

      proc.wait()
      rc = proc.returncode
    
    except FileNotFoundError:
      return False, None, "FFprobe not found!"

    except Exception as e:
      create_logs(str(e))
      return False, None, "Error occured!\nCheck logs for details"
    
    else:
      if rc != 0:
        create_logs(err)
        return False, None, "Error occured!\nCheck logs for details"
      
      if fps is None:
        return False, None, "Error Occurred!\nFPS not found!"
      
      fps = fps[:2]
      return True, int(fps), None