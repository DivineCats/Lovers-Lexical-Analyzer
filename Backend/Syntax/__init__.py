# Backend/Syntax/__init__.py
"""Syntax analysis module for the Lovers language."""

from Backend.Syntax.Parser import (
    Parser,
    parse,
    parse_with_errors,
    get_parser,
)
from Backend.Syntax.RecursiveDescentParser import (
    RecursiveDescentParser,
    parse_from_source,
    parse_with_errors_rd,
)
from Backend.Syntax.SimpleRecursiveDescentParser import (
    SimpleRecursiveDescentParser,
    parse_with_errors_simple_rd,
    get_simple_parser,
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
    "get_parser",
    # Recursive Descent Parser
    "RecursiveDescentParser",
    "parse_from_source",
    "parse_with_errors_rd",
    # Simple Recursive Descent Parser
    "SimpleRecursiveDescentParser",
    "parse_with_errors_simple_rd",
    "get_simple_parser",
    # Errors
    "SyntaxError",
    "format_syntax_error",
    "create_error_context",
]
