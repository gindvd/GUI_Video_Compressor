from dataclasses import dataclass

from services.ffmpeg_service import FFmpegService
from services.ffprobe_service import FFprobeService
from services.vlc_playback_service import VLCService


@dataclass
class Services:
    ffmpeg_service: FFmpegService
    ffprobe_service: FFprobeService
    vlc_service: VLCService