# Backend/Lexical/lexer.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Optional

from Backend.Syntax.DELIMETERS import (
    Literals,
    expanded_reserved_word_follows,
    expanded_identifier_follows,
    expanded_reserved_symbol_follows,
    expanded_int_lit,
    expanded_string_lit,
    TOKEN_DISPLAY_NAME,
    MULTI_CHAR_OPERATORS,
    SINGLE_CHAR_TOKENS,
)

IDENTIFIER_DELIMS = expanded_identifier_follows.get("identifier", set())
NUMBER_DELIMS = expanded_int_lit.get("int_lit", set())
STRING_DELIMS = expanded_string_lit.get("string_lit", set())
ALPHA = Literals["alphabet"]
DIGIT = Literals["digit"]
ALNUM = Literals["alphanum"]
WHITESPACE = {" ", "\t", "\n"}
# Disallow only symbols that should never appear immediately after an identifier.
BAD_SYMBOLS_AFTER_IDENTIFIER = set("!@#$^?~")
IDENT_FOLLOW_CHARS = IDENTIFIER_DELIMS or WHITESPACE
NUMBER_FOLLOW_CHARS = (
    NUMBER_DELIMS
    | WHITESPACE
)
MAX_IDENTIFIER_LEN = 20

@dataclass
class Token:
    kind: str
    lexeme: str
    literal: Optional[str] = None
    line: int = 1
    column: int = 1

    @property
    def token(self) -> str:
        """Get the simplified display token name (Token column - lowercase keyword)."""
        # Token kinds now match grammar terminals directly (id, dear_lit, dearest_lit, rant_lit)
        # If kind is already lowercase (keyword or grammar terminal), return it directly
        if self.kind.islower() and self.kind in TOKEN_DISPLAY_NAME:
            return self.kind
        # Otherwise use TOKEN_DISPLAY_NAME mapping
        return TOKEN_DISPLAY_NAME.get(self.kind, self.kind.lower())

    def to_dict(self) -> dict:
        return asdict(self)

