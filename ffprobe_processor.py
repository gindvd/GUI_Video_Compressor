import subprocess

class FFprobeProcessor():
  def __init__(self, ffprobe):
    self.ffprobe = ffprobe
    
  def get_duration(self, filepath):
    command = [self.ffprobe, "-v", "error", "-show_entries", 
               "format=duration", "-of", 
               "default=noprint_wrappers=1:nokey=1", 
               "-sexagesimal", filepath]
    
    try:
      duration, _ = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, shell=False, text=True)
    
      return duration
    
    except FileNotFoundError as err:
      pass
    except subprocess.CalledProcessError as err:
      pass
    except Exception as err:
      pass  