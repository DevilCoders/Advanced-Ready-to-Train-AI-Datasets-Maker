"""Helper entrypoint for building the CLI executable with PyInstaller."""

from art_dataset_maker.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
