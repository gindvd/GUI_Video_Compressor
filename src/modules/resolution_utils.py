def get_list_of_smaller_res(self, vid_res: str) -> list[str]:
  dimensions = vid_res.split('x')
    
  width = int(dimensions[0])
  height = int(dimensions[1])

  aspect_ratio = width / height

  # List of some reoccuring standard pixel measurements for height and width
  # Not a comprehessive list, but enough for a list of usable target 
  # resolutions for compressing too
   
  if width >= height:
    std_width = [5120, 3840, 2560, 1920, 1600, 1280, 854, 640]
    std_height = [2880, 2160, 1440, 1080, 900, 720, 480, 360]

  elif width < height:
    std_width = [2880, 2160, 1440, 1080, 900, 720, 480, 360]
    std_height = [5120, 3840, 2560, 1920, 1600, 1280, 854, 640]

  temp_res = []

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

  # Turns list into set to remove any duplicate resolutions, then reverts back to a list
  temp_res = list(set(temp_res))
    
  # Sort the list based on width
  temp_res = sorted(temp_res, key=lambda x: int(x.split('x')[0]), reverse=True)

  resolutions = []
    
  # Resolutions with width / height of 360 are too small so will remove them
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
    
  # Return video resolution if it has a height or width smaller than 360
  if not resolutions:
    return [vid_res]

  return resolutions

def round_to_even(f: float) -> int:
  return int(round(f / 2.) * 2)