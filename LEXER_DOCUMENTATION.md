# Lexer Documentation - Detailed Explanation

## Overview
The **Lexer** is the first phase of your compiler. It scans source code and converts it into **tokens** - meaningful units like keywords, identifiers, numbers, and symbols. This allows the syntax analyzer to work with structured data instead of raw characters.

---

## Core Components

### 1. **Token Class** (Line 93-104)
```python
@dataclass
class Token:
    kind: str                          # Token type (e.g., "IDENTIFIER", "INT_LITERAL")
    lexeme: str                        # Original text from source (e.g., "myVar")
    literal: Optional[str] = None      # Normalized/computed value (e.g., "3.14")
    line: int = 1                      # Line number in source
    column: int = 1                    # Column position in source
    cpp_equivalent: Optional[str]      # C++ equivalent for keywords
```
**Purpose**: Represents a single token with its type, original text, position, and metadata.

---

### 2. **LexerError Exception** (Line 106-111)
```python
class LexerError(Exception):
    def __init__(self, message: str, tokens: Optional[List["Token"]] = None):
        super().__init__(message)
        self.tokens = tokens or []
```
**Purpose**: Custom exception thrown when lexical errors occur (e.g., invalid delimiter, unexpected character). Includes the message and partial tokens collected so far.

---

### 3. **Lexer Class** (Line 113+)

#### **Initialization** (Lines 113-127)
```python
def __init__(self, source: str):
    self.source = source              # Source code string to scan
    self.length = len(source)         # Total length
    self.start = 0                    # Start position of current token
    self.pos = 0                      # Current scanning position
    self.line = 1                     # Current line number
    self.column = 1                   # Current column number
    self._partial_tokens: List[Token] = []        # Tokens collected so far
    self._identifier_continuation: bool = False   # Is identifier overflowing?
    self._number_continuation: bool = False       # Is number overflowing?
    self._lexical_errors: List[str] = []         # Non-fatal errors collected
```
**Purpose**: Set up the lexer state with source code and initialize tracking variables.

---

## Main Scanning Methods

### 4. **scan_tokens()** (Lines 129-143)
**Purpose**: Main entry point to tokenize the entire source code.

**How it works**:
1. Loop through source code character by character
2. Track starting position (line, column) for each token
3. Call `_scan_single_token()` for each character
4. Append EOF token at the end
5. Return list of all tokens

```python
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
```

### 5. **scan_tokens_collect_errors()** (Lines 145-167)
**Purpose**: Same as `scan_tokens()` but catches `LexerError` exceptions and collects them instead of crashing.

**How it works**:
1. Try to scan each token
2. If `LexerError` occurs, add it to error list and recover
3. Continue scanning instead of stopping
4. Return both tokens AND error list

**Key feature**: Allows error recovery - the lexer keeps going even after finding errors.

---

## Token Recognition Methods

### 6. **_scan_single_token()** (Lines 171-218)
**Purpose**: Dispatcher that identifies what type of token starts with a given character and calls appropriate handler.

**What it handles**:
- **Newlines**: Converts `\n` to NEWLINE token
- **Whitespace**: Skips spaces and tabs
- **Comments**: Handles `/* ... */` block comments
- **Strings**: Delegates to `_string_token()` for `'` or `"`
- **Identifier Continuation**: Handles overflow identifiers (21+ characters)
- **Number Continuation**: Handles overflow numbers (11+ digits)
- **Negative Numbers**: Detects `-` followed by digit
- **Numbers**: Delegates to `_number_token()` for digit
- **Identifiers**: Delegates to `_identifier_token()` for letter
- **Multi-char Operators**: Recognizes `==`, `!=`, `&&`, `||`, etc.
- **Single-char Tokens**: Recognizes `;`, `(`, `)`, `+`, `-`, etc.

### 7. **_identifier_token()** (Lines 237-311)
**Purpose**: Scan and validate identifier tokens (variable names, keyword names).

**Rules enforced**:
- Max length: **20 characters**
- Valid start: Letter or underscore
- Valid continuation: Letters, digits, underscores
- Must be followed by valid delimiter

**How it works**:
1. Read up to 20 characters that are identifier parts
2. If exactly 20 chars found AND more identifier chars follow → overflow error
3. Check for bad symbols after identifier (like `!`, `@`, `#` without `!=`, etc.)
4. Check if it's a keyword (reserved word)
5. If not keyword → validate identifier delimiter
6. Return IDENTIFIER or KEYWORD token

