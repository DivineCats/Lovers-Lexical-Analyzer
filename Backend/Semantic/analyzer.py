from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from Backend.Syntax.AST import (
    Program,
    Namespace,
    Function,
    MainFunction,
    FunctionBody,
    Declaration,
    Statement,
    AssignmentStatement,
    FunctionCallStatement,
    UnaryStatement,
    InputStatement,
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
    FunctionCallExpression,
    LiteralExpression,
    ArrayLiteralExpression,
    ParenthesizedExpression,
    ASTNode,
)


TYPE_KEYWORDS = {"dear", "dearest", "rant", "status"}


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


def _is_assignable(target_type: str, value_type: Optional[str]) -> bool:
    if value_type is None:
        return True
    if target_type == value_type:
        return True
    if target_type in {"dear", "dearest", "status"} and value_type in {"dear", "dearest", "status"}:
        return True
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

    # Collect struct type information from the original tokens.
    struct_types = _collect_struct_types(tokens)

    return analyze_program_ast(program, struct_types)


def analyze_program_ast(
    program: Program,
    struct_types: Dict[str, Dict[str, str]],
) -> List[SemanticError]:
    """
    AST-based semantic analyzer.

    Initial responsibilities:
    - Build symbol tables from declarations (globals, locals, parameters)
    - Report redeclaration in the same scope

    You can extend this incrementally with:
    - Undeclared identifier checks
    - Const assignment checks
    - Type compatibility for declarations/assignments
    - Function calls, returns, structs, arrays, etc.
    """
    errors: List[SemanticError] = []

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


def _collect_struct_types(tokens: List) -> Dict[str, Dict[str, str]]:
    """
    Build a struct type table from top-level `struct` definitions:
      struct_types[StructName][field] = type_name
    where type_name is either a primitive (dear/dearest/rant/status)
    or another struct name (for nested struct fields).
    """
    struct_types: Dict[str, Dict[str, str]] = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind != "struct" or i + 2 >= len(tokens):
            i += 1
            continue

        # struct Name { ... };
        if tokens[i + 1].kind != "id" or tokens[i + 2].kind != "LBRACE":
            i += 1
            continue

        struct_name = tokens[i + 1].lexeme
        fields: Dict[str, str] = {}
        i += 3  # skip 'struct Name {'

        while i < len(tokens) and tokens[i].kind != "RBRACE":
            # Primitive field: dear x;
            if tokens[i].kind in TYPE_KEYWORDS:
                if (
                    i + 2 < len(tokens)
                    and tokens[i + 1].kind == "id"
                    and tokens[i + 2].kind == "SEMICOLON"
                ):
                    fields[tokens[i + 1].lexeme] = tokens[i].kind
                    i += 3
                    continue

            # Nested struct field: struct Address addr;
            if tokens[i].kind == "struct":
                if (
                    i + 3 < len(tokens)
                    and tokens[i + 1].kind == "id"
                    and tokens[i + 2].kind == "id"
                    and tokens[i + 3].kind == "SEMICOLON"
                ):
                    fields[tokens[i + 2].lexeme] = tokens[i + 1].lexeme
                    i += 4
                    continue

            i += 1

        # Skip closing brace and optional semicolon
        if i < len(tokens) and tokens[i].kind == "RBRACE":
            i += 1
        if i < len(tokens) and tokens[i].kind == "SEMICOLON":
            i += 1

        struct_types[struct_name] = fields

    return struct_types


def _declare_variable_ast(
    decl: Declaration,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """
    Declare a variable in the given scope, reporting redeclaration errors.
    This handles the primary identifier on a Declaration; you can extend it
    later to also handle decl.multi_declarations.
    """
    current_scope = scopes[-1]
    name = decl.identifier
    if not name:
        return

    if name in current_scope:
        errors.append(SemanticError(
            message=f"Redeclaration of '{name}' in the same scope.",
            node=decl,
        ))
        return

    current_scope[name] = SymbolInfo(
        name=name,
        type_name=decl.data_type,
        is_const=decl.is_const,
        line=decl.line,
        column=decl.column,
    )

    # If there is an initializer, type-check it against the declared type.
    if decl.initial_value is not None:
        # Array initializer needs per-element validation (C++ style).
        if isinstance(decl.initial_value, ArrayLiteralExpression):
            _check_array_initializer_elements(
                declared_type=decl.data_type,
                declared_dims=decl.array_dimensions,
                array_lit=decl.initial_value,
                decl_name=name,
                scopes=scopes,
                struct_types=struct_types,
                function_table=function_table,
                errors=errors,
            )
        else:
            value_type = _infer_expression_type_ast(
                decl.initial_value,
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
                    node=decl,
                ))


