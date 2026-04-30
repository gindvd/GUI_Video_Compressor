import platform
import subprocess
import re

class CompatibiltyError(Exception):
  def __init__(self, message: str, oper_system: str) -> None:
    super().__init__()
    self._oper_system = oper_system
    self._message = message
  
  def __str__(self) -> str:
    return f"{self._message}\n(Incompatible Operating System: {self._oper_system})\n\nCompatible Operating Stsyems: Windows, Linux, MacOS"

system_commands: dict = {
    "Linux" : (("lspci"), ("grep", "-iE", "VGA|3D|video"), ("awk", "-F", ": ", "{print $2}"), ("sed", "s/ (rev .*)$//")),
    "Darwin" : (("system_profiler", "SPDisplaysDataType"),  ("grep", "Chipset Model"), ("awk", "-F", ": ", "{print $2}")),
    # empty list is temp solution to keep parent command from being set to 'powershell' / "wmic" and not the full list
    "win11" : (("powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"), () ),
    "win-legacy" : (("wmic", "path", "Win32_VideoController", "get", "name"), ())
}

def get_gpu_names() -> str:
  oper_system: str = platform.system()

  if oper_system not in ["Linux", "Darwin", "Windows"]:
    raise CompatibiltyError("The GPU info cannot be obtained on this device", oper_system)

  # use powershell on Windows 11, bash on older Windows versions
  if oper_system == "Windows":
    version = platform.release()
    if version != "11":
      oper_system = "win-legacy"
    
    else:
      oper_system = "win11"

  parent_cmd = system_commands[oper_system][0]
  child_cmds = system_commands[oper_system][1:]

  output: bytes = run_parent(parent_cmd)

  if child_cmds[0] == ():
    return output.decode()

  for child_cmd in child_cmds:
    output = run_child(child_cmd, output)

  return output.decode()
  
def run_parent(cmd: list[str]) -> bytes:
  try:
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            shell=False)

    out, err = proc.communicate()
    proc.wait()
    
    rc = proc.returncode

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
  
def run_child(child_cmd: list[str], parent_output: bytes) -> bytes:
  try:
    proc = subprocess.Popen(child_cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=False) 
    
    out, err = proc.communicate(input=parent_output)
    proc.wait()
    rc = proc.returncode

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

  device_manufacturers = []
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