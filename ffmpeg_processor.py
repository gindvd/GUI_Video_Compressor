import subprocess

class FFmpegProcessor():
  def __init__(self, ffmpeg):
    self.ffmpeg = ffmpeg

  def compress(self, input_file, file_format, resolution, codec, fps, quality, audio):
    basename, _ = os.path.splitext(input_file)
    output_file = basename + "_compressed." + file_format

    width, height = resolution.split("x")
    scale = "scale={}:{}".format(width, height)
    
    crf = self.crf_converter(quality)
    
    if codec == "libvpx-vp9":
      audio_codec = "libopus"
    else:
      audio_codec = "aac"

    command = [self.ffmpeg, 
               "i", input_file, 
               "-c:v", codec,
               "-r", fps,
               "-crf", crf, 
               "-vf", scale]

    if not audio:
      command.extend(["-an"])
    elif audio:
        command.extend(["-c:a", audio_codec, 
                        "-b:a", "128k"]) 
    
    command.extend(output_file)

    try:
      _, err = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, shell=False, text=True)

      return "success"
    
    except FileNotFoundError as err:
     pass
    except subprocess.CalledProcessError as err:
      pass
    except Exception as err:
      pass

  """ 
  Converts quality which will be a number between 100 and 0 to
  a number between 0 and 51 which will be in the range of all
  codec options
  """
  def crf_converter(self, quality):
    return math.floor((quality / 100) * 51)