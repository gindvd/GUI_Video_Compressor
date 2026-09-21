from dataclasses import dataclass


@dataclass
class OptimizeSettings:
    video_codec: str = "libx264"
    container: str = "mp4"
    resolution: str = "1920x1080"
    frame_rate: str = "60"
    quality: int = 90
    include_audio: bool = True
    audio_codec: str | None = "aac"
    audio_bitrate: str | None = "128k"
    preset: str | None = "medium"
