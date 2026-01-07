# Backend/Lexical/lexer.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Optional

from Backend.Syntax.token_map import (
    Literals,
    expanded_reserved_word_follows,
    expanded_identifier_follows,
    expanded_reserved_symbol_follows,
    expanded_int_lit,
    expanded_string_lit,
)

RESERVED_WORDS = {
    "give": ("KEYWORD_IO_GIVE", "give"),
    "express": ("KEYWORD_IO_EXPRESS", "express"),
    "overshare": ("KEYWORD_IO_OVERSHARE", "overshare"),
    "dear": ("KEYWORD_TYPE_INT", "dear"),
    "dearest": ("KEYWORD_TYPE_FLOAT", "dearest"),
    "rant": ("KEYWORD_TYPE_STRING", "rant"),
    "status": ("KEYWORD_TYPE_BOOL", "status"),
    "forever": ("KEYWORD_IF", "forever"),
    "more": ("KEYWORD_ELSE", "more"),
    "forevermore": ("KEYWORD_ELSEIF", "forevermore"),
    "choose": ("KEYWORD_SWITCH", "choose"),
    "phase": ("KEYWORD_CASE", "phase"),
    "bareminimum": ("KEYWORD_DEFAULT", "bareminimum"),
    "for": ("KEYWORD_FOR", "for"),
    "while": ("KEYWORD_WHILE", "while"),
    "pursue": ("KEYWORD_DO_WHILE", "pursue"),
    "breakup": ("KEYWORD_BREAK", "breakup"),
    "moveon": ("KEYWORD_CONTINUE", "moveon"),
    "love": ("KEYWORD_MAIN", "love"),
    "periodt": ("KEYWORD_ENDL", "periodt"),
    "const": ("KEYWORD_CONST", "const"),
    "redflag": ("BOOL_LITERAL_FALSE", "redflag"),
    "greenflag": ("BOOL_LITERAL_TRUE", "greenflag"),
    "boundaries": ("KEYWORD_NAMESPACE", "boundaries"),
    "comeback": ("KEYWORD_RETURN", "comeback"),
}

MULTI_CHAR_OPERATORS = {
    "==": "OP_EQ",
    "!=": "OP_NEQ",
    ">=": "OP_GTE",
    "<=": "OP_LTE",
    ">>": "OP_RSHIFT",
    "<<": "OP_LSHIFT",
    "&&": "OP_AND",
    "||": "OP_OR",
    "++": "OP_INC",
    "--": "OP_DEC",
    "+=": "OP_PLUS_ASSIGN",
    "-=": "OP_MINUS_ASSIGN",
    "*=": "OP_MUL_ASSIGN",
    "/=": "OP_DIV_ASSIGN",
    "%=": "OP_MOD_ASSIGN",
    "::": "OP_SCOPE",
    "->": "OP_ARROW",
}

SINGLE_CHAR_TOKENS = {
    ";": "SEMICOLON",
    ",": "COMMA",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ":": "COLON",
    ".": "DOT",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "=": "ASSIGN",
    ">": "GT",
    "<": "LT",
    "!": "BANG",
    "|": "OR",
}


TOKEN_TYPE_OVERRIDES: dict = {}

IDENTIFIER_DELIMS = expanded_identifier_follows.get("identifier", set())
NUMBER_DELIMS = expanded_int_lit.get("int_lit", set())
STRING_DELIMS = expanded_string_lit.get("string_lit", set())
ALPHA = Literals["alphabet"]
DIGIT = Literals["digit"]
ALNUM = Literals["alphanum"]
WHITESPACE = {" ", "\t", "\n"}
DISALLOWED_IDENTIFIERS: set[str] = set()
# Disallow only symbols that should never appear immediately after an identifier.
BAD_SYMBOLS_AFTER_IDENTIFIER = set("!@#$^\\?~")
IDENT_FOLLOW_CHARS = IDENTIFIER_DELIMS or WHITESPACE
NUMBER_FOLLOW_CHARS = (
    NUMBER_DELIMS
    | WHITESPACE
)

