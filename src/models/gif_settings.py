from dataclasses import dataclass

@dataclass
class GifSettings:
    output_file: str | None = None

    resolution: str = "854x480"
    fps: str = "15"
    loops: int = 0
