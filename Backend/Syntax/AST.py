from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union


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
class Program(ASTNode):
    """
    Root node for Lovers program:
      <program> -> <top_decls_opt> love ( ) { <body_func> }

    - All top-level declarations before `love` (variables, consts, functions, namespaces)
      are represented in the lists below.
    """
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
    """Main function: love() { body_func }"""
    body: "FunctionBody" = None


# =============================================================================
# Declarations
# =============================================================================


@dataclass
class Declaration(ASTNode):
    """Variable declaration: data_type id [array_decl] [= expr] [multi_decl];"""
    data_type: str = ""  # "dear", "dearest", "rant", "status"
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
    """Function: return_type id (parameters) { body_func }"""
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
    """Function body: local_decl_list statements"""
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
class AssignmentStatement(Statement):
    """Assignment: id [index_array] assign_op expr;"""
    identifier: str = ""
    array_indices: List["Expression"] = field(default_factory=list)
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
class InputStatement(Statement):
    """Input: give >> id; or overshare(id);"""
    method: str = ""  # "give" or "overshare"
    identifier: str = ""


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
class ParenthesizedExpression(Expression):
    """Parenthesized: (expr)"""
    expression: "Expression" = None

