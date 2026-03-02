import asyncio
import os

class FFmpegProcessor():
  def __init__(self, ffmpeg):
    self.ffmpeg = ffmpeg

  async def compress(self, input_file, file_format, resolution, codec, fps, quality, audio):
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
               "-i", input_file, 
               "-c:v", codec,
               "-r", fps,
               "-crf", str(crf), 
               "-vf", scale]

    if not audio:
      command.extend(["-an"])
    elif audio:
        command.extend(["-c:a", audio_codec, 
                        "-b:a", "128k"]) 
    
    command.extend([output_file])

    cmd_str = " ".join(command)

    print(cmd_str)

    try:
      proc = await asyncio.create_subprocess_exec(cmd_str, 
                                                  stdout=asyncio.subprocess.PIPE, 
                                                  stderr=asyncio.subprocess.PIPE)

      output, error = await proc.communicate()

      print(error)

      if proc.returncode != 0:
        return False, error.decode()
      
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