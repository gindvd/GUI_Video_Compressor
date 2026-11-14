from os import path 


def check_file(abs_path: str) -> None:
    if not path.isfile(abs_path):
        raise SystemExit(f"Missing dependency: {abs_path}")


def check_path(abs_path: str) -> None:
    if not path.exists(abs_path):
        raise SystemExit(f"Missing dependency: {abs_path}")