@dataclass
class Token:
    kind: str
    lexeme: str
    literal: Optional[str] = None
    line: int = 1
    column: int = 1
    cpp_equivalent: Optional[str] = None

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
        tokens.append(Token("EOF", "", line=self.line, column=self.column))
        return tokens, errors

    # --- single token scanner ----------------------------------------------

    def _scan_single_token(self, ch: str, tokens: List[Token], start_line: int, start_col: int) -> None:
        if ch in WHITESPACE:
            return
        if ch == "\n":
            tokens.append(Token("NEWLINE", "\\n", line=start_line, column=start_col))
            return
        if ch == "/" and self._match("*"):
            self._skip_block_comment()
            return
        if ch in {"'", '"'}:
            tokens.append(self._string_token(ch, start_line, start_col))
            return
        if ch == "-" and self._peek().isdigit():
            # Negative number literal
            tokens.append(self._number_token(start_line, start_col, allow_negative=True))
            return
        if ch.isdigit():
            tokens.append(self._number_token(start_line, start_col))
            return
        if self._is_identifier_start(ch):
            tokens.append(self._identifier_token(start_line, start_col))
            return

        two_char = ch + self._peek()
        if two_char in MULTI_CHAR_OPERATORS:
            self._advance()
            self._validate_symbol_follow(two_char, start_line, start_col)
            tokens.append(Token(MULTI_CHAR_OPERATORS[two_char], two_char, line=start_line, column=start_col))
            return

        if ch in SINGLE_CHAR_TOKENS:
            lexeme = ch
            self._validate_symbol_follow(lexeme, start_line, start_col)
            tokens.append(Token(SINGLE_CHAR_TOKENS[lexeme], lexeme, line=start_line, column=start_col))
            return

        raise LexerError(f"Unexpected character {ch!r} at {start_line}:{start_col}", tokens)

    def _recover_after_error(self) -> None:
        # Skip ahead until a likely delimiter/whitespace to continue scanning.
        self._advance() if not self._is_at_end() else None
        while not self._is_at_end():
            ch = self._peek()
            if ch in WHITESPACE or ch == "\n" or ch in IDENTIFIER_DELIMS:
                return
            self._advance()

    # --- helpers -----------------------------------------------------------

    def _identifier_token(self, line: int, col: int) -> Token:
        while self._is_identifier_part(self._peek()):
            self._advance()
        lexeme = self.source[self.start:self.pos]
        if len(lexeme) > 20:
            raise LexerError(
                f"Identifier `{lexeme}` exceeds the maximum length of 20 characters (current: {len(lexeme)}) at {line}:{col}",
                self._partial_tokens,
            )
        nxt = self._peek()
        # Special-case single ampersand so users get a clear hint to use '&&'.
        if nxt == "&" and self._peek_next() != "&":
            raise LexerError(
                f"Single '&' is not allowed after identifier `{lexeme}` at {line}:{col}. Use '&&' instead.",
                self._partial_tokens,
            )
        if nxt in BAD_SYMBOLS_AFTER_IDENTIFIER:
            if nxt == "!" and self._peek_next() == "=":
                pass  # allow '!='
            elif nxt == "|" and self._peek_next() == "|":
                pass  # allow '||'
            else:
                raise LexerError(
                    f"Invalid delimiter after identifier `{lexeme}` at {line}:{col}\n\nExpected: {self._format_expected(IDENT_FOLLOW_CHARS)}",
                    self._partial_tokens,
                )
        
        # Character-by-character keyword matching
        keyword_result = self._match_keyword(lexeme)
        if keyword_result is None:
            lowered = lexeme.lower()
            keyword_result = self._match_keyword(lowered)
            if keyword_result is not None:
                raise LexerError(
                    f"Reserved word `{lowered}` must be written in lowercase at {line}:{col}",
                    self._partial_tokens,
                )
            # Validate delimiter for regular identifiers too
            nxt = self._peek()
            allowed = expanded_identifier_follows.get("identifier", IDENT_FOLLOW_CHARS)
            if nxt not in allowed:
                raise LexerError(
                    f"Invalid delimiter after identifier `{lexeme}` at {line}:{col}\n\nExpected: {self._format_expected(allowed)}",
                    self._partial_tokens,
                )
        if keyword_result:
            nxt = self._peek()
            if nxt == "&" and self._peek_next() != "&":
                raise LexerError(
                    f"Single '&' is not allowed after `{lexeme}` at {line}:{col}. Use '&&' instead.",
                    self._partial_tokens,
                )
            allowed = expanded_reserved_word_follows.get(lexeme, IDENT_FOLLOW_CHARS)
            if nxt not in allowed:
                raise LexerError(
                    f"Reserved word `{lexeme}` must be followed by a delimiter at {line}:{col}\n\nExpected: {self._format_expected(allowed)}",
                    self._partial_tokens,
                )
            kind, cpp_equiv = keyword_result
            literal = cpp_equiv if kind.startswith("BOOL_LITERAL") else None
            return Token(kind=kind,
                         lexeme=lexeme,
                         literal=literal,
                         line=line,
                         column=col,
                         cpp_equivalent=cpp_equiv)
        return Token("IDENTIFIER", lexeme, line=line, column=col)
    
    def _match_keyword(self, value: str) -> tuple[str, str] | None:
        """Character-by-character keyword matching for performance."""
        length = len(value)
        if length == 0:
            return None
        
        first = value[0]
        
        # 'b' keywords
        if first == 'b':
            if length == 7 and value[1] == 'r' and value[2] == 'e' and value[3] == 'a' and value[4] == 'k' and value[5] == 'u' and value[6] == 'p':
                return ("KEYWORD_BREAK", "breakup")
            elif length == 10 and value[1] == 'o' and value[2] == 'u' and value[3] == 'n' and value[4] == 'd' and value[5] == 'a' and value[6] == 'r' and value[7] == 'i' and value[8] == 'e' and value[9] == 's':
                return ("KEYWORD_NAMESPACE", "boundaries")
            elif length == 12 and value[1] == 'a' and value[2] == 'r' and value[3] == 'e' and value[4] == 'm' and value[5] == 'i' and value[6] == 'n' and value[7] == 'i' and value[8] == 'm' and value[9] == 'u' and value[10] == 'm':
                return ("KEYWORD_DEFAULT", "bareminimum")
        
        # 'c' keywords
        elif first == 'c':
            if length == 5 and value[1] == 'o' and value[2] == 'n' and value[3] == 's' and value[4] == 't':
                return ("KEYWORD_CONST", "const")
            elif length == 6 and value[1] == 'h' and value[2] == 'o' and value[3] == 'o' and value[4] == 's' and value[5] == 'e':
                return ("KEYWORD_SWITCH", "choose")
            elif length == 8 and value[1] == 'o' and value[2] == 'm' and value[3] == 'e' and value[4] == 'b' and value[5] == 'a' and value[6] == 'c' and value[7] == 'k':
                return ("KEYWORD_RETURN", "comeback")
        
        # 'd' keywords
        elif first == 'd':
            if length == 4 and value[1] == 'e' and value[2] == 'a' and value[3] == 'r':
                return ("KEYWORD_TYPE_INT", "dear")
            elif length == 7 and value[1] == 'e' and value[2] == 'a' and value[3] == 'r' and value[4] == 'e' and value[5] == 's' and value[6] == 't':
                return ("KEYWORD_TYPE_FLOAT", "dearest")
        
        # 'e' keywords
        elif first == 'e':
            if length == 7 and value[1] == 'x' and value[2] == 'p' and value[3] == 'r' and value[4] == 'e' and value[5] == 's' and value[6] == 's':
                return ("KEYWORD_IO_EXPRESS", "express")
        
        # 'f' keywords
        elif first == 'f':
            if length == 3 and value[1] == 'o' and value[2] == 'r':
                return ("KEYWORD_FOR", "for")
            elif length == 7 and value[1] == 'o' and value[2] == 'r' and value[3] == 'e' and value[4] == 'v' and value[5] == 'e' and value[6] == 'r':
                return ("KEYWORD_IF", "forever")
            elif length == 11 and value[1] == 'o' and value[2] == 'r' and value[3] == 'e' and value[4] == 'v' and value[5] == 'e' and value[6] == 'r' and value[7] == 'm' and value[8] == 'o' and value[9] == 'r' and value[10] == 'e':
                return ("KEYWORD_ELSEIF", "forevermore")
        
        # 'g' keywords
        elif first == 'g':
            if length == 4 and value[1] == 'i' and value[2] == 'v' and value[3] == 'e':
                return ("KEYWORD_IO_GIVE", "give")
            elif length == 9 and value[1] == 'r' and value[2] == 'e' and value[3] == 'e' and value[4] == 'n' and value[5] == 'f' and value[6] == 'l' and value[7] == 'a' and value[8] == 'g':
                return ("BOOL_LITERAL_TRUE", "greenflag")
        
        # 'l' keywords
        elif first == 'l':
            if length == 4 and value[1] == 'o' and value[2] == 'v' and value[3] == 'e':
                return ("KEYWORD_MAIN", "love")
        
        # 'm' keywords
        elif first == 'm':
            if length == 4 and value[1] == 'o' and value[2] == 'r' and value[3] == 'e':
                return ("KEYWORD_ELSE", "more")
            elif length == 6 and value[1] == 'o' and value[2] == 'v' and value[3] == 'e' and value[4] == 'o' and value[5] == 'n':
                return ("KEYWORD_CONTINUE", "moveon")
        
        # 'o' keywords
        elif first == 'o':
            if length == 10 and value[1] == 'v' and value[2] == 'e' and value[3] == 'r' and value[4] == 's' and value[5] == 'h' and value[6] == 'a' and value[7] == 'r' and value[8] == 'e':
                return ("KEYWORD_IO_OVERSHARE", "overshare")
        
        # 'p' keywords
        elif first == 'p':
            if length == 5 and value[1] == 'h' and value[2] == 'a' and value[3] == 's' and value[4] == 'e':
                return ("KEYWORD_CASE", "phase")
            elif length == 7 and value[1] == 'e' and value[2] == 'r' and value[3] == 'i' and value[4] == 'o' and value[5] == 'd' and value[6] == 't':
                return ("KEYWORD_ENDL", "periodt")
            elif length == 6 and value[1] == 'u' and value[2] == 'r' and value[3] == 's' and value[4] == 'u' and value[5] == 'e':
                return ("KEYWORD_DO_WHILE", "pursue")
        
        # 'r' keywords
        elif first == 'r':
            if length == 4 and value[1] == 'a' and value[2] == 'n' and value[3] == 't':
                return ("KEYWORD_TYPE_STRING", "rant")
            elif length == 7 and value[1] == 'e' and value[2] == 'd' and value[3] == 'f' and value[4] == 'l' and value[5] == 'a' and value[6] == 'g':
                return ("BOOL_LITERAL_FALSE", "redflag")
        
        # 's' keywords
        elif first == 's':
            if length == 6 and value[1] == 't' and value[2] == 'a' and value[3] == 't' and value[4] == 'u' and value[5] == 's':
                return ("KEYWORD_TYPE_BOOL", "status")
        
        # 'w' keywords
        elif first == 'w':
            if length == 5 and value[1] == 'h' and value[2] == 'i' and value[3] == 'l' and value[4] == 'e':
                return ("KEYWORD_WHILE", "while")
        
        return None

    def _number_token(self, line: int, col: int, allow_negative: bool = False) -> Token:
        # Handle optional minus sign for negative literals
        if allow_negative and self._peek() == "-":
            self._advance()
        
        while self._peek().isdigit():
            self._advance()
        token_kind = "INT_LITERAL"
        if self._peek() == "." and self._peek_next().isdigit():
            token_kind = "FLOAT_LITERAL"
            self._advance()
            while self._peek().isdigit():
                self._advance()
        lexeme = self.source[self.start:self.pos]
        nxt = self._peek()
        if nxt not in NUMBER_FOLLOW_CHARS:
            human_kind = "float" if token_kind == "FLOAT_LITERAL" else "integer"
            raise LexerError(
                f"Invalid delimiter after {human_kind} {lexeme}: {nxt} at {line}:{self.column}\nExpected: {self._format_expected(NUMBER_FOLLOW_CHARS)}",
                self._partial_tokens,
            )
        if token_kind == "INT_LITERAL":
            # Enforce dear literal rules: max 10 digits (ignoring leading zeros and minus sign) and max value ±9999999999.
            digits_only = lexeme.lstrip("-0") or "0"
            if len(digits_only) > 10:
                raise LexerError(
                    f"Integer literal `{lexeme}` exceeds maximum length of 10 digits at {line}:{col}",
                    self._partial_tokens,
                )
            value = int(digits_only)
            if value > 9999999999:
                raise LexerError(
                    f"Integer literal `{lexeme}` exceeds maximum value ±9999999999 at {line}:{col}",
                    self._partial_tokens,
                )
            return Token(token_kind, lexeme, literal=lexeme, line=line, column=col)

        # FLOAT_LITERAL: dearest rules
        int_part, _, frac_part = lexeme.partition(".")
        norm_int = int_part.lstrip("0") or "0"
        norm_frac_raw = frac_part.rstrip("0")
        truncated_frac = norm_frac_raw[:6] if norm_frac_raw else "0"

        if len(norm_int) > 10:
            raise LexerError(
                f"Float literal `{lexeme}` exceeds 10 digits before decimal at {line}:{col}",
                self._partial_tokens,
            )
        if len(norm_int) + len(truncated_frac) > 16:
            raise LexerError(
                f"Float literal `{lexeme}` exceeds 16 total digits at {line}:{col}",
                self._partial_tokens,
            )
        try:
            numeric_val = Decimal(f"{norm_int}.{truncated_frac}")
        except (InvalidOperation, ValueError):
            raise LexerError(
                f"Invalid float literal `{lexeme}` at {line}:{col}",
                self._partial_tokens,
            )
        if numeric_val > Decimal("9999999999.999999"):
            raise LexerError(
                f"Float literal `{lexeme}` exceeds maximum value ±9999999999.999999 at {line}:{col}",
                self._partial_tokens,
            )
        literal_clean = f"{norm_int}.{truncated_frac}"
        # Preserve the minus sign if present
        if lexeme.startswith("-"):
            literal_clean = "-" + literal_clean
        return Token(token_kind, lexeme, literal=literal_clean, line=line, column=col)

    def _string_token(self, quote: str, line: int, col: int) -> Token:
        if quote != '"':
            raise LexerError(
                f'String values must be enclosed in double quotes (") at {line}:{col}',
                self._partial_tokens,
            )
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
                lexeme = self.source[self.start:self.pos]
                inner = "".join(content_chars)
                # Validate delimiter after closing quote
                nxt = self._peek()
                if nxt not in STRING_DELIMS:
                    raise LexerError(
                        f"Invalid delimiter after string literal: {nxt} at {line}:{self.column}\nExpected: {self._format_expected(STRING_DELIMS)}",
                        self._partial_tokens,
                    )
                return Token("STRING_LITERAL", lexeme, literal=inner, line=line, column=col)
            if c == "\n":
                raise LexerError(f"Unterminated string at {line}:{col}", self._partial_tokens)
            content_chars.append(c)
        raise LexerError(f"Unterminated string at {line}:{col}", self._partial_tokens)

    def _skip_line_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        raise LexerError("Unterminated block comment", self._partial_tokens)

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

    def _peek_non_whitespace(self) -> str:
        i = self.pos
        while i < self.length and self.source[i] in {" ", "\t", "\r", "\n"}:
            i += 1
        if i >= self.length:
            return "\0"
        return self.source[i]

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.pos] != expected:
            return False
        self.pos += 1
        self.column += 1
        return True

    def _is_at_end(self) -> bool:
        return self.pos >= self.length

    def _format_expected(self, allowed: set[str]) -> str:
        parts: List[str] = []
        seen: set[str] = set()
        covered_chars: set[str] = set()

        def add(label: str, ch: str) -> None:
            if ch in allowed and label not in seen:
                parts.append(label)
                seen.add(label)

        # Whitespace and EOF
        add("space", " ")
        add("tab", "\t")
        add("newline", "\n")
        add("EOF", "\0")

        # Single-character delimiters
        for ch in ["(", ")", "[", "]", "{", "}", ";", ",", ":"]:
            add(ch, ch)
        for ch in ["+", "-", "*", "/", "%", "=", "!", ">", "<", "&", "|", "."]:
            add(ch, ch)
        
        # Double quote (special handling for clarity)
        if '"' in allowed and '"' not in seen:
            parts.append('"')
            seen.add('"')
        
        # Single quote (special handling for clarity)
        if "'" in allowed and "'" not in seen:
            parts.append("'")
            seen.add("'")

        # If full ranges exist in allowed, show compact labels and mark covered
        from string import ascii_uppercase as _UC, ascii_lowercase as _LC, digits as _DG
        uc = set(_UC)
        lc = set(_LC)
        dg = set(_DG)

        if uc.issubset(allowed):
            parts.append("A:Z")
            covered_chars |= uc
        if lc.issubset(allowed):
            parts.append("a:z")
            covered_chars |= lc
        if dg.issubset(allowed):
            parts.append("0:9")
            covered_chars |= dg

        # Collect remaining characters and group into ranges
        remaining = []
        for item in sorted(allowed):
            # Skip if already covered above
            if item in seen or len(item) > 1 or item in covered_chars:  # Skip multi-char tokens and covered ranges
                continue
            remaining.append(item)
        
        # Group consecutive characters into ranges
        if remaining:
            i = 0
            while i < len(remaining):
                start = remaining[i]
                end = start
                # Find consecutive characters
                while i + 1 < len(remaining) and ord(remaining[i + 1]) == ord(remaining[i]) + 1:
                    i += 1
                    end = remaining[i]
                
                # Format as range if 3+ consecutive, otherwise list individually
                if ord(end) - ord(start) >= 2:  # 3 or more consecutive
                    parts.append(f"{start}:{end}")
                else:
                    # Add individual characters
                    for j in range(ord(start), ord(end) + 1):
                        parts.append(chr(j))
                i += 1
        
        # Add remaining multi-character tokens (e.g., &&, ||)
        for item in sorted(allowed):
            if len(item) > 1 and item not in seen:
                parts.append(item)
                seen.add(item)

        if not parts:
            parts.append(", ".join(sorted(a for a in allowed)))
        return "- " + "- ".join(parts)

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
                f"Invalid delimiter after operator `{lexeme}` at {line}:{col}\n\nExpected: {expected}",
                self._partial_tokens,
            )

