"""
User-facing error messages for ICG and VM phases.

`detail` in API responses still carries the raw VM / codegen string where attached.
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
        return "Code generation stopped: no error detail was provided."
    return f"Code generation stopped: {core}"


def humanize_runtime_message(message: str) -> str:
    """Map VMError strings to short, precise explanations."""
    m = (message or "").strip()
    if not m:
        return "The program stopped before finishing."

    sym = _first_backtick_symbol(m)
    parts = m.split()

    if m.startswith("undefined symbol"):
        name = sym or "that name"
        return (
            f"`{name}` is undefined"
            "Declare it and assign a value before use, and check scope (for example inside `love()`)."
        )

    if m.startswith("missing __love_main label"):
        return (
            "No main program entry was found."
            "Define `love() { ... }` so execution has a starting point."
        )

    if m.startswith("unknown function label"):
        name = sym or "that function"
        return (
            f"No compiled function matches `{name}`."
            "Check the name, overload, and that the callee is defined with the right parameters."
        )

    if m == "RECV_PARAM outside function":
        return (
            "Internal error while setting up function parameters (parameter receive outside a function)."
            "This usually indicates a compiler bug; keep a copy of your source to report."
        )

    if m == "not enough arguments":
        return (
            "Too few arguments were passed in a function call."
            "Match the callee's parameter count and order."
        )

    if m == "return outside of frame":
        return (
            "Internal error: `comeback` ran without an active function frame."
            "Use `comeback` only inside a function body."
        )

    if m == "bad array index load":
        return (
            "The array index is out of bounds."
            "Please check the array size and index value."
        )

    if m == "bad string index load":
        return (
            "The string index is out of bounds."
            "Please use an index from 0 through length minus one."
        )

    if m == "INDEX_LOAD on non-indexable value":
        return (
            "`[]` can only be used on an array or a string."
            "Check that the variable is still an array or `rant`, not a scalar."
        )

    if m == "INDEX_STORE on non-array":
        return (
            "Assignment with `[]` requires an array on the left."
            "Declare the target as an array or assign without subscripts for scalars."
        )

    if m.startswith("MEMBER_LOAD on non-struct") or m.startswith(
        "MEMBER_STORE on non-struct"
    ):
        return (
            "`.` can only be used on a struct value."
            "Check the type of the expression before `.`."
        )

    if m.startswith("missing field"):
        field = sym or "that member"
        return (
            f"The struct has no member `{field}`."
            "Compare with the `struct` definition and fix spelling."
        )

    if m.startswith("unsupported quad op"):
        return (
            "The runtime hit an unknown instruction."
            "Rebuild or update the toolchain; if it persists, share the instruction name from the technical detail."
        )

    if m == "no activation frame":
        return (
            "Internal error: no active function call stack."
            "Execution should start from `love()`; if this repeats, report it with your source."
        )

    if m.startswith("bad string binop"):
        op = parts[-1] if len(parts) >= 3 else "this operator"
        return (
            f"The operator `{op}` is not valid for these string operands."
            "Use only supported comparisons or concatenation rules for `rant`."
        )

    if m.startswith("bad binop"):
        op = parts[-1] if len(parts) >= 3 else "this operator"
        return (
            f"The operator `{op}` is not valid for these operand types (for example int vs string)."
            "Use matching types or convert before applying the operator."
        )

    return m
