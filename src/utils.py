from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parents[1]

def create_logs(err_msg):
  now = datetime.now()
  basename = str(now) + ".log"

  log_directory = ROOT_DIR / 'logs'
  log_directory.mkdir(exist_ok=True)
  log_file = log_directory / basename

  with open(log_file, 'w') as f:
    f.write(err_msg)