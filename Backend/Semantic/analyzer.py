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


def _collect_struct_types(tokens: List, errors: List[SemanticError]) -> Dict[str, Dict[str, str]]:
    # ============================================================
    # === STRUCT TYPE TABLE COLLECTION                         ===
    # ===                                                     ===
    # === Scans top-level 'struct' definitions and builds a   ===
    # === mapping: struct_types[StructName][field] = type     ===
    # === where 'type' is either a built-in (dear/dearest/    ===
    # === rant/status) or another struct name for nested      ===
    # === struct fields.                                      ===
    # ============================================================
    struct_types: Dict[str, Dict[str, str]] = {}
    i = 0
    while i < len(tokens):
        if tokens[i].kind != "struct":
            i += 1
            continue
        if i + 2 >= len(tokens) or tokens[i + 1].kind != "id" or tokens[i + 2].kind != "LBRACE":
            i += 1
            continue

        struct_name = tokens[i + 1].lexeme
        i += 3  
        fields: Dict[str, str] = {}

        while i < len(tokens) and tokens[i].kind != "RBRACE":
            
            if tokens[i].kind in TYPE_KEYWORDS:
                if i + 2 < len(tokens) and tokens[i + 1].kind == "id" and tokens[i + 2].kind == "SEMICOLON":
                    fields[tokens[i + 1].lexeme] = tokens[i].kind
                    i += 3
                    continue

            
            if tokens[i].kind == "struct":
                if i + 3 < len(tokens) and tokens[i + 1].kind == "id" and tokens[i + 2].kind == "id" and tokens[i + 3].kind == "SEMICOLON":
                    fields[tokens[i + 2].lexeme] = tokens[i + 1].lexeme
                    i += 4
                    continue

            i += 1

        
        if i < len(tokens) and tokens[i].kind == "RBRACE":
            i += 1
        if i < len(tokens) and tokens[i].kind == "SEMICOLON":
            i += 1

        struct_types[struct_name] = fields

    return struct_types

def _lookup(scopes: List[Dict[str, SymbolInfo]], name: str) -> Optional[SymbolInfo]:
    for scope in reversed(scopes):
        if name in scope:
            return scope[name]
    return None


def _is_numeric(type_name: str) -> bool:
    return type_name in {"dear", "dearest", "status"}


def _is_assignable(target_type: str, value_type: Optional[str]) -> bool:
    if value_type is None:
        return True
    if target_type == value_type:
        return True
    
    if target_type in {"dear", "dearest", "status"} and value_type in {"dear", "dearest", "status"}:
        return True
    return False


