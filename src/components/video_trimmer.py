import customtkinter as ctk

import vlc
import platform

class VideoTrimmer(ctk.CTkFrame):
  def __init__(self):
    super().__init__()
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._instance = self._platform_specific_inst()
    self._vid_player = self._instance.media_player_new()

    self._vid_panel = ctk.CTkFrame(self, bg="black")
    self._vid_panel.pack(fill='both', expand=True)

    self._control_panel = ctk.CTkFrame(self)
    self._control_panel.pack(fill='x', padx=10, pady=10)

    self._add_controls()

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
            self.destroy()
        
        else:
            return vlc.Instance("--plugin-path={}".format(vlc_path))
    
    else:
        return vlc.Instance()
      
  def _add_controls(self):
    self._play_pause_btn = ctk.CTkButton(self._control_panel, text="Play", command=self._play_pause)
    self._play_pause_btn.pack(padx=5, pady=5)

  def _play_pause(self):
    btn_text = self._play_pause_btn['text']

    if btn_text == "Play":
      self._vid_player.play()
      self._play_pause_btn.configure(text='Pause')
    
    elif btn_text == "Pause":
      self._vid_player.pause()
      self._play_pause_btn.configure(text="Play")
  
