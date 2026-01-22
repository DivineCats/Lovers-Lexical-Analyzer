# Backend/Syntax/errors.py
"""Syntax error handling for the Lovers language parser."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class SyntaxError(Exception):
    """
    Represents a syntax error found during parsing.
    
    Attributes:
        message: Human-readable description of the error.
        line: Line number where the error occurred (1-indexed).
        column: Column number where the error occurred (1-indexed).
        expected: List of expected tokens/rules at this position.
        found: The actual token/character that was found.
    """
    message: str
    line: int
    column: int
    expected: List[str]
    found: str

    def __str__(self) -> str:
        """Return a formatted error message."""
        return format_syntax_error(self)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def format_syntax_error(error: SyntaxError) -> str:
    """
    Format a syntax error into a human-readable string.
    
    Args:
        error: The SyntaxError to format.
        
    Returns:
        A formatted error string.
    """
    lines = [f"Syntax error at line {error.line}, column {error.column}"]
    lines.append(f"  {error.message}")
    
    if error.found:
        lines.append(f"  Found: {error.found}")
    
    if error.expected:
        # Format expected tokens nicely
        expected_formatted = format_expected_tokens(error.expected)
        lines.append(f"  Expected: {expected_formatted}")
    
    return "\n".join(lines)


def format_expected_tokens(expected: List[str]) -> str:
    """
    Format a list of expected tokens into a readable string.
    
    Args:
        expected: List of expected token names.
        
    Returns:
        A formatted string of expected tokens.
    """
    if not expected:
        return "unknown"
    
    # Map internal token names to human-readable names
    token_names = {
        # Keywords
        "LOVE": "'love'",
        "BOUNDARIES": "'boundaries'",
        "CONST": "'const'",
        "AVOIDANT": "'avoidant'",
        "COMEBACK": "'comeback'",
        "DEAR": "'dear'",
        "DEAREST": "'dearest'",
        "RANT": "'rant'",
        "STATUS": "'status'",
        "FOREVER": "'forever'",
        "FOREVERMORE": "'forevermore'",
        "MORE": "'more'",
        "CHOOSE": "'choose'",
        "PHASE": "'phase'",
        "BAREMINIMUM": "'bareminimum'",
        "FOR": "'for'",
        "WHILE": "'while'",
        "PURSUE": "'pursue'",
        "BREAKUP": "'breakup'",
        "GIVE": "'give'",
        "EXPRESS": "'express'",
        "OVERSHARE": "'overshare'",
        "PERIODT": "'periodt'",
        "GREENFLAG": "'greenflag'",
        "REDFLAG": "'redflag'",
        
        # Operators
        "ASSIGN": "'='",
        "PLUS_ASSIGN": "'+='",
        "MINUS_ASSIGN": "'-='",
        "MUL_ASSIGN": "'*='",
        "DIV_ASSIGN": "'/='",
        "MOD_ASSIGN": "'%='",
        "INC": "'++'",
        "DEC": "'--'",
        "EQ": "'=='",
        "NEQ": "'!='",
        "LT": "'<'",
        "LTE": "'<='",
        "GT": "'>'",
        "GTE": "'>='",
        "AND": "'&&'",
        "OR": "'||'",
        "PLUS": "'+'",
        "MINUS": "'-'",
        "STAR": "'*'",
        "SLASH": "'/'",
        "PERCENT": "'%'",
        
        # Symbols
        "SEMICOLON": "';'",
        "COMMA": "','",
        "LPAREN": "'('",
        "RPAREN": "')'",
        "LBRACE": "'{'",
        "RBRACE": "'}'",
        "LBRACKET": "'['",
        "RBRACKET": "']'",
        "COLON": "':'",
        "DOT": "'.'",
        "SCOPE": "'::'",
        "LSHIFT": "'<<'",
        "RSHIFT": "'>>'",
        
        # Literals
        "IDENTIFIER": "identifier",
        "INT_LITERAL": "integer literal",
        "FLOAT_LITERAL": "float literal",
        "STRING_LITERAL": "string literal",
    }
    
    # Convert tokens to readable names
    readable = []
    for token in expected:
        if token in token_names:
            readable.append(token_names[token])
        elif token.startswith("__"):
            # Skip internal rules
            continue
        else:
            readable.append(token)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for item in readable:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    
    if len(unique) == 0:
        return "unknown"
    elif len(unique) == 1:
        return unique[0]
    elif len(unique) == 2:
        return f"{unique[0]} or {unique[1]}"
    else:
        return ", ".join(unique[:-1]) + f", or {unique[-1]}"


def create_error_context(source: str, line: int, column: int, context_lines: int = 2) -> str:
    """
    Create a code snippet showing the error location with context.
    
    Args:
        source: The full source code.
        line: The error line number (1-indexed).
        column: The error column number (1-indexed).
        context_lines: Number of lines to show before and after the error.
        
    Returns:
        A formatted string showing the error location in context.
    """
    lines = source.splitlines()
    
    # Calculate the range of lines to show
    start_line = max(0, line - 1 - context_lines)
    end_line = min(len(lines), line + context_lines)
    
    result = []
    
    for i in range(start_line, end_line):
        line_num = i + 1
        prefix = ">>> " if line_num == line else "    "
        result.append(f"{prefix}{line_num:4d} | {lines[i]}")
        
        # Add caret pointing to the error column
        if line_num == line:
            caret_line = "    " + " " * 4 + " | " + " " * (column - 1) + "^"
            result.append(caret_line)
    
    return "\n".join(result)
