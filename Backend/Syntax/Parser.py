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

    def parse_with_full_recovery(self, source: str) -> Tuple[Optional[Tree], List[SyntaxError]]:
        """
        Parse source code with error recovery to detect all syntax errors.
        
        Uses Context-Aware Recovery:
        - Tracks brace depth to understand parse context
        - Only skips within current structure (doesn't skip past block boundaries)
        - Prioritizes sync points intelligently (semicolons, matching braces, keywords)
        - Filters cascading errors to remove false positives
        
        This approach minimizes false positives while detecting all real errors.
        
        Args:
            source: The source code to parse.
            
        Returns:
            A tuple of (tree, errors) where tree is None if parsing failed completely,
            and errors is a list of all SyntaxError objects found during parsing.
        """
        errors: List[SyntaxError] = []
        max_errors = 100  # Prevent infinite loops
        
        # Track current position in source (character index)
        current_pos = 0
        parsed_successfully = False
        tree = None
        
        # Keywords that can start new statements/declarations
        sync_keywords = [
            'love', 'forever', 'forevermore', 'while', 'for', 'pursue',
            'choose', 'comeback', 'dear', 'dearest', 'rant', 'status',
            'avoidant', 'more', 'give', 'express', 'overshare', 'boundaries'
        ]
        
        while current_pos < len(source) and len(errors) < max_errors:
            # Get remaining source from current position
            remaining_source = source[current_pos:]
            
            if not remaining_source.strip():
                # No more source to parse
                break
            
            # Calculate line offset for error reporting
            # Count how many newlines we've skipped
            line_offset = source[:current_pos].count('\n')
            
            # Try to parse from current position
            try:
                tree = self.parser.parse(remaining_source)
                parsed_successfully = True
                break
                
            except UnexpectedToken as e:
                # Adjust line number to account for skipped lines
                adjusted_line = e.line + line_offset
                
                # Record the error
                token_str = str(e.token)
                expected_raw = list(e.expected) if e.expected else []
                
                # Generate error message
                reserved_msg = self._get_reserved_word_message(token_str, expected_raw)
                if reserved_msg:
                    error_msg = reserved_msg
                else:
                    error_msg = f"Unexpected token '{token_str}'"
                
                # Create enhanced error with full source context
                error = self._create_enhanced_syntax_error(
                    error_msg=error_msg,
                    line=adjusted_line,
                    column=e.column,
                    expected_tokens=expected_raw,
                    unexpected_token=token_str,
                    source=source  # Use full source for bracket analysis
                )
                
                # Add error and use context-aware skipping
                errors.append(error)
                
                # Context-aware sync point detection
                new_pos = self._find_context_aware_sync_point(
                    source, current_pos, adjusted_line, e.column, sync_keywords, errors
                )
                
                # Prevent infinite loops - if we didn't advance, skip at least one character
                if new_pos <= current_pos:
                    new_pos = current_pos + 1
                
                current_pos = new_pos
                
            except UnexpectedCharacters as e:
                # Adjust line number to account for skipped lines
                adjusted_line = e.line + line_offset
                
                # Record the error
                expected_raw = list(e.allowed) if e.allowed else []
                
                errors.append(self._create_enhanced_syntax_error(
                    error_msg=f"Unexpected character '{e.char}'",
                    line=adjusted_line,
                    column=e.column,
                    expected_tokens=expected_raw,
                    unexpected_token=e.char,
                    source=source
                ))
                
                # Use context-aware sync point detection
                new_pos = self._find_context_aware_sync_point(
                    source, current_pos, adjusted_line, e.column, sync_keywords, errors
                )
                
                # Prevent infinite loops
                if new_pos <= current_pos:
                    new_pos = current_pos + 1
                
                current_pos = new_pos
                
            except UnexpectedInput as e:
                # Adjust line number to account for skipped lines
                line = getattr(e, 'line', -1)
                column = getattr(e, 'column', -1)
                adjusted_line = (line if line > 0 else 1) + line_offset
                
                token_info = getattr(e, 'token', None)
                token_str = str(token_info) if token_info else ""
                
                error_msg = f"Unexpected input: {token_str}" if token_str else "Unexpected input"
                errors.append(self._create_enhanced_syntax_error(
                    error_msg=error_msg,
                    line=adjusted_line,
                    column=column if column > 0 else 1,
                    expected_tokens=[],
                    unexpected_token=token_str if token_str else None,
                    source=source
                ))
                
                # Use context-aware sync point detection
                new_pos = self._find_context_aware_sync_point(
                    source, current_pos, adjusted_line, column, sync_keywords, errors
                )
                
                # Prevent infinite loops
                if new_pos <= current_pos:
                    new_pos = current_pos + 1
                
                current_pos = new_pos
                
            except Exception as e:
                # Unexpected error - record and try to continue
                # Use line offset for consistency
                adjusted_line = 1 + line_offset
                errors.append(self._create_enhanced_syntax_error(
                    error_msg=str(e),
                    line=adjusted_line,
                    column=1,
                    expected_tokens=[],
                    unexpected_token=None,
                    source=source
                ))
                # Skip to next line
                current_pos = self._skip_to_next_line_in_source(source, current_pos)
        
        # Filter out cascading errors (errors that are likely artifacts of recovery)
        errors = self._filter_cascading_errors(errors, source)
        
        # Deduplicate errors (same position, same message)
        errors = self._deduplicate_errors(errors)
        
        if parsed_successfully:
            return tree, errors
        else:
            return None, errors

    def _skip_to_next_line_in_source(self, source: str, current_pos: int) -> int:
        """
        Skip to the start of the next line in source.
        
        Args:
            source: Original source code.
            current_pos: Current character position.
            
        Returns:
            Character position of start of next line, or end of source.
        """
        if current_pos >= len(source):
            return len(source)
        
        # Find next newline
        next_newline = source.find('\n', current_pos)
        if next_newline != -1:
            return next_newline + 1
        else:
            # No more newlines - return end
            return len(source)


    def _deduplicate_errors(self, errors: List[SyntaxError]) -> List[SyntaxError]:
        """
        Remove duplicate errors (same line, column, and message).
        
        Args:
            errors: List of syntax errors.
            
        Returns:
            Deduplicated list of errors.
        """
        seen = set()
        unique_errors = []
        
        for error in errors:
            # Create a key from line, column, and message
            key = (error.line, error.column, error.message)
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)
        
        return unique_errors

    def _filter_cascading_errors(self, errors: List[SyntaxError], source: str) -> List[SyntaxError]:
        """
        Filter out cascading errors that are likely artifacts of error recovery.
        
        Cascading errors are errors that occur after recovery and are likely false positives,
        such as errors on closing braces when we've already reported the real error.
        
        Args:
            errors: List of syntax errors.
            source: Original source code.
            
        Returns:
            Filtered list of errors with cascading errors removed.
        """
        if len(errors) <= 1:
            return errors
        
        source_lines = source.splitlines()
        filtered = []
        
        for i, error in enumerate(errors):
            # Skip errors that are clearly cascading
            is_cascading = False
            
            # Rule 1: If this is a closing brace/paren/bracket error
            # and there's a previous error within 3 lines, it's likely cascading
            if error.found in ['}', ')', ']']:
                for prev_error in errors[:i]:
                    line_distance = abs(error.line - prev_error.line)
                    # If previous error was on a statement/declaration line
                    # and this error is on a closing brace nearby, it's cascading
                    if line_distance <= 3:
                        # Check if the closing brace is actually on the reported line
                        if error.line <= len(source_lines) and error.line > 0:
                            line_text = source_lines[error.line - 1].strip()
                            # If the line is just a closing brace (or mostly whitespace + brace)
                            # and we had an error nearby, it's likely cascading
                            if line_text == error.found or line_text.endswith(error.found):
                                # But only if there was a real error before it
                                if 'Unexpected token' in prev_error.message or 'Unexpected' in prev_error.message:
                                    is_cascading = True
                                    break
            
            # Rule 2: If two errors are very close together (same line or adjacent)
            # and the second is about structural tokens, it's likely cascading
            if not is_cascading and i > 0:
                prev_error = errors[i - 1]
                line_distance = abs(error.line - prev_error.line)
                
                # Same line errors - second one is likely cascading if it's structural
                if line_distance == 0 and error.found in ['}', ')', ']', ';']:
                    is_cascading = True
                # Adjacent line errors with structural tokens
                elif line_distance == 1 and error.found in ['}', ')', ']']:
                    # If previous error was about an unexpected token in a declaration/statement
                    # and this is a closing brace, it's likely cascading
                    if 'Unexpected token' in prev_error.message:
                        is_cascading = True
            
            # Rule 3: If error is on a closing brace that's far from any code
            # (just whitespace + brace), and we have previous errors, it's likely cascading
            if not is_cascading and error.found == '}':
                if error.line <= len(source_lines) and error.line > 0:
                    line_text = source_lines[error.line - 1].strip()
                    # Line is just a closing brace (or mostly empty)
                    if line_text == '}' or (len(line_text) <= 2 and '}' in line_text):
                        # Check if there are any previous errors
                        if i > 0:
                            # If the previous error was about a declaration/statement issue
                            # this closing brace error is likely cascading
                            prev_error = errors[i - 1]
                            if 'Unexpected token' in prev_error.message:
                                is_cascading = True
            
            if not is_cascading:
                filtered.append(error)
        
        return filtered


    def _find_context_aware_sync_point(
        self,
        source: str,
        current_pos: int,
        error_line: int,
        error_col: int,
        sync_keywords: List[str],
        existing_errors: List[SyntaxError]
    ) -> int:
        """
        Find synchronization point with context awareness.
        
        Tracks what structure we're in (function, block, etc.) and only
        skips within that structure, not past boundaries.
        
        Args:
            source: Original source code.
            current_pos: Current position in source.
            error_line: Line number of error.
            error_col: Column number of error.
            sync_keywords: List of keywords that can start new statements.
            existing_errors: List of errors found so far.
            
        Returns:
            Character position of next sync point.
        """
        # Calculate brace depth to understand context
        source_before_error = source[:current_pos]
        open_braces = source_before_error.count('{')
        close_braces = source_before_error.count('}')
        brace_depth = open_braces - close_braces
        
        # Get source from error position
        source_from_error = source[current_pos:]
        
        # Look for sync points, but respect brace depth
        import re
        
        # Priority 1: Semicolon (statement end)
        semicolon_match = re.search(r'[;]', source_from_error)
        if semicolon_match:
            return current_pos + semicolon_match.end()
        
        # Priority 2: Closing brace at same depth (end of current block)
        if brace_depth > 0:
            # Count braces to find matching closing brace
            depth = brace_depth
            pos = 0
            for i, char in enumerate(source_from_error):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == brace_depth - 1:
                        # Found matching closing brace
                        return current_pos + i + 1
                pos = i
        
        # Priority 3: Keywords (new statement/declaration)
        for keyword in sync_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            keyword_match = re.search(pattern, source_from_error, re.IGNORECASE)
            if keyword_match:
                return current_pos + keyword_match.start()
        
        # Priority 4: Opening brace (new block)
        open_brace_match = re.search(r'[{]', source_from_error)
        if open_brace_match:
            return current_pos + open_brace_match.start()
        
        # Fallback: Skip to next line
        return self._skip_to_next_line_in_source(source, current_pos)


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


def parse_with_full_recovery(source: str) -> Tuple[Optional[Tree], List[SyntaxError]]:
    """Parse source code with full error recovery to detect all errors."""
    return get_parser().parse_with_full_recovery(source)