class LexerError(Exception):
    def __init__(self, message: str, tokens: Optional[List["Token"]] = None):
        super().__init__(message)
        self.tokens = tokens or []

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.start = 0
        self.pos = 0
        self.line = 1
        self.column = 1
        self._partial_tokens: List[Token] = []
        self._identifier_continuation: bool = False
        self._number_continuation: bool = False
        self._lexical_errors: List[str] = []

    def _add_lexical_error(self, message: str) -> None:
        self._lexical_errors.append(message)

    def scan_tokens(self) -> List[Token]:
        tokens: List[Token] = []
        self._partial_tokens = tokens
        while not self._is_at_end():
            self.start = self.pos
            start_line, start_col = self.line, self.column
            ch = self._advance()
            self._scan_single_token(ch, tokens, start_line, start_col)

        tokens.append(Token("EOF", "", line=self.line, column=self.column))
        return tokens

    def scan_tokens_collect_errors(self) -> tuple[List[Token], List[str]]:
        tokens: List[Token] = []
        errors: List[str] = []
        self._partial_tokens = tokens   
        while not self._is_at_end():
            self.start = self.pos
            start_line, start_col = self.line, self.column
            ch = self._advance()
            try:
                self._scan_single_token(ch, tokens, start_line, start_col)
            except LexerError as exc:
                errors.append(str(exc))
                self._recover_after_error()
                continue
        # Include lexical errors from chunking/delimiters
        if self._lexical_errors:
            errors.extend(self._lexical_errors)
        tokens.append(Token("EOF", "", line=self.line, column=self.column))
        return tokens, errors

    # --- single token scanner ----------------------------------------------

    def _scan_single_token(self, ch: str, tokens: List[Token], start_line: int, start_col: int) -> None:
        if ch == "\n":
            tokens.append(Token("NEWLINE", "\\n", line=start_line, column=start_col))
            return
        if ch in WHITESPACE:
            return
        if ch == "/" and self._match("*"):
            self._skip_block_comment()
            return
        if ch in {"'", '"'}:
            tokens.append(self._string_token(ch, start_line, start_col))
            return
        # Handle continuation chunks for overlong identifiers
        if self._identifier_continuation:
            if self._is_identifier_part(ch):
                tok = self._identifier_continuation_token(start_line, start_col)
                if tok is not None:
                    tokens.append(tok)
                return
            self._identifier_continuation = False
        # Handle continuation chunks for numbers
        if self._number_continuation:
            if ch.isdigit():
                tok = self._number_continuation_token(start_line, start_col)
                if tok is not None:
                    tokens.append(tok)
                return
            self._number_continuation = False
        if ch == "-" and self._peek().isdigit():
            # Only treat as negative number if NOT preceded by a number, identifier, or )
            # Otherwise it's subtraction: 1-3 => 1, -, 3
            prev_token = tokens[-1] if tokens else None
            is_subtraction = prev_token and prev_token.kind in {
                "dear_lit", "dearest_lit", "id", "RPAREN", "RBRACKET",
                "greenflag", "redflag", "OP_INC", "OP_DEC"
            }
            if not is_subtraction:
                # Negative number literal
                tok = self._number_token(start_line, start_col, allow_negative=True)
                if tok is not None:
                    tokens.append(tok)
                return
            # Otherwise fall through to treat '-' as operator
        if ch.isdigit():
            tok = self._number_token(start_line, start_col)
            if tok is not None:
                tokens.append(tok)
            return
        if self._is_identifier_start(ch):
            tok = self._identifier_token(start_line, start_col)
            if tok is not None:
                tokens.append(tok)
            return
        three_char = ch + self._peek() + self._peek_next()
        if three_char in MULTI_CHAR_OPERATORS:
            self._advance()
            self._advance()
            self._validate_symbol_follow(three_char, self.line, self.column)
            tokens.append(Token(MULTI_CHAR_OPERATORS[three_char], three_char, line=start_line, column=start_col))
            return

        two_char = ch + self._peek()
        if two_char in MULTI_CHAR_OPERATORS:
            # Treat "--" as OP_DEC only when not followed by '-' or digit (so --- and --5 are minus/negation)
            if two_char == "--":
                # Maximal munch: treat "--" as OP_DEC (decrement). Exception: after ) or ] emit two MINUS so (value)-- id = minus minus.
                if tokens and tokens[-1].kind in ("RPAREN", "RBRACKET"):
                    tokens.append(Token("MINUS", "-", line=start_line, column=start_col))
                    return
                self._advance()
                self._validate_symbol_follow(two_char, self.line, self.column)
                tokens.append(Token(MULTI_CHAR_OPERATORS[two_char], two_char, line=start_line, column=start_col))
                return
            else:
                self._advance()
                self._validate_symbol_follow(two_char, self.line, self.column)
                tokens.append(Token(MULTI_CHAR_OPERATORS[two_char], two_char, line=start_line, column=start_col))
                return

        if ch in SINGLE_CHAR_TOKENS:
            lexeme = ch
            self._validate_symbol_follow(lexeme, self.line, self.column)
            tokens.append(Token(SINGLE_CHAR_TOKENS[lexeme], lexeme, line=start_line, column=start_col))
            return

        raise LexerError(f"Unexpected character '{ch}' at {start_line}:{start_col}", tokens)

    def _recover_after_error(self) -> None:
        # The error already occurred at the current token position.
        # Don't advance - let the next iteration of scan_tokens_collect_errors handle the next character.
        # This prevents consuming valid characters during recovery.
        pass

    # --- helpers -----------------------------------------------------------

    def _identifier_token(self, line: int, col: int) -> Token:
        # Read up to MAX_IDENTIFIER_LEN characters
        while self._is_identifier_part(self._peek()) and (self.pos - self.start) < MAX_IDENTIFIER_LEN:
            self._advance()
        lexeme = self.source[self.start:self.pos]
        nxt = self._peek()
        # If we hit the limit and more identifier chars follow, it's an error
        if len(lexeme) == MAX_IDENTIFIER_LEN and self._is_identifier_part(nxt):
            self._identifier_continuation = True
            self._add_lexical_error(
                f"Identifier exceeds {MAX_IDENTIFIER_LEN} characters; not tokenized Invalid delimeter at {self.line}:{self.column}"
            )
            return None  # Signal to skip token emission
        
        # Check if it's a keyword (exact match only); wrong case is treated as identifier
        keyword_result = self._match_keyword(lexeme)
        nxt = self._peek()
        
        # If it's a keyword, validate against keyword-specific delimiters
        if keyword_result:
            if nxt == "&" and self._peek_next() != "&":
                raise LexerError(
                    f"Single '&' is not allowed after `{lexeme}` at {self.line}:{self.column}. Use '&&' instead.",
                    self._partial_tokens,
                )
            allowed = expanded_reserved_word_follows.get(lexeme, IDENT_FOLLOW_CHARS)
            if nxt not in allowed:
                raise LexerError(
                    f"Reserved word `{lexeme}` must be followed by a valid delimiter at {self.line}:{self.column}\n\nExpected delimiter: {self._format_expected(allowed)}",
                    self._partial_tokens,
                )
            kind, _ = keyword_result
            literal = None
            if kind in {"greenflag", "redflag"}:
                literal = "true" if kind == "greenflag" else "false"
            return Token(kind=kind,
                         lexeme=lexeme,
                         literal=literal,
                         line=line,
                         column=col)
        
        # It's a regular identifier - validate delimiter
        # Special-case single ampersand so users get a clear hint to use '&&'.
        if nxt == "&" and self._peek_next() != "&":
            raise LexerError(
                f"Single '&' is not allowed after identifier `{lexeme}` at {self.line}:{self.column}. Use '&&' instead.",
                self._partial_tokens,
            )
        if nxt in BAD_SYMBOLS_AFTER_IDENTIFIER:
            if nxt == "!" and self._peek_next() == "=":
                pass  # allow '!='
            elif nxt == "|" and self._peek_next() == "|":
                pass  # allow '||'
            else:
                raise LexerError(
                    f"Invalid delimiter after identifier `{lexeme}` at {self.line}:{self.column}\n\nExpected delimiter: {self._format_expected(IDENT_FOLLOW_CHARS)}",
                    self._partial_tokens,
                )
        
        allowed = expanded_identifier_follows.get("identifier", IDENT_FOLLOW_CHARS)
        if nxt not in allowed:
            raise LexerError(
                f"Invalid delimiter after identifier `{lexeme}` at {self.line}:{self.column}\n\nExpected delimiter: {self._format_expected(allowed)}",
                self._partial_tokens,
            )
        return Token("id", lexeme, line=line, column=col)

    def _identifier_continuation_token(self, line: int, col: int) -> Token:
        """Continue scanning from 21st+ char after exceeding identifier limit."""
        while self._is_identifier_part(self._peek()) and (self.pos - self.start) < MAX_IDENTIFIER_LEN:
            self._advance()
        lexeme = self.source[self.start:self.pos]
        nxt = self._peek()
        # Check if we need to continue or if we can emit this chunk
        if len(lexeme) == MAX_IDENTIFIER_LEN and self._is_identifier_part(nxt):
            # Still exceeding, keep continuation mode active
            self._identifier_continuation = True
            # Add error for this continuation chunk too
            self._add_lexical_error(
                f"Identifier exceeds {MAX_IDENTIFIER_LEN} characters; not tokenized Invalid delimeter at {self.line}:{self.column}"
            )
            # Don't emit token while still continuing
            return None
        else:
            # Hit delimiter or shorter chunk; end continuation
            self._identifier_continuation = False
            # Only validate delimiter at the very end when continuation stops
            allowed = expanded_identifier_follows.get("identifier", IDENT_FOLLOW_CHARS)
            if nxt not in allowed:
                raise LexerError(
                    f"Invalid delimiter after identifier `{lexeme}` at {self.line}:{self.column}\n\nExpected delimiter: {self._format_expected(allowed)}",
                    self._partial_tokens,
                )
            # Only emit token if delimiter is valid
            return Token("id", lexeme, line=line, column=col)
    
    def _match_keyword(self, value: str) -> tuple[str, str] | None:
        """Character-by-character keyword matching for performance.
        Returns (token_kind, keyword) - token_kind matches what grammar expects."""
        length = len(value)
        if length == 0:
            return None
        
        first = value[0]
        
        # 'a' keywords
        if first == 'a':
            if length == 8 and value[1] == 'v' and value[2] == 'o' and value[3] == 'i' and value[4] == 'd' and value[5] == 'a' and value[6] == 'n' and value[7] == 't':
                return ("avoidant", "avoidant")
        
        # 'b' keywords
        elif first == 'b':
            if length == 7 and value[1] == 'r' and value[2] == 'e' and value[3] == 'a' and value[4] == 'k' and value[5] == 'u' and value[6] == 'p':
                return ("breakup", "breakup")
            elif length == 10 and value[1] == 'o' and value[2] == 'u' and value[3] == 'n' and value[4] == 'd' and value[5] == 'a' and value[6] == 'r' and value[7] == 'i' and value[8] == 'e' and value[9] == 's':
                return ("boundaries", "boundaries")
            elif length == 11 and value[1] == 'a' and value[2] == 'r' and value[3] == 'e' and value[4] == 'm' and value[5] == 'i' and value[6] == 'n' and value[7] == 'i' and value[8] == 'm' and value[9] == 'u' and value[10] == 'm':
                return ("bareminimum", "bareminimum")
        
        # 'c' keywords
        elif first == 'c':
            if length == 5 and value[1] == 'o' and value[2] == 'n' and value[3] == 's' and value[4] == 't':
                return ("const", "const")
            elif length == 6 and value[1] == 'h' and value[2] == 'o' and value[3] == 'o' and value[4] == 's' and value[5] == 'e':
                return ("choose", "choose")
            elif length == 8 and value[1] == 'o' and value[2] == 'm' and value[3] == 'e' and value[4] == 'b' and value[5] == 'a' and value[6] == 'c' and value[7] == 'k':
                return ("comeback", "comeback")
        
        # 'd' keywords
        elif first == 'd':
            if length == 4 and value[1] == 'e' and value[2] == 'a' and value[3] == 'r':
                return ("dear", "dear")
            elif length == 7 and value[1] == 'e' and value[2] == 'a' and value[3] == 'r' and value[4] == 'e' and value[5] == 's' and value[6] == 't':
                return ("dearest", "dearest")
        
        # 'e' keywords
        elif first == 'e':
            if length == 7 and value[1] == 'x' and value[2] == 'p' and value[3] == 'r' and value[4] == 'e' and value[5] == 's' and value[6] == 's':
                return ("express", "express")
        
        # 'f' keywords
        elif first == 'f':
            if length == 3 and value[1] == 'o' and value[2] == 'r':
                return ("for", "for")
            elif length == 7 and value[1] == 'o' and value[2] == 'r' and value[3] == 'e' and value[4] == 'v' and value[5] == 'e' and value[6] == 'r':
                return ("forever", "forever")
            elif length == 11 and value[1] == 'o' and value[2] == 'r' and value[3] == 'e' and value[4] == 'v' and value[5] == 'e' and value[6] == 'r' and value[7] == 'm' and value[8] == 'o' and value[9] == 'r' and value[10] == 'e':
                return ("forevermore", "forevermore")
        
        # 'g' keywords
        elif first == 'g':
            if length == 4 and value[1] == 'i' and value[2] == 'v' and value[3] == 'e':
                return ("give", "give")
            elif length == 9 and value[1] == 'r' and value[2] == 'e' and value[3] == 'e' and value[4] == 'n' and value[5] == 'f' and value[6] == 'l' and value[7] == 'a' and value[8] == 'g':
                return ("greenflag", "greenflag")
        
        # 'l' keywords
        elif first == 'l':
            if length == 4 and value[1] == 'o' and value[2] == 'v' and value[3] == 'e':
                return ("love", "love")
        
        # 'm' keywords
        elif first == 'm':
            if length == 4 and value[1] == 'o' and value[2] == 'r' and value[3] == 'e':
                return ("more", "more")
            elif length == 6 and value[1] == 'o' and value[2] == 'v' and value[3] == 'e' and value[4] == 'o' and value[5] == 'n':
                return ("moveon", "moveon")
        
        # 'o' keywords
        elif first == 'o':
            if length == 9 and value[1] == 'v' and value[2] == 'e' and value[3] == 'r' and value[4] == 's' and value[5] == 'h' and value[6] == 'a' and value[7] == 'r' and value[8] == 'e':
                return ("overshare", "overshare")
        
        # 'p' keywords
        elif first == 'p':
            if length == 5 and value[1] == 'h' and value[2] == 'a' and value[3] == 's' and value[4] == 'e':
                return ("phase", "phase")
            elif length == 7 and value[1] == 'e' and value[2] == 'r' and value[3] == 'i' and value[4] == 'o' and value[5] == 'd' and value[6] == 't':
                return ("periodt", "periodt")
            elif length == 6 and value[1] == 'u' and value[2] == 'r' and value[3] == 's' and value[4] == 'u' and value[5] == 'e':
                return ("pursue", "pursue")
        
        # 'r' keywords
        elif first == 'r':
            if length == 4 and value[1] == 'a' and value[2] == 'n' and value[3] == 't':
                return ("rant", "rant")
            elif length == 7 and value[1] == 'e' and value[2] == 'd' and value[3] == 'f' and value[4] == 'l' and value[5] == 'a' and value[6] == 'g':
                return ("redflag", "redflag")
        
        # 's' keywords
        elif first == 's':
            if length == 6 and value[1] == 't' and value[2] == 'a' and value[3] == 't' and value[4] == 'u' and value[5] == 's':
                return ("status", "status")
            elif length == 6 and value[1] == 't' and value[2] == 'r' and value[3] == 'u' and value[4] == 'c' and value[5] == 't':
                return ("struct", "struct")
        
        # 'w' keywords
        elif first == 'w':
            if length == 5 and value[1] == 'h' and value[2] == 'i' and value[3] == 'l' and value[4] == 'e':
                return ("while", "while")
        
        return None

    def _number_token(self, line: int, col: int, allow_negative: bool = False) -> Token:
        # For negative numbers, we need to consume the first digit
        # For positive numbers, the first digit was already consumed in _scan_single_token
        if allow_negative:
            # Minus was already consumed; consume first digit of the number
            self._advance()
            int_count = 1
        else:
            # First digit was already consumed in _scan_single_token
            int_count = 1
        
        # Read remaining digits up to 10 total digits for integer part
        while self._peek().isdigit():
            if int_count >= 10:
                if self._peek().isdigit():
                    self._number_continuation = True
                    lexeme = self.source[self.start:self.pos]
                    self._add_lexical_error(
                        f"Integer literal exceeds 10 digits at {self.line}:{self.column}"
                    )
                    return None  # Signal to skip token emission
                break
            self._advance()
            int_count += 1
        
        token_kind = "dear_lit"
        if self._peek() == "." and self._peek_next().isdigit():
            token_kind = "dearest_lit"
            self._advance()
            frac_count = 0
            while self._peek().isdigit():
                if frac_count >= 6:
                    # Hit 6-digit fractional limit; if more digits follow, skip first chunk
                    if self._peek().isdigit():
                        self._number_continuation = True
                        lexeme = self.source[self.start:self.pos]
                        self._add_lexical_error(
                            f"Float literal exceeds 6 fractional digits; not tokenized Invalid delimeter at {self.line}:{self.column}"
                        )
                        return None  # Signal to skip token emission
                    break
                self._advance()
                frac_count += 1
        
        lexeme = self.source[self.start:self.pos]
        
        # Validate limits (log lexical errors for overflow but still return token)
        if token_kind == "dear_lit":
            raw_digits = lexeme.lstrip("-")
            digits_only = lexeme.lstrip("-0") or "0"
            value = int(digits_only)
            if value > 9999999999:
                self._add_lexical_error(
                    f"Integer literal `{lexeme}` exceeds maximum value ±9999999999 at {line}:{col}"
                )
        
        # dearest_lit: validate ranges (log errors but continue)
        if token_kind == "dearest_lit":
            int_part, _, frac_part = lexeme.partition(".")
            norm_int = int_part.lstrip("0") or "0"
            norm_frac_raw = frac_part.rstrip("0")
            truncated_frac = norm_frac_raw[:6] if norm_frac_raw else "0"

            if len(norm_int) + len(truncated_frac) > 16:
                self._add_lexical_error(
                    f"Float literal `{lexeme}` exceeds 16 total digits at {line}:{col}"
                )
            try:
                numeric_val = Decimal(f"{norm_int}.{truncated_frac}")
                if numeric_val > Decimal("9999999999.999999"):
                    self._add_lexical_error(
                        f"Float literal `{lexeme}` exceeds maximum value ±9999999999.999999 at {line}:{col}"
                    )
            except (InvalidOperation, ValueError):
                raise LexerError(
                    f"Invalid float literal `{lexeme}` at {line}:{col}",
                    self._partial_tokens,
                )
        
        # Now validate delimiter
        nxt = self._peek()
        if nxt not in NUMBER_FOLLOW_CHARS:
            # Special case: if next char is a letter or alphanumeric, this is an invalid token
            # e.g., "123qwe" - identifiers cannot start with a digit
            # Consume up to MAX_IDENTIFIER_LEN total chars, then let rest be a new token
            if nxt in ALPHA or self._is_identifier_part(nxt):
                # Consume alphanumeric chars up to the 20-char limit
                while self._is_identifier_part(self._peek()) and (self.pos - self.start) < MAX_IDENTIFIER_LEN:
                    self._advance()
                invalid_lexeme = self.source[self.start:self.pos]
                # Check if more identifier chars follow - if so, set continuation mode
                if self._is_identifier_part(self._peek()):
                    self._identifier_continuation = True
                self._add_lexical_error(
                    f"Invalid token `{invalid_lexeme}`: identifiers cannot start with a digit at {line}:{col}"
                )
                return None  # Don't emit a token, let continuation handle the rest
            human_kind = "float" if token_kind == "dearest_lit" else "integer"
            raise LexerError(
                f"Invalid delimiter after {human_kind} `{lexeme}` at {line}:{self.column}\n\nExpected delimiter: {self._format_expected(NUMBER_FOLLOW_CHARS)}",
                self._partial_tokens,
            )
        
        if token_kind == "dear_lit":
            return Token(token_kind, lexeme, literal=lexeme, line=line, column=col)

        # Return float token
        # Extract minus sign if present
        is_negative = lexeme.startswith("-")
        int_part, _, frac_part = lexeme.partition(".")
        # Remove the minus sign before normalizing
        if is_negative:
            int_part = int_part[1:]
        norm_int = int_part.lstrip("0") or "0"
        norm_frac_raw = frac_part.rstrip("0")
        truncated_frac = norm_frac_raw[:6] if norm_frac_raw else "0"
        # Reconstruct with normalized parts
        literal_clean = f"{norm_int}.{truncated_frac}"
        # Add minus sign back if it was present
        if is_negative:
            literal_clean = "-" + literal_clean
        return Token(token_kind, lexeme, literal=literal_clean, line=line, column=col)

    def _number_continuation_token(self, line: int, col: int) -> Token:
        """Continue scanning from 11th+ digit or 7th+ fractional digit after exceeding limit."""
        count = 1
        token_kind = "dear_lit"
        
        # Consume digits
        while self._peek().isdigit() and count < 10:
            self._advance()
            count += 1
        
        # Check if there's a decimal point followed by more digits (makes it a float)
        if self._peek() == "." and self._peek_next().isdigit():
            token_kind = "dearest_lit"
            self._advance()  # consume the '.'
            # Consume fractional digits up to 6
            frac_count = 0
            while self._peek().isdigit():
                if frac_count >= 6:
                    # Hit 6-digit fractional limit; if more digits follow, stay in continuation
                    if self._peek().isdigit():
                        self._number_continuation = True
                        lexeme = self.source[self.start:self.pos]
                        self._add_lexical_error(
                            f"Float literal exceeds 6 fractional digits; not tokenized Invalid delimeter at {self.line}:{self.column}"
                        )
                        return None  # Don't emit this token, continue consuming
                    break
                self._advance()
                frac_count += 1
        
        lexeme = self.source[self.start:self.pos]
        nxt = self._peek()
        
        # Check if we need to continue or if we can emit this chunk
        if count == 10 and nxt.isdigit():
            # Still exceeding, keep continuation mode active
            self._number_continuation = True
            # Add error for this continuation chunk too
            self._add_lexical_error(
                f"Integer literal exceeds 10 digits at {self.line}:{self.column}"
            )
            # Don't emit token while still continuing
            return None
        elif nxt == "." and self._peek_next().isdigit():
            # Another decimal point - continue consuming as malformed number
            self._number_continuation = True
            return None
        else:
            # Hit delimiter or shorter chunk; end continuation
            self._number_continuation = False
            # Only validate delimiter at the very end when continuation stops
            if nxt not in NUMBER_FOLLOW_CHARS:
                # If next char is a letter or alphanumeric, consume the entire invalid token
                if nxt in ALPHA or self._is_identifier_part(nxt):
                    while self._is_identifier_part(self._peek()):
                        self._advance()
                    invalid_lexeme = self.source[self.start:self.pos]
                    raise LexerError(
                        f"Invalid token `{invalid_lexeme}`: identifiers cannot start with a digit at {self.line}:{self.column}",
                        self._partial_tokens,
                    )
                human_kind = "float" if token_kind == "dearest_lit" else "integer"
                raise LexerError(
                    f"Invalid delimiter after {human_kind} `{lexeme}` at {self.line}:{self.column}\n\nExpected delimiter: {self._format_expected(NUMBER_FOLLOW_CHARS)}",
                    self._partial_tokens,
                )
            
            # Emit the overflow token
            if token_kind == "dear_lit":
                return Token(token_kind, lexeme, literal=lexeme, line=line, column=col)
            else:
                # Format float literal
                int_part, _, frac_part = lexeme.partition(".")
                norm_int = int_part.lstrip("0") or "0"
                norm_frac_raw = frac_part.rstrip("0")
                truncated_frac = norm_frac_raw[:6] if norm_frac_raw else "0"
                literal_clean = f"{norm_int}.{truncated_frac}"
                return Token(token_kind, lexeme, literal=literal_clean, line=line, column=col)

    def _string_token(self, quote: str, line: int, col: int) -> Token:
        if quote != '"':
            raise LexerError(
                f'String values must be enclosed in double quotes (") at {line}:{col}',
                self._partial_tokens,
            )
        # Save position after opening quote for recovery
        pos_after_quote = self.pos
        line_after_quote = self.line
        col_after_quote = self.column
        
        escaped = False
        content_chars: list[str] = []
        while not self._is_at_end():
            c = self._advance()
            if escaped:
                if c == '"':
                    content_chars.append('"')
                elif c == "\\":
                    content_chars.append("\\")
                elif c == "n":
                    content_chars.append("\n")
                elif c == "t":
                    content_chars.append("\t")
                else:
                    raise LexerError(
                        f"Invalid escape sequence `\\{c}` in string at {line}:{col}",
                        self._partial_tokens,
                    )
                escaped = False
                continue
            if c == "\\":
                escaped = True
                continue
            if c == quote:
                # First " starts the string; this " ends it.
                lexeme = self.source[self.start:self.pos]
                inner = "".join(content_chars)
                nxt = self._peek()
                if nxt not in STRING_DELIMS:
                    # Stray quote (e.g. "hello""): report once, consume it, return the string token.
                    if nxt == '"':
                        self._add_lexical_error(
                            f"Invalid delimiter after string literal at {line}:{self.column}\n\nExpected delimiter: {self._format_expected(STRING_DELIMS)}",
                        )
                        self._advance()
                        return Token("rant_lit", lexeme, literal=inner, line=line, column=col)
                    raise LexerError(
                        f"Invalid delimiter after string literal at {line}:{self.column}\n\nExpected delimiter: {self._format_expected(STRING_DELIMS)}",
                        self._partial_tokens,
                    )
                return Token("rant_lit", lexeme, literal=inner, line=line, column=col)
            if c == "\n":
                # Unterminated string - reset position to after the opening quote
                # so remaining characters can be tokenized
                self.pos = pos_after_quote
                self.line = line_after_quote
                self.column = col_after_quote
                raise LexerError(f"Unterminated string at {line}:{col}", self._partial_tokens)
            content_chars.append(c)
        # EOF reached - reset position to after the opening quote
        # so remaining characters can be tokenized
        self.pos = pos_after_quote
        self.line = line_after_quote
        self.column = col_after_quote
        raise LexerError(f"Unterminated string at {line}:{col}", self._partial_tokens)

    def _skip_line_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        # Save position after /* for recovery
        pos_after_start = self.pos
        line_after_start = self.line
        col_after_start = self.column
        
        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        # EOF reached - reset position to after /* so remaining characters can be tokenized
        self.pos = pos_after_start
        self.line = line_after_start
        self.column = col_after_start
        raise LexerError("Unterminated block comment at start", self._partial_tokens)

    def _is_identifier_start(self, ch: str) -> bool:
        # Must start with a letter (no leading underscores per language rules).
        return ch in ALPHA

    def _is_identifier_part(self, ch: str) -> bool:
        return ch in ALNUM or ch == "_"

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= self.length:
            return "\0"
        return self.source[self.pos + 1]


    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.pos] != expected:
            return False
        self.pos += 1
        self.column += 1
        return True

    def _is_at_end(self) -> bool:
        return self.pos >= self.length

    def _format_expected(self, allowed: set[str]) -> str:
        """Format expected delimiters in a human-readable way.
        Format: Space, Tab, Newline, "(", "{", "+", etc.
        """
        parts: List[str] = []
        seen: set[str] = set()
        covered_chars: set[str] = set()

        # Whitespace first (readable names, no quotes)
        if " " in allowed:
            parts.append("Space")
            seen.add(" ")
        if "\t" in allowed:
            parts.append("Tab")
            seen.add("\t")
        if "\n" in allowed:
            parts.append("Newline")
            seen.add("\n")
        if "\0" in allowed:
            parts.append("EOF")
            seen.add("\0")

        # Check for alphabet/digit ranges
        from string import ascii_uppercase as _UC, ascii_lowercase as _LC, digits as _DG
        uc = set(_UC)
        lc = set(_LC)
        dg = set(_DG)
        
        has_alphabet = (uc | lc).issubset(allowed)
        has_digit = dg.issubset(allowed)
        
        if has_alphabet and has_digit:
            # Show as separate ranges: 0-9, A-Z, a-z
            parts.append("0-9")
            parts.append("A-Z")
            parts.append("a-z")
            covered_chars |= uc | lc | dg
        elif has_alphabet:
            # Show as separate ranges: A-Z, a-z
            parts.append("A-Z")
            parts.append("a-z")
            covered_chars |= uc | lc
        elif has_digit:
            parts.append("0-9")
            covered_chars |= dg

        # Collect symbols (single chars that aren't whitespace or covered)
        symbols = []
        for ch in sorted(allowed):
            if ch in seen or ch in covered_chars:
                continue
            if len(ch) == 1:
                symbols.append(ch)
                seen.add(ch)
        
        # Add symbols without quotes
        for sym in symbols:
            parts.append(sym)

        return ", ".join(parts)

    def _validate_symbol_follow(self, lexeme: str, line: int, col: int) -> None:
        # Get allowed delimiters for this symbol, or use default (whitespace)
        allowed = expanded_reserved_symbol_follows.get(lexeme)
        if not allowed:
            # Default: any symbol without specific rules must be followed by whitespace
            allowed = WHITESPACE
        
        # If immediate next char is whitespace and whitespace is allowed, accept.
        ws_chars = {" ", "\t", "\r", "\n"} | WHITESPACE
        immediate = self._peek()
        if immediate in ws_chars and allowed.intersection(ws_chars):
            return

        # Otherwise, find next non-whitespace character (tracking any whitespace seen).
        i = self.pos
        saw_ws = immediate in ws_chars
        while i < self.length and self.source[i] in ws_chars:
            i += 1
        nxt = self.source[i] if i < self.length else "\0"
        if nxt not in allowed:
            expected = self._format_expected(allowed)
            raise LexerError(
                f"Invalid delimiter after operator `{lexeme}` at {line}:{col}\n\nExpected delimiter: {expected}",
                self._partial_tokens,
            )