def _check_array_initializer_elements(
    declared_type: str,
    declared_dims: int,
    array_lit: ArrayLiteralExpression,
    decl_name: str,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
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


def _analyze_namespace_ast(
    ns: Namespace,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
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
    struct_types: Dict[str, Dict[str, str]],
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

    _analyze_body_ast(fn.body, scopes, struct_types, function_table, errors)
    scopes.pop()


def _analyze_main_ast(
    main: MainFunction,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    # Main function gets its own scope.
    scopes.append({})
    _analyze_body_ast(main.body, scopes, struct_types, function_table, errors)
    scopes.pop()


def _analyze_body_ast(
    body: FunctionBody,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    # Declarations at top of the block in the current scope.
    for decl in body.local_declarations:
        _declare_variable_ast(decl, scopes, struct_types, function_table, errors)

    # Statements will be analyzed incrementally as you add checks.
    for stmt in body.statements:
        _analyze_statement_ast(stmt, scopes, struct_types, function_table, errors)


def _analyze_statement_ast(
    stmt: Statement,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> None:
    """
    Statement-level semantic checks.

    Current responsibilities:
    - Assignments: const assignment + basic type compatibility
    - Conditions: run expression inference for logical/arithmetic checks
      in if/while/do-while/for and switch.

    You can extend this later for:
    - function calls
    - returns
    - switch/case body rules, etc.
    """
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

        rhs_type = _infer_expression_type_ast(stmt.value, scopes, struct_types, function_table, errors)
        if not _is_assignable(sym.type_name, rhs_type):
            errors.append(SemanticError(
                message=(
                    f"Type mismatch: cannot assign {rhs_type or 'unknown'} "
                    f"to {sym.type_name} variable '{stmt.identifier}'."
                ),
                node=stmt,
            ))
        return

    # If / else-if / else
    if isinstance(stmt, IfStatement):
        _infer_expression_type_ast(stmt.condition, scopes, struct_types, function_table, errors)
        _analyze_body_ast(stmt.then_body, scopes, struct_types, function_table, errors)
        for clause in stmt.elif_clauses:
            _infer_expression_type_ast(clause.condition, scopes, struct_types, function_table, errors)
            _analyze_body_ast(clause.body, scopes, struct_types, function_table, errors)
        if stmt.else_body is not None:
            _analyze_body_ast(stmt.else_body, scopes, struct_types, function_table, errors)
        return

    # While
    if isinstance(stmt, WhileStatement):
        _infer_expression_type_ast(stmt.condition, scopes, struct_types, function_table, errors)
        _analyze_body_ast(stmt.body, scopes, struct_types, function_table, errors)
        return

    # Do-while (pursue)
    if isinstance(stmt, DoWhileStatement):
        _analyze_body_ast(stmt.body, scopes, struct_types, function_table, errors)
        _infer_expression_type_ast(stmt.condition, scopes, struct_types, function_table, errors)
        return

    # For
    if isinstance(stmt, ForStatement):
        # For now, only validate the condition expression if present.
        if stmt.condition is not None:
            _infer_expression_type_ast(stmt.condition, scopes, struct_types, function_table, errors)
        _analyze_body_ast(stmt.body, scopes, struct_types, function_table, errors)
        return

    # Switch (choose)
    if isinstance(stmt, SwitchStatement):
        _infer_expression_type_ast(stmt.expression, scopes, struct_types, function_table, errors)
        # Case/default bodies are regular FunctionBody instances.
        for case in stmt.cases:
            _analyze_body_ast(case.body, scopes, struct_types, function_table, errors)
        if stmt.default_case is not None:
            _analyze_body_ast(stmt.default_case, scopes, struct_types, function_table, errors)
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

    # Other statement types (I/O, unary inc/dec, etc.) have no expression
    # semantics wired yet; they can be handled later as needed.
    return


def _infer_expression_type_ast(
    expr: Expression,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
    function_table: Dict[str, List[FunctionInfo]],
    errors: List[SemanticError],
) -> Optional[str]:
    """
    AST-based expression type inference.

    Current responsibilities:
    - Literals: dear/dearest/rant/status
    - Identifiers: lookup in scopes, report undeclared usage
    - Unary '!': forbid rant, result is status
    - Binary logical (&&, ||): forbid rant operands, result is status
    - Binary comparisons (==, !=, <, >, <=, >=): result is status
    - Binary arithmetic (+, -, *, /, %):
        - For -, *, /, %: forbid rant operands
        - For +: support rant concatenation if any operand is rant
        - Numeric result type: dear/dearest/status based on operands

    This function can be extended later to handle:
    - FunctionCallExpression
    - MemberAccessExpression
    - ArrayLiteralExpression
    - ParenthesizedExpression
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

        # Array index type checks: each index must be dear or status.
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

        field_type = fields.get(expr.member)
        if field_type is None:
            errors.append(SemanticError(
                message=f"Struct '{base_type}' has no field '{expr.member}'.",
                node=expr,
            ))
            return None

        return field_type

    # Function call in expression
    if isinstance(expr, FunctionCallExpression):
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

    # Other expression kinds (calls, member access, arrays) will be handled later.
    return None


def _resolve_overload(
    name: str,
    arg_exprs: List[Expression],
    call_node: ASTNode,
    scopes: List[Dict[str, SymbolInfo]],
    struct_types: Dict[str, Dict[str, str]],
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
        errors.append(SemanticError(
            message=f"No overload of '{name}' matches {len(arg_types)} argument(s).",
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
