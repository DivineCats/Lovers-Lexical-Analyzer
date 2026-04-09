from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union


# =============================================================================
# AST NODE CLASSES (shared across parsers)
# =============================================================================


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 1
    column: int = 1


# =============================================================================
# Program Structure
# =============================================================================


@dataclass
class StructFieldDesc(ASTNode):
    """One field in a struct: scalar or fixed-size array (sizes are int literals per dimension)."""

    type_name: str = ""  # element type: primitive or struct name
    array_dims: int = 0
    shape: Tuple[Optional[int], ...] = field(default_factory=tuple)  # length array_dims; None = unspecified `[]`


@dataclass
class StructDefinition(ASTNode):
    """struct Name { fields }; — fields map: member name -> StructFieldDesc."""
    name: str = ""
    fields: Dict[str, StructFieldDesc] = field(default_factory=dict)


@dataclass
class Program(ASTNode):
    """
    Root node for Lovers program:
      <program> -> <top_decls_opt> love ( ) { <body_func> } [ ; ]

    - All top-level declarations before `love` (variables, consts, functions, namespaces)
      are represented in the lists below.
    """
    # Top-level `struct` definitions (before `love`)
    struct_definitions: List["StructDefinition"] = field(default_factory=list)
    # All top-level namespaces created via `boundaries id { ... }`
    namespaces: List["Namespace"] = field(default_factory=list)
    # Top-level (non-namespace) variable / const declarations before `love`
    global_declarations: List["Declaration"] = field(default_factory=list)
    # Top-level functions before `love` (both typed and `avoidant`/void)
    sub_functions: List["Function"] = field(default_factory=list)
    main_function: Optional["MainFunction"] = None


@dataclass
class Namespace(ASTNode):
    """Namespace: boundaries id { ... }"""
    name: str = ""
    global_declarations: List["Declaration"] = field(default_factory=list)
    sub_functions: List["Function"] = field(default_factory=list)


@dataclass
class MainFunction(ASTNode):
    """Main function: love() { body_func } [optional `;`]."""
    body: "FunctionBody" = None


# =============================================================================
# Declarations
# =============================================================================


@dataclass
class Declaration(ASTNode):
    """Variable declaration: data_type id [array_decl] [= expr] [multi_decl];"""
    data_type: str = ""  # "dear", "dearest", "rant", "status", or a struct name
    identifier: str = ""
    array_dimensions: int = 0  # Number of [] pairs
    initial_value: Optional["Expression"] = None
    is_const: bool = False
    multi_declarations: List["MultiDeclaration"] = field(default_factory=list)


@dataclass
class MultiDeclaration(ASTNode):
    """Multiple declarations: , id [array_decl] [= expr]"""
    identifier: str = ""
    array_dimensions: int = 0
    initial_value: Optional["Expression"] = None


# =============================================================================
# Functions
# =============================================================================


@dataclass
class Function(ASTNode):
    """Function: return_type id (parameters) { body_func } [optional `;`]."""
    return_type: Optional[str] = None  # None for "avoidant" (void)
    name: str = ""
    parameters: List["Parameter"] = field(default_factory=list)
    body: "FunctionBody" = None


@dataclass
class Parameter(ASTNode):
    """Function parameter: data_type id [array_decl]"""
    data_type: str = ""
    identifier: str = ""
    array_dimensions: int = 0


@dataclass
class FunctionBody(ASTNode):
    """Function body: ordered block items (use `statements`; locals via DeclarationStatement)."""
    local_declarations: List["Declaration"] = field(default_factory=list)
    statements: List["Statement"] = field(default_factory=list)


# =============================================================================
# Statements
# =============================================================================


@dataclass
class Statement(ASTNode):
    """Base class for all statements."""
    pass


@dataclass
class DeclarationStatement(Statement):
    """Local declaration as a block item (may appear after other statements)."""
    declaration: Optional[Declaration] = None


@dataclass
class AssignmentStatement(Statement):
    """Assignment: id [index_array] [. field]* [ [expr] ]* assign_op expr;"""
    identifier: str = ""
    array_indices: List["Expression"] = field(default_factory=list)
    member_path: List[str] = field(default_factory=list)
    post_member_indices: List["Expression"] = field(default_factory=list)
    operator: str = "="  # "=", "+=", "-=", "*=", "/=", "%="
    value: "Expression" = None


@dataclass
class FunctionCallStatement(Statement):
    """Function call: id [::id] (arguments);"""
    identifier: str = ""
    namespace: Optional[str] = None
    arguments: List["Expression"] = field(default_factory=list)


@dataclass
class UnaryStatement(Statement):
    """Unary operation: ++id; or --id; or id++; or id--;"""
    operator: str = ""  # "++" or "--"
    identifier: str = ""
    is_prefix: bool = True  # True for ++x, False for x++


@dataclass
class InputTarget(ASTNode):
    """One destination in give >> id [subs] >> id ... ;"""

    identifier: str = ""
    array_indices: List["Expression"] = field(default_factory=list)


