from dataclasses import dataclass


@dataclass
class MediaAttrs:
    input_file: str | None = None
    output_file: str | None = None

    base_resolution: str = "1920x1080"
    full_duration_seconds: float = 0.0
    full_duration_ms: int = 0

    average_fps_str: str = "30/1"
    average_fps_int: int = 30

    has_audio: bool = True
