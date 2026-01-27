# Backend/Syntax/Parser.py
"""Syntax analyzer using Lark parser with custom Lexer.py for the Lovers language."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Set
from lark import Lark, Tree, UnexpectedInput, UnexpectedToken, UnexpectedCharacters, Token as LarkToken
from Backend.Syntax.errors import (
    SyntaxError, 
    format_syntax_error, 
    convert_tokens_to_readable,
    process_syntax_error_enhanced
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
    
    def _create_enhanced_syntax_error(
        self,
        error_msg: str,
        line: int,
        column: int,
        expected_tokens: List[str],
        unexpected_token: Optional[str] = None,
        source: str = ""
    ) -> SyntaxError:
        """
        Create a SyntaxError with enhanced analysis (bracket balancing, token categorization).
        
        Args:
            error_msg: Original error message.
            line: Line number (1-indexed).
            column: Column number (1-indexed).
            expected_tokens: List of expected token names.
            unexpected_token: The unexpected token.
            source: Full source code for context.
            
        Returns:
            Enhanced SyntaxError object.
        """
        # Use enhanced error processing
        enhanced = process_syntax_error_enhanced(
            error_msg=error_msg,
            line=line,
            column=column,
            expected_tokens=expected_tokens,
            unexpected_token=unexpected_token,
            code=source
        )
        
        # Create SyntaxError with all enhanced fields
        return SyntaxError(
            message=enhanced["message"],
            line=enhanced["line"],
            column=enhanced["column"],
            expected=enhanced["expected"],
            found=enhanced["unexpected"],
            raw_message=enhanced["rawMessage"],
            keywords=enhanced["keywords"],
            literals=enhanced["literals"],
            symbols=enhanced["symbols"],
            others=enhanced["others"],
            is_end_of_input=enhanced["isEndOfInput"]
        )

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
            error_msg = f"Unexpected token '{token_str}'"
            raise self._create_enhanced_syntax_error(
                error_msg=error_msg,
                line=e.line,
                column=e.column,
                expected_tokens=expected_raw,
                unexpected_token=token_str,
                source=source
            ) from e
        except UnexpectedCharacters as e:
            expected_raw = list(e.allowed) if e.allowed else []
            error_msg = f"Unexpected character '{e.char}' at line {e.line}, column {e.column}"
            raise self._create_enhanced_syntax_error(
                error_msg=error_msg,
                line=e.line,
                column=e.column,
                expected_tokens=expected_raw,
                unexpected_token=e.char,
                source=source
            ) from e
        except UnexpectedInput as e:
            error_msg = f"Syntax error at line {e.line}, column {e.column}"
            raise self._create_enhanced_syntax_error(
                error_msg=error_msg,
                line=e.line,
                column=e.column,
                expected_tokens=[],
                unexpected_token=None,
                source=source
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
            
            # Check if a reserved word was used incorrectly
            reserved_msg = self._get_reserved_word_message(token_str, expected_raw)
            if reserved_msg:
                error_msg = reserved_msg
            else:
                error_msg = f"Unexpected token '{e.token}'"
            
            errors.append(self._create_enhanced_syntax_error(
                error_msg=error_msg,
                line=e.line,
                column=e.column,
                expected_tokens=expected_raw,
                unexpected_token=token_str,
                source=source
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
                            error_msg = f"Reserved word '{word}' cannot be used as an identifier or variable name"
                            errors.append(self._create_enhanced_syntax_error(
                                error_msg=error_msg,
                                line=e.line,
                                column=e.column,
                                expected_tokens=expected_raw,
                                unexpected_token=word,
                                source=source
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
                            
                            error_msg = f"Incomplete keyword '{incomplete}'. Did you mean '{keyword}'?"
                            errors.append(self._create_enhanced_syntax_error(
                                error_msg=error_msg,
                                line=ident_line,
                                column=ident_col,
                                expected_tokens=[keyword],
                                unexpected_token=incomplete,
                                source=source
                            ))
                            return None, errors
            
            error_msg = f"Unexpected character '{e.char}'"
            errors.append(self._create_enhanced_syntax_error(
                error_msg=error_msg,
                line=e.line,
                column=e.column,
                expected_tokens=expected_raw,
                unexpected_token=e.char,
                source=source
            ))
        except UnexpectedInput as e:
            line = getattr(e, 'line', -1)
            column = getattr(e, 'column', -1)
            
            token_info = getattr(e, 'token', None)
            if token_info:
                token_str = str(token_info)
                reserved_msg = self._get_reserved_word_message(token_str, [])
                if reserved_msg:
                    error_msg = reserved_msg
                else:
                    error_msg = f"Unexpected input: {token_str}"
                errors.append(self._create_enhanced_syntax_error(
                    error_msg=error_msg,
                    line=line if line > 0 else 1,
                    column=column if column > 0 else 1,
                    expected_tokens=[],
                    unexpected_token=token_str,
                    source=source
                ))
            else:
                errors.append(self._create_enhanced_syntax_error(
                    error_msg="Unexpected input",
                    line=line if line > 0 else 1,
                    column=column if column > 0 else 1,
                    expected_tokens=[],
                    unexpected_token=None,
                    source=source
                ))
        except Exception as e:
            errors.append(self._create_enhanced_syntax_error(
                error_msg=str(e),
                line=1,
                column=1,
                expected_tokens=[],
                unexpected_token=None,
                source=source
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


