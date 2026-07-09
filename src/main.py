from platform import system

# Only available on Windows devices, pass if not found
try:
    from ctypes import windll
except:
    pass

from app import App

from resource_paths import setup_vlc_environment


def main() -> None:
    if system() == "Windows":
        # Set up the VLC dll / plugin paths before the python-vlc library is imported
        setup_vlc_environment()

        # Compatibility with high DPI monitor with windows
        windll.shcore.SetProcessDpiAwareness(2)

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.teardown)
    app.mainloop()


if __name__ == "__main__":
    main()
