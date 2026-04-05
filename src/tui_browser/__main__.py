import sys

from .app import run


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else None
    run(url=url)


if __name__ == "__main__":
    main()
