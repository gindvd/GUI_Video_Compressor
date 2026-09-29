from os import path

from controllers.ffmpeg_controller import FFmpegController

from views.downloader_view import DownloaderView


class DownloaderPresenter():

    def __init__(
        self,
        downloader_view: DownloaderView,
        ffmpeg_controller:FFmpegController
    ) -> None:
        
        self._downloader_view = downloader_view
        self._ffmpeg_controller = ffmpeg_controller

        self._download_filename: str | None = None

        self._bind()
    
    def on_url_entry(self, url: str) -> None:
        if url == "":
            self._download_filename = None

            self._disable_download(msg="")
            return

        netloc = "www.youtube.com"
        path = "/watch"
        status_code = 200

        from urllib.parse import urlparse

        try:
            parsed_url = urlparse(url)
        except ValueError:
            self._disable_download(msg="Invalid URL!")
            return

        if parsed_url.netloc != netloc:
            self._disable_download(msg="Invalid YouTube Link!")

            return
        
        if parsed_url.path != path:
            self._disable_download(msg="Invalid YouTube Video!")

            return
        
        from urllib.request import urlopen

        return_code = urlopen(url).getcode()
        
        if return_code != status_code:
            self._disable_download(msg="Webpage Unreachable!")

            return
        
        created = self._create_filename(url)

        if not created:
            self._disable_download(msg="YouTube Video not Found!")

            return
        
        self._downloader_view.error_message = ""
        self._downloader_view.download_btn_state = "normal"

    def on_download(self, url: str) -> None:
        if self._downloader_view.download_btn_state == "disabled":
            return
        
        if self._download_filename is None:
            return
        
        from tkinter import filedialog

        output_directory: str | tuple = filedialog.askdirectory(
            parent=self._downloader_view,
            title="Folder Output Selection",
            initialdir=path.expanduser("~"),
        )

        if output_directory == "" or output_directory==():
            return

        if isinstance(output_directory, tuple):
            return
        
        ext = self._downloader_view.container

        basename =  self._download_filename + "." +  ext

        output_file: str = path.join(output_directory, basename)

        self._ffmpeg_controller.download_video(
            url=url,
            ext=ext,
            output_file=output_file
        )

    def _create_filename(self, url: str) -> bool:
        not_found = "This video isn't available anymore"
        no_title = 'Title not found'

        import requests
        from bs4 import BeautifulSoup
        
        try:
            response = requests.get(url)
        except Exception:
            return False
        
        html_content = response.text

        # Processing the HTML Code with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extracting <title> tag's content
        title_tag = soup.find('meta', property='og:title')
        video_title = str(title_tag['content']) if title_tag else no_title

        if video_title in [not_found, no_title]:
            return False
        
        self._download_filename = video_title

        return True

    def _disable_download(self, msg: str) -> None:
        self._downloader_view.error_message = msg
        self._downloader_view.download_btn_state = "disabled"

    def _bind(self) -> None:
        self._downloader_view.on_url_entry = self.on_url_entry
        self._downloader_view.on_download = self.on_download
