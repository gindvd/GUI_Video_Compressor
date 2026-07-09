from pathlib import Path

import sys
import os
import shutil


def resource_path(relative_path: str = "") -> str:
    """Get absolute paths of resources"""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


def setup_vlc_environment() -> None:
    """Set up VLC paths for the python-vlc library to use bundled VLC dlls / plugins in the lib folder"""

    vlc_dir = resource_path(os.path.join("lib", "vlc"))

    if not os.path.isdir(vlc_dir):
        return

    os.environ["PYTHON_VLC_MODULE_PATH"] = str(vlc_dir)
    os.environ["PYTHON_VLC_LIB_PATH"] = str(os.path.join(vlc_dir, "libvlc.dll"))

    # add dlls explicitly
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(vlc_dir))

    os.environ["PATH"] = str(vlc_dir) + os.pathsep + os.environ.get("PATH", "")


setup_vlc_environment()


def get_dependencies(device_os: str) -> list[str]:
    """Gets absolute path for VLC, FFmpeg, and FFprobe"""
    if device_os == "Windows":
        return get_win_dependencies()
    elif device_os == "Linux":
        return get_linux_dependencies()

    raise SystemExit(f"App not compatible with {device_os}")


def get_win_dependencies() -> list[str]:
    """Gets the paths for FFmpeg, FFprobe, and VLC in the lib folder"""
    proc_paths: list[str] = []

    for proc in ("ffmpeg", "ffprobe", "vlc"):
        # gets path of the vlc plugins folder
        if proc == "vlc":
            abs_path = resource_path(os.path.join("lib", "vlc", "plugins"))

            if not os.path.isdir(abs_path):
                raise SystemExit(f"Missing dependency: {proc} missing from lib folder!")

            else:
                proc_paths.append(abs_path)

        else:
            abs_path = resource_path(os.path.join("lib", f"{proc}.exe"))

            if not os.path.isfile(abs_path):
                raise SystemExit(f"Missing dependency: {proc} missing from lib folder!")

            else:
                proc_paths.append(abs_path)

    return proc_paths


def get_linux_dependencies() -> list[str]:
    """get command strings for linux"""
    proc_paths: list[str] = []

    for proc in ("ffmpeg", "ffprobe", "vlc"):
        if shutil.which(proc):
            proc_paths.append(proc)

        else:
            raise SystemExit(f"Missing dependency: {proc}")

    return proc_paths


def get_icon() -> str | None:
    """Get path of png icon file"""
    icon_abspath: str = resource_path(
        os.path.join("assets", "images", "icons", "thestrawhat.png")
    )

    if not os.path.isfile(icon_abspath):
        return None

    return icon_abspath


def get_ico() -> str | None:
    """Get path of ico file"""
    icon_abspath: str = resource_path(
        os.path.join("assets", "images", "icons", "thestrawhat.ico")
    )

    if not os.path.isfile(icon_abspath):
        return None

    return icon_abspath


def get_button_image_path(file_name: str) -> str:
    """Get paths of button icons stored in the assets/images folder"""
    image_path: str = resource_path(
        os.path.join("assets", "images", "video_control_icons", file_name)
    )

    if not os.path.isfile(image_path):
        raise SystemExit(f"Missing image file: {file_name}")

    return image_path
