import logging
import os

from datetime import datetime

from resource_paths import resource_path

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# Creates the actual log file when logger is called
if not logger.handlers:
    now = datetime.now()
    strnow = now.strftime("%m-%d-%Y_%H-%M-%S")

    log_file: str = resource_path(os.path.join("logs", f"{strnow}.log"))
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    file_handler = logging.FileHandler(log_file, delay=True)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
