from app import App
from utils.log_utils import logger
from utils.path_utils import setup_vlc_environment

def main():
  setup_vlc_environment()

  app = App()
  app.protocol("WM_DELETE_WINDOW", app.on_quit)
  app.mainloop()

if __name__ == "__main__":
  main()