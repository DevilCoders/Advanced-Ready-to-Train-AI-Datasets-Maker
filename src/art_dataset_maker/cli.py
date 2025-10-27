"""Command line interface for the dataset maker."""
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Optional
import sys

from .config import PipelineConfig, discover_config
from .pipeline import build_pipeline


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Build release ready code datasets from massive repositories")
    parser.add_argument("root", type=Path, nargs="?", help="Path to the root of the source repository")
    parser.add_argument("output", type=Path, nargs="?", help="Directory where the dataset will be stored")
    parser.add_argument("--config", type=Path, help="Optional path to a JSON/YAML configuration file")
    parser.add_argument(
        "--discover-config",
        action="store_true",
        help="Discover configuration files in the root directory (dataset.yml or dataset.json)",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Optional workspace directory for remote checkouts when scraping additional sources",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the advanced GUI tool for configuring large scale scraping",
    )
    return parser


def load_pipeline_config(args) -> PipelineConfig:
    if args.config:
        config_path = args.config
    elif args.discover_config and args.root:
        config_path = discover_config(
            [args.root / "dataset.yaml", args.root / "dataset.yml", args.root / "dataset.json"]
        )
    else:
        config_path = None

    if config_path:
        config = PipelineConfig.load(config_path)
    else:
        if not args.root or not args.output:
            raise SystemExit("root and output paths are required unless launching the GUI")
        config = PipelineConfig(root=args.root, output_dir=args.output)
    if args.root:
        config.root = args.root.resolve()
    if args.output:
        config.output_dir = args.output.resolve()
    if args.workspace:
        config.workspace = args.workspace.resolve()
    return config


def launch_gui(preload_config: Optional[Path] = None, workspace: Optional[Path] = None) -> None:
    from .gui import DatasetMakerGUI

    app = DatasetMakerGUI(preload_config=preload_config, workspace=workspace)
    app.mainloop()


def main(argv: Optional[list[str]] = None) -> None:
    argv = list(argv or sys.argv[1:])
    if argv and argv[0] == "gui":
        gui_parser = ArgumentParser(description="Launch the advanced dataset GUI")
        gui_parser.add_argument("--config", type=Path, help="Optional configuration file to pre-load")
        gui_parser.add_argument(
            "--workspace",
            type=Path,
            help="Workspace directory for materialising gigantic remote sources",
        )
        args = gui_parser.parse_args(argv[1:])
        launch_gui(preload_config=args.config, workspace=args.workspace)
        return

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui:
        launch_gui(preload_config=args.config, workspace=args.workspace)
        return

    config = load_pipeline_config(args)
    stats = build_pipeline(config)
    print(stats.format_summary())


if __name__ == "__main__":
    main()
