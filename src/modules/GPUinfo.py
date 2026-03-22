import platform
import subprocess
import re

from collections.abc import Callable

from utils import create_logs
from utils import DEVICE_OS

class OSCompatibiltyError(Exception):
  def __init__(self, message: str, os: str) -> None:
    super().__init__(message)
    self.os = os
  
  def __str__(self) -> str:
    return f"{self.message} (Non-Compatible OS: {self.os})\nList of compatible OS [Windows, Linux, Mac OS]"

CMD_DICT = {
  "Linux" : "lspci | grep -iE VGA|3D|video",
  "Darwin" : "system_profiler SPDisplaysDataType"
  "Windows" : {
    "11" : "powershell -Command Get-CimInstance Win32_VideoController | Select-Object name",
    "legacy" : "wmic path win32_VideoController get name"
    }
}

def get_card_info() -> Callable[[list[str]], list[str]] | Callable[[list[str], list[str]] list[str]]:
  try:
    if DEVICE_OS not in ["Windows", "Linux", "Darwin"]:
      raise OSCompatibiltyError("Current OS is not compatible with this module.", DEVICE_OS)
  
  except OSCompatibiltyError as e:
    create_logs(str(e))
    raise

  if DEVICE_OS == "Windows":
    win_ver = platform.release()
  
    if win_ver != "11":
      win_ver = "legacy"
      
    cmd =  CMD_DICT.get(device_os, {}).get(win_ver)
  
  else:
    cmd = CMD_DICT.get(device_os)
    
  # Need to seperate commands in 2 if it contains a pipe
  # Then turn both commands into lists
  cmd_lists: list[list[str]] = [word.split() for word in cmd.split('|', 1)]
  
  assert len(cmd_lists) <= 2, "Command list contains too many lists of commands, Max Num of list: 2"

  primary_cmd: list[str] = cmd_lists[0]
  secondary_cmd: list[str] | None = None
  
  if len(cmd_lists) == 2:
    secondary_cmd = cmd_lists[1]

  assert primary_cmd != None, "Primary command is set to None"

  if secondary_cmd == None:
    return run_cmd(primary_cmd)

  return run_piped_cmd(primary_cmd, secondary_cmd)

def run_cmd(cmd: list[str]) -> list[str]:
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
    create_logs(e)
  
  except Exception as e:
    create_logs(e)

  else:
    if rc != 0:
      create_logs(err)

    else:
      return out.split()


def run_piped_cmd(cmd1: list[str], cmd2: list[str]) -> list[str]:
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
    create_logs(e)
  
  except Exception as e:
    create_logs(e)
    
  else:
    if rc != 0:
      create_logs(err)

    else:
      return out.split()

def clean_data(gpu_list: list[str]) -> list[str]:
  clean_list = []
  
  for string in gpu_list:
    stripped = re.sub(r"[\(\[$@*&?-].*[\)\]$@*&?-]", "", string)
    clean_list.append(stripped)

  return clean_list
  
def manufacturer() -> list[str]:
  gpus = clean_data(get_card_info())
  
  manufacturers = []
  
  for string in gpus:
    if string in ["NVIDIA", "AMD", "Intel"]:
      manufacturers.append(string)
      
  return manufacturers