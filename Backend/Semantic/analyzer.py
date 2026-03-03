from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


TYPE_KEYWORDS = {"dear", "dearest", "rant", "status"}
ASSIGNMENT_OPS = {"ASSIGN", "OP_PLUS_ASSIGN", "OP_MINUS_ASSIGN", "OP_MUL_ASSIGN", "OP_DIV_ASSIGN", "OP_MOD_ASSIGN"}
ARITHMETIC_OPS = {"PLUS", "MINUS", "STAR", "SLASH", "PERCENT", "OP_PLUS_ASSIGN", "OP_MINUS_ASSIGN", "OP_MUL_ASSIGN", "OP_DIV_ASSIGN", "OP_MOD_ASSIGN"}
COMPARISON_OPS = {"OP_EQ", "OP_NEQ", "LT", "GT", "OP_LTE", "OP_GTE"}
LOGICAL_OPS = {"OP_AND", "OP_OR", "NOT"}


@dataclass
class SemanticError:
    message: str
    line: int
    column: int
    code: str = "ERR_SEMANTIC"

    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "code": self.code,
        }


@dataclass
class SymbolInfo:
    name: str
    type_name: str
    is_const: bool
    line: int
    column: int


def _lookup(scopes: List[Dict[str, SymbolInfo]], name: str) -> Optional[SymbolInfo]:
    for scope in reversed(scopes):
        if name in scope:
            return scope[name]
    return None


def _is_numeric(type_name: str) -> bool:
    return type_name in {"dear", "dearest"}


def _is_assignable(target_type: str, value_type: Optional[str]) -> bool:
    if value_type is None:
        return True
    if target_type == value_type:
        return True
    if target_type == "dearest" and value_type == "dear":
        return True
    return False


def _infer_expression_type(
    expr_tokens: List,
    scopes: List[Dict[str, SymbolInfo]],
    function_names: set,
    errors: List[SemanticError],
) -> Optional[str]:
    if not expr_tokens:
        return None

    kinds = {tok.kind for tok in expr_tokens}
    if kinds & LOGICAL_OPS:
        return "status"
    if kinds & COMPARISON_OPS:
        return "status"

    observed_types: List[str] = []

    i = 0
    while i < len(expr_tokens):
        tok = expr_tokens[i]

        if tok.kind == "dear_lit":
            observed_types.append("dear")
        elif tok.kind == "dearest_lit":
            observed_types.append("dearest")
        elif tok.kind == "rant_lit":
            observed_types.append("rant")
        elif tok.kind in {"greenflag", "redflag"}:
            observed_types.append("status")
        elif tok.kind == "id":
            if i + 1 < len(expr_tokens) and expr_tokens[i + 1].kind == "LPAREN":
                name = tok.lexeme
                if name not in function_names:
                    errors.append(SemanticError(
                        message=f"Undefined function '{name}'.",
                        line=tok.line,
                        column=tok.column,
                    ))
                i += 1
            else:
                symbol = _lookup(scopes, tok.lexeme)
                if symbol is None:
                    errors.append(SemanticError(
                        message=f"Undeclared identifier '{tok.lexeme}'.",
                        line=tok.line,
                        column=tok.column,
                    ))
                else:
                    observed_types.append(symbol.type_name)
        i += 1

    if not observed_types:
        return None

    if any(t == "rant" for t in observed_types):
        if "PLUS" in kinds and all(t in {"rant", "dear", "dearest", "status"} for t in observed_types):
            return "rant"
        return "rant"

    if any(t == "status" for t in observed_types):
        if kinds & ARITHMETIC_OPS:
            return None
        return "status"

    if "dearest" in observed_types:
        return "dearest"
    return "dear"


def _collect_function_names(tokens: List) -> set:
    names = set()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind in TYPE_KEYWORDS.union({"avoidant"}):
            if i + 2 < len(tokens) and tokens[i + 1].kind == "id" and tokens[i + 2].kind == "LPAREN":
                names.add(tokens[i + 1].lexeme)
        i += 1
    return names


def _parse_params(param_tokens: List) -> List[Tuple[str, object]]:
    params: List[Tuple[str, object]] = []
    i = 0
    while i < len(param_tokens):
        tok = param_tokens[i]
        if tok.kind in TYPE_KEYWORDS:
            if i + 1 < len(param_tokens) and param_tokens[i + 1].kind == "id":
                params.append((tok.kind, param_tokens[i + 1]))
                i += 2
                continue
        i += 1
    return params


