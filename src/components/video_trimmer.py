import customtkinter as ctk

import vlc
import platform

class VideoTrimmer(CTkFrame):
  def __init__(self):
    super().__init__()

    self._instance = self._platform_specific_inst()

  def _platform_specific_inst(self):

    if platform.system() == "Windows":

      try:
        vlc_path = os.path.abspath("lib/win32/vlc-win32.exe")

        except FileNotFoundError:
          close = CTkMessagebox(title="Missing FFmpeg Exe", 
                                message="""
                                        ERROR!\n
                                        vlc-win32.exe is missing from lib folder!\n
                                        Please ensure FFmpeg is installed correctly!
                                        """, 
                                icon="cancel",
                                option_1="Ok")
        
          if close.get() == "Ok":
            self.quit()
        
        else:
            return vlc.Instance("--plugin-path={}".format(vlc_path))
    
    else:
        return vlc.Instance()
      