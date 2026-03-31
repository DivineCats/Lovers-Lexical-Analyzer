"""
User-facing error messages for ICG and VM phases.

Keeps raw technical text available in `detail` when callers attach it separately.
"""

from __future__ import annotations

import re
from typing import Optional

_SYM_RE = re.compile(r"`([^`]+)`")


def _first_backtick_symbol(message: str) -> Optional[str]:
    m = _SYM_RE.search(message)
    return m.group(1) if m else None


def humanize_icg_message(message: str) -> str:
    """Turn TacGenError / codegen strings into clearer validation-style text."""
    core = (message or "").strip()
    if not core:
        return "Sorry, code generation could not continue for an unknown reason."
    return f"Sorry, code generation could not continue: {core}"


def humanize_runtime_message(message: str) -> str:
    """Map VMError strings to student-friendly explanations."""
    m = (message or "").strip()
    if not m:
        return "Sorry, the program stopped because a runtime error occurred."

    sym = _first_backtick_symbol(m)

    if m.startswith("undefined symbol"):
        name = sym or "identifier"
        return (
            f"Sorry, '{name}' was used before it had a value (or the name may be misspelled). "
            "Please declare it and assign a value before using it."
        )

    if m.startswith("missing __love_main label"):
        return "Sorry, the program is missing the main entry `love() { ... }`. Please add a main block."

    if m.startswith("unknown function label"):
        name = sym or "function"
        return (
            f"Sorry, the function target '{name}' could not be found at run time. "
            "Please check the function name, overload, and that it is defined before use."
        )

    if m == "RECV_PARAM outside function":
        return (
            "Sorry, an internal runtime issue occurred while setting up function parameters. "
            "Please try again, and if this continues, report it with your source code."
        )

    if m == "not enough arguments":
        return (
            "Sorry, a function call received fewer arguments than required. "
            "Please check the number of arguments passed to that function."
        )

    if m == "return outside of frame":
        return (
            "Sorry, an internal runtime issue occurred while processing a return statement. "
            "Please try again, and if it persists, report it with your source code."
        )

    if m == "bad array index load":
        return (
            "Sorry, the array index is out of bounds (or the value being indexed is not an array). "
            "Please check the array size and index value."
        )

    if m == "bad string index load":
        return "Sorry, the string index is out of bounds. Please use an index from 0 to length-1."

    if m == "INDEX_LOAD on non-indexable value":
        return "Sorry, [] was used on a value that is not indexable. Please use a string or array."

    if m == "INDEX_STORE on non-array":
        return "Sorry, assignment with [] only works on arrays. Please check the target variable type."

    if m.startswith("MEMBER_LOAD on non-struct") or m.startswith("MEMBER_STORE on non-struct"):
        return "Sorry, member access (.) was used on a value that is not a struct."

    if m.startswith("missing field"):
        field = sym or "field"
        return f"Sorry, this struct has no member named '{field}'. Please check the struct definition and spelling."

    if m.startswith("unsupported quad op"):
        return (
            "Sorry, an internal runtime issue occurred (unknown instruction). "
            "Please try again, and report it if it continues."
        )

    if m == "no activation frame":
        return (
            "Sorry, an internal runtime issue occurred (no active function frame). "
            "Please try again, and report it if it continues."
        )

    if m.startswith("bad string binop") or m.startswith("bad binop"):
        return (
            "Sorry, this operation is not valid for the given operand types. "
            "Please check the operator and the types of both values."
        )

    return m
