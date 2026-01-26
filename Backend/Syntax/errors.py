# Backend/Syntax/errors.py
"""Syntax error handling for the Lovers language parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Tuple

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
        raw_message: Optional original error message from parser.
        keywords: Optional list of expected keywords.
        literals: Optional list of expected literals.
        symbols: Optional list of expected symbols.
        others: Optional list of other expected tokens.
        is_end_of_input: Optional flag indicating end-of-input error.
    """
    message: str
    line: int
    column: int
    expected: List[str]
    found: str
    raw_message: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    literals: List[str] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    others: List[str] = field(default_factory=list)
    is_end_of_input: bool = False

    def __str__(self) -> str:
        """Return a formatted error message."""
        return format_syntax_error(self)
    

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Rename is_end_of_input to isEndOfInput for frontend compatibility
        if 'is_end_of_input' in result:
            result['isEndOfInput'] = result.pop('is_end_of_input')
        return result


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


def analyze_open_brackets(fragment: str) -> List[str]:
    """
    Analyze which brackets are currently open in the code fragment.
    
    Uses a stack to track opening brackets and matches closing brackets.
    
    Args:
        fragment: Code fragment up to the error position.
        
    Returns:
        List of currently open brackets in order (most recent last).
    """
    stack = []
    bracket_pairs = {'(': ')', '[': ']', '{': '}'}
    
    for ch in fragment:
        if ch in bracket_pairs:  # Opening bracket
            stack.append(ch)
        elif ch in bracket_pairs.values():  # Closing bracket
            # Find matching opening bracket
            for opening, closing in bracket_pairs.items():
                if ch == closing:
                    # If we have a matching open bracket, pop it
                    if stack and stack[-1] == opening:
                        stack.pop()
                    break
    
    # Return list of currently open brackets
    return stack


