import platform
import subprocess
import re

from collections.abc import Callable

from utils import create_logs
from utils import DEVICE_OS

class OSCompatibiltyError(Exception):
  def __init__(self, message: str, os: str) -> None:
    super().__init__()
    self._os = os
    self._message = message
  
  def __str__(self) -> str:
    return f"{self._message} (Non-Compatible OS: {self._os})\nCompatible OS: Windows , Linux"

CMD_DICT = {
  "Linux" : "lspci | grep -iE VGA|3D|video",
  "Darwin" : "system_profiler SPDisplaysDataType",
  "Windows" : {
    "11" : "powershell -Command Get-CimInstance Win32_VideoController | Select-Object name",
    "legacy" : "wmic path win32_VideoController get name"
    }
}

def get_card_info() -> list[str] | None:
  try:
    if DEVICE_OS not in ["Windows", "Linux", "Darwin"]:
      raise OSCompatibiltyError("Current OS is not compatible with this module.", DEVICE_OS)
  
  except OSCompatibiltyError as e:
    create_logs(str(e))
    return None

  if DEVICE_OS == "Windows":
    win_ver = platform.release()
  
    if win_ver != "11":
      win_ver = "legacy"
      
    cmd =  CMD_DICT.get(DEVICE_OS, {}).get(win_ver)
  
  else:
    cmd = CMD_DICT.get(DEVICE_OS)
    
  # Need to seperate commands in 2 if it contains a pipe
  # Then turn both commands into lists
  cmd_lists: list[list[str]] = [word.split() for word in cmd.split('|', 1)]
  
  assert len(cmd_lists) <= 2, "Command list contains too many lists of commands, Max Num of list: 2"

  parent_cmd: list[str] = cmd_lists[0]
  child_cmd: list[str] | None = None

  try:
    if parent_cmd is None:
      raise AttributeError

  except AttributeError:
    create_logs("Parent command set to None")

    return None
  
  if len(cmd_lists) == 2:
    child_cmd = cmd_lists[1]

  if child_cmd == None:
    return run_cmd(parent_cmd)

  return run_piped_cmd(parent_cmd, child_cmd)

def run_cmd(cmd: list[str]) -> list[str] | None:
  proc = subprocess.Popen(cmd, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          shell=False, 
                          text=True)

  try:
    out, err = proc.communicate()
    proc.wait()
    
    rc = proc.returncode

  except FileNotFoundError as e:
    create_logs(str(e))

    return None
  
  except Exception as e:
    create_logs(str(e))

    return None

  else:
    if rc != 0:
      create_logs(err)
      
      return None

    return out.split()


def run_piped_cmd(cmd1: list[str], cmd2: list[str]) -> list[str] | None:
  proc1 = subprocess.Popen(cmd1,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False,
                            text=True)

  proc2 = subprocess.Popen(cmd2,
                             stdin=proc1.stdout,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False,
                             text=True) 
  
  try:
    proc1.stdout.close() 
    out, err = proc2.communicate()

    proc2.wait()
    rc = proc2.returncode

  except FileNotFoundError as e:
    create_logs(str(e))

    return None
  
  except Exception as e:
    create_logs(str(e))

    return None
    
  else:
    if rc != 0:
      create_logs(err)

      return None

    return out.split()

def clean_data(gpu_list: list[str]) -> list[str]:
  clean_list = []
  
  for string in gpu_list:
    stripped = re.sub(r"[\(\[$@*&?-].*[\)\]$@*&?-]", "", string)
    clean_list.append(stripped)

  return clean_list
  
def manufacturer() -> list[str] | None:
  gpus = get_card_info()

  if gpus is None:
    return None

  gpus = clean_data(gpus)
  
  manufacturers = []
  
  for string in gpus:
    if string in ["NVIDIA", "AMD", "Intel"]:
      manufacturers.append(string)
      
  return manufacturers