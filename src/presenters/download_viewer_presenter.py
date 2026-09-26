from os import path

from controllers.ffmpeg_controller import FFmpegController

from views.downloader_viewer import DownloadViewer

class DownloadViewerPresenter():

    def __init__(
        self,
        download_viewer: DownloadViewer,
        ffmpeg_controller:FFmpegController
    ) -> None:
        
        self._download_view = download_viewer
        self._ffmpeg_controller = ffmpeg_controller

        self._bind()
    
    def on_url_entry(self, url: str) -> None:
        pass

    def on_download(self, url: str) -> None:
        from tkinter import filedialog

        output_directory: str = filedialog.askdirectory(
            parent=self._download_view,
            title="Folder Output Selection",
            initialdir=path.expanduser("~"),
        )

        if output_directory == "":
            return
        
        ext = self._download_view.container

        self._ffmpeg_controller.download_video(
            url=url,
            ext=ext,
            output_folder=output_directory
        )

    def _bind(self) -> None:
        self._download_view.on_url_entry = self.on_url_entry
        self._download_view.on_download = self.on_download