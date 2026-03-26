"""
Three-address code (TAC) / intermediate code generation from a validated Lovers AST.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from Backend.Interpreter.interpreter import mangle_function
from Backend.Syntax.AST import (
    ArrayLiteralExpression,
    AssignmentStatement,
    BinaryExpression,
    BreakStatement,
    ContinueStatement,
    Declaration,
    DoWhileStatement,
    Expression,
    ForStatement,
    ForUpdate,
    Function,
    FunctionBody,
    FunctionCallExpression,
    FunctionCallStatement,
    IdentifierExpression,
    IfStatement,
    InputStatement,
    LiteralExpression,
    MemberAccessExpression,
    Namespace,
    OutputStatement,
    ParenthesizedExpression,
    Program,
    ReturnStatement,
    Statement,
    SwitchStatement,
    UnaryExpression,
    UnaryStatement,
    WhileStatement,
)


class TacGenError(Exception):
    def __init__(self, message: str, node: Any = None):
        super().__init__(message)
        self.node = node


@dataclass
class Quad:
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    res: Optional[str] = None

    def format(self) -> str:
        o = self.op
        if o == "LABEL":
            return f"{self.res}:"
        if o == "GOTO":
            return f"goto {self.arg1}"
        if o == "IF_FALSE":
            return f"ifFalse {self.arg1} goto {self.arg2}"
        if o == "IF_TRUE":
            return f"ifTrue {self.arg1} goto {self.arg2}"
        if o == "ASSIGN":
            return f"{self.res} = {self.arg1}"
        if o == "PARAM":
            return f"param {self.arg1}"
        if o == "CALL":
            return f"{self.res} = call {self.arg1}, {self.arg2}"
        if o == "CALL_VOID":
            return f"call {self.arg1}, {self.arg2}"
        if o == "RETURN":
            return f"return {self.arg1}" if self.arg1 else "return"
        if o == "PRINT":
            return f"print {self.arg1}"
        if o == "PRINT_NL":
            return "printNewline"
        if o == "READ_INT":
            return f"readInt {self.res}"
        if o == "READ_FLOAT":
            return f"readFloat {self.res}"
        if o == "READ_BOOL":
            return f"readBool {self.res}"
        if o == "READ_LINE":
            return f"readLine {self.res}"
        if o == "INDEX_LOAD":
            return f"{self.res} = {self.arg1}[{self.arg2}]"
        if o == "INDEX_STORE":
            return f"{self.arg1}[{self.arg2}] = {self.res}"
        if o == "MEMBER_LOAD":
            return f"{self.res} = {self.arg1}.{self.arg2}"
        if o == "MEMBER_STORE":
            return f"{self.arg1}.{self.arg2} = {self.res}"
        if o == "STRCAT":
            return f"{self.res} = strcat({self.arg1}, {self.arg2})"
        if o == "STRLEN":
            return f"{self.res} = strlen({self.arg1})"
        if o in {"ADD", "SUB", "MUL", "DIV", "MOD", "EQ", "NE", "LT", "LE", "GT", "GE", "LAND", "LOR"}:
            return f"{self.res} = {self.arg1} {o} {self.arg2}"
        if o in {"NEG", "NOT", "LNOT"}:
            return f"{self.res} = {o} {self.arg1}"
        if o == "ASET":
            return f"{self.arg1}[{self.arg2}] = {self.res}"
        if o == "COMMENT":
            return f"// {self.arg1}"
        if o == "RECV_PARAM":
            return f"{self.res} = recv_param {self.arg1}"
        return f"{o} {self.arg1} {self.arg2} -> {self.res}"


_TEMP_NAME_RE = re.compile(r"^t(\d+)$", re.I)


def _human_symbol(name: Optional[str]) -> Optional[str]:
    """Display-only: rename compiler temps t1, t2, ... -> T1, T2, ..."""
    if name is None:
        return None
    m = _TEMP_NAME_RE.match(name)
    if m:
        return f"T{m.group(1)}"
    return name


_BINOP_INFIX: Dict[str, str] = {
    "ADD": "+",
    "SUB": "-",
    "MUL": "*",
    "DIV": "/",
    "MOD": "%",
    "EQ": "==",
    "NE": "!=",
    "LT": "<",
    "LE": "<=",
    "GT": ">",
    "GE": ">=",
    "LAND": "&&",
    "LOR": "||",
}


def format_tac_human_line(q: Quad) -> str:
    """
    One line of textbook-style TAC: infix arithmetic, && / ||, and Tn temporaries.
    (Instruction index is added by format_tac_human.)
    """
    o = q.op
    a1, a2, r = _human_symbol(q.arg1), _human_symbol(q.arg2), _human_symbol(q.res)
    if o == "LABEL":
        return f"{r}:"
    if o == "GOTO":
        return f"goto {a1}"
    if o == "IF_FALSE":
        return f"ifFalse {a1} goto {a2}"
    if o == "IF_TRUE":
        return f"ifTrue {a1} goto {a2}"
    if o == "ASSIGN":
        return f"{r} = {a1}"
    if o == "PARAM":
        return f"param {a1}"
    if o == "CALL":
        return f"{r} = call {a1}, {a2}"
    if o == "CALL_VOID":
        return f"call {a1}, {a2}"
    if o == "RETURN":
        return f"return {a1}" if q.arg1 else "return"
    if o == "PRINT":
        return f"print {a1}"
    if o == "PRINT_NL":
        return "printNewline"
    if o == "READ_INT":
        return f"readInt {r}"
    if o == "READ_FLOAT":
        return f"readFloat {r}"
    if o == "READ_BOOL":
        return f"readBool {r}"
    if o == "READ_LINE":
        return f"readLine {r}"
    if o == "INDEX_LOAD":
        return f"{r} = {a1}[{a2}]"
    if o == "INDEX_STORE":
        return f"{a1}[{a2}] = {r}"
    if o == "MEMBER_LOAD":
        return f"{r} = {a1}.{a2}"
    if o == "MEMBER_STORE":
        return f"{a1}.{a2} = {r}"
    if o == "STRCAT":
        return f"{r} = strcat({a1}, {a2})"
    if o == "STRLEN":
        return f"{r} = strlen({a1})"
    if o in _BINOP_INFIX:
        sym = _BINOP_INFIX[o]
        return f"{r} = {a1} {sym} {a2}"
    if o == "NEG":
        return f"{r} = -{a1}"
    if o == "LNOT":
        return f"{r} = !{a1}"
    if o == "NOT":
        return f"{r} = ~{a1}"
    if o == "ASET":
        return f"{a1}[{a2}] = {r}"
    if o == "COMMENT":
        return f"// {q.arg1}"
    if o == "RECV_PARAM":
        return f"{r} = recv_param {a1}"
    return f"{o} {a1} {a2} -> {r}"


def format_tac_human(quads: List[Quad]) -> str:
    """Numbered, slide-style listing: (0) T1 = y * z, etc."""
    lines: List[str] = []
    for i, q in enumerate(quads):
        lines.append(f"({i}) {format_tac_human_line(q)}")
    return "\n".join(lines) + "\n"


class TacEmitter:
    def __init__(self, program: Program) -> None:
        self.program = program
        self.quads: List[Quad] = []
        self._temp = 0
        self._lbl = 0
        self._loop_stack: List[Tuple[Optional[str], str]] = []
        self.struct_fields: Dict[str, Dict[str, str]] = {}
        for sd in program.struct_definitions:
            self.struct_fields[sd.name] = dict(sd.fields)
        self.fn_map: Dict[str, Tuple[Function, Optional[str]]] = {}
        for fn in program.sub_functions:
            k = mangle_function(fn.name, [p.data_type for p in fn.parameters])
            self.fn_map[k] = (fn, None)
        for ns in program.namespaces:
            for fn in ns.sub_functions:
                qual = f"{ns.name}::{fn.name}"
                k = mangle_function(qual, [p.data_type for p in fn.parameters])
                self.fn_map[k] = (fn, ns.name)
        self.scope_types: List[Dict[str, str]] = [{}]

    def fresh_temp(self) -> str:
        self._temp += 1
        return f"t{self._temp}"

    def fresh_label(self, hint: str = "L") -> str:
        self._lbl += 1
        return f"_{hint}_{self._lbl}"

    def push_scope(self) -> None:
        self.scope_types.append({})

    def pop_scope(self) -> None:
        self.scope_types.pop()

    def declare(self, name: str, lovers_type: str) -> None:
        self.scope_types[-1][name] = lovers_type

    def lookup_type(self, name: str) -> Optional[str]:
        for scope in reversed(self.scope_types):
            if name in scope:
                return scope[name]
        return None

    def emit(self, op: str, a1: Optional[str] = None, a2: Optional[str] = None, res: Optional[str] = None) -> None:
        self.quads.append(Quad(op, a1, a2, res))

    def comment(self, text: str) -> None:
        self.emit("COMMENT", text, None, None)

    def expr_type(self, expr: Optional[Expression]) -> str:
        if expr is None:
            return "dear"
        if isinstance(expr, LiteralExpression):
            return {
                "int": "dear",
                "float": "dearest",
                "string": "rant",
                "bool": "status",
            }.get(expr.literal_type, "dear")
        if isinstance(expr, IdentifierExpression):
            return self.lookup_type(expr.name) or "dear"
        if isinstance(expr, ParenthesizedExpression):
            return self.expr_type(expr.expression)
        if isinstance(expr, UnaryExpression):
            if expr.operator == "!":
                return "status"
            return self.expr_type(expr.operand)
        if isinstance(expr, BinaryExpression):
            op = expr.operator
            if op == ".=":
                op = "=="
            if op in {"&&", "||", "==", "!=", "<", ">", "<=", ">="}:
                return "status"
            if expr.operator == "+" and (
                self.expr_type(expr.left) == "rant" or self.expr_type(expr.right) == "rant"
            ):
                return "rant"
            lt, rt = self.expr_type(expr.left), self.expr_type(expr.right)
            if "dearest" in {lt, rt}:
                return "dearest"
            return "dear"
        if isinstance(expr, MemberAccessExpression):
            bt = self.expr_type(expr.object)
            fields = self.struct_fields.get(bt)
            if fields and expr.member in fields:
                return fields[expr.member]
            return "dear"
        if isinstance(expr, FunctionCallExpression):
            types = [self.expr_type(a) for a in expr.arguments]
            qual = (
                f"{expr.namespace}::{expr.identifier}"
                if expr.namespace
                else expr.identifier
            )
            hit = self.fn_map.get(mangle_function(qual, types))
            if hit and hit[0].return_type is not None:
                return hit[0].return_type
            return "dear"
        if isinstance(expr, ArrayLiteralExpression):
            return "array_literal"
        return "dear"

    def _literal_place(self, expr: LiteralExpression) -> str:
        if expr.literal_type == "string":
            return repr(str(expr.value))
        if expr.literal_type == "bool":
            return "1" if expr.value else "0"
        if expr.literal_type == "float":
            return str(float(expr.value))
        return str(int(expr.value))

    def emit_expr(self, expr: Expression) -> str:
        if isinstance(expr, LiteralExpression):
            return self._literal_place(expr)
        if isinstance(expr, IdentifierExpression):
            base = expr.name
            if not expr.array_indices:
                return base
            cur = base
            for ix in expr.array_indices:
                it = self.emit_expr(ix)
                nt = self.fresh_temp()
                self.emit("INDEX_LOAD", cur, it, nt)
                cur = nt
            return cur
        if isinstance(expr, ParenthesizedExpression):
            return self.emit_expr(expr.expression)
        if isinstance(expr, UnaryExpression):
            inner = self.emit_expr(expr.operand)
            if expr.operator == "!":
                tt = self.fresh_temp()
                self.emit("LNOT", inner, None, tt)
                return tt
            if expr.operator == "-":
                tt = self.fresh_temp()
                self.emit("NEG", inner, None, tt)
                return tt
            if expr.operator == "+":
                return inner
            raise TacGenError(f"unsupported unary `{expr.operator}`", expr)
        if isinstance(expr, BinaryExpression):
            raw = expr.operator
            op = "=" if raw == ".=" else raw
            lt, rt = self.expr_type(expr.left), self.expr_type(expr.right)
            L = self.emit_expr(expr.left)
            R = self.emit_expr(expr.right)
            if raw == "+" and (lt == "rant" or rt == "rant"):
                if lt != "rant" or rt != "rant":
                    raise TacGenError("rant + requires two strings", expr)
                tt = self.fresh_temp()
                self.emit("STRCAT", L, R, tt)
                return tt
            if op in {"&&", "||"}:
                tl = self._emit_truthy_temp(expr.left, L, lt)
                tr = self._emit_truthy_temp(expr.right, R, rt)
                tt = self.fresh_temp()
                self.emit("LAND" if op == "&&" else "LOR", tl, tr, tt)
                return tt
            tac_op = {
                "==": "EQ",
                "!=": "NE",
                "<": "LT",
                "<=": "LE",
                ">": "GT",
                ">=": "GE",
                "+": "ADD",
                "-": "SUB",
                "*": "MUL",
                "/": "DIV",
                "%": "MOD",
            }.get(op)
            if tac_op is None:
                raise TacGenError(f"unsupported binary `{raw}`", expr)
            out = self.fresh_temp()
            self.emit(tac_op, L, R, out)
            return out
        if isinstance(expr, MemberAccessExpression):
            obj = self.emit_expr(expr.object)
            tt = self.fresh_temp()
            self.emit("MEMBER_LOAD", obj, expr.member, tt)
            return tt
        if isinstance(expr, FunctionCallExpression):
            if expr.namespace is None and expr.identifier == "length":
                if len(expr.arguments) != 1:
                    raise TacGenError("length(...) expects exactly one argument", expr)
                arg = self.emit_expr(expr.arguments[0])
                t = self.fresh_temp()
                self.emit("STRLEN", arg, None, t)
                return t
            return self._emit_call(expr.identifier, expr.namespace, expr.arguments, expr)
        if isinstance(expr, ArrayLiteralExpression):
            raise TacGenError("array literal not allowed here", expr)
        raise TacGenError(f"unsupported expression `{type(expr).__name__}`", expr)

    def _emit_truthy_temp(self, expr: Expression, place: str, lovers_t: str) -> str:
        if lovers_t == "status":
            return place
        out = self.fresh_temp()
        if lovers_t == "dear":
            self.emit("NE", place, "0", out)
            return out
        if lovers_t == "dearest":
            z = self.fresh_temp()
            self.emit("ASSIGN", "0.0", None, z)
            self.emit("NE", place, z, out)
            return out
        if lovers_t == "rant":
            self.emit("NE", place, '""', out)
            return out
        self.emit("NE", place, "0", out)
        return out

    def _emit_call(
        self,
        name: str,
        namespace: Optional[str],
        args: List[Expression],
        node: Any,
    ) -> str:
        types = [self.expr_type(a) for a in args]
        qual = f"{namespace}::{name}" if namespace else name
        key = mangle_function(qual, types)
        hit = self.fn_map.get(key)
        if not hit:
            raise TacGenError(f"unresolved call `{qual}`", node)
        fn, _ = hit
        for a in args:
            self.emit("PARAM", self.emit_expr(a), None, None)
        k = str(len(args))
        if fn.return_type is None:
            self.emit("CALL_VOID", key, k, None)
            return "0"
        t = self.fresh_temp()
        self.emit("CALL", key, k, t)
        return t

    def _emit_call_stmt(self, stmt: FunctionCallStatement) -> None:
        self._emit_call(stmt.identifier, stmt.namespace, stmt.arguments, stmt)

    def _resolve_lhs_array(self, name: str, indices: List[Expression]) -> Tuple[str, str]:
        if not indices:
            raise TacGenError("expected array indices")
        cur = name
        for ix in indices[:-1]:
            it = self.emit_expr(ix)
            nt = self.fresh_temp()
            self.emit("INDEX_LOAD", cur, it, nt)
            cur = nt
        last = self.emit_expr(indices[-1])
        return cur, last

    def emit_stmt(self, stmt: Statement) -> None:
        if isinstance(stmt, AssignmentStatement):
            rhs = self.emit_expr(stmt.value)
            op = "=" if stmt.operator == ".=" else stmt.operator
            if stmt.array_indices:
                arr, last_i = self._resolve_lhs_array(stmt.identifier, stmt.array_indices)
                if op != "=":
                    tmp = self.fresh_temp()
                    self.emit("INDEX_LOAD", arr, last_i, tmp)
                    tac_op = {"+=": "ADD", "-=": "SUB", "*=": "MUL", "/=": "DIV", "%=": "MOD"}.get(op)
                    if tac_op is None:
                        raise TacGenError(f"bad compound `{op}`", stmt)
                    comb = self.fresh_temp()
                    self.emit(tac_op, tmp, rhs, comb)
                    rhs = comb
                self.emit("INDEX_STORE", arr, last_i, rhs)
                return
            if op == "=":
                self.emit("ASSIGN", rhs, None, stmt.identifier)
            else:
                tac_op = {"+=": "ADD", "-=": "SUB", "*=": "MUL", "/=": "DIV", "%=": "MOD"}.get(op)
                if tac_op is None:
                    raise TacGenError(f"bad op `{op}`", stmt)
                tmp = self.fresh_temp()
                self.emit(tac_op, stmt.identifier, rhs, tmp)
                self.emit("ASSIGN", tmp, None, stmt.identifier)
            return
        if isinstance(stmt, FunctionCallStatement):
            self._emit_call_stmt(stmt)
            return
        if isinstance(stmt, UnaryStatement):
            one = "1" if stmt.operator == "++" else "-1"
            tmp = self.fresh_temp()
            self.emit("ADD", stmt.identifier, one, tmp)
            self.emit("ASSIGN", tmp, None, stmt.identifier)
            return
        if isinstance(stmt, InputStatement):
            cell = stmt.identifier
            t = self.lookup_type(cell) or "dear"
            if t == "dear":
                self.emit("READ_INT", None, None, cell)
            elif t == "dearest":
                self.emit("READ_FLOAT", None, None, cell)
            elif t == "status":
                self.emit("READ_BOOL", None, None, cell)
            elif t == "rant":
                self.emit("READ_LINE", None, None, cell)
            else:
                raise TacGenError(f"READ unsupported for `{t}`", stmt)
            return
        if isinstance(stmt, OutputStatement):
            for item in stmt.values:
                if item == "periodt":
                    self.emit("PRINT_NL", None, None, None)
                elif isinstance(item, Expression):
                    self.emit("PRINT", self.emit_expr(item), None, None)
            return
        if isinstance(stmt, ReturnStatement):
            if stmt.value is None:
                self.emit("RETURN", None, None, None)
            else:
                self.emit("RETURN", self.emit_expr(stmt.value), None, None)
            return
        if isinstance(stmt, IfStatement):
            l_end = self.fresh_label("ifEnd")
            l_chain = self.fresh_label("ifGo")
            c0 = self.emit_expr(stmt.condition)
            t0 = self._emit_truthy_temp(
                stmt.condition, c0, self.expr_type(stmt.condition)
            )
            self.emit("IF_FALSE", t0, l_chain, None)
            self.emit_block(stmt.then_body)
            self.emit("GOTO", l_end, None, None)
            for el in stmt.elif_clauses:
                self.emit("LABEL", None, None, l_chain)
                l_chain = self.fresh_label("ifGo")
                ce = self.emit_expr(el.condition)
                te = self._emit_truthy_temp(
                    el.condition, ce, self.expr_type(el.condition)
                )
                self.emit("IF_FALSE", te, l_chain, None)
                self.emit_block(el.body)
                self.emit("GOTO", l_end, None, None)
            self.emit("LABEL", None, None, l_chain)
            if stmt.else_body:
                self.emit_block(stmt.else_body)
            self.emit("LABEL", None, None, l_end)
            return
        if isinstance(stmt, WhileStatement):
            lstart = self.fresh_label("while")
            lend = self.fresh_label("endWhile")
            self._loop_stack.append((lstart, lend))
            self.emit("LABEL", None, None, lstart)
            tc = self._emit_truthy_temp(
                stmt.condition,
                self.emit_expr(stmt.condition),
                self.expr_type(stmt.condition),
            )
            self.emit("IF_FALSE", tc, lend, None)
            self.emit_block(stmt.body)
            self.emit("GOTO", lstart, None, None)
            self.emit("LABEL", None, None, lend)
            self._loop_stack.pop()
            return
        if isinstance(stmt, DoWhileStatement):
            lstart = self.fresh_label("do")
            lend = self.fresh_label("endDo")
            self._loop_stack.append((lstart, lend))
            self.emit("LABEL", None, None, lstart)
            self.emit_block(stmt.body)
            tc = self._emit_truthy_temp(
                stmt.condition,
                self.emit_expr(stmt.condition),
                self.expr_type(stmt.condition),
            )
            self.emit("IF_TRUE", tc, lstart, None)
            self.emit("LABEL", None, None, lend)
            self._loop_stack.pop()
            return
        if isinstance(stmt, ForStatement):
            self.push_scope()
            lstart = self.fresh_label("for")
            lupdate = self.fresh_label("forUp")
            lend = self.fresh_label("endFor")
            self._loop_stack.append((lupdate, lend))
            if stmt.init:
                fi = stmt.init
                if fi.data_type is not None:
                    v = self.emit_expr(fi.value)
                    self.declare(fi.identifier, fi.data_type)
                    self.emit("ASSIGN", v, None, fi.identifier)
                else:
                    self.emit("ASSIGN", self.emit_expr(fi.value), None, fi.identifier)
            self.emit("LABEL", None, None, lstart)
            if stmt.condition is not None:
                tc = self._emit_truthy_temp(
                    stmt.condition,
                    self.emit_expr(stmt.condition),
                    self.expr_type(stmt.condition),
                )
                self.emit("IF_FALSE", tc, lend, None)
            self.emit_block(stmt.body)
            self.emit("LABEL", None, None, lupdate)
            if stmt.update:
                self._emit_for_update(stmt.update)
            self.emit("GOTO", lstart, None, None)
            self.emit("LABEL", None, None, lend)
            self._loop_stack.pop()
            self.pop_scope()
            return
        if isinstance(stmt, SwitchStatement):
            disc = self.emit_expr(stmt.expression)
            dt = self.expr_type(stmt.expression)
            lend = self.fresh_label("endSwitch")
            self._loop_stack.append((None, lend))
            n = len(stmt.cases)
            l_next = self.fresh_label("sw0")
            for i, case in enumerate(stmt.cases):
                self.emit("LABEL", None, None, l_next)
                if i + 1 < n:
                    l_next = self.fresh_label(f"sw{i + 1}")
                else:
                    l_next = self.fresh_label("swDef") if stmt.default_case else lend
                m = self.fresh_temp()
                self._emit_case_compare(disc, dt, case.value, m)
                self.emit("IF_FALSE", m, l_next, None)
                self.emit_block(case.body)
                self.emit("GOTO", lend, None, None)
            if l_next != lend:
                self.emit("LABEL", None, None, l_next)
            if stmt.default_case:
                self.emit_block(stmt.default_case)
            self.emit("LABEL", None, None, lend)
            self._loop_stack.pop()
            return
        if isinstance(stmt, BreakStatement):
            if not self._loop_stack:
                raise TacGenError("break outside loop/switch", stmt)
            self.emit("GOTO", self._loop_stack[-1][1], None, None)
            return
        if isinstance(stmt, ContinueStatement):
            if not self._loop_stack or self._loop_stack[-1][0] is None:
                raise TacGenError("continue outside loop", stmt)
            self.emit("GOTO", self._loop_stack[-1][0], None, None)
            return
        raise TacGenError(f"unsupported statement `{type(stmt).__name__}`", stmt)

    def _emit_case_compare(self, disc: str, dt: str, val: Any, out: str) -> None:
        if dt == "rant":
            self.emit("EQ", disc, repr(str(val)), out)
        elif isinstance(val, float):
            self.emit("EQ", disc, str(val), out)
        else:
            self.emit("EQ", disc, str(int(val)), out)

    def _emit_for_update(self, u: ForUpdate) -> None:
        if u.operator in {"++", "--"}:
            one = "1" if u.operator == "++" else "-1"
            tmp = self.fresh_temp()
            self.emit("ADD", u.identifier, one, tmp)
            self.emit("ASSIGN", tmp, None, u.identifier)
            return
        rhs = self.emit_expr(u.value) if u.value else "0"
        op = u.operator
        if op == ".=":
            op = "="
        if op == "=":
            self.emit("ASSIGN", rhs, None, u.identifier)
            return
        tac_op = {"+=": "ADD", "-=": "SUB", "*=": "MUL", "/=": "DIV", "%=": "MOD"}.get(op)
        if tac_op is None:
            raise TacGenError(f"bad for-update `{u.operator}`")
        tmp = self.fresh_temp()
        self.emit(tac_op, u.identifier, rhs, tmp)
        self.emit("ASSIGN", tmp, None, u.identifier)

    def emit_block(self, body: Optional[FunctionBody]) -> None:
        if body is None:
            return
        self.push_scope()
        for decl in body.local_declarations:
            self.emit_declaration(decl)
        for st in body.statements:
            self.emit_stmt(st)
        self.pop_scope()

    def emit_declaration(self, decl: Declaration) -> None:
        segs: List[Tuple[str, int, Optional[Expression], Any]] = [
            (decl.identifier, decl.array_dimensions, decl.initial_value, decl),
        ]
        for md in decl.multi_declarations:
            segs.append((md.identifier, md.array_dimensions, md.initial_value, md))
        for name, dims, init, node in segs:
            if not name:
                continue
            self.declare(name, decl.data_type)
            if dims > 0:
                if isinstance(init, ArrayLiteralExpression):
                    for i, ex in enumerate(init.items):
                        self.emit("ASET", name, str(i), self.emit_expr(ex))
                elif init is not None:
                    raise TacGenError("unsupported array initializer", node)
                else:
                    raise TacGenError("array needs initializer", node)
            elif init is not None:
                self.emit("ASSIGN", self.emit_expr(init), None, name)

    def emit_global_decl(self, decl: Declaration, prefix: str) -> None:
        segs: List[Tuple[str, int, Optional[Expression], Any]] = [
            (decl.identifier, decl.array_dimensions, decl.initial_value, decl),
        ]
        for md in decl.multi_declarations:
            segs.append((md.identifier, md.array_dimensions, md.initial_value, md))
        for name, dims, init, node in segs:
            if not name:
                continue
            sym = prefix + name
            self.declare(sym, decl.data_type)
            if dims > 0:
                if isinstance(init, ArrayLiteralExpression):
                    for i, ex in enumerate(init.items):
                        self.emit("ASET", sym, str(i), self.emit_expr(ex))
                elif init is not None:
                    raise TacGenError("unsupported global array init", node)
                else:
                    raise TacGenError("array needs initializer", node)
            elif init is not None:
                self.emit("ASSIGN", self.emit_expr(init), None, sym)

    def _ns_alias_prologue(self, ns_name: str) -> None:
        ns_obj = next((n for n in self.program.namespaces if n.name == ns_name), None)
        if not ns_obj:
            return
        for gd in ns_obj.global_declarations:
            shorts = [gd.identifier] + [m.identifier for m in gd.multi_declarations]
            for short in shorts:
                if not short:
                    continue
                self.declare(short, gd.data_type)
                self.emit("ASSIGN", f"{ns_name}__{short}", None, short)

    def emit_one_function(self, fn: Function, qual: str, ns: Optional[str]) -> None:
        key = mangle_function(qual, [p.data_type for p in fn.parameters])
        self.comment(f"function {qual}")
        self.emit("LABEL", None, None, key)
        self.push_scope()
        if ns:
            self._ns_alias_prologue(ns)
        for p in fn.parameters:
            self.declare(p.identifier, p.data_type)
        for i, p in enumerate(fn.parameters):
            self.emit("RECV_PARAM", str(i), None, p.identifier)
        if fn.body:
            for decl in fn.body.local_declarations:
                self.emit_declaration(decl)
            for st in fn.body.statements:
                self.emit_stmt(st)
        self.pop_scope()

    def emit_program(self) -> None:
        self.comment("--- global storage ---")
        self.push_scope()
        for decl in self.program.global_declarations:
            self.emit_global_decl(decl, "")
        for ns in self.program.namespaces:
            for decl in ns.global_declarations:
                self.emit_global_decl(decl, f"{ns.name}__")

        self.emit("GOTO", "__love_main", None, None)
        self.comment("--- procedures ---")
        for fn in self.program.sub_functions:
            self.emit_one_function(fn, fn.name, None)
        for ns in self.program.namespaces:
            for fn in ns.sub_functions:
                self.emit_one_function(fn, f"{ns.name}::{fn.name}", ns.name)

        self.comment("--- love() main ---")
        self.emit("LABEL", None, None, "__love_main")
        self.push_scope()
        main = self.program.main_function
        if main and main.body:
            for decl in main.body.local_declarations:
                self.emit_declaration(decl)
            for st in main.body.statements:
                self.emit_stmt(st)
        self.emit("RETURN", "0", None, None)
        self.pop_scope()
        self.pop_scope()


def generate_tac_quads(program: Program) -> List[Quad]:
    em = TacEmitter(program)
    em.emit_program()
    return em.quads


def generate_tac_text(program: Program) -> str:
    return format_tac_human(generate_tac_quads(program))


def lovers_source_to_tac(source: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    from Backend.Interpreter.interpreter import analyze_and_build_program

    program, err = analyze_and_build_program(source)
    if err is not None:
        return None, err
    assert program is not None
    try:
        return generate_tac_text(program), None
    except TacGenError as exc:
        return None, {"phase": "icg", "message": str(exc)}