def tokenize(source: str) -> List[Token]:
    return Lexer(source).scan_tokens()

def tokenize_with_errors(source: str) -> tuple[List[Token], List[str]]:
    return Lexer(source).scan_tokens_collect_errors()

def _format_tokenizer(tok: Token) -> str:
    display_name_overrides = {
        "(": "parenthesis",
        ")": "parenthesis",
        "{": "brace",
        "}": "brace",
        "[": "bracket",
        "]": "bracket",
        ";": "semicolon",
        ",": "comma",
    }
    # Display lexeme for all tokens (literals use their inner value).
    if tok.literal is not None:
        return tok.literal
    return display_name_overrides.get(tok.lexeme, tok.lexeme)


def _token_type(kind: str) -> str:
    if kind in {"INT_LITERAL"}:
        name = "INT_LIT"
    elif kind in {"FLOAT_LITERAL"}:
        name = "FLOAT_LIT"
    elif kind in {"STRING_LITERAL"}:
        name = "STRING_LIT"
    elif kind in {"CHAR_LITERAL"}:
        name = "CHAR_LIT"
    elif kind in {"BOOL_LITERAL_FALSE", "BOOL_LITERAL_TRUE"}:
        name = "BOOL_LIT"
    else:
        name = TOKEN_TYPE_OVERRIDES.get(kind, kind)
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
