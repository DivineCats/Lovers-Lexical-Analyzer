"""
Lightweight syntax analyzer facade.

For now this just wraps the lexer to surface lexical errors in a parser-like
shape so the editor can show errors without a full grammar parse.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from Backend.Lexical import tokenize_with_errors, tokens_as_rows


def analyze(
    code: str,
    pre_analyzed_tokens: Optional[Iterable[dict]] = None,
    lexical_errors: Optional[List[dict]] = None,
) -> Tuple[bool, Any]:
    """
    Returns (ok, payload). If lexical errors are provided or discovered, returns
    a structured error payload. Otherwise returns (True, tokens) as a placeholder
    until a full parser is wired up.
    """
    # If caller already supplied lexical errors, surface the first one.
    if lexical_errors:
        first = lexical_errors[0]
        return False, {
            "message": first.get("message"),
            "rawMessage": first.get("message"),
            "expected": [],
            "unexpected": "invalid token",
            "line": first.get("line"),
            "column": first.get("column"),
            "value": "",
            "type": "lexical",
            "keywords": [],
            "literals": [],
            "symbols": [],
            "others": [],
            "isEndOfInput": False,
        }

    tokens = list(pre_analyzed_tokens) if pre_analyzed_tokens is not None else None
    errors: List[str] = []

    if tokens is None:
        toks, errs = tokenize_with_errors(code)
        tokens = toks
        errors = errs or []

    if errors:
        # Use the first lexical error. Line/column are embedded in the message string.
        return False, {
            "message": errors[0],
            "rawMessage": errors[0],
            "expected": [],
            "unexpected": "invalid token",
            "line": None,
            "column": None,
            "value": "",
            "type": "lexical",
            "keywords": [],
            "literals": [],
            "symbols": [],
            "others": [],
            "isEndOfInput": False,
        }

    # Placeholder success: echo tokens for now
    return True, tokens_as_rows(tokens)


if __name__ == "__main__":
    import sys

    src = sys.stdin.read()
    ok, payload = analyze(src)
    if ok:
        print("OK")
        for row in payload:
            print(row)
    else:
        print("ERROR")
        print(payload)
