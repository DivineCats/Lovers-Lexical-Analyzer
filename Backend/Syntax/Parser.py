# Backend/Syntax/Parser.py
"""Syntax analyzer using Lark parser for the Lovers language."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple
from lark import Lark, Tree, UnexpectedInput, UnexpectedToken, UnexpectedCharacters
from Backend.Syntax.errors import SyntaxError, format_syntax_error


class Parser:
    """Lark-based parser for the Lovers programming language."""

    # Reserved words that cannot be used as identifiers
    RESERVED_WORDS = {
        "love", "boundaries", "const", "avoidant", "comeback",
        "dear", "dearest", "rant", "status", "forever", "forevermore",
        "more", "choose", "phase", "bareminimum", "for", "while",
        "pursue", "breakup", "give", "express", "overshare", "periodt",
        "greenflag", "redflag", "moveon"
    }

    def __init__(self):
        """Initialize the parser by loading the grammar file."""
        grammar_path = Path(__file__).parent / "grammar.lark"
        grammar_text = grammar_path.read_text(encoding="utf-8")
        
        self.parser = Lark(
            grammar_text,
            start='start',
            parser='earley',
            ambiguity='resolve',  # Resolve ambiguity - prefer keywords over identifiers
            propagate_positions=True,  # Enables line/column tracking in tree nodes
        )
    
    def _is_reserved_word(self, token_str: str) -> bool:
        """Check if a token value is a reserved word."""
        # Extract the actual value from token string (e.g., "Token('LOVE', 'love')" -> "love")
        token_lower = token_str.lower().strip()
        # Direct match
        if token_lower in self.RESERVED_WORDS:
            return True
        # Check if token contains a reserved word
        for word in self.RESERVED_WORDS:
            if word in token_lower:
                return True
        return False
    
    def _get_reserved_word_message(self, token: str, expected: list) -> str:
        """Generate helpful message when reserved word is used incorrectly."""
        # Extract the actual word from token
        token_lower = str(token).lower()
        for word in self.RESERVED_WORDS:
            if word in token_lower:
                if "IDENTIFIER" in expected or not expected:
                    return f"Reserved word '{word}' cannot be used as an identifier or variable name"
                else:
                    return f"Reserved word '{word}' cannot be used here"
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
            raise SyntaxError(
                message=f"Unexpected token '{e.token}' at line {e.line}, column {e.column}",
                line=e.line,
                column=e.column,
                expected=list(e.expected) if e.expected else [],
                found=str(e.token),
            ) from e
        except UnexpectedCharacters as e:
            raise SyntaxError(
                message=f"Unexpected character '{e.char}' at line {e.line}, column {e.column}",
                line=e.line,
                column=e.column,
                expected=list(e.allowed) if e.allowed else [],
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
            expected_list = list(e.expected) if e.expected else []
            
            # Check if a reserved word was used incorrectly
            reserved_msg = self._get_reserved_word_message(token_str, expected_list)
            if reserved_msg:
                message = reserved_msg
            else:
                message = f"Unexpected token '{e.token}'"
            
            errors.append(SyntaxError(
                message=message,
                line=e.line,
                column=e.column,
                expected=expected_list,
                found=token_str,
            ))
        except UnexpectedCharacters as e:
            expected_list = list(e.allowed) if e.allowed else []
            
            # Check if this looks like a reserved word being used as identifier
            # Get the remaining text from this position to check for reserved words
            remaining = source[e.pos_in_stream:] if hasattr(e, 'pos_in_stream') else ""
            word_match = None
            import re
            word_pattern = re.match(r'([a-zA-Z][a-zA-Z0-9_]*)', remaining)
            if word_pattern:
                word = word_pattern.group(1).lower()
                if word in self.RESERVED_WORDS and "IDENTIFIER" in expected_list:
                    errors.append(SyntaxError(
                        message=f"Reserved word '{word}' cannot be used as an identifier or variable name",
                        line=e.line,
                        column=e.column,
                        expected=expected_list,
                        found=word,
                    ))
                    return None, errors
            
            errors.append(SyntaxError(
                message=f"Unexpected character '{e.char}'",
                line=e.line,
                column=e.column,
                expected=expected_list,
                found=e.char,
            ))
        except UnexpectedInput as e:
            # Try to extract more info from the exception
            line = getattr(e, 'line', -1)
            column = getattr(e, 'column', -1)
            
            # Check if there's token info in the exception
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
            # Catch-all for any other parsing errors
            errors.append(SyntaxError(
                message=str(e),
                line=1,
                column=1,
                expected=[],
                found="",
            ))
        
        return None, errors

    def get_tree_string(self, tree: Tree) -> str:
        """
        Get a pretty-printed string representation of the parse tree.
        
        Args:
            tree: The parse tree to format.
            
        Returns:
            A formatted string showing the tree structure.
        """
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
