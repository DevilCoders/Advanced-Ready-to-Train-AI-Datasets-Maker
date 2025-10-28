"""Utilities for producing standalone executables via PyInstaller."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable

try:  # pragma: no cover - optional dependency
    import PyInstaller.__main__ as _pyinstaller_main  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    _pyinstaller_main = None

PACKAGE_ROOT = Path(__file__).resolve().parent
ENTRYPOINTS = {
    "cli": PACKAGE_ROOT / "_pyinstaller_cli.py",
    "gui": PACKAGE_ROOT / "_pyinstaller_gui.py",
}


def build_executable(flavour: str, dist_dir: Path, clean: bool = False, onefile: bool = True) -> None:
    """Invoke PyInstaller to produce an executable for the requested flavour."""

    if _pyinstaller_main is None:
        raise RuntimeError(
            "PyInstaller is required to build executables. Install the optional "
            "'build' extras with `pip install art-dataset-maker[build]`."
        )

    entrypoint = ENTRYPOINTS[flavour]
    if not entrypoint.exists():  # pragma: no cover - safety check
        raise FileNotFoundError(entrypoint)

    dist_dir.mkdir(parents=True, exist_ok=True)

    args: list[str] = [
        str(entrypoint),
        "--name",
        "art-dataset-maker" if flavour == "cli" else "art-dataset-maker-gui",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(dist_dir / "build"),
        "--specpath",
        str(dist_dir / "spec"),
        "--console" if flavour == "cli" else "--windowed",
    ]

    if onefile:
        args.append("--onefile")
    if clean:
        args.append("--clean")

    _pyinstaller_main.run(args)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build standalone executables for the project")
    parser.add_argument(
        "flavour",
        choices=sorted(ENTRYPOINTS.keys()),
        help="Which launcher to package (CLI or GUI)",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Output directory for the generated executable",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previous build artefacts before packaging",
    )
    parser.add_argument(
        "--no-onefile",
        dest="onefile",
        action="store_false",
        help="Generate a directory-based build instead of a single binary",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    if args.clean:
        shutil.rmtree(args.dist_dir / "build", ignore_errors=True)
        shutil.rmtree(args.dist_dir / "spec", ignore_errors=True)

    build_executable(args.flavour, args.dist_dir, clean=args.clean, onefile=args.onefile)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
