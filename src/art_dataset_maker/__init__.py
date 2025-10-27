"""Advanced Ready-to-Train dataset maker package."""

from .config import (
    PipelineConfig,
    CodeSourceConfig,
    CommandSourceConfig,
)
from .pipeline import build_pipeline
from .stats import PipelineStats

try:  # pragma: no cover - optional dependency
    from .gui import DatasetMakerGUI  # type: ignore
except Exception:  # pragma: no cover - environments without Tk
    DatasetMakerGUI = None  # type: ignore

__all__ = [
    "PipelineConfig",
    "CodeSourceConfig",
    "CommandSourceConfig",
    "PipelineStats",
    "build_pipeline",
]

if DatasetMakerGUI is not None:  # pragma: no cover - conditional export
    __all__.append("DatasetMakerGUI")