def tokenize(source: str) -> List[Token]:
    return Lexer(source).scan_tokens()

def tokenize_with_errors(source: str) -> tuple[List[Token], List[str]]:
    return Lexer(source).scan_tokens_collect_errors()

def _format_tokenizer(tok: Token) -> str:
    """Format token for display - uses the simplified token name from TOKEN_DISPLAY_NAME."""
    return tok.token


def _token_type(kind: str) -> str:
    """Get the token type name (Token Type column - uppercase type)."""
    # Use TOKEN_DISPLAY_NAME mapping for token type display
    # Lowercase tokens (dear_lit, dearest_lit, rant_lit, id, keywords) map to uppercase types (INT_LIT, FLOAT_LIT, STRING_LIT, IDENTIFIER, MAIN, etc.)
    # Uppercase tokens (LPAREN, OP_LSHIFT, etc.) are used as-is (their TOKEN_DISPLAY_NAME entries map to display symbols, not types)
    
    # Check if lowercase version exists in mapping (for dear_lit, rant_lit, id, keywords)
    kind_lower = kind.lower()
    if kind_lower in TOKEN_DISPLAY_NAME:
        mapped = TOKEN_DISPLAY_NAME[kind_lower]
        # If mapped value is uppercase (token type), use it; otherwise it's a display symbol, use original uppercased
        if mapped.isupper():
            name = mapped  # e.g., "rant_lit" → "STRING_LIT", "love" → "MAIN"
        else:
            name = kind.upper()  # Display symbol mapping, use original uppercased
    elif kind.isupper():
        # Already uppercase (LPAREN, OP_LSHIFT, etc.) - use as-is
        name = kind
    else:
        # Fallback
        name = kind.upper()
    return name[:12]


def tokens_as_rows(tokens: Iterable[Token]) -> List[dict]:
    rows: List[dict] = []
    for tok in tokens:
        if tok.kind == "EOF":
            continue
        rows.append(
            {
                "lexeme": tok.lexeme,
                "token": _format_tokenizer(tok),
                "tokenType": _token_type(tok.kind),
            }
        )
    return rows
