from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple, Union

from Backend.Syntax.AST import (
    Program,
    Namespace,
    Function,
    MainFunction,
    FunctionBody,
    Declaration,
    DeclarationStatement,
    Statement,
    AssignmentStatement,
    FunctionCallStatement,
    UnaryStatement,
    InputStatement,
    InputTarget,
    OutputStatement,
    ReturnStatement,
    IfStatement,
    ElifClause,
    WhileStatement,
    DoWhileStatement,
    ForStatement,
    ForInit,
    ForUpdate,
    SwitchStatement,
    BreakStatement,
    ContinueStatement,
    CaseClause,
    Expression,
    BinaryExpression,
    UnaryExpression as ExprUnaryExpression,
    IdentifierExpression,
    MemberAccessExpression,
    SubscriptExpression,
    StructFieldDesc,
    FunctionCallExpression,
    LiteralExpression,
    ArrayLiteralExpression,
    ParenthesizedExpression,
    PostfixUpdateExpression,
    ASTNode,
)


TYPE_KEYWORDS = {"dear", "dearest", "rant", "status"}

# struct name -> (field name -> descriptor)
StructLayout = Dict[str, Dict[str, StructFieldDesc]]

# Stacked struct array fields: "__af:{rank}:{elem_type}" (internal inferred type).
_ARRAY_FIELD_PREFIX = "__af:"


def _pack_array_field_type(rank: int, elem: str) -> str:
    return f"{_ARRAY_FIELD_PREFIX}{rank}:{elem}"


def _unpack_array_field_type(t: Optional[str]) -> Optional[Tuple[int, str]]:
    if not t or not t.startswith(_ARRAY_FIELD_PREFIX):
        return None
    rest = t[len(_ARRAY_FIELD_PREFIX) :]
    col = rest.find(":")
    if col < 0:
        return None
    return int(rest[:col]), rest[col + 1 :]

# Types allowed in if / while / for / pursue conditions (C++-style truthiness).
_CONDITION_TRUTH_TYPES = {"dear", "dearest", "status"}

# Types that support ++/-- (same as typical C arithmetic / bool-as-int style).
_INCREMENTABLE_TYPES = {"dear", "dearest", "status"}


@dataclass(frozen=True)
class AnalysisContext:
    """
    Context while walking function bodies.

    - return_type: None means void (avoidant, or love() main).
    - loop_depth / switch_depth: for validating breakup / moveon placement.
    """
    return_type: Optional[str] = None
    loop_depth: int = 0
    switch_depth: int = 0


@dataclass
class SemanticError(Exception):
    """
    Semantic error that can be created either from a raw (line, column)
    or from an AST node. Existing token-based code passes explicit line/column,
    while new AST-based code can pass `node=some_ast_node`.
    """
    message: str
    line: int = 1
    column: int = 1
    code: str = "ERR_SEMANTIC"
    node: Optional[ASTNode] = None

    def to_dict(self) -> dict:
        # Prefer node position if present, otherwise fall back to stored line/column.
        line = getattr(self.node, "line", self.line) if self.node is not None else self.line
        column = getattr(self.node, "column", self.column) if self.node is not None else self.column
        return {
            "message": self.message,
            "line": line,
            "column": column,
            "code": self.code,
        }


@dataclass
class SymbolInfo:
    name: str
    type_name: str
    is_const: bool
    line: int
    column: int
    array_dimensions: int = 0
    array_shape: Optional[Tuple[int, ...]] = None


@dataclass
class FunctionInfo:
    """Collected information about a function overload."""
    fn: Function
    return_type: Optional[str]          # None for avoidant
    param_types: List[str]

def _lookup(scopes: List[Dict[str, SymbolInfo]], name: str) -> Optional[SymbolInfo]:
    for scope in reversed(scopes):
        if name in scope:
            return scope[name]
    return None


def _is_numeric(type_name: str) -> bool:
    return type_name in {"dear", "dearest", "status"}


# Inferred type for `{ ... }` when it appears as a general expression (not at declaration).
# Never assignable to scalars via `_is_assignable`.
ARRAY_LITERAL_EXPR_TYPE = "array_literal"


def _is_assignable(target_type: str, value_type: Optional[str]) -> bool:
    if value_type is None:
        return True
    if value_type == ARRAY_LITERAL_EXPR_TYPE:
        return False
    if target_type == value_type:
        return True
    if target_type in {"dear", "dearest", "status"} and value_type in {"dear", "dearest", "status"}:
        return True
    return False


def _collect_struct_types_from_program(
    program: Program,
    errors: List[SemanticError],
) -> StructLayout:
    """Build struct layout table from `Program.struct_definitions` (AST — single source)."""
    struct_types: StructLayout = {}
    for sd in program.struct_definitions:
        if sd.name in struct_types:
            errors.append(SemanticError(
                message=f"Redeclaration of struct '{sd.name}'.",
                node=sd,
            ))
            continue
        struct_types[sd.name] = dict(sd.fields)
    return struct_types


def _case_literal_type(value: Union[int, float, str]) -> str:
    """Semantic type of a `phase` literal constant."""
    if isinstance(value, bool):
        return "status"
    if isinstance(value, int):
        return "dear"
    if isinstance(value, float):
        return "dearest"
    return "rant"


