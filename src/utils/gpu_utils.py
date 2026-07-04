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
type Pipeline = tuple[str, ...]
type SystemCommands = dict[str, Pipeline]

# Dictonary on parent and child commands to retreive GPU names from a specific device
system_commands: SystemCommands = {
    "Linux" : ("lspci",),
    "Darwin" : ("system_profiler", "SPDisplaysDataType"),
    "win11" : ("powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"),
    "win-legacy" : ("wmic", "path", "Win32_VideoController", "get", "name")
}

def get_device_output() -> str:
  """ Calls system to get string of connected GPUs """
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

  cmd: Pipeline = system_commands[device_os]

  flags: dict[str, Any] = {}
    
  # flags to hide console window
  if device_os in ("win-legacy", "win11", "Windows"):
    flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    flags["startupinfo"] = si
    
  else:
    flags["start_new_session"] = True

  output = run_cmd(cmd, flags)
  
  return output
    
def run_cmd(cmd: Sequence[str], flags: dict[str, Any]) -> str:
  """ Run parent command, returns undecode bytes to be piped into child commands """
  try:
    output = subprocess.run(
      cmd, 
      capture_output=True,
      check=True,
      shell=False,
      text=True,
      **flags
    )
 
  # Raise errors to stop script if issues occur, errors are caught in the _get_codec_values function
  except FileNotFoundError as e:
    raise FileNotFoundError("Command not found in PATH") from e

  except PermissionError as e:
    raise PermissionError("Permission denied when running system command") from e

  except subprocess.CalledProcessError as e:
    raise RuntimeError("Subprocess failed") from e

  except OSError as e:
    raise OSError("OS error while running subprocess") from e
    
  else:
    return output.stdout

def parse_linux_output(output: str) -> list[str]:
  gpus = []

  for line in output.splitlines():
    if any(x in line.lower() for x in ("vga", "3d", "video")):
      gpus.append(line.split(": ", 1)[1].split(" (rev")[0])
  
  return gpus

def parse_mac_output(output: str) -> list[str]:
  gpus = []

  for line in output.splitlines():
    if "Chipset Model:" in line:
      gpus.append(line.split(":", 1)[1].strip())
  
  returngpus

def parse_win_output(output: str) -> list[str]:
  gpus = []

  for line in output.splitlines():
    if line.lower not in ["name", "names"] or line != "":
      gpus.append(line)
  
  return gpus
  
def gpu_splitter(name: str) -> list[str]:
  """ Remove characters and symbols added to GPU names and returns clean names for better comparison """
  split_name = []

  for string in name.split():
    stripped = re.sub(r"[\($@*&?-].*[\)$@*&?-]", "", string).strip()

    if stripped != "":
      split_name.append(stripped)
  
  return split_name
  
def manufacturers() -> list[str]:
  """
  Returns manufacturer names of all connected GPUs
  
  Possible returns options:
  NVIDIA - for NVIDIA GPUS
  AMD - for AMD for dedicated and integrated GPUs
  Intel - for Intel for dedicated and integrated GPUs
  Apple - for Macbook M5 GPUs
  Adapter - possible returns on Virtual Machines and Container hosted OS
  """

  output: str = get_device_output()
  
  device_os: str = platform.system()

  if device_os == "Windows":
    gpus = parse_win_output(output)
  elif device_os == "Linux":
    gpus = parse_linux_output(output)
  elif device_os == "Darwin":
    gpus = parse_mac_output(output)
  

  gpu_manufacturers: list[str] = []

  for gpu in gpus:
    name = gpu_splitter(gpu)

    # Linux devices may use Advanced Micro Devices, Inc instead on AMD
    if name[0] == "Advanced":
      gpu_manufacturers.append("AMD")
      continue

    # possible options for OS run on virtual machines, and containers
    elif name[0] in ["Microsoft", "VMware", "VirtualBox"]:
      gpu_manufacturers.append("Adpter")

    gpu_manufacturers.append(name[0])

  return gpu_manufacturers