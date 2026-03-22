import os
import subprocess
import re

from utils import create_logs
from utils import DEVICE_OS

class FFmpegProcessor():
  def __init__(self, ffmpeg: os.PathLike | str) -> None:
    self._ffmpeg: os.PathLike | str = ffmpeg
    self._proc: subprocess.Popen[str] | None = None
    self._terminated: bool = False

  def compress(self, 
              input_file: os.PathLike | str, 
              file_format: str, 
              resolution: str, 
              codec: str, 
              fps: str, 
              quality: int, 
              audio: bool) -> tuple[bool, str | None]:

    basename, _ = os.path.splitext(input_file)
    output_file = basename + "_compressed." + file_format
    
    width, height = resolution.split("x")
    scale = "scale={}:{}".format(width, height)
        
    if codec in ["libvpx-vp9", "libsvtav1"]:
      audio_codec = "libopus"
    else:
      audio_codec = "aac"

    cmd = [self._ffmpeg]
           

    hw_spec_arg = self._select_quality_control(codec)

    if hw_spec_arg[1] is not None:
      cmd.extend(hw_spec_arg[1])

    cmd.extend(["-i", input_file, 
                "-c:v", codec,
                "-r", fps,
                "-vf", scale])
    
    assert hw_spec_arg[0] is not None, "Command arg is set to None!"
    cmd.extend(hw_spec_arg[0])

    qual = self._quality_converter(quality)
    cmd.extend([qual])

    if not audio:
      cmd.extend(["-an"])
    elif audio:
        cmd.extend(["-c:a", audio_codec, 
                    "-b:a", "128k"]) 
    
    cmd.extend([output_file])

    creation_flags = {}

    if DEVICE_OS == "Windows":
      creation_flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
      creation_flags["start_new_session"] = True

    print(" ".join(cmd))
    
    self._proc = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              shell=False,
                              text=True,
                              **creation_flags)

    try:
      out, _ = self._proc.communicate()
      self._proc.wait()
    
      rc = self._proc.returncode

    # AttributeError sometimes raised when cancelling video compression due to _proc being set to None which has no wait
    # Must be a timing thing
    # Addding except to ignore and treat like normal termination as it still properly kills the process
    except AttributeError:
      if os.path.exists(output_file):
        os.remove(output_file)
        
      return False,  None
    
    except FileNotFoundError:
      return False, "FFmpeg could not be found!"        
    
    except Exception as e: 
      create_logs(str(e))

      return False, "Error Occured!\nCheck logs for details!"
    
    else:
      if rc != 0 and self._terminated == False:
        if os.path.exists(output_file):
                os.remove(output_file)
        
        create_logs(f"{' '.join(cmd)}\n" + out)
        return False, "Compression Failed\nCheck logs for details!"

      elif rc != 0 and self._terminated == True:
        if os.path.exists(output_file):
                os.remove(output_file)
        
        return False,  None

      else:
        return True, None
    
    finally:
      self._proc = None
      self._terminated = False
    
  def terminate_compression(self) -> tuple[bool, str | None]:
    # _proc_poll will only be None when process is running
    if self._proc and self._proc.poll() is None:
      self._proc.terminate()
      self._terminated = True

      try:
        self._proc.wait(timeout=5)
      
      except subprocess.TimeoutExpired:
        self._proc.kill()
        return True, "Video compression killed"
      
      else:
        return True, "Video compression terminated"

      finally:
        self._proc = None
    
    else:
      return False, ""

  @staticmethod
  def _quality_converter(quality: int) -> str:
    # Quality needs be inverted as the lower the CRF number, the better the quality
    quality_inverted = abs(quality / 100 - 1)
    crf = quality_inverted * 41 + 10
    return str(int(crf))

  @staticmethod
  def _select_quality_control(codec: str) -> list[list[str] | None]:
    if re.search('nvenc', codec):
      return [["-cq"]]
    
    elif re.search('amf', codec):
      return [["-qvbr_quality_level"]]

    elif re.search('qsv', codec):
      return [["-global_quality"], ["-init_hw_device", "qsv=hw", "-filter_hw_device", "hw"],]
    
    else:
      return [["-crf"]]
