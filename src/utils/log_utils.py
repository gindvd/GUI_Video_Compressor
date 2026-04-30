import logging
import os

from datetime import datetime

from utils.path_utils import resource_path

logger = logging.getLogger('app_logger')
logger.setLevel(logging.DEBUG)

if not logger.handlers:
  now = datetime.now()
  strnow = now.strftime("%m-%d-%Y_%H-%M-%S")

  log_file = resource_path(os.path.join("logs", f"{strnow}.log"))
  os.makedirs(os.path.dirname(log_file), exist_ok=True)

  file_handler = logging.FileHandler(log_file)
  file_handler.setLevel(logging.DEBUG)

  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
  file_handler.setFormatter(formatter)

  logger.addHandler(file_handler)