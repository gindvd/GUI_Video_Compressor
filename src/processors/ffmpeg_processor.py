import os
import subprocess
import platform

class FFmpegProcessor():
  def __init__(self, ffmpeg):
    self._ffmpeg = ffmpeg
    self._proc = None
    self._terminated = False

  def compress(self, input_file, file_format, resolution, codec, fps, quality, audio):
    basename, _ = os.path.splitext(input_file)
    output_file = basename + "_compressed." + file_format
    
    width, height = resolution.split("x")
    scale = "scale={}:{}".format(width, height)
    
    crf = self._crf_converter(quality)
    
    if codec in ["libvpx-vp9", "libsvtav1"]:
      audio_codec = "libopus"
    else:
      audio_codec = "aac"

    cmd = [self._ffmpeg,
           "-i", input_file, 
           "-c:v", codec,
           "-r", fps,
           "-crf", str(crf), 
           "-vf", scale]

    if not audio:
      cmd.extend(["-an"])
    elif audio:
        cmd.extend(["-c:a", audio_codec, 
                    "-b:a", "128k"]) 
    
    cmd.extend([output_file])

    creation_flags = {}

    if platform.system() == "Windows":
      creation_flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
      creation_flags["start_new_session"] = True
    
    self._proc = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              shell=False,
                              **creation_flags)

    try:
      out, err = self._proc.communicate()
      self._proc.wait()
    
      rc = self._proc.returncode

    # AttributeError sometimes raised when cancelling video compression due to _proc being set to None which has no wait
    # Must be a timing thing
    # Addding except to ignore and treat like normal termination as it still properly kills the process
    except AttributeError:
      if os.path.exists(output_file):
        os.remove(output_file)
        
      return False,  ""
    
    except FileNotFoundError:
      return False, "FFmpeg could not be found!"        
    
    except Exception as e: 
      self._log_errors(e)
      return False, "Error Occured!\nCheck logs for details!"
    
    else:
      if rc != 0 and self._terminated == False:
        if os.path.exists(output_file):
                os.remove(output_file)
        
        print(err)
        return False, "Compression Failed\nCheck logs for details!"

      elif rc != 0 and self._terminated == True:
        if os.path.exists(output_file):
                os.remove(output_file)
        
        return False,  ""

      else:
        return True, None
    
    finally:
      self._proc = None
      self._terminated = False
    
  def terminate_compression(self):
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
  def _crf_converter(quality):
    # Quality needs be inverted as the lower the CRF number, the better the quality
    quality_inverted = abs(quality / 100 - 1)
    crf = quality_inverted * 41 + 10
    return int(crf)

  @staticmethod
  def _log_errors( err_msg):
    now = datetime.now()

    basename= now + ".log"
    parent = os.path.abspath(os.path.join(cwd, os.pardir))

    filepath = os.path.join(parent, 'log')

    os.makedirs(filepath, exist_ok=True)

    log_file = os.path.join(filepath, basename)

    with open(log_file, 'w') as f:
      f.write(err_msg)  