@dataclass
class InputStatement(Statement):
    """Input: give >> id [ [expr] ] ( >> id [ [expr] ] )* ; or overshare(id);"""
    method: str = ""  # "give" or "overshare"
    targets: List[InputTarget] = field(default_factory=list)


@dataclass
class OutputStatement(Statement):
    """Output: express << value [<< value ...] [<< periodt];"""
    values: List[Union["Expression", str]] = field(default_factory=list)  # str for "periodt"


@dataclass
class ReturnStatement(Statement):
    """Return: comeback [expr];"""
    value: Optional["Expression"] = None


@dataclass
class IfStatement(Statement):
    """If: forever (expr) { body } [forevermore ...] [more { body }]"""
    condition: "Expression" = None
    then_body: "FunctionBody" = None
    elif_clauses: List["ElifClause"] = field(default_factory=list)
    else_body: Optional["FunctionBody"] = None


@dataclass
class ElifClause(ASTNode):
    """Else-if: forevermore (expr) { body }"""
    condition: "Expression" = None
    body: "FunctionBody" = None


@dataclass
class WhileStatement(Statement):
    """While: while (expr) { body }"""
    condition: "Expression" = None
    body: "FunctionBody" = None


@dataclass
class DoWhileStatement(Statement):
    """Do-while: pursue (expr) { body }"""
    condition: "Expression" = None
    body: "FunctionBody" = None


@dataclass
class ForStatement(Statement):
    """For: for (init; condition; update) { body }"""
    init: Optional["ForInit"] = None
    condition: Optional["Expression"] = None
    update: Optional["ForUpdate"] = None
    body: "FunctionBody" = None


@dataclass
class ForInit(ASTNode):
    """For initialization: [data_type] id = expr"""
    data_type: Optional[str] = None
    identifier: str = ""
    value: "Expression" = None


@dataclass
class ForUpdate(ASTNode):
    """For update: id assign_op expr | id unary_op | unary_op id"""
    identifier: str = ""
    operator: str = ""  # "=", "+=", "-=", "*=", "/=", "%=", "++", "--"
    value: Optional["Expression"] = None  # None for unary operations
    is_prefix: bool = True  # For unary operations


@dataclass
class SwitchStatement(Statement):
    """Switch: choose (expr) { phase ... [bareminimum ...] }"""
    expression: "Expression" = None
    cases: List["CaseClause"] = field(default_factory=list)
    default_case: Optional["FunctionBody"] = None


@dataclass
class BreakStatement(Statement):
    """Break: breakup; (used inside choose/phase/bareminimum bodies conceptually)."""
    pass


@dataclass
class ContinueStatement(Statement):
    """Continue: moveon; (used inside loops)."""
    pass


@dataclass
class CaseClause(ASTNode):
    """Case: phase const : body breakup;"""
    value: Union[int, float, str] = None  # Literal value
    body: "FunctionBody" = None


# =============================================================================
# Expressions
# =============================================================================


@dataclass
class Expression(ASTNode):
    """Base class for all expressions."""
    pass


@dataclass
class BinaryExpression(Expression):
    """Binary operation: left op right"""
    operator: str = ""
    left: "Expression" = None
    right: "Expression" = None


@dataclass
class UnaryExpression(Expression):
    """Unary operation: op expr"""
    operator: str = ""
    operand: "Expression" = None


@dataclass
class IdentifierExpression(Expression):
    """Identifier: id [index_array]"""
    name: str = ""
    array_indices: List["Expression"] = field(default_factory=list)


@dataclass
class MemberAccessExpression(Expression):
    """Member access: expr . id (supports chaining)."""
    object: "Expression" = None
    member: str = ""


@dataclass
class SubscriptExpression(Expression):
    """Postfix subscript: base [ index ] (left-associative; chain for multi-index)."""
    base: "Expression" = None
    index: "Expression" = None


@dataclass
class FunctionCallExpression(Expression):
    """Function call in expression: id [::id] (arguments)"""
    identifier: str = ""
    namespace: Optional[str] = None
    arguments: List["Expression"] = field(default_factory=list)


@dataclass
class LiteralExpression(Expression):
    """Literal: int, float, string, or bool"""
    value: Union[int, float, str, bool] = None
    literal_type: str = ""  # "int", "float", "string", "bool"


@dataclass
class ArrayLiteralExpression(Expression):
    """Array literal: { expr (, expr)* }"""
    items: List["Expression"] = field(default_factory=list)


@dataclass
class ParenthesizedExpression(Expression):
    """Parenthesized: (expr)"""
    expression: "Expression" = None


# =============================================================================
# AST BUILDING (recursive-descent, used after LL(1) validation)
# =============================================================================


DATA_TYPES = {"dear", "dearest", "rant", "status"}
BOOL_LITS = {"greenflag", "redflag"}

ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%="}
UNARY_OPS = {"++", "--"}

