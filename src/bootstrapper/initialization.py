from sys import platform

from app import App

from models.app_state import AppState
from models.media_attrs import MediaAttrs
from models.optimize_settings import OptimizeSettings
from models.media_timestamps import MediaTimestamps
from models.gif_settings import GifSettings


def initialize_app() -> App:
    app_state: AppState = AppState(
        media=MediaAttrs(),
        settings=OptimizeSettings(),
        timestamps=MediaTimestamps,
        gif_settings=GifSettings
    )

    if platform.startswith("win"):
        from bootstrapper.win_bootstrapper import initialize_win

        app: App = initialize_win(app_state)

    elif platform.startswith("linux"):
        from bootstrapper.linux_bootstrapper import initialize_linux

        app = initialize_linux(app_state)
    
    else:
        SystemExit("Not currently compatible with running operating system!")

    return app