from platform import system

try:
  from ctypes import windll
except:
  pass

from app import App

from resource_paths import setup_vlc_environment

def main():
  setup_vlc_environment()

  if system() == "Windows":
    windll.shcore.SetProcessDpiAwareness(2)

  app = App()
  app.protocol("WM_DELETE_WINDOW", app.on_quit)
  app.mainloop()

if __name__ == "__main__":
  main()