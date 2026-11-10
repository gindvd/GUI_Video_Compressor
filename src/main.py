from app import App

from sys import platform

if platform.startswith("win"):
    from ctypes import windll

    try:
        windll.user32.SetProcessDpiAwarenessContext(-4)
    except AttributeError:
        windll.shcore.SetProcessDpiAwareness(2)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
