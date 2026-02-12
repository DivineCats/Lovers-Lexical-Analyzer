"""Token follow-set mappings for the Lovers language."""

from string import ascii_letters, digits
from typing import Iterable, Set

# --- base character classes -------------------------------------------------

alphabet: Set[str] = set(ascii_letters)
digit: Set[str] = set(digits)
alphanum: Set[str] = alphabet | digit

# --- Literal character sets (transferred from Literals.py) -----------------

Literals = {
    'alphabet': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    },
    'digit': {'0','1','2','3','4','5','6','7','8','9'},
    'alphanum': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0','1','2','3','4','5','6','7','8','9',
    },
}

# --- Reserved words and their expected followers ---------------------------

reserved_word_follows = {
    # Data Types
    "dear": {" ", "\t", "\n", },
    "dearest": {" ", "\t", "\n"},
    "rant": {" ", "\t", "\n"},
    "status": {" ", "\t", "\n"},
    # I/O
    "give": {" ", "\t", "\n", ">"},
    "express": {" ", "\t", "\n", "<"},
    "overshare": {" ", "\t", "\n", "("},
    # Conditionals / Loops
    "for": {" ", "\t", "\n", "("},
    "forever": {" ", "\t", "\n", "("},
    "more": {" ", "\t", "\n", "{"},
    "forevermore": {" ", "\t", "\n", "("},
    "choose": {" ", "\t", "\n", "("},
    "phase": {" ", "\t", "\n",},
    "bareminimum": {" ", "\t", "\n",":"},
    "while": {" ", "\t", "\n", "("},
    "pursue": {" ", "\t", "\n", "("},
    "moveon": {" ", "\t", "\n",";"},
    "breakup": {" ", "\t", "\n",";"},
    # Others
    "love": {" ", "\t", "\n", "("},
    "periodt": {" ", "\t", "\n",";"},
    "const": {" ", "\t", "\n"},
    "greenflag": {" ", "\t", "\n",";", ":",")"},
    "redflag": {" ", "\t", "\n",";", ":",")"},
    "boundaries": {" ", "\t", "\n"},
    "comeback": {";", "(", '"', "-", "!", " ", "\t", "\n"},
    "avoidant": {" ", "\t", "\n"},
    
}


# --- Reserved symbols and their expected followers -------------------------

reserved_symbol_follows = {
    # Arithmetic  (+ and - may be followed by unary +/-/++/--)
    "+": {" ", "\t", "\n", "alphanum", "(", "+", "-"},
    "-": {" ", "\t", "\n", "alphanum", "(", "+", "-"},
    "*": {" ", "\t", "\n", "alphanum", "(", "+", "-"},
    "/": {" ", "\t", "\n", "alphanum", "(", "+", "-"},
    "%": {" ", "\t", "\n", "alphanum", "(", "+", "-"},
    # Assignment
    "=": {" ", "\t", "\n", '"', "alphanum", "(", "{"},
    "+=": {" ", "\t", "\n", "alphanum", '"', "("},
    "-=": {" ", "\t", "\n", "alphanum", '"', "("},
    "*=": {" ", "\t", "\n", "alphanum", '"', "("},
    "/=": {" ", "\t", "\n", "alphanum", '"', "("},
    "%=": {" ", "\t", "\n", "alphanum", '"', "("},
    # Logical
    "&&": {" ", "\t", "\n", "alphanum", '"', "(", "!"},
    "||": {" ", "\t", "\n", "alphanum", '"', "(", "!"},
    "!": {" ", "\t", "\n", "alphanum"   , "("},
    # Relational
    "==": {" ", "\t", "\n", "alphanum", '"', "("},
    "!=": {" ", "\t", "\n", "alphanum", '"', "("},
    ">": {" ", "\t", "\n", "alphanum", '"', "(",},
    "<": {" ", "\t", "\n", "alphanum", '"', "("},
    ">=": {" ", "\t", "\n", "alphanum", '"', "("},
    "<=": {" ", "\t", "\n", "alphanum", '"', "("},
    # Unary (postfix produces a value; prefix can precede any factor incl. parens)
    "++": {" ", "\t", "\n", ";", ")", "(", "alphabet", "alphanum",
           "+", "-", "*", "/", "%", ",", "]", "}", "<", ">", "=", "&", "|", ".", "\0"},
    "--": {" ", "\t", "\n", ";", ")", "(", "alphabet", "alphanum",
           "+", "-", "*", "/", "%", ",", "]", "}", "<", ">", "=", "&", "|", ".", "\0"},
    # Other
    "(": {" ", "\t", "\n", "alphanum", '"', "(", "!", ")", "-"},
    ")": {" ", "\t", "\n", "{", "+", "-", "*", "/", "%", "&&", "|", ";", ".", ")", "<", ","},
    "[": {" ", "\t", "\n", "]", "alphanum", '"', "(", "+", "-"},
    "]": {" ", "\t", "\n", "=", ".", "[", ")", ",", ";", "+", "-", "*", "/", "%",},
    "{": {" ", "\t", "\n", "}", '"', "alphanum", "{", "-" },
    "}": {" ", "\t", "\n", "alphabet", "\0" , ";", ",", "}"},
    ";": {" ", "\t", "\n", "\0"},
    ":": {" ", "\t", "\n"},
    "::":{" ", "\t", "\n", "alphabet"},
    '"': {" ", "\t", "\n", ";", ")", "<", "alphanum"},
    "<<": {" ", "\t", "\n", "alphanum", '"'},
    ">>": {" ", "\t", "\n", "alphabet"},
    "/*": {" ", "\t", "\n"},
    "*/": {" ", "\t", "\n"},
    ",": {" ", "\t", "\n", "alphanum", '"'},
}



