"""Intermediate representations (e.g. three-address code)."""

from .tac import (
    Quad,
    TacGenError,
    format_tac_human,
    generate_tac_text,
    lovers_source_to_tac,
)

__all__ = [
    "Quad",
    "TacGenError",
    "format_tac_human",
    "generate_tac_text",
    "lovers_source_to_tac",
]


def __getattr__(name: str):
    """Lazy import so `Backend.IR.exec` does not load before `Backend.IR.tac` is ready."""
    if name == "run_lovers_source":
        from .exec import run_lovers_source as rs

        return rs
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
