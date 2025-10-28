"""Helper entrypoint for building the GUI executable with PyInstaller."""

from art_dataset_maker.gui import launch


if __name__ == "__main__":
    raise SystemExit(launch())
