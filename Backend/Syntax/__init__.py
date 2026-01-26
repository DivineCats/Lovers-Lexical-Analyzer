# Backend/Syntax/__init__.py
"""Syntax analysis module for the Lovers language."""

from Backend.Syntax.Parser import (
    Parser,
    parse,
    parse_with_errors,
    parse_with_full_recovery,
    get_parser,
)
from Backend.Syntax.RecursiveDescentParser import (
    RecursiveDescentParser,
    parse_from_source,
    parse_with_errors_rd,
)
from Backend.Syntax.errors import (
    SyntaxError,
    format_syntax_error,
    create_error_context,
)

__all__ = [
    # Parser
    "Parser",
    "parse",
    "parse_with_errors",
    "parse_with_full_recovery",
    "get_parser",
    # Recursive Descent Parser
    "RecursiveDescentParser",
    "parse_from_source",
    "parse_with_errors_rd",
    # Errors
    "SyntaxError",
    "format_syntax_error",
    "create_error_context",
]
