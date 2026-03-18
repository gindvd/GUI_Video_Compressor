import platform
import subprocess
import re

class OSCompatibiltyError(Exception):
  def __init__(self, message, os):
    super().__init__(message)
    self.os = os
  
  def __str__(self):
    return "{} (Non-Compatible OS: {}) List of compatible OS [Windows, Linux, Mac OS]".format(self.message, self.os)

CMD_DICT = {
  "Linux" : "lspci | grep -iE VGA|3D|video",
  "Darwin" : "system_profiler SPDisplaysDataType",
  "Windows" : {
    "11" : "powershell -Command Get-CimInstance Win32_VideoController | Select-Object name",
    "legacy" : "wmic path win32_VideoController get name"
    }
}

def get_card_info():
  device_os = platform.system()
  
  if device_os not in ["Windows", "Linux", "Darwin"]:
    raise OSCompatibiltyError("Current OS is not compatible with this module.", device_os)

  if device_os == "Windows":
    win_ver = platform.release()
  
    if win_ver != "11":
      win_ver = "legacy"
      
    cmd =  CMD_DICT.get(device_os, {}).get(win_ver)
  
  else:
    cmd = CMD_DICT.get(device_os)
    
  # Need to seperate commands in 2 if it contains a pipe
  # Then turn both commands into lists
  cmd_lists = [word.split() for word in cmd.split('|', 1)]
  
  assert len(cmd_lists) <= 2, "Command list contains too many lists of commands, Max Num of list: 2"

  primary_cmd = cmd_lists[0]
  secondary_cmd = None
  
  if len(cmd_lists) == 2:
    GPUname_cmd2 = cmd_lists[1]

  assert primary_cmd != None, "Primary command is set to None"

  if secondary_cmd == None:
    return run_cmd(primary_cmd)

  return run_piped_cmds(primary_cmd, secondary_cmd)

def run_cmd(cmd):
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
    print(e)
  
  except Exception as e:
    print(e)

  else:
    if rc != 0:
      print(f"{str(rc)}: {err}")

    else:
      return out.split()


def run_piped_cmd(cmd1, cmd2):
  proc1 = subprocess.Popen(cmd1,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False,
                            text=True)

  proc2 = subprocess.Popen(secondary_cmd,
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
    print(e)
  
  except Exception as e:
    print(e)
    
  else:
    if rc != 0:
      print(f"{str(rc)}: {err}")

    else:
      return out.split()

def clean_data(list):
  clean_list = []
  
  for string in list:
    stripped = re.sub(r"[\(\[$@*&?-].*[\)\]$@*&?-]", "", string)
    clean_list.append(stripped)

  return clean_list
  
def manufacturer():
  gpus = clean_data(GPU_names())
  manufacturers = []
  
  for string in gpus:
    if string in ["NVIDIA", "AMD", "Intel"]:
      manufacturers.append(string)
      
  return manufacturers
  
def brand():
  gpus = clean_data(GPU_names())
  brand_list = []
  
  for string in gpus:
    if string in ["GeForce", "Radeon", "Arc", "Iris", "UHD", "HD"]:
      brand_list.append(string)
      
  return brands