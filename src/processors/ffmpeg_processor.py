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
              audio: bool,
              start_time: str ,
              duration: str) -> tuple[bool, str | None]:

    basename, _ = os.path.splitext(input_file)
    output_file = basename + "_compressed." + file_format

    if os.path.exists(output_file):
      output_file = self._uniquify(output_file)

    width, height = resolution.split("x")

    crf = self._quality_converter(quality)
    
    if not audio:
      aud_opts = ["-an"]
    elif audio:
      aud_opts = ["-c:a", self._audio_codec(codec), "-b:a", "128k"]

    hwaccel_args = None
    scale_args = ["-vf", f"scale={width}:{height},fps={fps}"]

    _,__, hw_id = codec.partition("_")

    match hw_id:
      case 'nvenc':
        quality_args = ["-rc", "vbr","-cq", str(crf), "-b:v", "0"]
    
      case 'amf':
        quality_args = ["-rc", "qvbr", "-qvbr_quality_level", str(crf)]

      case 'qsv':
        hwaccel_args = ["-init_hw_device", "qsv=hw", "-filter_hw_device", "hw"]
        quality_args = ["-global_quality", str(crf), "-look_ahead", "1"]
    
      case "vaapi":
        hwaccel_args = ["-vaapi_device", "/dev/dri/renderD128"]
        scale_args = ["-vf", f"format=nv12,fps={fps},hwupload,scale_vaapi=w={width}:h={height}"]
        quality_args = ["-qp", str(crf)]
    
      case _:
        quality_args = ["-crf", str(crf)]
    
    cmd = [self._ffmpeg] 
    
    if hwaccel_args is not None:
      cmd.extend(hwaccel_args)
    
    cmd.extend(["-i", input_file,
                "-c:v", codec, 
                *scale_args, 
                *quality_args, 
                *aud_opts,
                "-ss", start_time,
                "-t", duration, 
                output_file])

    creation_flags = {}

    if DEVICE_OS == "Windows":
      creation_flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
      creation_flags["start_new_session"] = True
    
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
        
        create_logs(f"{' '.join(cmd)}\n\n" + out)
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
    
    else:
      return False, ""

  @staticmethod
  def _quality_converter(quality: int) -> int:
    # Quality needs be inverted as the lower the CRF number, the better the quality
    quality_inverted = abs(quality / 100 - 1)
    crf = quality_inverted * 33 + 18  # Range 18 to 51
    return int(crf)

  @staticmethod
  def _uniquify(path: os.PathLike | str) -> os.PathLike | str:
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path
  
  @staticmethod
  def _audio_codec(codec: str) -> str:
    if codec in ["libvpx-vp9", "libsvtav1"]:
      return "libopus"
    
    return "aac"