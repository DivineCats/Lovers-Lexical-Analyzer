"""Lovers pipeline: frontend analysis + TAC VM execution."""

from .interpreter import analyze_and_build_program

__all__ = ["InterpretError", "analyze_and_build_program", "run_lovers_source"]


def run_lovers_source(*args, **kwargs):
    from Backend.IR.exec import run_lovers_source as _impl

    return _impl(*args, **kwargs)


def __getattr__(name: str):
    if name == "InterpretError":
        from Backend.IR.vm import VMError

        return VMError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