**Overflow handling**: Sets `_identifier_continuation = True` and returns `None` (no token emitted yet)

### 8. **_identifier_continuation_token()** (Lines 313-347)
**Purpose**: Handle continuation of overflowed identifiers.

**How it works**:
1. Continue reading identifier characters (up to 20 more per chunk)
2. If still exceeding 20 chars → stay in continuation mode, add error, return `None`
3. If hits valid delimiter → exit continuation mode, validate delimiter, emit IDENTIFIER token
4. If hits invalid delimiter → throw `LexerError`

**Key point**: The token is only emitted when a valid delimiter is finally encountered.

### 9. **_number_token()** (Lines 444-559)
**Purpose**: Scan integer and float literals with limit enforcement.

**Rules enforced**:
- **Integer**: Max 10 digits
- **Float**: Max 10 integer digits + 6 fractional digits
- Must be followed by valid delimiter (space, newline, symbol, etc.)
- Validates numeric ranges

**How it works**:
1. Read up to 10 integer digits
2. If found `.` followed by digit → switch to FLOAT_LITERAL mode
3. Read up to 6 fractional digits
4. If overflow → set continuation, add error, return `None`
5. Validate delimiter after number
6. Return INT_LITERAL or FLOAT_LITERAL token with normalized literal value

**Special handling**:
- Negative numbers: Detects and handles `-` prefix
- Float normalization: Removes leading zeros and trailing zeros
- Decimal handling: Supports fractional parts

### 10. **_number_continuation_token()** (Lines 561-635)
**Purpose**: Handle continuation of overflowed numbers (11+ integer digits OR 7+ fractional digits).

**How it works**:
1. Continue reading digits
2. If sees decimal point with digits → treat as FLOAT (respecting 6-digit fractional limit)
3. If still exceeding 10 integer digits → stay in continuation
4. If hits decimal point again → continue consuming (malformed number)
5. When valid delimiter found → emit the overflow token (INT_LITERAL or FLOAT_LITERAL)

**Example**: `123.1234561.123123`
- First pass: `123.123456` (valid FLOAT)
- Overflow: `1` detected, enters continuation
- Continuation: Sees `.123123`, converts to FLOAT
- Result: Emits `1.123123` as FLOAT token when delimiter met

### 11. **_string_token()** (Lines 637-704)
**Purpose**: Scan string literals enclosed in `'` or `"`.

**Rules enforced**:
- Max length: 255 characters
- Escape sequences: `\\`, `\'`, `\"`, `\n`, `\t`
- Unterminated strings raise error
- Overflow truncates (logs warning)

**How it works**:
1. Read opening quote (`'` or `"`)
2. Loop consuming characters until closing quote
3. Handle escape sequences (`\n` → newline, `\\` → backslash, etc.)
4. If exceeds 255 chars → warn and truncate
5. Verify string is terminated
6. Return STRING_LITERAL token

---

## Helper/Utility Methods

### 12. **_match_keyword()** (Lines 349-450)
**Purpose**: Character-by-character keyword matching (optimized for speed).

**Keywords recognized** (27 total):
- I/O: `give`, `express`, `overshare`
- Types: `dear` (int), `dearest` (float), `rant` (string), `status` (bool)
- Control: `forever` (if), `more` (else), `forevermore` (elseif), `choose` (switch), `phase` (case), `bareminimum` (default)
- Loops: `for`, `while`, `pursue` (do-while)
- Jump: `breakup` (break), `moveon` (continue)
- Structure: `love` (main), `boundaries` (namespace), `comeback` (return)
- Booleans: `redflag` (false), `greenflag` (true)
- Misc: `periodt` (endl), `const`

**How it works**:
- Instead of dictionary lookup, uses character-by-character comparison
- Checks first char, then second char position by position
- Much faster for long strings

### 13. **_validate_symbol_follow()** (Lines 814-850)
**Purpose**: Ensure symbols/operators are followed by valid delimiters.

**How it works**:
1. Get expected delimiters for the symbol from `token_map.py`
2. Check if next character is in allowed set
3. If not → throw `LexerError` with expected tokens list
4. Error position: Where the invalid delimiter is found

**Example**: After `(`, valid delimiters are: whitespace, identifiers, `!`, `)`, `(`, `-`, etc.

### 14. **_format_expected()** (Lines 715-803)
**Purpose**: Format list of valid delimiters into human-readable output.

**How it works**:
1. Converts character set to readable format
2. Groups similar items: numbers, letters, operators
3. Removes duplicates
4. Sorts for consistency
5. Wraps long lines at 80 characters

