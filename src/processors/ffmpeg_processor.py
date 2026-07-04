import os
import subprocess
from typing import Any
from pathlib import Path

from utils.log_utils import logger

class FFmpegProcessHandler():
  """ Handler class for running FFmpeg to compress media file """
  
  def __init__(self, ffmpeg: Path, device_os: str) -> None:
    self._ffmpeg: Path = ffmpeg
    self._proc: subprocess.Popen[str] | None = None
    self._terminated: bool = False
    self._device_os: str = device_os

  def compress(self, 
              input_file: Path, 
              file_format: str, 
              resolution: str, 
              codec: str, 
              fps: str,
              preset: str | None,
              quality: int, 
              audio: bool,
              audio_codec: str,
              audio_bitrate: str,
              start_time: str ,
              duration: str,
              output_directory: str) -> tuple[bool, str | None]:
    """ Creates FFmpeg command with all args and executes it to compress video files """

    basename = os.path.basename(input_file)
    name, _ = basename.split(".")
    new_name = name + "_compressed." + file_format

    output_file = os.path.join(output_directory, new_name)

    if os.path.exists(output_file):
      output_file = self._uniquify(output_file)

    width, height = resolution.split("x")
    
    crf = self._quality_converter(quality)
    
    if not audio:
      aud_opts = ["-an"]
    elif audio:
      aud_opts = ["-c:a", audio_codec, "-b:a", audio_bitrate]
    
    # Base hardware and scale args that might change based on hardware codecs
    hwaccel_args = None
    scale_args = ["-vf", f"scale={width}:{height},fps={fps}"]

    _,__, hw_id = codec.partition("_")
    
    # Matches hardware codec and changes the quality args that work with the codec
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
    
    if codec == "libvpx-vp9":
      quality_args.extend(["-b:v", "0"])
    
    # Begin assembling the command list in order
    cmd = [self._ffmpeg] 
    
    if hwaccel_args is not None:
      cmd.extend(hwaccel_args)
    
    cmd.extend(["-ss", start_time,
                "-t", duration, 
                "-i", input_file,
                "-c:v", codec, 
                *scale_args])
    
    if preset is not None:
      cmd.extend(["-preset", preset])
                
    cmd.extend([*quality_args, 
                *aud_opts,
                output_file])

    flags: dict[str, Any] = {}
    
    # flags to hide console window
    if self._device_os == "Windows":
      flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
      si = subprocess.STARTUPINFO()
      si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      flags["startupinfo"] = si
    else:
      flags["start_new_session"] = True
    
    # Try compressing the video file and cleaning log / display any errors that occur
    try:
      self._proc = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              shell=False,
                              text=True,
                              **flags)

      out, err = self._proc.communicate()
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

    except PermissionError as e:
      logger.exception(str(e))
      return False, "Permission Error Occured!\nCheck logs for details!"

    except subprocess.SubprocessError as e:
      logger.exception(str(e))
      return False, "Subprocess Error Occured!\nCheck logs for details!"

    except OSError as e:
      logger.exception(str(e))
      return False, "OS Error Occured!\nCheck logs for details!"
    
    else:
      # Log / display error when return code is non-zero and process was not terminated by user
      if rc != 0 and self._terminated == False:
        if os.path.exists(output_file):
          os.remove(output_file)

        logger.error("FFmpeg failed with exit code %d\n"
                     "Command: %s\n"
                     "Output:\n%s",
                     rc,
                     " ".join(str(arg) for arg in cmd),
                     out,)
        
        return False, "Compression Failed\nCheck logs for details!"

      # Handles user terminating the process and supresses error messages
      elif rc != 0 and self._terminated == True:
        if os.path.exists(output_file):
          os.remove(output_file)
        
        return False,  None

      else:
        return True, None
    
    finally:
      # Resets values
      self._proc = None
      self._terminated = False
    
  def terminate_compression(self) -> tuple[bool, str]:
    """ Terminates compression process running at users request """
    # _proc_poll will only be None when process is running
    if self._proc and self._proc.poll() is None:
      
      # Send termination command to the process
      self._proc.terminate()
      self._terminated = True
      
      try:
        self._proc.wait(timeout=5)
      
      except subprocess.TimeoutExpired:
        # Send harsher kill command if timeout expires
        self._proc.kill()
        return True, "Video compression killed"
      
      else:
        return True, "Video compression terminated"
    
    else:
      return False, ""

  @staticmethod
  def _quality_converter(quality: int) -> int:
    """ Converts quality percentage into inerted CRF number to specify bitrate """
    # Quality needs be inverted as the lower the CRF number, the better the quality
    quality_inverted = abs(quality / 100 - 1)
    crf = quality_inverted * 33 + 18  # Range 18 to 51
    return int(crf)

  @staticmethod
  def _uniquify(file_path: str) -> Path:
    """ Adds unique number to filename, if file already exists """
    filename, extension = os.path.splitext(file_path)
    counter = 1

    while os.path.exists(file_path):
        file_path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return Path(file_path)