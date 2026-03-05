import os
import subprocess
import platform

class FFmpegProcessor():
  def __init__(self, ffmpeg):
    self._ffmpeg = ffmpeg
    self._proc = None

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
    
    command.extend([output_file])

    if platform.system() == "Windows":
      creationflag = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
      creationflag = 0

    try:
      proc = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              shell=False,
                              text=True)

      output, error = proc.communicate()

      if proc.returncode != 0:
        return False, error
      
      return True, None
    
    except Exception as e:
      print(e)
      return False, str(e)

  @staticmethod
  def crf_converter(quality):
    """ Convert quality percentage (0-100) to CRF value (10-51) """
    quality_inverted = abs(quality / 100 - 1)
    crf = quality_inverted * 41 + 10
    return int(crf)