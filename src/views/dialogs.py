from os import path
from typing import Any

from CTkMessagebox import CTkMessagebox

from widgets.messagebox_popup import MessageboxPopup

from utils.resource_paths import resource_path


def show_error(master: Any, title: str, message: str) -> None:
    """Show a blocking error dialog."""
    CTkMessagebox(master=master, title=title, message=message, icon="cancel")


def show_warning(master: Any, title: str, message: str) -> None:
    """Show a blocking warning dialog."""
    CTkMessagebox(master=master, title=title, message=message, icon="warning")


def show_info(master: Any, title: str, message: str) -> None:
    """Show a blocking informational dialog."""
    CTkMessagebox(master=master, title=title, message=message, icon="info")


def show_success(master: Any, title: str, message: str) -> None:
    """Show a blocking success dialog."""
    CTkMessagebox(master=master, title=title, message=message, icon="check")


def _show_text_file(master: Any, title: str, relative_path: str) -> None:
    """Read a bundled text file and display it in a scrollable popup."""
    path = resource_path(relative_path)
    with open(path, "r") as f:
        text = f.read()

    popup = MessageboxPopup(master=master, title=title, message=text)
    popup.resizable(True, True)
    popup.transient(master)


def show_about(master: Any) -> None:
    """Show the About popup with app info and license information."""
    _show_text_file(
        master=master, title="About", relative_path=path.join("assets", "about.txt")
    )


def show_license(master: Any) -> None:
    """Show the app's GPLv3.0 license."""
    _show_text_file(
        master=master,
        title="GPLv3.0 License",
        relative_path=path.join("assets", "licenses", "LICENSE.GPL-3.0.txt"),
    )


def show_third_party_licenses(master: Any) -> None:
    """Show the third-party library licenses."""
    _show_text_file(
        master=master,
        title="Third Party Libraries Licenses",
        relative_path=path.join("assets", "licenses", "thirdpartylicenses.txt"),
    )
