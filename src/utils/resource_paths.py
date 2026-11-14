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
