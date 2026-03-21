import os
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_logs(err_msg):
  now = datetime.now()

  log_basename = str(now) + ".log"

  log_dir_path = os.path.join(ROOT_DIR, 'logs')
  os.makedirs(log_dir_path, exist_ok=True)

  log_file = os.path.join(log_dir_path, log_basename)

  with open(log_file, 'w') as f:
    f.write(err_msg)