# Backend/Syntax/Parser.py
"""Syntax analyzer using Lark parser with custom Lexer.py for the Lovers language."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple
from lark import Lark, Tree, UnexpectedInput, UnexpectedToken, UnexpectedCharacters
from Backend.Syntax.errors import (
    SyntaxError, 
    format_syntax_error, 
    convert_tokens_to_readable
)
from Backend.Syntax.custom_lexer import CustomLarkLexer
from Backend.Syntax.token_map import TOKEN_DISPLAY_NAME


class Parser:
    """Lark-based parser using custom Lexer.py for the Lovers programming language."""

    # Reserved words that cannot be used as identifiers
    RESERVED_WORDS = {
        "love", "boundaries", "const", "avoidant", "comeback",
        "dear", "dearest", "rant", "status", "forever", "forevermore",
        "more", "choose", "phase", "bareminimum", "for", "while",
        "pursue", "breakup", "give", "express", "overshare", "periodt",
        "greenflag", "redflag", "moveon"
    }

    def __init__(self):
        """Initialize the parser by loading the grammar file with custom lexer."""
        grammar_path = Path(__file__).parent / "grammar.lark"
        grammar_text = grammar_path.read_text(encoding="utf-8")
        
        self.parser = Lark(
            grammar_text,
            start='start',
            parser='earley',
            lexer=CustomLarkLexer,  # Use our custom Lexer.py
            ambiguity='resolve',
            propagate_positions=True,
        )
    
    def _is_reserved_word(self, token_str: str) -> bool:
        """Check if a token value is a reserved word."""
        token_lower = token_str.lower().strip()
        if token_lower in self.RESERVED_WORDS:
            return True
        for word in self.RESERVED_WORDS:
            if word in token_lower:
                return True
        return False
    
    def _get_reserved_word_message(self, token: str, expected: list) -> str:
        """Generate helpful message when reserved word is used incorrectly."""
        token_lower = str(token).lower().strip()
        # Only check for exact matches to avoid false positives
        # (e.g., "love" in "lover" should not trigger an error)
        if token_lower in self.RESERVED_WORDS:
            # Check for ID (new grammar terminal) or IDENTIFIER (old name) or "identifier" (readable format)
            if "ID" in expected or "IDENTIFIER" in expected or "identifier" in expected or not expected:
                return f"Reserved word '{token_lower}' cannot be used as an identifier or variable name"
            else:
                return f"Reserved word '{token_lower}' cannot be used here"
        return None

    def parse(self, source: str) -> Tree:
        """
        Parse source code and return the parse tree.
        
        Args:
            source: The source code to parse.
            
        Returns:
            A Lark Tree representing the parsed program.
            
        Raises:
            SyntaxError: If the source code contains syntax errors.
        """
        try:
            return self.parser.parse(source)
        except UnexpectedToken as e:
            expected_raw = list(e.expected) if e.expected else []
            token_str = str(e.token)
            # Convert expected tokens to readable format
            expected_readable = convert_tokens_to_readable(expected_raw)
            # Create a more helpful message
            message = f"Unexpected token '{token_str}'"
            raise SyntaxError(
                message=message,
                line=e.line,
                column=e.column,
                expected=expected_readable,  # Pass readable tokens for error formatting
                found=token_str,
            ) from e
        except UnexpectedCharacters as e:
            expected_raw = list(e.allowed) if e.allowed else []
            # Convert expected tokens to readable format
            expected_readable = convert_tokens_to_readable(expected_raw)
            raise SyntaxError(
                message=f"Unexpected character '{e.char}' at line {e.line}, column {e.column}",
                line=e.line,
                column=e.column,
                expected=expected_readable,
                found=e.char,
            ) from e
        except UnexpectedInput as e:
            raise SyntaxError(
                message=f"Syntax error at line {e.line}, column {e.column}",
                line=e.line,
                column=e.column,
                expected=[],
                found="",
            ) from e

    def parse_safe(self, source: str) -> Tuple[Optional[Tree], List[SyntaxError]]:
        """
        Parse source code with error collection instead of exceptions.
        
        Args:
            source: The source code to parse.
            
        Returns:
            A tuple of (tree, errors) where tree is None if parsing failed,
            and errors is a list of SyntaxError objects.
        """
        errors: List[SyntaxError] = []
        
        try:
            tree = self.parser.parse(source)
            return tree, errors
        except UnexpectedToken as e:
            token_str = str(e.token)
            expected_raw = list(e.expected) if e.expected else []
            # Convert expected tokens to readable format
            expected_readable = convert_tokens_to_readable(expected_raw)
            
            # Check if a reserved word was used incorrectly
            reserved_msg = self._get_reserved_word_message(token_str, expected_raw)
            if reserved_msg:
                message = reserved_msg
            else:
                message = f"Unexpected token '{e.token}'"
            
            errors.append(SyntaxError(
                message=message,
                line=e.line,
                column=e.column,
                expected=expected_readable,  # Pass readable tokens for error formatting
                found=token_str,
            ))
        except UnexpectedCharacters as e:
            expected_raw = list(e.allowed) if e.allowed else []
            import re
            
            # Check if this looks like a reserved word being used as identifier
            # Only check if we have position information and ID (or IDENTIFIER) is expected
            if hasattr(e, 'pos_in_stream') and ("ID" in expected_raw or "IDENTIFIER" in expected_raw):
                # Get the character at the error position
                if e.pos_in_stream < len(source):
                    # Look for a word starting at the error position
                    remaining = source[e.pos_in_stream:]
                    word_pattern = re.match(r'([a-zA-Z][a-zA-Z0-9_]*)', remaining)
                    if word_pattern:
                        word = word_pattern.group(1).lower()
                        # Only flag if it's an EXACT match with a reserved word (not substring)
                        # This prevents false positives like "love" in "lover"
                        if word in self.RESERVED_WORDS:
                            # Convert expected tokens to readable format
                            expected_readable = convert_tokens_to_readable(expected_raw)
                            errors.append(SyntaxError(
                                message=f"Reserved word '{word}' cannot be used as an identifier or variable name",
                                line=e.line,
                                column=e.column,
                                expected=expected_readable,
                                found=word,
                            ))
                            return None, errors
            
            # Check for incomplete keyword
            if hasattr(e, 'pos_in_stream'):
                before_text = source[:e.pos_in_stream].rstrip()
                ident_match = re.search(r'([a-zA-Z][a-zA-Z0-9_]*)\s*$', before_text)
                if ident_match:
                    incomplete = ident_match.group(1).lower()
                    for keyword in self.RESERVED_WORDS:
                        if keyword.startswith(incomplete) and incomplete != keyword and len(incomplete) >= 2:
                            text_before_ident = before_text[:ident_match.start()]
                            ident_line = text_before_ident.count('\n') + 1
                            last_newline = text_before_ident.rfind('\n')
                            ident_col = len(text_before_ident) - last_newline if last_newline >= 0 else len(text_before_ident) + 1
                            
                            errors.append(SyntaxError(
                                message=f"Incomplete keyword '{incomplete}'. Did you mean '{keyword}'?",
                                line=ident_line,
                                column=ident_col,
                                expected=[keyword],
                                found=incomplete,
                            ))
                            return None, errors
            
            # Convert expected tokens to readable format
            expected_readable = convert_tokens_to_readable(expected_raw)
            errors.append(SyntaxError(
                message=f"Unexpected character '{e.char}'",
                line=e.line,
                column=e.column,
                expected=expected_readable,
                found=e.char,
            ))
        except UnexpectedInput as e:
            line = getattr(e, 'line', -1)
            column = getattr(e, 'column', -1)
            
            token_info = getattr(e, 'token', None)
            if token_info:
                token_str = str(token_info)
                reserved_msg = self._get_reserved_word_message(token_str, [])
                if reserved_msg:
                    errors.append(SyntaxError(
                        message=reserved_msg,
                        line=line if line > 0 else 1,
                        column=column if column > 0 else 1,
                        expected=[],
                        found=token_str,
                    ))
                else:
                    errors.append(SyntaxError(
                        message=f"Unexpected input: {token_str}",
                        line=line if line > 0 else 1,
                        column=column if column > 0 else 1,
                        expected=[],
                        found=token_str,
                    ))
            else:
                errors.append(SyntaxError(
                    message="Unexpected input",
                    line=line if line > 0 else 1,
                    column=column if column > 0 else 1,
                    expected=[],
                    found="",
                ))
        except Exception as e:
            errors.append(SyntaxError(
                message=str(e),
                line=1,
                column=1,
                expected=[],
                found="",
            ))
        
        return None, errors

    def get_tree_string(self, tree: Tree) -> str:
        """Get a pretty-printed string representation of the parse tree."""
        return tree.pretty()


# Module-level convenience functions
_parser_instance: Optional[Parser] = None


def get_parser() -> Parser:
    """Get or create a singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = Parser()
    return _parser_instance


def parse(source: str) -> Tree:
    """Parse source code using the singleton parser."""
    return get_parser().parse(source)


def parse_with_errors(source: str) -> Tuple[Optional[Tree], List[SyntaxError]]:
    """Parse source code with error collection using the singleton parser."""
    return get_parser().parse_safe(source)
