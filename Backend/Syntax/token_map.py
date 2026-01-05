"""Token follow-set mappings for the Lovers language."""

from string import ascii_letters, digits, printable
from typing import Iterable, Set

# --- base character classes -------------------------------------------------

alphabet: Set[str] = set(ascii_letters)
digit: Set[str] = set(digits)
alphanum: Set[str] = alphabet | digit
# string.printable includes whitespace like "\t" and "\n"; exclude those here.
ascii_printable: Set[str] = set(printable) - {"\t", "\n"}


# --- named delimiter/follower sets (as declared in the spec) ----------------

def chars(items: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for it in items:
        if isinstance(it, str):
            out.add(it)
    return out


set_defs = {
    "alphabet": {"a : z", "A : Z"},
    "digit" : {"0;", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
    "alphanum": {"alphabet", "digit"},
    "arith_op": {"+", "-", "*", "/", "%", "<", ">"},
    "space_del": {" ", "\t", "\n"},
    "give_del": {"space_del",">"},
    "express_del": {"space_del", "<"},
    "overshare_del": {"space_del", "("},
    "more_del": {"space_del", "{"},
    "phase_del": {"space_del", "digit", " ' "},
    "love_del": {"space_del", "("},
    "crement_del": {"alphabet", ";"},
    "flag_del": {";", ":"},
    "symbol_del": {"space_del", "alphanum",'"', "("},
    "equal_del": {"space_del", '"'},
    "log_del": {"space_del", "alphanum"},
    "not_del": {"space_del", "alphabet", "("},
    "rel_del": {"space_del", "alphanum"},
    "open_paren_del": {"rel_del", "!"},
    "close_paren_del": {"space_del", "{", "arith_op", "&", "|"},
    "open_brack_del": {"log_del"},
    "close_brack_del": {"space_del", "=", "<", ">"},
    "start_quote_del": {"space_del", "alphanum", "ascii"},
    "end_quote_del": {"space_del", ";", "<"},
    "express_end_del": {"rel_del", '"'},
    "give_end_del": {"space_del", "alphabet"},
    "iden_del" : {"space_del", "arith_op", "=", "&", "|", "["},
    "num_del" : {"space_del", "arith_op", "&", "|", "=", "]", "(", ")", ";"},

}


# --- Reserved words and their expected followers ---------------------------

reserved_word_follows = {
    # Data Types
    "dear": {"space_del"},
    "dearest": {"space_del"},
    "rant": {"space_del"},
    "status": {"space_del"},
    # I/O
    "give": {"give_del"},
    "express": {"express_del"},
    "overshare": {"overshare_del"},
    # Conditionals / Loops
    "for": {"overshare_del"},
    "forever": {"overshare_del"},
    "more": {"space_del", "{"},
    "forevermore": {"overshare_del"},
    "choose": {"overshare_del"},
    "phase": {"space_del", "digit", '"'},
    "bareminimum": {":"},
    "while": {"overshare_del"},
    "pursue": {"overshare_del"},
    "moveon": {";"},
    "breakup": {";"},
    # Others
    "love": {"love_del"},
    "periodt": {";"},
    "const": {"space_del"},
    "greenflag": {";", ":"},
    "redflag": {";", ":"},
    "boundaries": {"space_del"},
    "comeback": {";", "(", '"', "alphanum", "-", "!", "space_del"},
    "avoidant": {"give_end_del"},
}


# --- Reserved symbols and their expected followers -------------------------

reserved_symbol_follows = {
    # Arithmetic
    "+": {"symbol_del"},
    "-": {"symbol_del"},
    "*": {"symbol_del"},
    "/": {"symbol_del"},
    "%": {"symbol_del"},
    # Assignment
    "=": {"symbol_del", '"', "alphanum", "("},
    "+=": {"symbol_del"},
    "-=": {"symbol_del"},
    "*=": {"symbol_del"},
    "/=": {"symbol_del"},
    "%=": {"symbol_del"},
    # Logical
    "&&": {"symbol_del", "!"},
    "||": {"symbol_del", "!"},
    "!": {"symbol_del", "("},
    # Relational
    "==": {"symbol_del"},
    "!=": {"symbol_del"},
    ">": {"symbol_del"},
    "<": {"symbol_del"},
    ">=": {"symbol_del"},
    "<=": {"symbol_del"},
    # Unary
    "++": {"space_del", ";", ")"},
    "--": {"space_del", ";", ")"},
    # Other
    "(": {"symbol_del", "!", ")"},
    ")": {"space_del", "{", "arith_op", "&", "|"},
    "[": {"log_del"},
    "]": {"space_del", "=", "<", ">"},
    "{": {"space_del"},
    "}": {"space_del", "alphabet"},   
    ";": {"space_del", "eof"},
    ":": {"space_del"},
    "::":{"alphabet"},
    '"': {"ascii", "space_del", ";", ")", "<"},  # Combined
    "<<": {"symbol_del", '"'},
    ">>": {"space_del", "alphabet"},
    "/*": {"ascii"},
    "*/": {"space_del"},
}


# --- Identifier followers ---------------------------------------------------

identifier_follows = {
    "iden_del": {"iden_del"}

}

int_lit = {
    "int_lit": {"int_lit"},
}

string_lit = {
    "string_lit": {
    "space_del", 
    ";", ",", ")", "}", "]",  # Separators
    "+",                     # Concatenation 
    "==", "!=",              # Comparison 
    "<<"                     # Output chaining 
},
}


# --- Utility to expand named sets into concrete characters ------------------

def resolve_set(name: str) -> Set[str]:
    """Return the fully expanded set for a named set or a single literal."""
    if name == "alphabet":
        return set(alphabet)
    if name == "digit":
        return set(digit)
    if name == "alphanum":
        return set(alphanum)
    if name == "space_del":
        return {" ", "\t", "\n"}
    if name == "eof":
        return {"\0"}
    if name == "ascii":
        return set(ascii_printable)
    if name in set_defs:
        expanded: Set[str] = set()
        for item in set_defs[name]:
            # Recurse so nested named sets are flattened to concrete chars.
            if len(item) == 1:
                expanded.add(item)
            else:
                expanded |= resolve_set(item)
        return expanded
    return {name}  # fallback: literal char/name


def expand_follow(raw: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for item in raw:
        if len(item) == 1:
            out.add(item)
        else:
            out |= resolve_set(item)
    return out


expanded_reserved_word_follows = {
    word: expand_follow(spec) for word, spec in reserved_word_follows.items()
}

expanded_reserved_symbol_follows = {
    sym: expand_follow(spec) for sym, spec in reserved_symbol_follows.items()
}

expanded_identifier_follows = {
    name: expand_follow(spec) for name, spec in identifier_follows.items()
}

expanded_int_lit = {
    name: expand_follow(spec) for name, spec in int_lit.items()
}

expanded_string_lit = {
    name: expand_follow(spec) for name, spec in string_lit.items()
}



