import platform
import subprocess
import re
from collections.abc import Sequence
from typing import Any

class CompatibiltyError(Exception):
  """ Error raised when devices operating system is not compatible with the script """
  def __init__(self, message: str, device_os: str) -> None:
    super().__init__()
    self._device_os: str = device_os
    self._message: str = message
  
  def __str__(self) -> str:
    """ Formatted string with information to get logged when error is raised """
    return f"{self._message}\n(Incompatible Operating System: {self._device_os})\n\nCompatible Operating Stsyems: Windows, Linux, MacOS"

# Type aliases for system cmmands dictinary
type Command = tuple[str, ...]
type Pipeline = tuple[Command, ...]
type SystemCommands = dict[str, Pipeline]

# Dictonary on parent and child commands to retreive GPU names from a specific device
system_commands: SystemCommands = {
    "Linux" : (("lspci"), ("grep", "-iE", "VGA|3D|video"), ("awk", "-F", ": ", "{print $2}"), ("sed", "s/ (rev .*)$//")),
    "Darwin" : (("system_profiler", "SPDisplaysDataType"),  ("grep", "Chipset Model"), ("awk", "-F", ": ", "{print $2}")),
    # empty list is temp solution to keep parent command from being set to 'powershell' / "wmic" and not the full list
    "win11" : (("powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"), () ),
    "win-legacy" : (("wmic", "path", "Win32_VideoController", "get", "name"), ())
}

def get_gpu_names() -> str:
  """ Begins process of getting the names of all connected GPUs """
  device_os: str = platform.system()

  if device_os not in ["Linux", "Darwin", "Windows"]:
    raise CompatibiltyError("The GPU info cannot be obtained on this device", device_os)

  # use powershell on Windows 11, batch on older Windows versions
  if device_os == "Windows":
    version = platform.release()
    if version != "11":
      device_os = "win-legacy"
    
    else:
      device_os = "win11"

  parent_cmd = system_commands[device_os][0]
  child_cmds = system_commands[device_os][1:]

  flags: dict[str, Any] = {}
    
  # flags to hide console window
  if device_os == "Windows":
    flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    flags["startupinfo"] = si
    
  else:
    flags["start_new_session"] = True

  output: bytes = run_parent(parent_cmd, flags)

  # Immediately returns decoded data if no child commands exist     
  if child_cmds[0] == ():
    return output.decode()
  
  # Runs all child commands inputting the output from the previous command
  for child_cmd in child_cmds:
    output = run_child(child_cmd, output, flags)

  return output.decode()
  
def run_parent(cmd: Sequence[str], flags: dict[str, Any]) -> bytes:
  """ Run parent command, returns undecode bytes to be piped into child commands """
  try:
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False,
                            **flags)

    out, err = proc.communicate()
    proc.wait()
    
    rc = proc.returncode
  
  # Raise errors to stop script if issues occur, errors are caught in the _get_codec_values function
  except FileNotFoundError as e:
    raise FileNotFoundError("Command not found in PATH") from e

  except PermissionError as e:
    raise PermissionError("Permission denied when running system command") from e

  except subprocess.SubprocessError as e:
    raise RuntimeError("Subprocess failed") from e

  except OSError as e:
    raise OSError("OS error while running subprocess") from e
    
  else:
    if rc != 0:
      raise subprocess.CalledProcessError(rc, cmd, output=out, stderr=err)

    return out
  
def run_child(child_cmd: Sequence[str], parent_output: bytes, flags: dict[str, Any]) -> bytes:
  """ Takes prvious commands output and runs new command to extract information """
  try:
    proc = subprocess.Popen(child_cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False,
                            **flags) 
    
    out, err = proc.communicate(input=parent_output)
    proc.wait()
    rc = proc.returncode
  
  # Raise errors to stop script if issues occur, errors are caught in the _get_codec_values function
  except FileNotFoundError as e:
    raise FileNotFoundError("Command not found in PATH") from e

  except PermissionError as e:
    raise PermissionError("Permission denied when running system command") from e
  
  except TypeError as e:
    raise TypeError("STDIN PIPE given incorrect type") from e 

  except subprocess.SubprocessError as e:
    raise RuntimeError("Subprocess failed") from e

  except OSError as e:
    raise OSError("OS error while running subprocess") from e
    
  else:
    if rc != 0:
      raise subprocess.CalledProcessError(rc, child_cmd, output=out, stderr=err)

    return out
  
def remove_symbols(input: str) -> str:
  """ Remove characters and symbols added to GPU names and returns clean names for better comparison """
  clean_list = []
  if input == "Name":
    return ""
  
  split_input = input.split()
  
  for string in split_input:
    stripped = re.sub(r"[\($@*&?-].*[\)$@*&?-]", "", string)
    clean_list.append(stripped)

  return " ".join(clean_list)
  
def manufacturers() -> list[str]:
  """
  Possible returns options:
  NVIDIA - for NVIDIA GPUS
  AMD - for AMD for dedicated and integrated GPUs
  Intel - for Intel for dedicated and integrated GPUs
  Apple - for Macbook M5 GPUs
  Adapter - possible returns on Virtual Machines and Container hosted OS
  """

  string_of_connected_gpus: str = get_gpu_names()
  
  list_of_connected_gpus: list[str] = string_of_connected_gpus.splitlines()

  device_manufacturers: list[str] = []
  for connected_gpu in list_of_connected_gpus:
    temp = []
    connected_gpu = remove_symbols(connected_gpu)
    temp = connected_gpu.split()

    if temp == []:
      continue
    
    name = temp[0]

    # Windows command batch will return name 
    if name in ("", "Name", "name"):
      continue

    # Linux devices may use Advanced Micro Devices, Inc instead on AMD
    elif name == "Advanced":
      name = "AMD"

    # possible options for OS run on virtual machines, and containers
    elif name in ["Microsoft", "VMware", "VirtualBox"]:
      name = "Adapter"

    device_manufacturers.append(name)

  return device_manufacturers