def analyze_semantics(tokens: List) -> List[SemanticError]:
    """
    Perform a lightweight semantic analysis over a syntactically-valid token stream.

    Checks implemented:
    - Redeclaration in same scope
    - Undeclared identifier usage
    - Assignment to const variable
    - Undefined function calls
    - Basic type-compatibility for declarations/assignments
    """
    filtered = [t for t in tokens if getattr(t, "kind", None) not in {"NEWLINE", "EOF"}]
    errors: List[SemanticError] = []
    if not filtered:
        return errors

    function_names = _collect_function_names(filtered)

    scopes: List[Dict[str, SymbolInfo]] = [dict()]
    pending_function_params: Optional[List[Tuple[str, object]]] = None

    i = 0
    while i < len(filtered):
        tok = filtered[i]

        if tok.kind == "LBRACE":
            scopes.append({})
            if pending_function_params:
                for type_name, ident_tok in pending_function_params:
                    current_scope = scopes[-1]
                    if ident_tok.lexeme in current_scope:
                        errors.append(SemanticError(
                            message=f"Redeclaration of '{ident_tok.lexeme}' in the same scope.",
                            line=ident_tok.line,
                            column=ident_tok.column,
                        ))
                    else:
                        current_scope[ident_tok.lexeme] = SymbolInfo(
                            name=ident_tok.lexeme,
                            type_name=type_name,
                            is_const=False,
                            line=ident_tok.line,
                            column=ident_tok.column,
                        )
                pending_function_params = None
            i += 1
            continue

        if tok.kind == "RBRACE":
            if len(scopes) > 1:
                scopes.pop()
            i += 1
            continue

        if tok.kind == "boundaries":
            i += 2 if i + 1 < len(filtered) and filtered[i + 1].kind == "id" else 1
            continue

        if tok.kind == "love" and i + 1 < len(filtered) and filtered[i + 1].kind == "LPAREN":
            j = i + 2
            depth = 1
            while j < len(filtered):
                if filtered[j].kind == "LPAREN":
                    depth += 1
                elif filtered[j].kind == "RPAREN":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            pending_function_params = []
            i = j + 1
            continue

        if tok.kind in TYPE_KEYWORDS.union({"avoidant"}):
            if i + 2 < len(filtered) and filtered[i + 1].kind == "id" and filtered[i + 2].kind == "LPAREN":
                j = i + 3
                depth = 1
                while j < len(filtered):
                    if filtered[j].kind == "LPAREN":
                        depth += 1
                    elif filtered[j].kind == "RPAREN":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                pending_function_params = _parse_params(filtered[i + 3 : j])
                i = j + 1
                continue

        if tok.kind == "const" or tok.kind in TYPE_KEYWORDS:
            decl_is_const = tok.kind == "const"
            type_tok = tok
            cursor = i
            if decl_is_const:
                if i + 1 >= len(filtered) or filtered[i + 1].kind not in TYPE_KEYWORDS:
                    i += 1
                    continue
                type_tok = filtered[i + 1]
                cursor = i + 1

            declared_type = type_tok.kind
            cursor += 1

            while cursor < len(filtered):
                if filtered[cursor].kind != "id":
                    break
                ident_tok = filtered[cursor]
                current_scope = scopes[-1]

                if ident_tok.lexeme in current_scope:
                    errors.append(SemanticError(
                        message=f"Redeclaration of '{ident_tok.lexeme}' in the same scope.",
                        line=ident_tok.line,
                        column=ident_tok.column,
                    ))
                else:
                    current_scope[ident_tok.lexeme] = SymbolInfo(
                        name=ident_tok.lexeme,
                        type_name=declared_type,
                        is_const=decl_is_const,
                        line=ident_tok.line,
                        column=ident_tok.column,
                    )

                cursor += 1

                while cursor + 1 < len(filtered) and filtered[cursor].kind == "LBRACKET" and filtered[cursor + 1].kind == "RBRACKET":
                    cursor += 2

                if cursor < len(filtered) and filtered[cursor].kind == "ASSIGN":
                    expr_start = cursor + 1
                    expr_end = expr_start
                    nest = 0
                    while expr_end < len(filtered):
                        k = filtered[expr_end].kind
                        if k in {"LPAREN", "LBRACKET", "LBRACE"}:
                            nest += 1
                        elif k in {"RPAREN", "RBRACKET", "RBRACE"}:
                            nest = max(0, nest - 1)
                        if nest == 0 and k in {"COMMA", "SEMICOLON"}:
                            break
                        expr_end += 1

                    expr_type = _infer_expression_type(filtered[expr_start:expr_end], scopes, function_names, errors)
                    if not _is_assignable(declared_type, expr_type):
                        errors.append(SemanticError(
                            message=(
                                f"Type mismatch: cannot assign {expr_type or 'unknown'} to {declared_type} "
                                f"variable '{ident_tok.lexeme}'."
                            ),
                            line=ident_tok.line,
                            column=ident_tok.column,
                        ))
                    cursor = expr_end

                if cursor < len(filtered) and filtered[cursor].kind == "COMMA":
                    cursor += 1
                    continue
                break

            while cursor < len(filtered) and filtered[cursor].kind != "SEMICOLON":
                cursor += 1
            i = cursor + 1
            continue

        if tok.kind == "id":
            next_i = i + 1

            if next_i < len(filtered) and filtered[next_i].kind == "LPAREN":
                if tok.lexeme not in function_names:
                    errors.append(SemanticError(
                        message=f"Undefined function '{tok.lexeme}'.",
                        line=tok.line,
                        column=tok.column,
                    ))
                i += 1
                continue

            target_tok = tok
            cursor = next_i
            while cursor + 2 < len(filtered) and filtered[cursor].kind == "LBRACKET":
                bracket_depth = 1
                cursor += 1
                while cursor < len(filtered) and bracket_depth > 0:
                    if filtered[cursor].kind == "LBRACKET":
                        bracket_depth += 1
                    elif filtered[cursor].kind == "RBRACKET":
                        bracket_depth -= 1
                    cursor += 1

            if cursor < len(filtered) and filtered[cursor].kind in ASSIGNMENT_OPS:
                symbol = _lookup(scopes, target_tok.lexeme)
                if symbol is None:
                    errors.append(SemanticError(
                        message=f"Undeclared identifier '{target_tok.lexeme}'.",
                        line=target_tok.line,
                        column=target_tok.column,
                    ))
                    i = cursor + 1
                    continue

                if symbol.is_const:
                    errors.append(SemanticError(
                        message=f"Cannot assign to const variable '{target_tok.lexeme}'.",
                        line=target_tok.line,
                        column=target_tok.column,
                    ))

                assign_op = filtered[cursor].kind
                expr_start = cursor + 1
                expr_end = expr_start
                nest = 0
                while expr_end < len(filtered):
                    k = filtered[expr_end].kind
                    if k in {"LPAREN", "LBRACKET", "LBRACE"}:
                        nest += 1
                    elif k in {"RPAREN", "RBRACKET", "RBRACE"}:
                        nest = max(0, nest - 1)
                    if nest == 0 and k == "SEMICOLON":
                        break
                    expr_end += 1

                expr_type = _infer_expression_type(filtered[expr_start:expr_end], scopes, function_names, errors)
                if assign_op != "ASSIGN" and not _is_numeric(symbol.type_name):
                    errors.append(SemanticError(
                        message=(
                            f"Operator '{filtered[cursor].lexeme}' requires numeric target, "
                            f"but '{target_tok.lexeme}' is {symbol.type_name}."
                        ),
                        line=target_tok.line,
                        column=target_tok.column,
                    ))
                elif not _is_assignable(symbol.type_name, expr_type):
                    errors.append(SemanticError(
                        message=(
                            f"Type mismatch: cannot assign {expr_type or 'unknown'} to {symbol.type_name} "
                            f"variable '{target_tok.lexeme}'."
                        ),
                        line=target_tok.line,
                        column=target_tok.column,
                    ))

                i = expr_end + 1
                continue

            symbol = _lookup(scopes, target_tok.lexeme)
            if symbol is None:
                errors.append(SemanticError(
                    message=f"Undeclared identifier '{target_tok.lexeme}'.",
                    line=target_tok.line,
                    column=target_tok.column,
                ))

        i += 1

    dedup: Dict[Tuple[str, int, int], SemanticError] = {}
    for err in errors:
        key = (err.message, err.line, err.column)
        if key not in dedup:
            dedup[key] = err
    return list(dedup.values())
