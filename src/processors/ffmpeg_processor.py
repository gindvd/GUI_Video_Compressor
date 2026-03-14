import os
import subprocess
import platform

class FFmpegProcessor():
  def __init__(self, ffmpeg):
    self._ffmpeg = ffmpeg
    self._proc = None
    self._proc_poll = 1

  def compress(self, input_file, file_format, resolution, codec, fps, quality, audio):
    basename, _ = os.path.splitext(input_file)
    output_file = basename + "_compressed." + file_format
    
    width, height = resolution.split("x")
    scale = "scale={}:{}".format(width, height)
    
    crf = self._crf_converter(quality)
    
    if codec == "libvpx-vp9":
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
    
    self._proc = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              shell=False,
                              creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

    try:
      out, err = self._proc.communicate()
      self._proc_poll = self._proc.poll()
    
    except subprocess.CalledProcessError:
      return False, err
    
    except FileNotFoundError:
      return False, "FFmpeg could not be found!"        
    
    except Exception as e: 
      return False, e
    
    else:
      return True, None
    
    finally:
      self._proc = None
      self._proc_poll = 1
    
  def terminate_compression(self):
    # _proc_poll will only be None when process is running
    if self._proc and self._proc_poll is None:
      self._proc.terminate()

      try:
        self._proc.wait(timeout=3)
        return True, "Video compression terminated"
      
      except subprocess.TimeoutExpired:
        self._proc.kill()
        return True, "Video compression killed"

      finally:
        self._proc = None
        self._proc_poll = 1
      
    return False, ""

  @staticmethod
  def _crf_converter(quality):
    # Quality needs be inverted as the lower the CRF number, the better the quality
    quality_inverted = abs(quality / 100 - 1)
    crf = quality_inverted * 41 + 10
    return int(crf)