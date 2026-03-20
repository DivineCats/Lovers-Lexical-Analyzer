"""
Pipeline for Lovers: lex → syntax → semantic → AST.

Execution uses TAC + `TacVM` (see `Backend.IR.exec`).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from Backend.Syntax.AST import Program


def _mangle_param_suffix(param_types: list[str]) -> str:
    if not param_types:
        return "void"
    safe = ["".join(ch if ch.isalnum() else "_" for ch in t) for t in param_types]
    return "_".join(safe)


def mangle_function(qualified_name: str, param_types: list[str]) -> str:
    q = qualified_name.replace("::", "_qn_")
    safe = "".join(ch if ch.isalnum() else "_" for ch in q)
    return f"lovers_{safe}__{_mangle_param_suffix(param_types)}"


def analyze_and_build_program(source: str) -> Tuple[Optional[Program], Optional[Dict[str, Any]]]:
    from Backend.Lexical.Lexer import LexerError, tokenize_with_errors
    from Backend.Semantic import analyze_semantics
    from Backend.Syntax import create_error_context, parse_with_errors_parserv2
    from Backend.Syntax.parsetv2 import parse_with_ast

    try:
        tokens, lex_errors = tokenize_with_errors(source)
    except LexerError as exc:
        return None, {"phase": "lexical", "message": str(exc)}
    if lex_errors:
        return None, {"phase": "lexical", "errors": list(lex_errors)}

    _, syntax_errors = parse_with_errors_parserv2(source)
    if syntax_errors:
        err = syntax_errors[0]
        return None, {
            "phase": "syntax",
            "message": err.message,
            "line": getattr(err, "line", 1),
            "column": getattr(err, "column", 1),
            "errors": [e.message for e in syntax_errors],
            "context": create_error_context(source, err.line, err.column),
        }

    sem_errors = analyze_semantics(tokens)
    if sem_errors:
        return None, {
            "phase": "semantic",
            "errors": [e.to_dict() for e in sem_errors],
            "message": sem_errors[0].message,
        }

    program, ast_errors = parse_with_ast(tokens, source_code=source)
    if ast_errors:
        return None, {"phase": "ast", "errors": [str(x) for x in ast_errors]}
    if program is None:
        return None, {"phase": "ast", "message": "AST build failed after semantic pass"}
    return program, None
