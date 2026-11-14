from app import App

from bootstrapper.initialization import initialize_app


def main() -> None:
    app: App = initialize_app()
    app.mainloop()


if __name__ == "__main__":
    main()