def _infer_expression_type(
    expr_tokens: List,
    scopes: List[Dict[str, SymbolInfo]],
    function_names: set,
    errors: List[SemanticError],
    struct_types: Optional[Dict[str, Dict[str, str]]] = None,
    function_returns: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    # ============================================================
    # === EXPRESSION TYPE INFERENCE                            ===
    # ===                                                     ===
    # === Given a flat list of tokens that form an expression,===
    # === best-effort infer a single resulting type:           ===
    # ===   - dear/dearest/rant/status from literals and ids   ===
    # ===   - status when logical/relational operators appear  ===
    # === Also validates function calls and struct field       ===
    # === access along the way, reporting semantic errors if   ===
    # === identifiers/functions/fields are unknown.            ===
    # ============================================================

    if not expr_tokens:
        return None

    kinds = {tok.kind for tok in expr_tokens}

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
                if function_returns and name in function_returns and function_returns[name] in TYPE_KEYWORDS:
                    observed_types.append(function_returns[name])
                i += 1
            elif (
                i + 3 < len(expr_tokens)
                and expr_tokens[i + 1].kind == "OP_SCOPE"
                and expr_tokens[i + 2].kind == "id"
                and expr_tokens[i + 3].kind == "LPAREN"
            ):
                qname = f"{tok.lexeme}::{expr_tokens[i + 2].lexeme}"
                if qname not in function_names:
                    errors.append(SemanticError(
                        message=f"Undefined function '{qname}'.",
                        line=tok.line,
                        column=tok.column,
                    ))
                if function_returns and qname in function_returns and function_returns[qname] in TYPE_KEYWORDS:
                    observed_types.append(function_returns[qname])
                i += 3
            else:
                symbol = _lookup(scopes, tok.lexeme)
                if symbol is None:
                    errors.append(SemanticError(
                        message=f"Undeclared identifier '{tok.lexeme}'.",
                        line=tok.line,
                        column=tok.column,
                    ))
                else:
                    current_type = symbol.type_name
                    j = i + 1
                    while (
                        struct_types is not None
                        and j + 1 < len(expr_tokens)
                        and expr_tokens[j].kind == "DOT"
                        and expr_tokens[j + 1].kind == "id"
                    ):
                        field_name = expr_tokens[j + 1].lexeme
                        if current_type in TYPE_KEYWORDS:
                            errors.append(SemanticError(
                                message=f"Type '{current_type}' has no fields (cannot access '{field_name}').",
                                line=expr_tokens[j].line,
                                column=expr_tokens[j].column,
                            ))
                            break
                        fields = struct_types.get(current_type)
                        if fields is None:
                            errors.append(SemanticError(
                                message=f"Unknown struct type '{current_type}'.",
                                line=expr_tokens[j].line,
                                column=expr_tokens[j].column,
                            ))
                            break
                        if field_name not in fields:
                            errors.append(SemanticError(
                                message=f"Struct '{current_type}' has no field '{field_name}'.",
                                line=expr_tokens[j + 1].line,
                                column=expr_tokens[j + 1].column,
                            ))
                            break
                        current_type = fields[field_name]
                        j += 2

                    observed_types.append(current_type)
        i += 1

    if not observed_types:
        return None

    # ============================================================
    # === LOGICAL EXPRESSION OPERAND VALIDATION                 ===
    # ===                                                       ===
    # === If the expression uses logical operators (&&, ||, !),  ===
    # === ensure no string-typed (rant) values participate.      ===
    # === We keep Option-B "truthiness" semantics: numeric and   ===
    # === status values are allowed in logical contexts.         ===
    # ============================================================
    if kinds & LOGICAL_OPS:
        if any(t == "rant" for t in observed_types):
            first_tok = next((t for t in expr_tokens if t.kind == "rant_lit"), expr_tokens[0])
            errors.append(SemanticError(
                message="Logical expressions cannot use rant operands.",
                line=first_tok.line,
                column=first_tok.column,
            ))
        return "status"

    # ============================================================
    # === ARITHMETIC OPERAND VALIDATION                        ===
    # ===                                                       ===
    # === For arithmetic operators other than PLUS, require     ===
    # === numeric operands. We allow string concatenation only  ===
    # === via PLUS; strings are invalid for -, *, /, %.         ===
    # === Option-B truthiness applies: status is numeric.       ===
    # ============================================================
    non_plus_arith = (kinds & ARITHMETIC_OPS) - {"PLUS", "OP_PLUS_ASSIGN"}
    if non_plus_arith:
        if any(t == "rant" for t in observed_types):
            first_tok = next((t for t in expr_tokens if t.kind == "rant_lit"), expr_tokens[0])
            errors.append(SemanticError(
                message="Arithmetic operators (-, *, /, %) cannot use rant (string) operands.",
                line=first_tok.line,
                column=first_tok.column,
            ))

    # Comparisons always yield status (bool-like).
    if kinds & COMPARISON_OPS:
        return "status"

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
        # Collect both global functions and namespaced functions declared inside boundaries blocks.
        # - Global: <type|avoidant> id ( ...
        # - Namespaced: boundaries NS { <type|avoidant> id ( ... }  => "NS::id"
        if tok.kind == "boundaries" and i + 3 < len(tokens) and tokens[i + 1].kind == "id" and tokens[i + 2].kind == "LBRACE":
            ns_name = tokens[i + 1].lexeme
            j = i + 3
            depth = 1
            while j < len(tokens) and depth > 0:
                if tokens[j].kind == "LBRACE":
                    depth += 1
                elif tokens[j].kind == "RBRACE":
                    depth -= 1
                # Function header inside boundaries: <type|avoidant> id (
                if depth == 1 and tokens[j].kind in TYPE_KEYWORDS.union({"avoidant"}):
                    if j + 2 < len(tokens) and tokens[j + 1].kind == "id" and tokens[j + 2].kind == "LPAREN":
                        names.add(f"{ns_name}::{tokens[j + 1].lexeme}")
                j += 1
            i = j
            continue

        if tok.kind in TYPE_KEYWORDS.union({"avoidant"}):
            if i + 2 < len(tokens) and tokens[i + 1].kind == "id" and tokens[i + 2].kind == "LPAREN":
                names.add(tokens[i + 1].lexeme)
        i += 1
    return names


def _collect_function_return_types(tokens: List) -> Dict[str, str]:
    """
    Collect function return types for both global and namespaced functions.
    Returns mapping name -> return_type, where name may be "foo" or "NS::foo".
    """
    returns: Dict[str, str] = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind == "boundaries" and i + 3 < len(tokens) and tokens[i + 1].kind == "id" and tokens[i + 2].kind == "LBRACE":
            ns_name = tokens[i + 1].lexeme
            j = i + 3
            depth = 1
            while j < len(tokens) and depth > 0:
                if tokens[j].kind == "LBRACE":
                    depth += 1
                elif tokens[j].kind == "RBRACE":
                    depth -= 1
                if depth == 1 and tokens[j].kind in TYPE_KEYWORDS.union({"avoidant"}):
                    if j + 2 < len(tokens) and tokens[j + 1].kind == "id" and tokens[j + 2].kind == "LPAREN":
                        returns[f"{ns_name}::{tokens[j + 1].lexeme}"] = tokens[j].kind
                j += 1
            i = j
            continue

        if tok.kind in TYPE_KEYWORDS.union({"avoidant"}):
            if i + 2 < len(tokens) and tokens[i + 1].kind == "id" and tokens[i + 2].kind == "LPAREN":
                returns[tokens[i + 1].lexeme] = tok.kind
        i += 1
    return returns


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
    function_returns = _collect_function_return_types(filtered)
    struct_types = _collect_struct_types(filtered, errors)

    scopes: List[Dict[str, SymbolInfo]] = [dict()]
    
    pending_function_params: Optional[List[Tuple[str, object]]] = None
    pending_function_return: Optional[str] = None
    
    function_return_stack: List[Optional[str]] = [None]

    i = 0
    while i < len(filtered):
        tok = filtered[i]

      
        if tok.kind == "struct" and i + 2 < len(filtered) and filtered[i + 1].kind == "id" and filtered[i + 2].kind == "LBRACE":
            j = i + 3
            depth = 1
            while j < len(filtered) and depth > 0:
                if filtered[j].kind == "LBRACE":
                    depth += 1
                elif filtered[j].kind == "RBRACE":
                    depth -= 1
                j += 1
            
            if j < len(filtered) and filtered[j].kind == "SEMICOLON":
                j += 1
            i = j
            continue

        if tok.kind == "LBRACE":
           
            scopes.append({})
            function_return_stack.append(function_return_stack[-1])
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
            if pending_function_return is not None:
                function_return_stack[-1] = pending_function_return
                pending_function_return = None
            i += 1
            continue

        if tok.kind == "RBRACE":
            if len(scopes) > 1:
                scopes.pop()
                function_return_stack.pop()
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

        # ============================================================
        # === CONDITION EXPRESSION VALIDATION                      ===
        # ===                                                       ===
        # === Run expression inference on loop/if conditions so we  ===
        # === can surface operand-type errors (e.g. rant in &&/||). ===
        # === We keep Option-B truthiness, so numeric/status types  ===
        # === are allowed as conditions; we only validate operands. ===
        # ============================================================
        if tok.kind in {"forever", "forevermore", "while", "pursue"} and i + 1 < len(filtered) and filtered[i + 1].kind == "LPAREN":
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
            # Condition tokens are between '(' and matching ')'
            cond_tokens = filtered[i + 2 : j]
            _infer_expression_type(cond_tokens, scopes, function_names, errors, struct_types, function_returns)
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
               
                pending_function_return = tok.kind
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

                    expr_type = _infer_expression_type(filtered[expr_start:expr_end], scopes, function_names, errors, struct_types, function_returns)
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

        
        if tok.kind == "struct":
            if (
                i + 3 < len(filtered)
                and filtered[i + 1].kind == "id"
                and filtered[i + 2].kind == "id"
                and filtered[i + 3].kind == "SEMICOLON"
            ):
                type_name = filtered[i + 1].lexeme
                var_tok = filtered[i + 2]
                current_scope = scopes[-1]

                if type_name not in struct_types:
                    errors.append(SemanticError(
                        message=f"Unknown struct type '{type_name}'.",
                        line=filtered[i + 1].line,
                        column=filtered[i + 1].column,
                    ))

                if var_tok.lexeme in current_scope:
                    errors.append(SemanticError(
                        message=f"Redeclaration of '{var_tok.lexeme}' in the same scope.",
                        line=var_tok.line,
                        column=var_tok.column,
                    ))
                else:
                    current_scope[var_tok.lexeme] = SymbolInfo(
                        name=var_tok.lexeme,
                        type_name=type_name,
                        is_const=False,
                        line=var_tok.line,
                        column=var_tok.column,
                    )
                i += 4
                continue

        # ============================================================
        # === RETURN STATEMENT TYPE CHECKING (comeback)             ===
        # ===                                                       ===
        # === Uses the current function's declared return type      ===
        # === (tracked in function_return_stack) and enforces:      ===
        # ===   - avoidant: comeback must NOT have a value          ===
        # ===   - dear/dearest/rant/status: comeback MUST have a    ===
        # ===     value that is assignable to that type.           ===
        # ============================================================
        if tok.kind == "comeback":
            current_return = function_return_stack[-1]

           
            expr_start = i + 1
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

            has_expr = expr_start < expr_end
            expr_type: Optional[str] = None
            if has_expr:
                expr_type = _infer_expression_type(filtered[expr_start:expr_end], scopes, function_names, errors, struct_types, function_returns)

            # Rules:
            # - avoidant: cannot return a value
            # - typed (dear/dearest/rant/status): must return a compatible value
            if current_return == "avoidant":
                if has_expr:
                    errors.append(SemanticError(
                        message="Void function cannot return a value.",
                        line=tok.line,
                        column=tok.column,
                    ))
            elif current_return in TYPE_KEYWORDS:
                if not has_expr:
                    errors.append(SemanticError(
                        message=f"Function must return a value of type {current_return}, but comeback has no value.",
                        line=tok.line,
                        column=tok.column,
                    ))
                elif not _is_assignable(current_return, expr_type):
                    errors.append(SemanticError(
                        message=f"Type mismatch in return: cannot return {expr_type or 'unknown'} from function of type {current_return}.",
                        line=tok.line,
                        column=tok.column,
                    ))
            

            i = expr_end + 1
            continue

        if tok.kind == "id":
            
            if i > 0 and filtered[i - 1].kind == "DOT":
                i += 1
                continue
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

            # ============================================================
            # === ARRAY INDEX SEMANTIC CHECKS (numeric index allowed)   ===
            # ===                                                         ===
            # === Walks all 'id[ ... ]' occurrences for this identifier   ===
            # === and collects each index expression slice. For every     ===
            # === slice, we infer its type and ensure it is numerically   ===
            # === usable: either 'dear' (integer) or 'status' (bool,      ===
            # === treated C-style as 0/1). Other types (dearest/rant)     ===
            # === are reported as invalid array indices.                  ===
            # ============================================================
            index_slices: List[Tuple[int, int]] = []
            while cursor + 2 < len(filtered) and filtered[cursor].kind == "LBRACKET":
                bracket_depth = 1
                index_start = cursor + 1
                cursor += 1
                while cursor < len(filtered) and bracket_depth > 0:
                    if filtered[cursor].kind == "LBRACKET":
                        bracket_depth += 1
                    elif filtered[cursor].kind == "RBRACKET":
                        bracket_depth -= 1
                    if bracket_depth == 0:
                        # index expression is [index_start:index_end]
                        index_end = cursor
                        index_slices.append((index_start, index_end))
                        break
                    cursor += 1
                cursor += 1 

           
            for start_idx, end_idx in index_slices:
                if start_idx >= end_idx:
                    continue
                index_expr_tokens = filtered[start_idx:end_idx]
                index_type = _infer_expression_type(index_expr_tokens, scopes, function_names, errors, struct_types, function_returns)
                if index_type is not None and index_type not in {"dear", "status"}:
                    first_tok = index_expr_tokens[0]
                    errors.append(SemanticError(
                        message=(
                            f"Invalid array index for '{target_tok.lexeme}': "
                           
                        ),
                        line=first_tok.line,
                        column=first_tok.column,
                    ))

           
            member_chain: List[str] = []
            while cursor + 1 < len(filtered) and filtered[cursor].kind == "DOT" and filtered[cursor + 1].kind == "id":
                member_chain.append(filtered[cursor + 1].lexeme)
                cursor += 2

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

                expr_type = _infer_expression_type(filtered[expr_start:expr_end], scopes, function_names, errors, struct_types, function_returns)

                
                target_type = symbol.type_name
                if member_chain:
                    current_type = target_type
                    for field in member_chain:
                        if current_type in TYPE_KEYWORDS:
                            errors.append(SemanticError(
                                message=f"Type '{current_type}' has no fields (cannot access '{field}').",
                                line=target_tok.line,
                                column=target_tok.column,
                            ))
                            current_type = None
                            break
                        fields = struct_types.get(current_type)
                        if fields is None:
                            errors.append(SemanticError(
                                message=f"Unknown struct type '{current_type}'.",
                                line=target_tok.line,
                                column=target_tok.column,
                            ))
                            current_type = None
                            break
                        if field not in fields:
                            errors.append(SemanticError(
                                message=f"Struct '{current_type}' has no field '{field}'.",
                                line=target_tok.line,
                                column=target_tok.column,
                            ))
                            current_type = None
                            break
                        current_type = fields[field]
                    if current_type is not None:
                        target_type = current_type

                if assign_op != "ASSIGN" and not _is_numeric(target_type):
                    errors.append(SemanticError(
                        message=(
                            f"Operator '{filtered[cursor].lexeme}' requires numeric target, "
                            f"but '{target_tok.lexeme}' is {target_type}."
                        ),
                        line=target_tok.line,
                        column=target_tok.column,
                    ))
                elif not _is_assignable(target_type, expr_type):
                    errors.append(SemanticError(
                        message=(
                            f"Type mismatch: cannot assign {expr_type or 'unknown'} to {target_type} "
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