def categorize_tokens(tokens: List[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Categorize tokens into keywords, literals, symbols, and others.
    
    Args:
        tokens: List of token names (already converted to readable format).
        
    Returns:
        Tuple of (keywords, literals, symbols, others) lists.
    """
    # Lovers language keywords
    KEYWORDS = {
        "love", "boundaries", "const", "avoidant", "comeback",
        "dear", "dearest", "rant", "status", "forever", "forevermore",
        "more", "choose", "phase", "bareminimum", "for", "while",
        "pursue", "breakup", "give", "express", "overshare", "periodt",
        "greenflag", "redflag", "moveon"
    }
    
    # Literal types
    LITERALS = {
        "integer literal", "float literal", "string literal",
        "INT_LIT", "FLOAT_LIT", "STRING_LIT", "DEAR_LIT", 
        "DEAREST_LIT", "RANT_LIT", "BOOL_LIT"
    }
    
    keywords_cat = []
    literals_cat = []
    symbols_cat = []
    others_cat = []
    
    for token in tokens:
        token_str = str(token).strip().lower()
        token_original = str(token).strip()
        
        # Check if it's a keyword (case-insensitive)
        if token_str in KEYWORDS:
            keywords_cat.append(token_str)
        # Check if it's a literal
        elif token_str in LITERALS or "literal" in token_str.lower():
            literals_cat.append(token_original)
        # Check if it's a symbol (non-alphanumeric, single or multi-char)
        elif re.match(r'^[^\w\s]+$', token_original):
            symbols_cat.append(token_original)
        # Check if it's "identifier" or similar
        elif token_str in ["identifier", "id"]:
            others_cat.append("identifier")
        else:
            others_cat.append(token_original)
    
    return keywords_cat, literals_cat, symbols_cat, others_cat


def filter_expected_by_bracket_context(
    expected: List[str], 
    open_brackets: List[str]
) -> List[str]:
    """
    Filter expected tokens based on bracket context.
    
    Only shows closing brackets that match currently open brackets.
    This prevents suggesting '}' when only '(' is open.
    
    Args:
        expected: List of expected tokens.
        open_brackets: List of currently open brackets.
        
    Returns:
        Filtered list of expected tokens.
    """
    bracket_pairs = {'(': ')', '[': ']', '{': '}'}
    reverse_pairs = {')': '(', ']': '[', '}': '{'}
    
    # Determine which closing brackets are valid
    valid_closers = set()
    if open_brackets:
        # Only the most recently opened bracket can be closed next
        valid_closers.add(bracket_pairs[open_brackets[-1]])
    
    filtered = []
    for token in expected:
        token_clean = str(token).strip("'\"")
        
        # If token is a closing bracket
        if token_clean in bracket_pairs.values():
            if token_clean in valid_closers:
                filtered.append(token)
        else:
            # For all other tokens (including opening brackets), keep them
            filtered.append(token)
    
    return filtered


def process_syntax_error_enhanced(
    error_msg: str,
    line: int,
    column: int,
    expected_tokens: List[str],
    unexpected_token: Optional[str] = None,
    code: str = ""
) -> dict:
    """
    Process a syntax error with enhanced analysis (bracket balancing, token categorization).
    
    This function provides the same enhanced error processing as the friend's code,
    adapted for our SyntaxError structure.
    
    Args:
        error_msg: Original error message from parser.
        line: Line number of error (1-indexed).
        column: Column number of error (1-indexed).
        expected_tokens: List of expected token names.
        unexpected_token: The unexpected token that caused the error.
        code: Full source code for context analysis.
        
    Returns:
        Dictionary with enhanced error information.
    """
    if expected_tokens is None:
        expected_tokens = []
    
    # Extract the fragment of the code up to the error column
    lines = code.splitlines() if code else []
    if 0 < line <= len(lines):
        # Include all previous lines and the current line up to the error column
        preceding_lines = "\n".join(lines[:line-1])
        current_fragment = lines[line - 1][:column] if column > 0 else ""
        line_fragment = preceding_lines + "\n" + current_fragment if preceding_lines else current_fragment
    else:
        line_fragment = code[:column] if code and column > 0 else ""
    
    # Analyze which brackets are currently open
    open_brackets = analyze_open_brackets(line_fragment)
    
    # Check for end of input
    is_end_of_input = False
    mapped_unexpected = "None"
    token_value = None
    
    if unexpected_token is not None:
        # Handle token object or string
        if hasattr(unexpected_token, 'type'):
            token_type = unexpected_token.type
            token_value = getattr(unexpected_token, 'value', None)
            mapped_unexpected = TOKEN_DISPLAY_NAME.get(token_type, str(token_value) if token_value else token_type)
            
            # Check if token is end of input/EOF
            if token_type in ['$END', '$EOF'] or mapped_unexpected == "end of input":
                is_end_of_input = True
        else:
            token_value = str(unexpected_token)
            mapped_unexpected = TOKEN_DISPLAY_NAME.get(token_value, token_value)
            
            # Check if token is end of input/EOF
            if token_value in ['$END', '$EOF'] or mapped_unexpected == "end of input":
                is_end_of_input = True
    
    # Map expected tokens using TOKEN_DISPLAY_NAME
    mapped_expected = []
    for token in expected_tokens:
        if token in TOKEN_DISPLAY_NAME:
            mapped_expected.append(TOKEN_DISPLAY_NAME[token])
        else:
            mapped_expected.append(token)
    
    # Convert to readable format
    readable_expected = convert_tokens_to_readable(mapped_expected)
    
    # Check for bracket-related errors
    bracket_pairs = {'(': ')', '[': ']', '{': '}'}
    all_brackets = set(bracket_pairs.keys()) | set(bracket_pairs.values())
    
    # Determine if this is a bracket-related error
    unexpected_grammar_error = False
    if mapped_unexpected in all_brackets:
        unexpected_grammar_error = True
        final_message = f"Syntax error at line {line}, column {column}: unexpected '{mapped_unexpected}'"
    elif is_end_of_input:
        unexpected_grammar_error = True
        final_message = f"Syntax error at line {line}, column {column}: unexpected end of input"
    elif open_brackets:
        # There are unclosed brackets - determine which one needs to be closed first
        last_open = open_brackets[-1]
        needed_closer = bracket_pairs[last_open]
        final_message = f"Syntax error at line {line}, column {column}: missing '{needed_closer}'"
        unexpected_grammar_error = True
    else:
        # Standard syntax error
        final_message = f"Syntax error at line {line}, column {column}"
    
    # Filter expected tokens based on bracket context
    filtered_expected = filter_expected_by_bracket_context(readable_expected, open_brackets)
    
    # Categorize the filtered tokens
    keywords_cat, literals_cat, symbols_cat, others_cat = categorize_tokens(filtered_expected)
    
    return {
        "message": final_message,
        "rawMessage": error_msg,
        "expected": filtered_expected,
        "unexpected": mapped_unexpected,
        "line": line,
        "column": column,
        "value": str(token_value) if token_value else "",
        "type": "syntax",
        "keywords": keywords_cat,
        "literals": literals_cat,
        "symbols": symbols_cat,
        "others": others_cat,
        "isEndOfInput": is_end_of_input
    }
