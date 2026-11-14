from bootstrapper.initialization import initiaize_app

from app import App


def main() -> None:
    app: App = initiaize_app()
    app.mainloop()


if __name__ == "__main__":
    main()
