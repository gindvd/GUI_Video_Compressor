from dataclasses import dataclass

from models.optimize_settings import OptimizeSettings
from models.media_attrs import MediaAttrs
from models.media_timestamps import MediaTimestamps
from models.gif_settings import GifSettings


@dataclass
class AppState:
    media: MediaAttrs
    settings: OptimizeSettings
    timestamps: MediaTimestamps
    gif_settings: GifSettings