# --- Identifier followers ---------------------------------------------------

identifier_del = {
    "identifier": {
        " ", "\t", "\n",
        ";", ",", ")", "}", "(", "{", "[", "]", ":",
        "=", "+", "-", "*", "/", "%", ">", "<", "&", "|", "!",
       
    }
}

int_lit = {
    "int_lit": {
        ":", ",", ";",
        "+", "-", "*", "/", "%", "<", ">", "=", "!", "&", "|",
        ")", "}", "]",
        " ", "\t", "\n",
        
        
    },
}

string_lit = {
    "string_lit": {
    " ", "\t", "\n", 
    ";", ",", ")", "}", "]",  # Separators
    "+",                     # Concatenation 
    "==", "!=",              # Comparison 
    "<<", ":"                   # Output chaining 
},
}


# --- Utility to resolve named sets (for alphabet, digit, alphanum) ---------

def resolve_set(name: str) -> Set[str]:
    """Return the fully expanded set for special named sets."""
    if name == "alphabet":
        return set(alphabet)
    if name == "digit":
        return set(digit)
    if name == "alphanum":
        return set(alphanum)
    if name == "eof":
        return {"\0"}
    return {name}  # fallback: literal char/name


def expand_follow(raw: Iterable[str]) -> Set[str]:
    """Expand any named sets (alphabet/digit/alphanum/eof) inside followers."""
    out: Set[str] = set()
    for item in raw:
        if len(item) == 1:
            out.add(item)
        else:
            out |= resolve_set(item)
    return out


# Pre-computed expansions for direct access
expanded_reserved_word_follows = {
    word: expand_follow(spec) for word, spec in reserved_word_follows.items()
}

expanded_reserved_symbol_follows = {
    sym: expand_follow(spec) for sym, spec in reserved_symbol_follows.items()
}

expanded_identifier_follows = {
    name: expand_follow(spec) for name, spec in identifier_del.items()
}

expanded_int_lit = {name: expand_follow(spec) for name, spec in int_lit.items()}

expanded_string_lit = {name: expand_follow(spec) for name, spec in string_lit.items()}


# =============================================================================
# TOKEN DEFINITIONS
# =============================================================================
# Mappings from lexemes (source code characters) to token kinds.
# Used by Lexer for tokenization.
# =============================================================================

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
    "!": "NOT",
    "|": "BIT OR",
}


# =============================================================================
# TOKEN DISPLAY MAPPING
# =============================================================================
# Unified mapping from token kinds to human-readable display names.
# Used by both Lexer (for frontend display) and Parser (for error messages).
# =============================================================================

TOKEN_DISPLAY_NAME = {
    # Delimiters - display the actual symbol
    "LPAREN": "(",
    "RPAREN": ")",
    "LBRACE": "{",
    "RBRACE": "}",
    "LBRACKET": "[",
    "RBRACKET": "]",
    "SEMICOLON": ";",
    "COMMA": ",",
    "COLON": ":",
    "DOT": ".",
    
    # Operators - display the actual symbol
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    "PERCENT": "%",
    "ASSIGN": "=",
    "LT": "<",
    "GT": ">",
    "NOT": "!",
    "OP_EQ": "==",
    "OP_NEQ": "!=",
    "OP_LTE": "<=",
    "OP_GTE": ">=",
    "OP_AND": "&&",
    "OP_OR": "||",
    "OP_INC": "++",
    "OP_DEC": "--",
    "OP_LSHIFT": "<<",
    "OP_RSHIFT": ">>",
    "OP_PLUS_ASSIGN": "+=",
    "OP_MINUS_ASSIGN": "-=",
    "OP_MUL_ASSIGN": "*=",
    "OP_DIV_ASSIGN": "/=",
    "OP_MOD_ASSIGN": "%=",
    "OP_SCOPE": "::",
    
    # Keywords - key is lowercase (token), value is uppercase (token type)
    "love": "MAIN",
    "boundaries": "NAMESPACE",
    "const": "CONST",
    "avoidant": "VOID",
    "comeback": "RETURN",
    "dear": "INT",
    "dearest": "FLOAT",
    "rant": "STRING",
    "status": "BOOL",
    "give": "INPUT",
    "express": "OUTPUT",
    "overshare": "GETLINE",
    "forever": "IF",
    "more": "ELSE",
    "forevermore": "ELSEIF",
    "choose": "SWITCH",
    "phase": "CASE",
    "bareminimum": "DEFAULT",
    "for": "FOR",
    "while": "WHILE",
    "pursue": "DOWHILE",
    "breakup": "BREAK",
    "moveon": "CONTINUE",
    "periodt": "ENDL",
    "greenflag": "TRUE",
    "redflag": "FALSE",
    
    # Identifiers and Literals - key is lowercase (token), value is uppercase (token type)
    "id": "IDENTIFIER",
    "dear_lit": "INT_LIT",
    "dearest_lit": "FLOAT_LIT",
    "rant_lit": "STRING_LIT",   
    
    # Special token type mappings (only for transformations)
    "greenflag": "BOOL_LIT",
    "redflag": "BOOL_LIT",
    
    # Special
    "NEWLINE": "\\n",
    "EOF": "EOF",
}

