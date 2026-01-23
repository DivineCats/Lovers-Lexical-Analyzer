# Backend/Syntax/errors.py
"""Syntax error handling for the Lovers language parser."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional

# Import TOKEN_DISPLAY_NAME for token name conversion
from Backend.Syntax.token_map import TOKEN_DISPLAY_NAME


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
    Format a syntax error into a human-readable string with helpful suggestions.
    
    Args:
        error: The SyntaxError to format.
        
    Returns:
        A formatted error string with context and suggestions.
    """
    lines = []
    
    # Main error message
    lines.append(f"Syntax error at line {error.line}, column {error.column}")
    lines.append("")
    
    # Enhanced error description
    enhanced_message = enhance_error_message(error)
    lines.append(f"  {enhanced_message}")
    lines.append("")
    
    # What was found
    if error.found:
        found_display = format_token_display(error.found)
        lines.append(f"  Found: {found_display}")
    
    # What was expected
    if error.expected:
        # Convert token names to readable symbols first (handles both raw and already-readable tokens)
        readable_tokens = convert_tokens_to_readable(error.expected)
        # Then format them into a string
        expected_formatted = format_expected_tokens_string(readable_tokens)
        lines.append(f"  Expected: {expected_formatted}")
    
    return "\n".join(lines)


def convert_tokens_to_readable(tokens: List[str]) -> List[str]:
    """
    Convert internal token names to human-readable symbols.
    Idempotent: can be called multiple times safely.
    Removes duplicates and normalizes quoted/unquoted tokens.
    
    Args:
        tokens: List of token names from Lark (e.g., ["ASSIGN", "SEMICOLON", "love", "ID", "DEAR_LIT"])
               or already-readable tokens (e.g., ["'='", "';'", "love", "identifier"])
        
    Returns:
        List of readable symbols (e.g., ["'='", "';'", "love", "identifier", "integer literal"])
    """
    # Mapping for new grammar terminals to readable names
    terminal_to_readable = {
        "ID": "identifier",
        "DEAR_LIT": "integer literal",
        "DEAREST_LIT": "float literal",
        "RANT_LIT": "string literal",
    }
    
    result = []
    seen_normalized = set()  # Track normalized tokens to avoid duplicates
    
    for token in tokens:
        # Skip empty tokens
        if not token or not token.strip():
            continue
            
        converted = None
        
        # If token is already in readable format (starts with quote or is a readable word), use as-is
        if (token.startswith("'") or token.startswith('"') or 
            token in ["identifier", "integer literal", "float literal", "string literal"]):
            converted = token
        # Check if it's a new grammar terminal
        elif token in terminal_to_readable:
            converted = terminal_to_readable[token]
        # If lowercase keyword, it's already readable - return as-is
        elif token.islower() and token in TOKEN_DISPLAY_NAME:
            converted = token
        # Otherwise use TOKEN_DISPLAY_NAME mapping (for operators/delimiters)
        else:
            converted = TOKEN_DISPLAY_NAME.get(token, token)
        
        # Normalize: remove quotes for comparison to avoid duplicates
        # e.g., both "COMMA" -> "," and "," should be treated as the same
        # Also handle cases where we get both quoted and unquoted versions
        if converted.startswith("'") or converted.startswith('"'):
            normalized = converted.strip("'\"")
            # For single-character symbols, prefer unquoted format for cleaner display
            if len(normalized) == 1:
                converted = normalized
        else:
            normalized = converted
        
        # Only add if we haven't seen this normalized token before
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            result.append(converted)
    
    return result


def format_token_display(token: str) -> str:
    """Format a token for display in error messages."""
    # Remove quotes if present
    token = token.strip("'\"")
    
    # Map common tokens to readable names (including new grammar terminals)
    token_display_map = {
        "INT_LIT": "integer literal",
        "FLOAT_LIT": "float literal", 
        "STRING_LIT": "string literal",
        "IDENTIFIER": "identifier",
        # New grammar terminals
        "ID": "identifier",
        "DEAR_LIT": "integer literal",
        "DEAREST_LIT": "float literal",
        "RANT_LIT": "string literal",
    }
    
    if token in token_display_map:
        return token_display_map[token]
    return f"'{token}'"


def enhance_error_message(error: SyntaxError) -> str:
    """
    Enhance error message with contextual information and helpful hints.
    
    Args:
        error: The SyntaxError to enhance.
        
    Returns:
        An enhanced error message string.
    """
    found = error.found.strip("'\"") if error.found else ""
    expected = error.expected or []
    
    # Convert expected to readable format for consistent checking
    expected_readable = convert_tokens_to_readable(expected)
    expected_set = set(str(e).lower() for e in expected_readable)
    found_clean = found.strip("'\"") if found else ""
    
    # Missing assignment operator (most common issue)
    if "=" in expected_set and found_clean and found_clean != "=":
        # Check if found is a literal value (number or string)
        is_literal = (
            found_clean.isdigit() or 
            (found_clean.replace(".", "").replace("-", "").isdigit()) or
            "integer literal" in found_clean.lower() or
            "float literal" in found_clean.lower() or
            "string literal" in found_clean.lower() or
            found_clean.startswith('"') or found_clean.startswith("'")
        )
        if is_literal:
            return f"Missing assignment operator '=' before value. Use: variable = {found_clean};"
        return "Missing assignment operator '='. Use: variable = value;"
    
    # Variable declaration patterns
    if any(dt in expected_set for dt in ["dear", "dearest", "rant", "status"]):
        if "=" in expected_set:
            return "Incomplete variable declaration. Expected: type identifier = value"
        return "Incomplete variable declaration. Expected: type identifier"
    
    # Function call patterns
    if "arguments" in " ".join(expected_readable).lower():
        return "Invalid function call syntax. Expected: function_name(arguments)"
    
    # Default message
    if error.message:
        return error.message
    return "Unexpected syntax at this location"


def format_expected_tokens_string(expected: List[str]) -> str:
    """
    Format a list of expected tokens (already converted to readable symbols) into a readable string.
    
    Args:
        expected: List of readable token symbols (e.g., ["'='", "';'", "identifier"]).
        
    Returns:
        A formatted string of expected tokens.
    """
    if not expected:
        return "unknown"
    
    # Remove duplicates while preserving order
    unique = list(dict.fromkeys(expected))
    
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
