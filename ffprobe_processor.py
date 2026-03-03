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
      duration, _ = subprocess.Popen(command, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     shell=False, 
                                     text=True)
    
      return duration
    
    except FileNotFoundError as err:
      pass
    except subprocess.CalledProcessError as err:
      pass
    except Exception as err:
      pass

  def get_resolutions(self, filepath):
    command = [self.ffprobe, "-v", "error", "-select_streams", 
               "v:0", "-show_entries", "stream=width,height", 
               "-of", "csv=s=x:p=0", filepath]
    
    try:
      result = subprocess.Popen(command, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                shell=False, 
                                text=True)
      
      resolution, _ = result.communicate()
      
      return self.updated_resolutions(resolution)
    
    except FileNotFoundError as err:
      print("1 {}".format(err))
    except subprocess.CalledProcessError as err:
      print("2 {}".format(err))
    except Exception as err:
      print("3 {}".format(err))

  def updated_resolutions(self, resolution):
    dimensions = resolution.split('x')
    
    width = int(dimensions[0])
    height = int(dimensions[1])

    aspect_ratio = width / height

    """ 
    List of some reoccuring standard pixel measurements for height and width
    Not a comprehessive list, but enough for a list of usable target 
    resolutions for compressing too
    """
    if width >= height:
      std_width = [5120, 3840, 2560, 1920, 1600, 1280, 854, 640]
      std_height = [2880, 2160, 1440, 1080, 900, 720, 480, 360]
    elif width < height:
      std_width = [2880, 2160, 1440, 1080, 900, 720, 480, 360]
      std_height = [5120, 3840, 2560, 1920, 1600, 1280, 854, 640]

    temp_res = []
    """ 
    Add original resolution to the list, useful for some 
    missing stanard screen resolutions
    """

    for size in std_width:
      if size <= width:
        h = self.round_to_even(size / aspect_ratio)
        new = str(size) + "x" + str(h)

        temp_res.extend([new])

    for size in std_height:
      if size <= height:
        w = self.round_to_even(size * aspect_ratio)
        new = str(w) + "x" + str(size)

        temp_res.extend([new])

    """ Turns list into set to remove any duplicate resolutions, then reverts back to a list """
    temp_res = list(set(temp_res))
    
    """ 
    Sorts list based of size by getting the width from the resolution string 
    and comparing it as an integer
    """
    temp_res = sorted(temp_res, key=lambda x: int(x.split('x')[0]), reverse=True)

    resolutions = []
    
    """ Removes resolutions with height or width smaller than 360 """
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

    return resolutions

  @staticmethod
  def round_to_even(f):
    return round(f / 2.) * 2