**Example output**: `space, tab, newline, ), ], }, ;, :, ,, ., >, <, +, -, *, /, %, =, !=, <=, >=, etc.`

### 15. **Position Tracking Methods**

```python
def _advance() -> str:
    """Consume current character, update line/column, return it."""
    # Updates self.pos, self.line, self.column for \n
    
def _peek() -> str:
    """Look at next character without consuming."""
    
def _peek_next() -> str:
    """Look at character 2 positions ahead."""
    
def _match(expected: str) -> bool:
    """If next char matches expected, consume it."""
    
def _is_at_end() -> bool:
    """Are we at end of source?"""
    
def _is_identifier_start(ch: str) -> bool:
    """Can character start identifier?"""
    
def _is_identifier_part(ch: str) -> bool:
    """Can character be in identifier?"""
```

**Purpose**: Core character scanning utilities for tracking position and lookahead.

---

## Error Handling & Validation

### Error Types

1. **Identifier Errors**:
   - Exceeds 20 chars: `"Identifier exceeds 20 characters; identifers not tokenized at X:Y"`
   - Invalid delimiter after: `"Invalid delimiter after identifier \`foo\` at X:Y\n\nExpected: ..."`
   - Reserved word not lowercase: `"Reserved word \`Foo\` must be written in lowercase at X:Y"`
   - Single `&` not allowed: `"Single '&' is not allowed after identifier \`x\` at X:Y. Use '&&' instead."`

2. **Number Errors**:
   - Integer exceeds 10 digits: `"Integer literal exceeds 10 digits at X:Y"`
   - Float exceeds 6 fractional digits: `"Float literal exceeds 6 fractional digits; not tokenized Invalid delimeter at X:Y"`
   - Invalid delimiter after: `"Invalid delimiter after integer \`123\`: at X:Y\n\nExpected: ..."`
   - Identifier can't start with digit: `"Identifiers cannot start with a digit. \`123abc\` should start with alphabet character at X:Y"`

3. **String Errors**:
   - Unterminated string: `"Unterminated string at X:Y"`
   - Invalid escape: `"Unknown escape sequence \\x in string at X:Y"`

4. **Syntax Errors**:
   - Unexpected character: `"Unexpected character '!' at X:Y"`

### Error Position Tracking
- **Error position points to problem, not start**: 
  - For identifiers: Error at column where 21st char detected
  - For numbers: Error at column where overflow digit detected
  - For symbols: Error at column where invalid delimiter found

---

## Token Limits Summary

| Type | Limit | Behavior |
|------|-------|----------|
| Identifier | 20 chars | Overflow → error, continuation, tokenize when delimiter met |
| Integer | 10 digits | Overflow → error, continuation |
| Float integer part | 10 digits | Same as integer |
| Float fractional part | 6 digits | Overflow → error, continuation, can become separate token |
| String | 255 chars | Overflow → truncate + warning |

---

## Example: Tokenizing `123.1234561.123123 `

**Input**: `123.1234561.123123 ` (space at end)

**Scanning process**:
1. Read `123` → 3 integer digits
2. See `.` → switch to FLOAT mode
3. Read `123456` → 6 fractional digits (at limit)
4. See `1` (7th decimal digit) → enter continuation, error logged
5. Continuation reads `1` then sees `.` → converts to new FLOAT token
6. Read `.123123` → 6 more digits
7. See space → valid delimiter!
8. Emit: `123.123456` (FLOAT), `1.123123` (FLOAT)

**Errors logged**:
- `"Float literal exceeds 6 fractional digits; not tokenized Invalid delimeter at 1:7"`

---

## Key Features

### 1. **Continuation Token System**
Handles tokens that exceed limits by:
- Logging error at overflow point
- Not emitting token until valid delimiter found
- Allowing overflow to continue across multiple chunks
- Emitting new valid tokens from overflow parts

### 2. **Position Accuracy**
- Error messages point to WHERE the problem is (overflow digit, invalid char)
- NOT where the token started
- Helps users identify exact issue location

### 3. **Comprehensive Validation**
- Delimiters after tokens
- Reserved word capitalization
- Valid escape sequences
- Numeric ranges

### 4. **Error Recovery**
- `scan_tokens_collect_errors()` catches errors and continues
- Allows finding multiple errors in one pass
- Better user experience (see all problems at once)

### 5. **Optimized Keyword Matching**
- Character-by-character comparison instead of hash lookup
- Faster for modern CPUs (cache locality)
- Eliminates hash collision issues