def _require_bool_convertible_condition(
    condition: Optional[Expression],
    report_node: ASTNode,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """
    C++-style conditions: dear / dearest / status are OK (implicit truth test:
    zero / false vs non-zero / true). rant, array literals, struct values, etc. are not.
    """
    if condition is None:
        return
    t = _infer_expression_type_ast(
        condition,
        scopes,
        struct_types,
        function_table,
        errors,
    )
    if t is None:
        return
    if t == ARRAY_LITERAL_EXPR_TYPE:
        errors.append(SemanticError(
            message="Condition cannot be an array literal.",
            node=report_node,
        ))
        return
    if t == "rant":
        errors.append(SemanticError(
            message=(
                "Condition cannot be rant (string); use a comparison that yields status, "
                "or a numeric/boolean expression."
            ),
            node=report_node,
        ))
        return
    if t not in _CONDITION_TRUTH_TYPES:
        errors.append(SemanticError(
            message=(
                f"Condition must be dear, dearest, or status (C++-style truth value), "
                f"not '{t}'."
            ),
            node=report_node,
        ))


def _infer_rectangular_array_shape(
    declared_dims: int,
    lit: ArrayLiteralExpression,
) -> Optional[Tuple[int, ...]]:
    """
    If the literal is a perfect rectangular tensor, return (d0, d1, ...).
    Otherwise return None (jagged or empty in a way we cannot summarize).
    """
    d = max(1, declared_dims)
    if d == 1:
        return (len(lit.items),)
    if not lit.items:
        return None
    sub_shapes: List[Tuple[int, ...]] = []
    for it in lit.items:
        if not isinstance(it, ArrayLiteralExpression):
            return None
        sh = _infer_rectangular_array_shape(d - 1, it)
        if sh is None:
            return None
        sub_shapes.append(sh)
    first = sub_shapes[0]
    if any(s != first for s in sub_shapes[1:]):
        return None
    return (len(lit.items),) + first


def _try_const_int_index(
    expr: Expression,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> Optional[int]:
    """Integer value of index if it is a compile-time constant (dear/status literal, parens, unary +/-)."""
    if isinstance(expr, LiteralExpression):
        if expr.literal_type == "int":
            return int(expr.value)
        if expr.literal_type == "bool":
            return 1 if expr.value else 0
        return None
    if isinstance(expr, ParenthesizedExpression):
        return _try_const_int_index(
            expr.expression, scopes, struct_types, function_table, errors,
        )
    if isinstance(expr, ExprUnaryExpression):
        if expr.operator == "+":
            return _try_const_int_index(
                expr.operand, scopes, struct_types, function_table, errors,
            )
        if expr.operator == "-":
            inner = _try_const_int_index(
                expr.operand, scopes, struct_types, function_table, errors,
            )
            return None if inner is None else -inner
    return None


def _validate_array_index_bounds(
    sym: SymbolInfo,
    indices: List[Expression],
    errors: List[SemanticError],
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
) -> None:
    if not indices or sym.array_shape is None:
        return
    shape = sym.array_shape
    for depth, idx_expr in enumerate(indices):
        if depth >= len(shape):
            break
        bound = shape[depth]
        ci = _try_const_int_index(
            idx_expr, scopes, struct_types, function_table, errors,
        )
        if ci is None:
            continue
        if ci < 0 or ci >= bound:
            errors.append(SemanticError(
                message=(
                    f"Array index {ci} is out of bounds for dimension {depth} of '{sym.name}' "
                    f"(valid indices are 0 through {bound - 1} for this dimension)."
                ),
                node=idx_expr,
            ))


def _validate_struct_member_assignment(
    stmt: AssignmentStatement,
    sym: SymbolInfo,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """Validate obj.f1... = rhs; last field may be a fixed-size array with post_member_indices."""
    if sym.array_dimensions > 0:
        d = sym.array_dimensions
        errors.append(SemanticError(
            message=(
                f"Array '{stmt.identifier}' needs {d} subscript(s) before field access."
            ),
            node=stmt,
        ))
        return

    cur_type = sym.type_name
    path = stmt.member_path
    if not path:
        return

    layout = struct_types.get(cur_type)
    for field in path[:-1]:
        if layout is None:
            errors.append(SemanticError(
                message=(
                    f"Type '{cur_type}' is not a struct "
                    f"(cannot use field `{field}` on `{stmt.identifier}`)."
                ),
                node=stmt,
            ))
            return
        desc = layout.get(field)
        if desc is None:
            errors.append(SemanticError(
                message=f"Struct '{cur_type}' has no field '{field}'.",
                node=stmt,
            ))
            return
        if desc.array_dims != 0:
            errors.append(SemanticError(
                message=f"Field '{field}' is an array; index it before using `.member` further.",
                node=stmt,
            ))
            return
        cur_type = desc.type_name
        layout = struct_types.get(cur_type)

    if layout is None:
        errors.append(SemanticError(
            message=f"Type '{cur_type}' is not a struct (invalid member access).",
            node=stmt,
        ))
        return

    last_f = path[-1]
    desc = layout.get(last_f)
    if desc is None:
        errors.append(SemanticError(
            message=f"Struct '{cur_type}' has no field '{last_f}'.",
            node=stmt,
        ))
        return

    n_post = len(stmt.post_member_indices)
    if desc.array_dims == 0:
        if n_post > 0:
            errors.append(SemanticError(
                message=f"Field '{last_f}' is not an array; remove `[ ]` before assigning.",
                node=stmt,
            ))
            return
        elem_t = desc.type_name
    else:
        if n_post != desc.array_dims:
            errors.append(SemanticError(
                message=(
                    f"Field '{last_f}' needs {desc.array_dims} subscript(s), "
                    f"got {n_post}."
                ),
                node=stmt,
            ))
            return
        for ix_expr in stmt.post_member_indices:
            idx_type = _infer_expression_type_ast(
                ix_expr,
                scopes,
                struct_types,
                function_table,
                errors,
            )
            if idx_type is not None and idx_type not in {"dear", "status"}:
                errors.append(SemanticError(
                    message=f"Array index for '{last_f}' must be dear/status, not {idx_type}.",
                    node=ix_expr,
                ))
        elem_t = desc.type_name

    rhs_type = _infer_expression_type_ast(
        stmt.value,
        scopes,
        struct_types,
        function_table,
        errors,
    )
    if not _is_assignable(elem_t, rhs_type):
        errors.append(SemanticError(
            message=(
                f"Type mismatch: cannot assign {rhs_type or 'unknown'} "
                f"to `{'.'.join(path)}` (expected element type {elem_t})."
            ),
            node=stmt,
        ))


def _validate_assignment_indices_and_rhs(
    stmt: AssignmentStatement,
    sym: SymbolInfo,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    if stmt.member_path:
        if stmt.array_indices:
            errors.append(SemanticError(
                message="Assignment with both `[]` and `.field` on the same target is not supported.",
                node=stmt,
            ))
            return
        _validate_struct_member_assignment(
            stmt, sym, scopes, struct_types, function_table, errors,
        )
        return

    n_idx = len(stmt.array_indices)
    dims = sym.array_dimensions

    if dims == 0 and n_idx > 0:
        errors.append(SemanticError(
            message=f"Cannot subscript non-array variable '{stmt.identifier}'.",
            node=stmt,
        ))
        return

    if dims > 0 and n_idx == 0:
        errors.append(SemanticError(
            message=(
                f"Cannot assign to array '{stmt.identifier}' without indexing "
                f"({dims} subscript(s) required)."
            ),
            node=stmt,
        ))
        return

    if dims > 0 and n_idx != dims:
        errors.append(SemanticError(
            message=(
                f"Wrong number of subscripts for '{stmt.identifier}': "
                f"expected {dims}, got {n_idx}."
            ),
            node=stmt,
        ))
        # still type-check indices & rhs for more errors
    for idx_expr in stmt.array_indices:
        idx_type = _infer_expression_type_ast(
            idx_expr,
            scopes,
            struct_types,
            function_table,
            errors,
        )
        if idx_type is not None and idx_type not in {"dear", "status"}:
            errors.append(SemanticError(
                message=(
                    f"Invalid array index for '{stmt.identifier}': "
                    f"type {idx_type} is not dear/status."
                ),
                node=idx_expr,
            ))

    _validate_array_index_bounds(
        sym, stmt.array_indices, errors, scopes, struct_types, function_table,
    )

    rhs_type = _infer_expression_type_ast(
        stmt.value,
        scopes,
        struct_types,
        function_table,
        errors,
    )
    if not _is_assignable(sym.type_name, rhs_type):
        errors.append(SemanticError(
            message=(
                f"Type mismatch: cannot assign {rhs_type or 'unknown'} "
                f"to {sym.type_name} element '{stmt.identifier}'."
            ),
            node=stmt,
        ))


def _validate_input_subscripts(
    sym: SymbolInfo,
    identifier: str,
    array_indices: List[Expression],
    tgt: InputTarget,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """give >> must target a scalar slot: no indices on non-array, full indices on arrays."""
    n_idx = len(array_indices)
    dims = sym.array_dimensions

    if dims == 0 and n_idx > 0:
        errors.append(SemanticError(
            message=f"Cannot subscript non-array variable '{identifier}'.",
            node=tgt,
        ))
        return

    if dims > 0 and n_idx == 0:
        errors.append(SemanticError(
            message=(
                f"Cannot read into array '{identifier}' without indexing "
                f"({dims} subscript(s) required)."
            ),
            node=tgt,
        ))
        return

    if dims > 0 and n_idx != dims:
        errors.append(SemanticError(
            message=(
                f"Wrong number of subscripts for '{identifier}': "
                f"expected {dims}, got {n_idx}."
            ),
            node=tgt,
        ))

    for idx_expr in array_indices:
        idx_type = _infer_expression_type_ast(
            idx_expr,
            scopes,
            struct_types,
            function_table,
            errors,
        )
        if idx_type is not None and idx_type not in {"dear", "status"}:
            errors.append(SemanticError(
                message=(
                    f"Invalid array index for '{identifier}': "
                    f"type {idx_type} is not dear/status."
                ),
                node=idx_expr,
            ))

    _validate_array_index_bounds(
        sym, array_indices, errors, scopes, struct_types, function_table,
    )


def _unify_array_literal_element_types(
    item_types: List[Optional[str]],
    array_lit: ArrayLiteralExpression,
    errors: List[SemanticError],
) -> Optional[str]:
    """
    Require a common element category for all items: primitives or one struct name,
    with numeric promotion (dear/dearest/status) like arithmetic.
    """
    if not item_types:
        errors.append(SemanticError(
            message="Array literal must contain at least one element.",
            node=array_lit,
        ))
        return None

    acc: Optional[str] = None
    for t in item_types:
        if t is None:
            continue
        if t == ARRAY_LITERAL_EXPR_TYPE:
            errors.append(SemanticError(
                message="Nested array literals are invalid in this array expression.",
                node=array_lit,
            ))
            return None
        if t == "rant":
            if acc is not None and acc != "rant":
                errors.append(SemanticError(
                    message="Array literal mixes incompatible types (rant with non-rant).",
                    node=array_lit,
                ))
                return None
            acc = "rant"
            continue
        if t in {"dear", "dearest", "status"}:
            if acc == "rant" or (acc is not None and acc not in {"dear", "dearest", "status"}):
                errors.append(SemanticError(
                    message="Array literal mixes incompatible element types.",
                    node=array_lit,
                ))
                return None
            if acc is None:
                acc = t
            elif "dearest" in {acc, t}:
                acc = "dearest"
            else:
                acc = "dear"
            continue
        # struct or other named type
        if acc is not None:
            if acc in {"dear", "dearest", "status", "rant"} or acc != t:
                errors.append(SemanticError(
                    message="Array literal mixes incompatible element types.",
                    node=array_lit,
                ))
                return None
        acc = t
    if acc is None:
        errors.append(SemanticError(
            message="Could not infer a uniform element type for array literal.",
            node=array_lit,
        ))
        return None
    return acc


def _typed_return_statement_returns_value(stmt: ReturnStatement) -> bool:
    return stmt.value is not None


def _body_definitely_returns_with_value(body: FunctionBody) -> bool:
    """Whether every control-flow path through `body` executes comeback <expr> (typed fn)."""
    return _stmts_definitely_return_with_value(body.statements)


def _stmts_definitely_return_with_value(stmts: List[Statement]) -> bool:
    for stmt in stmts:
        if isinstance(stmt, DeclarationStatement):
            continue
        if isinstance(stmt, ReturnStatement):
            return _typed_return_statement_returns_value(stmt)
        if isinstance(stmt, IfStatement):
            then_returns = _body_definitely_returns_with_value(stmt.then_body)
            elifs_return = all(
                _body_definitely_returns_with_value(clause.body)
                for clause in stmt.elif_clauses
            )
            else_returns = (
                stmt.else_body is not None
                and _body_definitely_returns_with_value(stmt.else_body)
            )

            # The if-statement itself definitely returns only when every branch
            # (then / all forevermore / more) definitely returns with value.
            if then_returns and elifs_return and else_returns:
                return True
            continue
        if isinstance(stmt, WhileStatement) or isinstance(stmt, ForStatement):
            continue
        if isinstance(stmt, DoWhileStatement):
            if _body_definitely_returns_with_value(stmt.body):
                return True
            continue
        if isinstance(stmt, SwitchStatement):
            if not stmt.cases:
                continue
            cases_return = all(
                _body_definitely_returns_with_value(case.body)
                for case in stmt.cases
            )
            default_returns = (
                stmt.default_case is not None
                and _body_definitely_returns_with_value(stmt.default_case)
            )
            if cases_return and default_returns:
                return True
            continue
    return False


def analyze_semantics(tokens: List) -> List[SemanticError]:
    """
    Public entrypoint used by the rest of the system.
    Now delegates to the AST-based semantic analyzer by first building a
    Program AST via parse_with_ast, then running analyze_program_ast.
    """
    from Backend.Syntax.parsetv2 import parse_with_ast

    if not tokens:
        return []

    program, ast_errors = parse_with_ast(tokens, source_code=None)
    if ast_errors:
        # Surface AST-building issues as semantic errors for now.
        return [
            SemanticError(message=str(msg), line=1, column=1)
            for msg in ast_errors
        ]
    if program is None:
        return []

    return analyze_program_ast(program)


def analyze_program_ast(program: Program) -> List[SemanticError]:
    """
    Full AST semantic pass: structs (from `Program.struct_definitions`), symbols,
    types, control flow, overloads, choose/phase labels, and return paths.
    """
    errors: List[SemanticError] = []

    struct_types = _collect_struct_types_from_program(program, errors)

    # Collect all function overloads (global + namespaced) into a table.
    function_table: Dict[str, List[FunctionInfo]] = _collect_function_table(program, errors)

    # Scope stack: scopes[-1] is the current scope dict[name] -> SymbolInfo
    scopes: List[Dict[str, SymbolInfo]] = [dict()]

    # 1) Global declarations before love()
    for decl in program.global_declarations:
        _declare_variable_ast(decl, scopes, struct_types, function_table, errors)

    # 2) Namespaces
    for ns in program.namespaces:
        _analyze_namespace_ast(ns, scopes, struct_types, function_table, errors)

    # 3) Top-level functions
    for fn in program.sub_functions:
        _analyze_function_ast(fn, scopes, struct_types, function_table, errors)

    # 4) Main love() function
    if program.main_function is not None:
        _analyze_main_ast(program.main_function, scopes, struct_types, function_table, errors)

    return errors


def _collect_function_table(
    program: Program,
    errors: List[SemanticError],
) -> Dict[str, List[FunctionInfo]]:
    """
    Build an overload-aware function table from the AST.

    Keys are fully-qualified names:
      - Global functions: "add"
      - Namespaced functions: "Tools::add"

    Values are lists of FunctionInfo (overloads).
    """
    table: Dict[str, List[FunctionInfo]] = {}

    # Global functions
    for fn in program.sub_functions:
        key = fn.name
        info = FunctionInfo(
            fn=fn,
            return_type=fn.return_type,
            param_types=[p.data_type for p in fn.parameters],
        )
        table.setdefault(key, []).append(info)

    # Namespaced functions
    for ns in program.namespaces:
        for fn in ns.sub_functions:
            key = f"{ns.name}::{fn.name}"
            info = FunctionInfo(
                fn=fn,
                return_type=fn.return_type,
                param_types=[p.data_type for p in fn.parameters],
            )
            table.setdefault(key, []).append(info)

    return table


def _declare_variable_ast(
    decl: Declaration,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """
    Declare one or more variables from a `Declaration` (comma-separated
    `multi_declarations` share the same data type and const-ness).
    """
    if (
        decl.data_type not in {"dear", "dearest", "rant", "status"}
        and decl.data_type not in struct_types
    ):
        errors.append(SemanticError(
            message=f"Unknown type '{decl.data_type}'.",
            node=decl,
        ))
        return

    current_scope = scopes[-1]
    segments: List[Tuple[str, int, Optional[Expression], ASTNode]] = [
        (decl.identifier, decl.array_dimensions, decl.initial_value, decl),
    ]
    for md in decl.multi_declarations:
        segments.append((md.identifier, md.array_dimensions, md.initial_value, md))

    for name, dims, init, node in segments:
        if not name:
            continue

        if name in current_scope:
            errors.append(SemanticError(
                message=f"Redeclaration of '{name}' in the same scope.",
                node=node,
            ))
            continue

        shape_opt: Optional[Tuple[int, ...]] = None

        if init is None:
            current_scope[name] = SymbolInfo(
                name=name,
                type_name=decl.data_type,
                is_const=decl.is_const,
                line=getattr(node, "line", decl.line),
                column=getattr(node, "column", decl.column),
                array_dimensions=dims,
                array_shape=None,
            )
            continue

        if isinstance(init, ArrayLiteralExpression):
            _check_array_initializer_elements(
                declared_type=decl.data_type,
                declared_dims=dims,
                array_lit=init,
                decl_name=name,
                scopes=scopes,
                struct_types=struct_types,
                function_table=function_table,
                errors=errors,
            )
            if dims > 0:
                shape_opt = _infer_rectangular_array_shape(dims, init)
        else:
            value_type = _infer_expression_type_ast(
                init,
                scopes,
                struct_types,
                function_table,
                errors,
            )
            if not _is_assignable(decl.data_type, value_type):
                errors.append(SemanticError(
                    message=(
                        f"Type mismatch: cannot assign {value_type or 'unknown'} "
                        f"to {decl.data_type} variable '{name}'."
                    ),
                    node=node,
                ))

        current_scope[name] = SymbolInfo(
            name=name,
            type_name=decl.data_type,
            is_const=decl.is_const,
            line=getattr(node, "line", decl.line),
            column=getattr(node, "column", decl.column),
            array_dimensions=dims,
            array_shape=shape_opt,
        )


def _check_array_initializer_elements(
    declared_type: str,
    declared_dims: int,
    array_lit: ArrayLiteralExpression,
    decl_name: str,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """
    Validate array initializer contents element-by-element.

    - For 1D arrays (declared_dims == 1), every item in `{ ... }` must be
      assignable to `declared_type`.
    - For multi-d arrays, nested `{ ... }` must match the declared brace depth
      (declared_dims), and scalar items are validated at the innermost level.
    """
    # If dims information is missing, fall back to validating as 1D.
    dims = max(1, declared_dims)

    # Innermost level: items are scalar elements.
    if dims == 1:
        for idx, item_expr in enumerate(array_lit.items):
            if isinstance(item_expr, ArrayLiteralExpression):
                errors.append(SemanticError(
                    message=(
                        f"Array initializer element {idx} for '{decl_name}' must be a scalar "
                        f"({declared_type}), but got a nested array initializer."
                    ),
                    node=item_expr,
                ))
                continue

            item_type = _infer_expression_type_ast(
                item_expr,
                scopes,
                struct_types,
                function_table,
                errors,
            )
            if not _is_assignable(declared_type, item_type):
                errors.append(SemanticError(
                    message=(
                        f"Type mismatch in array initializer for '{decl_name}': "
                        f"element {idx} expects {declared_type}, got {item_type or 'unknown'}."
                    ),
                    node=item_expr,
                ))
        return

    # Outer levels: items must themselves be array literals.
    for idx, item_expr in enumerate(array_lit.items):
        if not isinstance(item_expr, ArrayLiteralExpression):
            errors.append(SemanticError(
                message=(
                    f"Type mismatch in array initializer for '{decl_name}': "
                    f"element {idx} expects a nested initializer for {dims}D array."
                ),
                node=item_expr,
            ))
            continue

        _check_array_initializer_elements(
            declared_type=declared_type,
            declared_dims=dims - 1,
            array_lit=item_expr,
            decl_name=decl_name,
            scopes=scopes,
            struct_types=struct_types,
            function_table=function_table,
            errors=errors,
        )


def _validate_incdec_symbol(
    sym: Optional[SymbolInfo],
    identifier: str,
    node: ASTNode,
    errors: List[SemanticError],
) -> bool:
    """
    Shared rules for ++/-- on a simple identifier (statement or for-update).
    Returns True if the operation is allowed.
    """
    if sym is None:
        errors.append(SemanticError(
            message=f"Undeclared identifier '{identifier}'.",
            node=node,
        ))
        return False
    if sym.is_const:
        errors.append(SemanticError(
            message=f"Cannot increment or decrement const variable '{identifier}'.",
            node=node,
        ))
        return False
    if sym.array_dimensions > 0:
        errors.append(SemanticError(
            message=(
                f"Cannot apply increment/decrement to array '{identifier}' "
                f"without a subscript."
            ),
            node=node,
        ))
        return False
    if sym.type_name not in _INCREMENTABLE_TYPES:
        errors.append(SemanticError(
            message=(
                f"Increment/decrement is not defined for type '{sym.type_name}' "
                f"on '{identifier}'."
            ),
            node=node,
        ))
        return False
    return True


def _analyze_for_update_ast(
    upd: ForUpdate,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    sym = _lookup(scopes, upd.identifier)
    if upd.operator in {"++", "--"}:
        _validate_incdec_symbol(sym, upd.identifier, upd, errors)
        return

    if sym is None:
        errors.append(SemanticError(
            message=f"Undeclared identifier '{upd.identifier}'.",
            node=upd,
        ))
        return
    if sym.is_const:
        errors.append(SemanticError(
            message=f"Cannot assign to const variable '{upd.identifier}' in for-update.",
            node=upd,
        ))
        return
    if upd.value is None:
        return
    rhs_type = _infer_expression_type_ast(
        upd.value,
        scopes,
        struct_types,
        function_table,
        errors,
    )
    if not _is_assignable(sym.type_name, rhs_type):
        errors.append(SemanticError(
            message=(
                f"Type mismatch in for-update: cannot assign {rhs_type or 'unknown'} "
                f"to {sym.type_name} variable '{upd.identifier}'."
            ),
            node=upd,
        ))


def _analyze_for_statement_ast(
    stmt: ForStatement,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
    ctx: AnalysisContext,
) -> None:
    """
    for-init may declare a loop variable (scoped to the whole for-statement)
    or assign to an existing variable.
    Condition/update share that scope; body is a nested block with loop depth +1.
    """
    pushed_for_scope = False
    if stmt.init is not None:
        init = stmt.init
        if init.data_type is not None:
            scopes.append({})
            pushed_for_scope = True
            fake_decl = Declaration(
                line=init.line,
                column=init.column,
                data_type=init.data_type,
                identifier=init.identifier,
                array_dimensions=0,
                initial_value=init.value,
                is_const=False,
                multi_declarations=[],
            )
            _declare_variable_ast(
                fake_decl,
                scopes,
                struct_types,
                function_table,
                errors,
            )
        else:
            sym = _lookup(scopes, init.identifier)
            if sym is None:
                errors.append(SemanticError(
                    message=f"Undeclared identifier '{init.identifier}' in for-init.",
                    node=init,
                ))
            elif sym.is_const:
                errors.append(SemanticError(
                    message=f"Cannot assign to const variable '{init.identifier}' in for-init.",
                    node=init,
                ))
            else:
                rhs_type = _infer_expression_type_ast(
                    init.value,
                    scopes,
                    struct_types,
                    function_table,
                    errors,
                )
                if not _is_assignable(sym.type_name, rhs_type):
                    errors.append(SemanticError(
                        message=(
                            f"Type mismatch in for-init: cannot assign {rhs_type or 'unknown'} "
                            f"to {sym.type_name} variable '{init.identifier}'."
                        ),
                        node=init,
                    ))

    if stmt.condition is not None:
        _require_bool_convertible_condition(
            stmt.condition,
            stmt,
            scopes,
            struct_types,
            function_table,
            errors,
        )
    if stmt.update is not None:
        _analyze_for_update_ast(
            stmt.update,
            scopes,
            struct_types,
            function_table,
            errors,
        )

    body_ctx = replace(ctx, loop_depth=ctx.loop_depth + 1)
    _analyze_body_ast(
        stmt.body,
        scopes,
        struct_types,
        function_table,
        errors,
        body_ctx,
    )

    if pushed_for_scope:
        scopes.pop()


def _analyze_namespace_ast(
    ns: Namespace,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    # Create a new scope for namespace contents.
    scopes.append({})

    for decl in ns.global_declarations:
        _declare_variable_ast(decl, scopes, struct_types, function_table, errors)

    for fn in ns.sub_functions:
        _analyze_function_ast(fn, scopes, struct_types, function_table, errors)

    scopes.pop()


def _analyze_function_ast(
    fn: Function,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    # New scope for this function's body.
    scopes.append({})

    # Parameters behave like local declarations.
    for param in fn.parameters:
        fake_decl = Declaration(
            line=param.line,
            column=param.column,
            data_type=param.data_type,
            identifier=param.identifier,
            array_dimensions=param.array_dimensions,
            initial_value=None,
            is_const=False,
            multi_declarations=[],
        )
        _declare_variable_ast(fake_decl, scopes, struct_types, function_table, errors)

    fn_ctx = AnalysisContext(return_type=fn.return_type)
    _analyze_body_ast(fn.body, scopes, struct_types, function_table, errors, fn_ctx)
    if fn.return_type is not None and not _body_definitely_returns_with_value(fn.body):
        errors.append(SemanticError(
            message=(
                f"Not all control paths return a value of type '{fn.return_type}' "
                f"in function '{fn.name}'."
            ),
            node=fn,
        ))
    scopes.pop()


def _analyze_main_ast(
    main: MainFunction,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    # Main function gets its own scope.
    scopes.append({})
    # C++-like behavior: love() may use `comeback <dear expr>` but may also omit comeback.
    # (Fall-through is handled by codegen/VM as an implicit 0.)
    main_ctx = AnalysisContext(return_type="dear")
    _analyze_body_ast(main.body, scopes, struct_types, function_table, errors, main_ctx)
    scopes.pop()


def _analyze_body_ast(
    body: FunctionBody,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
    ctx: AnalysisContext,
) -> None:
    # Each {...} body introduces a lexical scope.
    # This ensures declarations inside if/while/else/do/choose blocks
    # do not leak outside their block.
    scopes.append({})
    try:
        for stmt in body.statements:
            if isinstance(stmt, DeclarationStatement):
                _declare_variable_ast(
                    stmt.declaration, scopes, struct_types, function_table, errors
                )
            else:
                _analyze_statement_ast(
                    stmt, scopes, struct_types, function_table, errors, ctx
                )
    finally:
        scopes.pop()


def _analyze_statement_ast(
    stmt: Statement,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
    ctx: AnalysisContext,
) -> None:
    """
    Statement-level semantic checks: assignments, control flow, I/O,
    comeback typing, breakup/moveon placement, for-init/update, ++/--.
    """
    # comeback [expr];
    if isinstance(stmt, ReturnStatement):
        if ctx.return_type is None:
            if stmt.value is not None:
                errors.append(SemanticError(
                    message="avoidant (void) function cannot return a value.",
                    node=stmt,
                ))
        else:
            if stmt.value is None:
                errors.append(SemanticError(
                    message=(
                        f"comeback must provide a value of type '{ctx.return_type}' "
                        f"for this function."
                    ),
                    node=stmt,
                ))
            else:
                val_type = _infer_expression_type_ast(
                    stmt.value,
                    scopes,
                    struct_types,
                    function_table,
                    errors,
                )
                if not _is_assignable(ctx.return_type, val_type):
                    errors.append(SemanticError(
                        message=(
                            f"comeback type mismatch: cannot return {val_type or 'unknown'} "
                            f"from a function with return type '{ctx.return_type}'."
                        ),
                        node=stmt,
                    ))
        return

    # breakup;
    if isinstance(stmt, BreakStatement):
        if ctx.loop_depth == 0 and ctx.switch_depth == 0:
            errors.append(SemanticError(
                message="'breakup' is only valid inside a loop or choose statement.",
                node=stmt,
            ))
        return

    # moveon;
    if isinstance(stmt, ContinueStatement):
        if ctx.loop_depth == 0:
            errors.append(SemanticError(
                message="'moveon' is only valid inside a loop.",
                node=stmt,
            ))
        return

    # give >> id ... ; / overshare(id);
    if isinstance(stmt, InputStatement):
        for tgt in stmt.targets:
            sym = _lookup(scopes, tgt.identifier)
            if sym is None:
                errors.append(SemanticError(
                    message=f"Undeclared identifier '{tgt.identifier}'.",
                    node=tgt,
                ))
                continue
            if sym.is_const:
                errors.append(SemanticError(
                    message=f"Cannot read input into const variable '{tgt.identifier}'.",
                    node=tgt,
                ))
                continue
            _validate_input_subscripts(
                sym,
                tgt.identifier,
                tgt.array_indices,
                tgt,
                scopes,
                struct_types,
                function_table,
                errors,
            )
        return

    # ++id; id++; --id; id--;
    if isinstance(stmt, UnaryStatement):
        sym = _lookup(scopes, stmt.identifier)
        _validate_incdec_symbol(sym, stmt.identifier, stmt, errors)
        return

    # Assignments
    if isinstance(stmt, AssignmentStatement):
        sym = _lookup(scopes, stmt.identifier)
        if sym is None:
            errors.append(SemanticError(
                message=f"Undeclared identifier '{stmt.identifier}'.",
                node=stmt,
            ))
            return

        if sym.is_const:
            errors.append(SemanticError(
                message=f"Cannot assign to const variable '{stmt.identifier}'.",
                node=stmt,
            ))
            return

        _validate_assignment_indices_and_rhs(
            stmt, sym, scopes, struct_types, function_table, errors,
        )
        return

    # If / else-if / else
    if isinstance(stmt, IfStatement):
        _require_bool_convertible_condition(
            stmt.condition, stmt, scopes, struct_types, function_table, errors,
        )
        _analyze_body_ast(stmt.then_body, scopes, struct_types, function_table, errors, ctx)
        for clause in stmt.elif_clauses:
            _require_bool_convertible_condition(
                clause.condition, clause, scopes, struct_types, function_table, errors,
            )
            _analyze_body_ast(clause.body, scopes, struct_types, function_table, errors, ctx)
        if stmt.else_body is not None:
            _analyze_body_ast(stmt.else_body, scopes, struct_types, function_table, errors, ctx)
        return

    # While
    if isinstance(stmt, WhileStatement):
        _require_bool_convertible_condition(
            stmt.condition, stmt, scopes, struct_types, function_table, errors,
        )
        loop_ctx = replace(ctx, loop_depth=ctx.loop_depth + 1)
        _analyze_body_ast(stmt.body, scopes, struct_types, function_table, errors, loop_ctx)
        return

    # Do-while (pursue)
    if isinstance(stmt, DoWhileStatement):
        loop_ctx = replace(ctx, loop_depth=ctx.loop_depth + 1)
        _analyze_body_ast(stmt.body, scopes, struct_types, function_table, errors, loop_ctx)
        _require_bool_convertible_condition(
            stmt.condition, stmt, scopes, struct_types, function_table, errors,
        )
        return

    # For
    if isinstance(stmt, ForStatement):
        _analyze_for_statement_ast(
            stmt,
            scopes,
            struct_types,
            function_table,
            errors,
            ctx,
        )
        return

    # Switch (choose)
    if isinstance(stmt, SwitchStatement):
        switch_ctx = replace(ctx, switch_depth=ctx.switch_depth + 1)
        disc_t = _infer_expression_type_ast(
            stmt.expression,
            scopes,
            struct_types,
            function_table,
            errors,
        )
        if disc_t is not None:
            for case in stmt.cases:
                lit_t = _case_literal_type(case.value)
                if disc_t != lit_t:
                    errors.append(SemanticError(
                        message=(
                            f"choose discriminant has type '{disc_t}' but "
                            f"phase literal has type '{lit_t}' (must match)."
                        ),
                        node=case,
                    ))
        for case in stmt.cases:
            _analyze_body_ast(case.body, scopes, struct_types, function_table, errors, switch_ctx)
        if stmt.default_case is not None:
            _analyze_body_ast(stmt.default_case, scopes, struct_types, function_table, errors, switch_ctx)
        return

    # Output: express << value [<< value ...] [<< periodt];
    if isinstance(stmt, OutputStatement):
        for v in stmt.values:
            if isinstance(v, Expression):
                _infer_expression_type_ast(v, scopes, struct_types, function_table, errors)
        return

    # Function call as a statement
    if isinstance(stmt, FunctionCallStatement):
        name = stmt.identifier
        _ = _resolve_overload(name, stmt.arguments, stmt, scopes, struct_types, function_table, errors)
        # We don't care about the return type here; using avoidant/typed
        # functions as statements is always allowed (like C++).
        return

    # Unknown / unhandled statement kind — no-op.
    return


def _unwrap_parenthesized_expr(expr: Expression) -> Expression:
    cur: Expression = expr
    while isinstance(cur, ParenthesizedExpression):
        cur = cur.expression
    return cur


def _validate_postfix_update_operand(
    operand: Expression,
    postfix_node: PostfixUpdateExpression,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """Ensure ++/-- in expression position targets a modifiable lvalue."""
    inner = _unwrap_parenthesized_expr(operand)
    if isinstance(inner, PostfixUpdateExpression):
        errors.append(SemanticError(
            message="Cannot apply `++` / `--` directly to the result of another `++` / `--`.",
            node=postfix_node,
        ))
        return

    if isinstance(inner, IdentifierExpression):
        sym = _lookup(scopes, inner.name)
        if sym is None:
            errors.append(SemanticError(
                message=f"Undeclared identifier '{inner.name}'.",
                node=inner,
            ))
            return
        if sym.is_const:
            errors.append(SemanticError(
                message=f"Cannot apply `{postfix_node.operator}` to const variable '{inner.name}'.",
                node=postfix_node,
            ))
            return
        if inner.array_indices:
            if sym.array_dimensions <= 0:
                errors.append(SemanticError(
                    message=f"Cannot subscript non-array variable '{inner.name}' for `{postfix_node.operator}`.",
                    node=postfix_node,
                ))
                return
            elem_t = _infer_expression_type_ast(
                inner, scopes, struct_types, function_table, errors,
            )
            if elem_t is not None and elem_t not in _INCREMENTABLE_TYPES:
                errors.append(SemanticError(
                    message=(
                        f"`{postfix_node.operator}` is not defined for type '{elem_t}' "
                        f"(array element of '{inner.name}')."
                    ),
                    node=postfix_node,
                ))
            return
        _validate_incdec_symbol(sym, inner.name, postfix_node, errors)
        return

    if isinstance(inner, SubscriptExpression):
        base = inner.base
        if not isinstance(base, IdentifierExpression) or base.array_indices:
            errors.append(SemanticError(
                message=(
                    "`++` / `--` here only supports a simple variable or indexed array "
                    "(e.g. `i++` or `arr[i]++`)."
                ),
                node=postfix_node,
            ))
            return
        sym = _lookup(scopes, base.name)
        if sym is None:
            errors.append(SemanticError(
                message=f"Undeclared identifier '{base.name}'.",
                node=base,
            ))
            return
        if sym.is_const:
            errors.append(SemanticError(
                message=f"Cannot apply `{postfix_node.operator}` to const variable '{base.name}'.",
                node=postfix_node,
            ))
            return
        elem_t = _infer_expression_type_ast(
            inner, scopes, struct_types, function_table, errors,
        )
        if elem_t is not None and elem_t not in _INCREMENTABLE_TYPES:
            errors.append(SemanticError(
                message=(
                    f"`{postfix_node.operator}` is not defined for type '{elem_t}' "
                    f"(indexed value)."
                ),
                node=postfix_node,
            ))
        return

    errors.append(SemanticError(
        message="Operand of `++` / `--` must be a variable or array element.",
        node=postfix_node,
    ))


def _infer_expression_type_ast(
    expr: Expression,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> Optional[str]:
    """
    Infer the type of an expression.

    Handles literals, identifiers (with array indices), parenthesized expressions,
    unary operators, binary operators, member access, function calls, and
    array literals. Array literals yield the sentinel type `ARRAY_LITERAL_EXPR_TYPE`
    (not assignable to scalars via `_is_assignable`).
    """
    if expr is None:
        return None

    # Literals
    if isinstance(expr, LiteralExpression):
        if expr.literal_type == "int":
            return "dear"
        if expr.literal_type == "float":
            return "dearest"
        if expr.literal_type == "string":
            return "rant"
        if expr.literal_type == "bool":
            return "status"
        return None

    # Identifier
    if isinstance(expr, IdentifierExpression):
        sym = _lookup(scopes, expr.name)
        if sym is None:
            errors.append(SemanticError(
                message=f"Undeclared identifier '{expr.name}'.",
                node=expr,
            ))
            return None

        # Array / string index type checks: each index must be dear or status.
        for idx_expr in expr.array_indices:
            idx_type = _infer_expression_type_ast(idx_expr, scopes, struct_types, function_table, errors)
            if idx_type is not None and idx_type not in {"dear", "status"}:
                errors.append(SemanticError(
                    message=(
                        f"Invalid array index for '{expr.name}': "
                        f"index type {idx_type or 'unknown'} is not dear/status."
                    ),
                    node=idx_expr,
                ))

        if expr.array_indices:
            if sym.type_name == "rant":
                if len(expr.array_indices) > 1:
                    errors.append(SemanticError(
                        message=f"String '{expr.name}' supports only one index dimension.",
                        node=expr,
                    ))
                # Character result is still modeled as rant.
                return "rant"
            if sym.array_dimensions <= 0:
                errors.append(SemanticError(
                    message=f"Cannot subscript non-array variable '{expr.name}'.",
                    node=expr,
                ))
                return None
            _validate_array_index_bounds(
                sym, expr.array_indices, errors, scopes, struct_types, function_table,
            )
        return sym.type_name

    # Parenthesized
    if isinstance(expr, ParenthesizedExpression):
        return _infer_expression_type_ast(expr.expression, scopes, struct_types, function_table, errors)

    # Unary expression
    if isinstance(expr, ExprUnaryExpression):
        op = expr.operator
        t = _infer_expression_type_ast(expr.operand, scopes, struct_types, function_table, errors)
        if op == "!":
            if t == "rant":
                errors.append(SemanticError(
                    message="Logical negation cannot be applied to rant (string).",
                    node=expr,
                ))
            return "status"
        if op in {"+", "-"}:
            if t == "rant":
                errors.append(SemanticError(
                    message=f"Unary '{op}' cannot be applied to rant (string).",
                    node=expr,
                ))
            return t
        # Other unary operators (e.g. ++/--) are not expected in pure expressions here.
        return t

    # Binary expression
    if isinstance(expr, BinaryExpression):
        op = expr.operator
        left_type = _infer_expression_type_ast(expr.left, scopes, struct_types, function_table, errors)
        right_type = _infer_expression_type_ast(expr.right, scopes, struct_types, function_table, errors)

        # Logical operators: &&, ||
        if op in {"&&", "||"}:
            if left_type == "rant" or right_type == "rant":
                errors.append(SemanticError(
                    message="Logical expressions cannot use rant (string) operands.",
                    node=expr,
                ))
            return "status"

        # Comparison operators
        if op in {"==", "!=", "<", ">", "<=", ">="}:
            # Optional: add stricter compatibility rules later.
            return "status"

        # Arithmetic operators
        if op in {"+", "-", "*", "/", "%"}:
            # Non-plus arithmetic: forbid rant operands.
            if op in {"-", "*", "/", "%"}:
                if left_type == "rant" or right_type == "rant":
                    errors.append(SemanticError(
                        message="Arithmetic operators (-, *, /, %) cannot use rant (string) operands.",
                        node=expr,
                    ))
            # Plus: concatenation if any operand is rant.
            if op == "+" and (left_type == "rant" or right_type == "rant"):
                return "rant"

            numeric_types = {"dear", "dearest", "status"}
            if left_type not in numeric_types or right_type not in numeric_types:
                # If one side is unknown, we can't infer a precise result.
                return None

            # If any side is dearest, promote to dearest.
            if "dearest" in {left_type, right_type}:
                return "dearest"
            # Status participates as numeric; we keep result as dear for arithmetic.
            if "status" in {left_type, right_type}:
                return "dear"
            # Otherwise both are dear.
            return "dear"

        # Unknown binary operator kind.
        return None

    # Member access: base.member (potentially chained via nested MemberAccessExpression)
    if isinstance(expr, MemberAccessExpression):
        base_type = _infer_expression_type_ast(expr.object, scopes, struct_types, function_table, errors)
        if base_type is None:
            return None

        if _unpack_array_field_type(base_type) is not None:
            errors.append(SemanticError(
                message=f"Cannot use `.{expr.member}` on an array value; index with `[` first.",
                node=expr,
            ))
            return None

        # Primitive types have no fields.
        if base_type in TYPE_KEYWORDS:
            errors.append(SemanticError(
                message=f"Type '{base_type}' has no fields; cannot access '.{expr.member}'.",
                node=expr,
            ))
            return None

        fields = struct_types.get(base_type)
        if fields is None:
            errors.append(SemanticError(
                message=f"Unknown struct type '{base_type}' in member access '.{expr.member}'.",
                node=expr,
            ))
            return None

        fdesc = fields.get(expr.member)
        if fdesc is None:
            errors.append(SemanticError(
                message=f"Struct '{base_type}' has no field '{expr.member}'.",
                node=expr,
            ))
            return None

        if fdesc.array_dims == 0:
            return fdesc.type_name
        return _pack_array_field_type(fdesc.array_dims, fdesc.type_name)

    if isinstance(expr, SubscriptExpression):
        base_type = _infer_expression_type_ast(expr.base, scopes, struct_types, function_table, errors)
        if base_type is None:
            return None

        idx_type = _infer_expression_type_ast(
            expr.index, scopes, struct_types, function_table, errors,
        )
        if idx_type is not None and idx_type not in {"dear", "status"}:
            errors.append(SemanticError(
                message=f"Array subscript must be dear/status, not {idx_type}.",
                node=expr.index,
            ))

        unpacked = _unpack_array_field_type(base_type)
        if unpacked is not None:
            rank, elem = unpacked
            if rank <= 1:
                return elem
            return _pack_array_field_type(rank - 1, elem)

        if base_type in TYPE_KEYWORDS:
            return base_type

        errors.append(SemanticError(
            message=f"Cannot apply `[` `]` to non-array value of type '{base_type}'.",
            node=expr,
        ))
        return None

    # Function call in expression
    if isinstance(expr, FunctionCallExpression):
        # Builtin: length(rant) -> dear
        if expr.namespace is None and expr.identifier == "length":
            if len(expr.arguments) != 1:
                errors.append(SemanticError(
                    message="Builtin 'length' expects exactly one argument.",
                    node=expr,
                ))
                return None
            arg_t = _infer_expression_type_ast(
                expr.arguments[0], scopes, struct_types, function_table, errors
            )
            if arg_t != "rant":
                errors.append(SemanticError(
                    message=f"Builtin 'length' expects rant, got {arg_t or 'unknown'}.",
                    node=expr,
                ))
                return None
            return "dear"

        name = expr.identifier  # already fully qualified like "Tools::triple" if needed
        info = _resolve_overload(name, expr.arguments, expr, scopes, struct_types, function_table, errors)
        if info is None:
            return None

        # Avoidant (void) functions are not allowed in expressions.
        if info.return_type is None:
            errors.append(SemanticError(
                message=f"Cannot use avoidant function '{name}' as a value.",
                node=expr,
            ))
            return None

        return info.return_type

    # Array literal `{ e1, e2, ... }` in expression position
    if isinstance(expr, ArrayLiteralExpression):
        item_types = [
            _infer_expression_type_ast(item, scopes, struct_types, function_table, errors)
            for item in expr.items
        ]
        _unify_array_literal_element_types(item_types, expr, errors)
        return ARRAY_LITERAL_EXPR_TYPE

    if isinstance(expr, PostfixUpdateExpression):
        _validate_postfix_update_operand(
            expr.operand,
            expr,
            scopes,
            struct_types,
            function_table,
            errors,
        )
        inner_e = _unwrap_parenthesized_expr(expr.operand)
        return _infer_expression_type_ast(
            inner_e, scopes, struct_types, function_table, errors,
        )

    return None


def _resolve_overload(
    name: str,
    arg_exprs: List[Expression],
    call_node: ASTNode,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: StructLayout,
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> Optional[FunctionInfo]:
    """
    Resolve a function overload using a simplified C++-style approach:
    - Require an exact arity match.
    - Require each parameter type to be assignable from the argument type.
    - If multiple viable overloads remain, report ambiguity.
    """
    overloads = function_table.get(name)
    if not overloads:
        errors.append(SemanticError(
            message=f"Undefined function '{name}'.",
            node=call_node,
        ))
        return None

    # Infer argument types once.
    arg_types: List[Optional[str]] = [
        _infer_expression_type_ast(arg, scopes, struct_types, function_table, errors)
        for arg in arg_exprs
    ]

    # Filter by arity.
    candidates = [fi for fi in overloads if len(fi.param_types) == len(arg_types)]
    if not candidates:
        expected_counts = sorted({len(fi.param_types) for fi in overloads})
        counts_txt = ", ".join(str(n) for n in expected_counts)
        errors.append(SemanticError(
            message=(
                f"Function '{name}' was called with {len(arg_types)} argument(s), "
                f"but available overloads expect: [{counts_txt}]. "
                "Add or remove arguments to match a definition."
            ),
            node=call_node,
        ))
        return None

    def is_viable(fi: FunctionInfo) -> bool:
        return all(
            _is_assignable(p_type, a_type)
            for p_type, a_type in zip(fi.param_types, arg_types)
        )

    viable = [fi for fi in candidates if is_viable(fi)]
    if not viable:
        errors.append(SemanticError(
            message=f"No overload of '{name}' matches the argument types.",
            node=call_node,
        ))
        return None

    if len(viable) > 1:
        errors.append(SemanticError(
            message=f"Ambiguous call to overloaded function '{name}'.",
            node=call_node,
        ))
        return None

    return viable[0]
