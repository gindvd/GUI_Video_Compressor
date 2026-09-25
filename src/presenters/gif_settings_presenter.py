from models.gif_settings import GifSettings

from viems.gif_settings_frame import GifSettingsFrame


class GifSettingsPresenter():
    def __init__(
        self, gif_settings: GifSettings, settings_frame: GifSettingsFrame
    ) -> None: 

        self._gif_settings: GifSettings = gif_settings
        self._settings_frame: GifSettingsFrame = settings_frame

        self._bind_view()
    
    def on_resolution_change(self, value: str) -> None:
        self._gif_settings.resolution = value
    
    def on_frame_rate_change(self, value: str) -> None:
        self._gif_settings.fps = value
    
    def on_loop_change(self, value: str) -> None:
        if value == "Infinite":
            loop_num = 0
        elif value == "1x":
            loop_num = -1
        elif value == "2x":
            loop_num = 1
        elif value == "5x":
            loop_num = 4
        elif value == "10x":
            loop_num = 9
        else:
            return

        self._gif_settings.loop = loop_num
    
    def on_create(self) -> None:
        pass
    
    def _bind_view(self) -> None:
        self._settings_frame.on_resolution_change = self.on_resolution_change
        self._settings_frame.on_frame_rate_change = self.on_frame_rate_change
        self._settings_frame.on_loop_change = on_loop_change

        self._settings_frame.on_create = self.on_create