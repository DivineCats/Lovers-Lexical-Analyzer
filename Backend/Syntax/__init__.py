# Backend/Syntax/__init__.py
"""Syntax analysis module for the Lovers language."""

from .parsetv2 import (
    parse_with_errors_parserv2,
)
from .errors import (
    SyntaxError,
    format_syntax_error,
    create_error_context,
)

__all__ = [
    # LL(1) Table-Driven Parser (parserv2)
    "parse_with_errors_parserv2",
    # Errors
    "SyntaxError",
    "format_syntax_error",
    "create_error_context",
]
