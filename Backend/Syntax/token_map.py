"""Token follow-set mappings for the Lovers language."""

from string import ascii_letters, digits, printable
from typing import Iterable, Set

# --- base character classes -------------------------------------------------

alphabet: Set[str] = set(ascii_letters)
digit: Set[str] = set(digits)
alphanum: Set[str] = alphabet | digit
# string.printable includes whitespace like "\t" and "\n"; exclude those here.
ascii_printable: Set[str] = set(printable) - {"\t", "\n"}

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

# --- named delimiter/follower sets (as declared in the spec) ----------------

def chars(items: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for it in items:
        if isinstance(it, str):
            out.add(it)
    return out


# --- Reserved words and their expected followers ---------------------------

reserved_word_follows = {
    # Data Types
    "dear": {" ", "\t", "\n"},
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
    "greenflag": {" ", "\t", "\n",";", ":"},
    "redflag": {" ", "\t", "\n",";", ":"},
    "boundaries": {" ", "\t", "\n"},
    "comeback": {";", "(", '"', "-", "!", " ", "\t", "\n"},
    "avoidant": {" ", "\t", "\n", "alphabet"},
    
}


# --- Reserved symbols and their expected followers -------------------------

reserved_symbol_follows = {
    # Arithmetic
    "+": {" ", "\t", "\n", "alphanum", '"', "("},
    "-": {" ", "\t", "\n", "alphanum", '"', "("},
    "*": {" ", "\t", "\n", "alphanum", '"', "("},
    "/": {" ", "\t", "\n", "alphanum", '"', "(",},
    "%": {" ", "\t", "\n", "alphanum", '"', "("},
    # Assignment
    "=": {" ", "\t", "\n", '"', "alphanum", "("},
    "+=": {" ", "\t", "\n", "alphanum", '"', "("},
    "-=": {" ", "\t", "\n", "alphanum", '"', "("},
    "*=": {" ", "\t", "\n", "alphanum", '"', "("},
    "/=": {" ", "\t", "\n", "alphanum", '"', "(", },
    "%=": {" ", "\t", "\n", "alphanum", '"', "("},
    # Logical
    "&&": {" ", "\t", "\n", "alphanum", '"', "(", "!"},
    "||": {" ", "\t", "\n", "alphanum", '"', "(", "!"},
    "!": {" ", "\t", "\n", "alphanum", '"', "("},
    # Relational
    "==": {" ", "\t", "\n", "alphanum", '"', "("},
    "!=": {" ", "\t", "\n", "alphanum", '"', "("},
    ">": {" ", "\t", "\n", "alphanum", '"', "(",},
    "<": {" ", "\t", "\n", "alphanum", '"', "("},
    ">=": {" ", "\t", "\n", "alphanum", '"', "("},
    "<=": {" ", "\t", "\n", "alphanum", '"', "("},
    # Unary
    "++": {" ", "\t", "\n", ";", ")", "alphanum"},
    "--": {" ", "\t", "\n", ";", ")", "alphanum"},
    # Other
    "(": {" ", "\t", "\n", "alphanum", '"', "(", "!", ")"},
    ")": {" ", "\t", "\n", "{", "+", "-", "*", "/", "%", "&&", "|", ";"},
    "[": {" ", "\t", "\n", "]"},
    "]": {" ", "\t", "\n", "=" },
    "{": {" ", "\t", "\n", "}", '"', "alphanum" },
    "}": {" ", "\t", "\n", "alphabet", "\0" , ";"},
    ";": {" ", "\t", "\n", "\0"},
    ":": {" ", "\t", "\n"},
    "::":{"alphabet"},
    '"': {" ", "\t", "\n", ";", ")", "<"},
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
        "=", "+", "-", "*", "/", "%", "!", ">", "<", "&", "|",
       
    }
}

int_lit = {
    "int_lit": {
        ":", ",", ";",
        "+", "-", "*", "/", "%", "<", ">", "=", "!", "&", "|",
        ")", "}", "]", "(",
        " ", "\t", "\n",
        '"',
        
    },
}

string_lit = {
    "string_lit": {
    " ", "\t", "\n", 
    ";", ",", ")", "}", "]",  # Separators
    "+",                     # Concatenation 
    "==", "!=",              # Comparison 
    "<<"                     # Output chaining 
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