_PREC: dict[str, int] = {
    "||": 1,
    "&&": 2,
    "==": 3,
    "!=": 3,
    "<": 4,
    ">": 4,
    "<=": 4,
    ">=": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "/": 6,
    "%": 6,
}


@dataclass(frozen=True)
class AstBuildError(Exception):
    message: str
    line: int = 1
    column: int = 1

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.message} (line {self.line}, col {self.column})"


class RecursiveDescentAstBuilder:
    """
    Builds a full Lovers AST from a token list produced by `Backend.Lexical.Lexer`.

    Constraints enforced:
    - Declarations can appear only at the top of a block.
    - `choose/phase` requires explicit `breakup;` inside each `phase` body (and default).
    - Qualified calls like `Tools::triple()` are represented as a single qualified name
      in the AST (stored in `identifier`, with `namespace=None`).
    """

    def __init__(self, tokens: Sequence[object]):
        # The lexer emits `NEWLINE` tokens (token display: "\\n"). The LL(1) parser
        # ignores them; AST building should do the same.
        self.tokens = [t for t in tokens if getattr(t, "token", getattr(t, "kind", "")) != "\\n"]
        self.i = 0

    # -------------------------
    # token helpers
    # -------------------------
    def _tok(self, offset: int = 0):
        idx = self.i + offset
        if idx < 0:
            idx = 0
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def _kind(self, offset: int = 0) -> str:
        t = self._tok(offset)
        return getattr(t, "token", getattr(t, "kind", "EOF"))

    def _lexeme(self, offset: int = 0) -> str:
        return getattr(self._tok(offset), "lexeme", "")

    def _pos(self, offset: int = 0) -> Tuple[int, int]:
        t = self._tok(offset)
        return int(getattr(t, "line", 1)), int(getattr(t, "column", 1))

    def _at_end(self) -> bool:
        return self._kind() == "EOF"

    def _match(self, *kinds: str) -> bool:
        if self._kind() in kinds:
            self.i += 1
            return True
        return False

    def _expect(self, kind: str, msg: str):
        if self._kind() != kind:
            line, col = self._pos()
            raise AstBuildError(f"{msg}. Expected `{kind}`, found `{self._kind()}`", line, col)
        t = self._tok()
        self.i += 1
        return t

    def _expect_any(self, kinds: Sequence[str], msg: str):
        if self._kind() not in kinds:
            line, col = self._pos()
            raise AstBuildError(f"{msg}. Expected one of {list(kinds)}, found `{self._kind()}`", line, col)
        t = self._tok()
        self.i += 1
        return t

    def _optional_top_func_semicolon(self) -> None:
        """Optional `;` after top-level `love()` / function `}` (CFG `<optional_top_func_semi>`)."""
        self._match(";")

    # -------------------------
    # entry
    # -------------------------
    def parse_program(self) -> Program:
        line, col = self._pos()
        structs: List[StructDefinition] = []
        namespaces: List[Namespace] = []
        globals_: List[Declaration] = []
        subs: List[Function] = []

        while self._kind() != "love" and not self._at_end():
            if self._kind() == "struct" and self._kind(1) == "id" and self._kind(2) == "{":
                structs.append(self._parse_struct_definition())
                continue
            if self._kind() == "boundaries":
                namespaces.append(self._parse_namespace())
                continue
            if self._kind() in ("avoidant",) or self._kind() in DATA_TYPES:
                # Could be function or global declaration.
                # Look ahead: type/avoidant id '(' => function, else declaration.
                if self._kind() == "avoidant":
                    subs.append(self._parse_function())
                else:
                    if self._kind(2) == "(":
                        subs.append(self._parse_function())
                    else:
                        globals_.append(self._parse_declaration(require_semicolon=True))
                continue
            if self._kind() == "const":
                globals_.append(self._parse_declaration(require_semicolon=True))
                continue

            l, c = self._pos()
            raise AstBuildError(f"Unexpected token at top-level: `{self._kind()}`", l, c)

        main = self._parse_main()
        return Program(
            line=line,
            column=col,
            struct_definitions=structs,
            namespaces=namespaces,
            global_declarations=globals_,
            sub_functions=subs,
            main_function=main,
        )

    # -------------------------
    # top-level constructs
    # -------------------------
    def _parse_struct_definition(self) -> StructDefinition:
        st_tok = self._expect("struct", "Expected `struct`")
        name_tok = self._expect("id", "Expected struct name")
        self._expect("{", "Expected `{` to start struct body")
        fields: Dict[str, StructFieldDesc] = {}
        while self._kind() != "}" and not self._at_end():
            if self._kind() in DATA_TYPES:
                ty = self._expect_any(sorted(DATA_TYPES), "Expected field type")
                fid = self._expect("id", "Expected field name")
                adims, shape = self._parse_struct_field_array_spec()
                self._expect(";", "Expected `;` after struct field")
                if fid.lexeme in fields:
                    line, col = self._pos()
                    raise AstBuildError(f"Duplicate field '{fid.lexeme}' in struct '{name_tok.lexeme}'", line, col)
                fields[fid.lexeme] = StructFieldDesc(
                    line=fid.line,
                    column=fid.column,
                    type_name=ty.token,
                    array_dims=adims,
                    shape=shape,
                )
            elif self._kind() == "struct":
                self._expect("struct", "Expected `struct` for nested field")
                inner = self._expect("id", "Expected nested struct type name")
                fid = self._expect("id", "Expected field name")
                adims, shape = self._parse_struct_field_array_spec()
                self._expect(";", "Expected `;` after struct field")
                if fid.lexeme in fields:
                    line, col = self._pos()
                    raise AstBuildError(f"Duplicate field '{fid.lexeme}' in struct '{name_tok.lexeme}'", line, col)
                fields[fid.lexeme] = StructFieldDesc(
                    line=fid.line,
                    column=fid.column,
                    type_name=inner.lexeme,
                    array_dims=adims,
                    shape=shape,
                )
            else:
                line, col = self._pos()
                raise AstBuildError(
                    f"Expected field declaration in struct body, found `{self._kind()}`",
                    line,
                    col,
                )
        self._expect("}", "Expected `}` to end struct body")
        self._expect(";", "Expected `;` after struct definition")
        return StructDefinition(
            line=st_tok.line,
            column=st_tok.column,
            name=name_tok.lexeme,
            fields=fields,
        )

    def _parse_namespace(self) -> Namespace:
        kw = self._expect("boundaries", "Expected `boundaries`")
        name_tok = self._expect("id", "Expected namespace name")
        self._expect("{", "Expected `{` to start namespace body")

        decls: List[Declaration] = []
        funcs: List[Function] = []

        while self._kind() != "}" and not self._at_end():
            if self._kind() == "const" or self._kind() in DATA_TYPES:
                if self._kind() != "const" and self._kind(2) == "(":
                    funcs.append(self._parse_function())
                else:
                    decls.append(self._parse_declaration(require_semicolon=True))
                continue
            if self._kind() == "avoidant":
                funcs.append(self._parse_function())
                continue
            l, c = self._pos()
            raise AstBuildError(f"Unexpected token in namespace: `{self._kind()}`", l, c)

        self._expect("}", "Expected `}` to end namespace")
        return Namespace(line=kw.line, column=kw.column, name=name_tok.lexeme, global_declarations=decls, sub_functions=funcs)

    def _parse_main(self) -> MainFunction:
        love_tok = self._expect("love", "Expected `love` main function")
        self._expect("(", "Expected `(` after `love`")
        self._expect(")", "Expected `)` after `love(`")
        body = self._parse_block_body()
        self._optional_top_func_semicolon()
        return MainFunction(line=love_tok.line, column=love_tok.column, body=body)

    def _parse_function(self) -> Function:
        if self._kind() == "avoidant":
            rt_tok = self._expect("avoidant", "Expected `avoidant`")
            return_type: Optional[str] = None
            start_line, start_col = rt_tok.line, rt_tok.column
        else:
            rt = self._expect_any(sorted(DATA_TYPES), "Expected return type")
            return_type = rt.token
            start_line, start_col = rt.line, rt.column

        name_tok = self._expect("id", "Expected function name")
        self._expect("(", "Expected `(` after function name")
        params = self._parse_parameters()
        self._expect(")", "Expected `)` after parameters")
        body = self._parse_block_body()
        self._optional_top_func_semicolon()
        return Function(line=start_line, column=start_col, return_type=return_type, name=name_tok.lexeme, parameters=params, body=body)

    def _parse_parameters(self) -> List[Parameter]:
        params: List[Parameter] = []
        if self._kind() == ")":
            return params
        while True:
            ty = self._expect_any(sorted(DATA_TYPES), "Expected parameter type")
            name_tok = self._expect("id", "Expected parameter name")
            dims = self._parse_array_dims_count()
            params.append(Parameter(line=ty.line, column=ty.column, data_type=ty.token, identifier=name_tok.lexeme, array_dimensions=dims))
            if not self._match(","):
                break
        return params

    # -------------------------
    # blocks, declarations, statements
    # -------------------------
    def _parse_block_body(self) -> FunctionBody:
        lbrace = self._expect("{", "Expected `{` to start block")
        stmts: List[Statement] = []

        while self._kind() != "}" and not self._at_end():
            if self._kind() == "struct" and self._kind(2) != "{":
                decl = self._parse_struct_local_declaration()
                stmts.append(
                    DeclarationStatement(
                        line=decl.line,
                        column=decl.column,
                        declaration=decl,
                    )
                )
            elif self._kind() in ("const",) or self._kind() in DATA_TYPES:
                decl = self._parse_declaration(require_semicolon=True)
                stmts.append(
                    DeclarationStatement(
                        line=decl.line,
                        column=decl.column,
                        declaration=decl,
                    )
                )
            else:
                stmts.append(self._parse_statement())

        self._expect("}", "Expected `}` to end block")
        return FunctionBody(line=lbrace.line, column=lbrace.column, local_declarations=[], statements=stmts)

    def _parse_struct_local_declaration(self) -> Declaration:
        """Local struct instance: struct TypeName varName; (not a struct definition)."""
        st_tok = self._expect("struct", "Expected `struct`")
        type_tok = self._expect("id", "Expected struct type name")
        id_tok = self._expect("id", "Expected variable name")
        self._expect(";", "Expected `;` after struct variable declaration")
        return Declaration(
            line=st_tok.line,
            column=st_tok.column,
            data_type=type_tok.lexeme,
            identifier=id_tok.lexeme,
            array_dimensions=0,
            initial_value=None,
            is_const=False,
            multi_declarations=[],
        )

    def _parse_declaration(self, require_semicolon: bool) -> Declaration:
        is_const = self._match("const")
        ty = self._expect_any(sorted(DATA_TYPES), "Expected data type")
        id_tok = self._expect("id", "Expected identifier")
        dims = self._parse_array_dims_count()
        init: Optional[Expression] = None

        if self._match("="):
            if self._kind() == "{":
                init = self._parse_array_literal()
            else:
                init = self._parse_expression()

        multi: List[MultiDeclaration] = []
        while self._match(","):
            mid = self._expect("id", "Expected identifier after `,`")
            mdims = self._parse_array_dims_count()
            minit: Optional[Expression] = None
            if self._match("="):
                if self._kind() == "{":
                    minit = self._parse_array_literal()
                else:
                    minit = self._parse_expression()
            multi.append(MultiDeclaration(line=mid.line, column=mid.column, identifier=mid.lexeme, array_dimensions=mdims, initial_value=minit))

        if require_semicolon:
            self._expect(";", "Expected `;` after declaration")

        return Declaration(
            line=ty.line,
            column=ty.column,
            data_type=ty.token,
            identifier=id_tok.lexeme,
            array_dimensions=dims,
            initial_value=init,
            is_const=is_const,
            multi_declarations=multi,
        )

    def _parse_statement(self) -> Statement:
        k = self._kind()

        if k == "breakup":
            t = self._expect("breakup", "Expected `breakup`")
            self._expect(";", "Expected `;` after breakup")
            return BreakStatement(line=t.line, column=t.column)
        if k == "moveon":
            t = self._expect("moveon", "Expected `moveon`")
            self._expect(";", "Expected `;` after moveon")
            return ContinueStatement(line=t.line, column=t.column)
        if k == "comeback":
            t = self._expect("comeback", "Expected `comeback`")
            if self._match(";"):
                return ReturnStatement(line=t.line, column=t.column, value=None)
            val = self._parse_expression()
            self._expect(";", "Expected `;` after comeback value")
            return ReturnStatement(line=t.line, column=t.column, value=val)
        if k == "give":
            t = self._expect("give", "Expected `give`")
            targets: List[InputTarget] = []
            self._expect(">>", "Expected `>>` after give")
            while True:
                name = self._expect("id", "Expected identifier after `>>`")
                indices = self._parse_index_list()
                targets.append(
                    InputTarget(
                        line=name.line,
                        column=name.column,
                        identifier=name.lexeme,
                        array_indices=indices,
                    )
                )
                if not self._match(">>"):
                    break
            self._expect(";", "Expected `;` after input statement")
            return InputStatement(line=t.line, column=t.column, method="give", targets=targets)
        if k == "overshare":
            t = self._expect("overshare", "Expected `overshare`")
            self._expect("(", "Expected `(` after overshare")
            name = self._expect("id", "Expected identifier in overshare()")
            self._expect(")", "Expected `)` after overshare identifier")
            self._expect(";", "Expected `;` after overshare()")
            return InputStatement(
                line=t.line,
                column=t.column,
                method="overshare",
                targets=[
                    InputTarget(
                        line=name.line,
                        column=name.column,
                        identifier=name.lexeme,
                        array_indices=[],
                    )
                ],
            )
        if k == "express":
            t = self._expect("express", "Expected `express`")
            values: List[Union[Expression, str]] = []
            self._expect("<<", "Expected `<<` after express")
            while True:
                if self._kind() == "periodt":
                    p = self._expect("periodt", "Expected `periodt`")
                    values.append(p.token)
                else:
                    values.append(self._parse_expression())
                if not self._match("<<"):
                    break
            self._expect(";", "Expected `;` after express statement")
            return OutputStatement(line=t.line, column=t.column, values=values)

        if k == "forever":
            return self._parse_if()
        if k == "while":
            return self._parse_while()
        if k == "pursue":
            return self._parse_do_while()
        if k == "for":
            return self._parse_for()
        if k == "choose":
            return self._parse_choose()

        if k in UNARY_OPS:
            op = self._expect_any(sorted(UNARY_OPS), "Expected unary op")
            name = self._expect("id", "Expected identifier after unary op")
            self._expect(";", "Expected `;` after unary statement")
            return UnaryStatement(line=op.line, column=op.column, operator=op.token, identifier=name.lexeme, is_prefix=True)

        if k == "id":
            head_tok = self._expect("id", "Expected identifier")
            qualified = head_tok.lexeme
            while self._match("::"):
                part = self._expect("id", "Expected identifier after `::`")
                qualified = f"{qualified}::{part.lexeme}"

            if self._kind() == "(":
                args = self._parse_call_arguments()
                self._expect(";", "Expected `;` after function call")
                return FunctionCallStatement(line=head_tok.line, column=head_tok.column, identifier=qualified, namespace=None, arguments=args)

            if self._kind() in UNARY_OPS:
                op = self._expect_any(sorted(UNARY_OPS), "Expected unary op")
                self._expect(";", "Expected `;` after unary statement")
                return UnaryStatement(line=head_tok.line, column=head_tok.column, operator=op.token, identifier=qualified, is_prefix=False)

            indices: List[Expression] = []
            if self._kind() == "[":
                if "::" in qualified:
                    l, c = self._pos()
                    raise AstBuildError("Qualified name cannot be indexed with `[]`", l, c)
                indices = self._parse_index_list()

            member_path: List[str] = []
            while self._kind() == ".":
                if "::" in qualified:
                    l, c = self._pos()
                    raise AstBuildError("Qualified name cannot use `.` member access", l, c)
                self._expect(".", "Expected `.`")
                mem = self._expect("id", "Expected field name after `.`")
                member_path.append(mem.lexeme)

            post_member_indices: List[Expression] = []
            if member_path and self._kind() == "[":
                post_member_indices = self._parse_index_list()

            if self._kind() in ASSIGN_OPS:
                op = self._expect_any(sorted(ASSIGN_OPS), "Expected assignment operator")
                value = self._parse_expression()
                self._expect(";", "Expected `;` after assignment")
                return AssignmentStatement(
                    line=head_tok.line,
                    column=head_tok.column,
                    identifier=qualified,
                    array_indices=indices,
                    member_path=member_path,
                    post_member_indices=post_member_indices,
                    operator=op.token,
                    value=value,
                )

            l, c = self._pos()
            raise AstBuildError("Expected function call, unary op, or assignment after identifier", l, c)

        l, c = self._pos()
        raise AstBuildError(f"Unexpected start of statement: `{k}`", l, c)

    def _parse_if(self) -> IfStatement:
        t = self._expect("forever", "Expected `forever`")
        self._expect("(", "Expected `(` after forever")
        cond = self._parse_expression()
        self._expect(")", "Expected `)` after condition")
        then_body = self._parse_block_body()

        elifs: List[ElifClause] = []
        while self._kind() == "forevermore":
            et = self._expect("forevermore", "Expected `forevermore`")
            self._expect("(", "Expected `(` after forevermore")
            econd = self._parse_expression()
            self._expect(")", "Expected `)` after condition")
            ebody = self._parse_block_body()
            elifs.append(ElifClause(line=et.line, column=et.column, condition=econd, body=ebody))

        else_body: Optional[FunctionBody] = None
        if self._kind() == "more":
            self._expect("more", "Expected `more`")
            else_body = self._parse_block_body()

        return IfStatement(line=t.line, column=t.column, condition=cond, then_body=then_body, elif_clauses=elifs, else_body=else_body)

    def _parse_while(self) -> WhileStatement:
        t = self._expect("while", "Expected `while`")
        self._expect("(", "Expected `(` after while")
        cond = self._parse_expression()
        self._expect(")", "Expected `)` after condition")
        body = self._parse_block_body()
        return WhileStatement(line=t.line, column=t.column, condition=cond, body=body)

    def _parse_do_while(self) -> DoWhileStatement:
        t = self._expect("pursue", "Expected `pursue`")
        self._expect("(", "Expected `(` after pursue")
        cond = self._parse_expression()
        self._expect(")", "Expected `)` after condition")
        body = self._parse_block_body()
        return DoWhileStatement(line=t.line, column=t.column, condition=cond, body=body)

    def _parse_for(self) -> ForStatement:
        t = self._expect("for", "Expected `for`")
        self._expect("(", "Expected `(` after for")

        init: Optional[ForInit] = None
        if self._kind() != ";":
            data_type: Optional[str] = None
            if self._kind() in DATA_TYPES:
                dt = self._expect_any(sorted(DATA_TYPES), "Expected data type in for-init")
                data_type = dt.token
                line, col = dt.line, dt.column
            else:
                line, col = self._pos()
            name = self._expect("id", "Expected identifier in for-init")
            self._expect("=", "Expected `=` in for-init")
            val = self._parse_expression()
            init = ForInit(line=line, column=col, data_type=data_type, identifier=name.lexeme, value=val)

        self._expect(";", "Expected `;` after for-init")

        cond: Optional[Expression] = None
        if self._kind() != ";":
            cond = self._parse_expression()
        self._expect(";", "Expected `;` after for-condition")

        update: Optional[ForUpdate] = None
        if self._kind() != ")":
            if self._kind() in UNARY_OPS:
                op = self._expect_any(sorted(UNARY_OPS), "Expected unary op")
                name = self._expect("id", "Expected id after unary op")
                update = ForUpdate(line=op.line, column=op.column, identifier=name.lexeme, operator=op.token, value=None, is_prefix=True)
            else:
                name = self._expect("id", "Expected id in for-update")
                if self._kind() in UNARY_OPS:
                    op = self._expect_any(sorted(UNARY_OPS), "Expected unary op")
                    update = ForUpdate(line=name.line, column=name.column, identifier=name.lexeme, operator=op.token, value=None, is_prefix=False)
                else:
                    op = self._expect_any(sorted(ASSIGN_OPS), "Expected assignment op in for-update")
                    val = self._parse_expression()
                    update = ForUpdate(line=name.line, column=name.column, identifier=name.lexeme, operator=op.token, value=val, is_prefix=True)

        self._expect(")", "Expected `)` after for-update")
        body = self._parse_block_body()
        return ForStatement(line=t.line, column=t.column, init=init, condition=cond, update=update, body=body)

    def _parse_choose(self) -> SwitchStatement:
        t = self._expect("choose", "Expected `choose`")
        self._expect("(", "Expected `(` after choose")
        expr = self._parse_expression()
        self._expect(")", "Expected `)` after choose expr")
        self._expect("{", "Expected `{` to start choose body")

        cases: List[CaseClause] = []
        default_body: Optional[FunctionBody] = None

        while self._kind() == "phase":
            pt = self._expect("phase", "Expected `phase`")
            lit = self._parse_case_literal()
            self._expect(":", "Expected `:` after phase literal")
            body = self._parse_case_body_require_breakup()
            cases.append(CaseClause(line=pt.line, column=pt.column, value=lit, body=body))

        if self._kind() == "bareminimum":
            self._expect("bareminimum", "Expected `bareminimum`")
            self._expect(":", "Expected `:` after bareminimum")
            default_body = self._parse_case_body_require_breakup()

        self._expect("}", "Expected `}` to end choose")
        return SwitchStatement(line=t.line, column=t.column, expression=expr, cases=cases, default_case=default_body)

    def _parse_case_body_require_breakup(self) -> FunctionBody:
        start_line, start_col = self._pos()
        stmts: List[Statement] = []

        while not (self._kind() == "breakup" or self._at_end()):
            if self._kind() == "struct" and self._kind(2) != "{":
                decl = self._parse_struct_local_declaration()
                stmts.append(
                    DeclarationStatement(
                        line=decl.line,
                        column=decl.column,
                        declaration=decl,
                    )
                )
            elif self._kind() in ("const",) or self._kind() in DATA_TYPES:
                decl = self._parse_declaration(require_semicolon=True)
                stmts.append(
                    DeclarationStatement(
                        line=decl.line,
                        column=decl.column,
                        declaration=decl,
                    )
                )
            else:
                stmts.append(self._parse_statement())

        self._expect("breakup", "Each phase/bareminimum must end with `breakup;`")
        self._expect(";", "Expected `;` after breakup")

        return FunctionBody(line=start_line, column=start_col, local_declarations=[], statements=stmts)

    # -------------------------
    # expressions (Pratt)
    # -------------------------
    def _parse_expression(self) -> Expression:
        return self._parse_pratt(0)

    def _parse_pratt(self, min_prec: int) -> Expression:
        left = self._parse_prefix()

        while True:
            op = self._kind()
            prec = _PREC.get(op)
            if prec is None or prec < min_prec:
                break
            self.i += 1
            right = self._parse_pratt(prec + 1)
            line, col = getattr(left, "line", 1), getattr(left, "column", 1)
            left = BinaryExpression(line=line, column=col, operator=op, left=left, right=right)

        return left

    def _parse_prefix(self) -> Expression:
        k = self._kind()
        line, col = self._pos()

        if k in ("!", "+", "-"):
            self.i += 1
            operand = self._parse_prefix()
            return UnaryExpression(line=line, column=col, operator=k, operand=operand)

        if k == "(":
            self._expect("(", "Expected `(`")
            expr = self._parse_expression()
            self._expect(")", "Expected `)`")
            return ParenthesizedExpression(line=line, column=col, expression=expr)

        if k == "dear_lit":
            t = self._expect("dear_lit", "Expected int literal")
            return LiteralExpression(line=t.line, column=t.column, value=int(t.literal or t.lexeme), literal_type="int")
        if k == "dearest_lit":
            t = self._expect("dearest_lit", "Expected float literal")
            return LiteralExpression(line=t.line, column=t.column, value=float(t.literal or t.lexeme), literal_type="float")
        if k == "rant_lit":
            t = self._expect("rant_lit", "Expected string literal")
            return LiteralExpression(line=t.line, column=t.column, value=str(t.literal if t.literal is not None else t.lexeme), literal_type="string")
        if k in BOOL_LITS:
            t = self._expect_any(sorted(BOOL_LITS), "Expected boolean literal")
            return LiteralExpression(line=t.line, column=t.column, value=(t.token == "greenflag"), literal_type="bool")
        if k == "{":
            return self._parse_array_literal()

        if k == "id":
            head = self._expect("id", "Expected identifier")
            qualified = head.lexeme
            while self._match("::"):
                part = self._expect("id", "Expected identifier after `::`")
                qualified = f"{qualified}::{part.lexeme}"

            if self._kind() == "(":
                args = self._parse_call_arguments()
                return FunctionCallExpression(line=head.line, column=head.column, identifier=qualified, namespace=None, arguments=args)

            expr: Expression = IdentifierExpression(line=head.line, column=head.column, name=qualified)

            if "::" not in qualified and self._kind() == "[":
                indices = self._parse_index_list()
                expr = IdentifierExpression(line=head.line, column=head.column, name=qualified, array_indices=indices)

            while self._kind() == ".":
                self._expect(".", "Expected `.`")
                mem = self._expect("id", "Expected member name after `.`")
                # Sugar: allow `a.length()` and lower it to builtin call `length(a)`.
                if mem.lexeme == "length" and self._kind() == "(":
                    args = self._parse_call_arguments()
                    if args:
                        raise AstBuildError("`length()` takes no arguments in method form", mem.line, mem.column)
                    expr = FunctionCallExpression(
                        line=mem.line,
                        column=mem.column,
                        identifier="length",
                        namespace=None,
                        arguments=[expr],
                    )
                else:
                    expr = MemberAccessExpression(line=mem.line, column=mem.column, object=expr, member=mem.lexeme)

            while self._kind() == "[":
                self._expect("[", "Expected `[`")
                ix = self._parse_expression()
                lb = self._expect("]", "Expected `]` after index")
                expr = SubscriptExpression(line=lb.line, column=lb.column, base=expr, index=ix)

            return expr

        raise AstBuildError(f"Unexpected token in expression: `{k}`", line, col)

    # -------------------------
    # misc helpers
    # -------------------------
    def _parse_struct_field_array_spec(self) -> Tuple[int, Tuple[Optional[int], ...]]:
        """Parse `[n]...` after a struct field name; bounds must be `dear` int literals or empty `[]`."""
        sizes: List[Optional[int]] = []
        while self._match("["):
            if self._kind() == "]":
                self._expect("]", "Expected `]` after `[`")
                sizes.append(None)
            else:
                if self._kind() != "dear_lit":
                    line, col = self._pos()
                    raise AstBuildError(
                        "Struct array field size must be a non-negative int literal (dear)",
                        line,
                        col,
                    )
                t = self._expect("dear_lit", "Expected int literal for array bound")
                n = int(t.literal or t.lexeme)
                if n < 0:
                    line, col = self._pos()
                    raise AstBuildError("Struct array bound must be non-negative", line, col)
                sizes.append(n)
                self._expect("]", "Expected `]` after array bound")
        return len(sizes), tuple(sizes)

    def _parse_array_dims_count(self) -> int:
        dims = 0
        while self._match("["):
            if self._kind() != "]":
                if self._kind() in ("dear_lit", "dearest_lit", "id"):
                    _ = self._parse_expression()
                else:
                    l, c = self._pos()
                    raise AstBuildError("Invalid array dimension", l, c)
            self._expect("]", "Expected `]` in array declaration")
            dims += 1
        return dims

    def _parse_index_list(self) -> List[Expression]:
        indices: List[Expression] = []
        while self._match("["):
            idx = self._parse_expression()
            self._expect("]", "Expected `]` after index expression")
            indices.append(idx)
        return indices

    def _parse_call_arguments(self) -> List[Expression]:
        self._expect("(", "Expected `(` for call")
        args: List[Expression] = []
        if self._kind() != ")":
            while True:
                args.append(self._parse_expression())
                if not self._match(","):
                    break
        self._expect(")", "Expected `)` after arguments")
        return args

    def _parse_array_literal(self) -> ArrayLiteralExpression:
        l, c = self._pos()
        self._expect("{", "Expected `{` to start array literal")
        items: List[Expression] = []
        if self._kind() != "}":
            while True:
                items.append(self._parse_expression())
                if not self._match(","):
                    break
        self._expect("}", "Expected `}` to end array literal")
        return ArrayLiteralExpression(line=l, column=c, items=items)

    def _parse_case_literal(self) -> Union[int, float, str]:
        k = self._kind()
        if k == "dear_lit":
            t = self._expect("dear_lit", "Expected int literal")
            return int(t.literal or t.lexeme)
        if k == "dearest_lit":
            t = self._expect("dearest_lit", "Expected float literal")
            return float(t.literal or t.lexeme)
        if k == "rant_lit":
            t = self._expect("rant_lit", "Expected string literal")
            return str(t.literal if t.literal is not None else t.lexeme)
        l, c = self._pos()
        raise AstBuildError("Invalid phase literal (must be a literal)", l, c)

