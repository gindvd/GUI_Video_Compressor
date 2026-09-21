from pathlib import Path

import sys
import os


def resource_path(relative_path: str = "") -> str:
    """Get absolute paths of resources"""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return str(base_path / relative_path)


def get_button_image_path(img_name: str) -> str:
    relative_path = os.path.join("assets", "images", "video_control_icons", img_name)

    abs_path = resource_path(relative_path)

    if not os.path.isfile(abs_path):
        raise SystemExit(f"Missing dependency: {abs_path}")

    return abs_path


def setup_vlc_environment() -> None:
    """Set up VLC paths for the python-vlc library to use bundled VLC dlls / plugins in the bin folder"""

    vlc_dir = resource_path(os.path.join("bin", "vlc"))

    if not os.path.isdir(vlc_dir):
        raise SystemError("Missing VLC plugins folder!")

    os.environ["PYTHON_VLC_MODULE_PATH"] = str(vlc_dir)
    os.environ["PYTHON_VLC_LIB_PATH"] = str(os.path.join(vlc_dir, "libvlc.dll"))

    # add dlls explicitly
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(vlc_dir))

    os.environ["PATH"] = str(vlc_dir) + os.pathsep + os.environ.get("PATH", "")


if sys.platform.startswith("win"):
    setup_vlc_environment()
