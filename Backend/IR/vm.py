"""
Execute three-address quads produced by TacEmitter (TAC virtual machine).
"""

from __future__ import annotations

import ast as pyast
import io
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from Backend.IR.tac import Quad


class VMError(Exception):
    pass


@dataclass
class _Frame:
    locals: Dict[str, Any] = field(default_factory=dict)
    return_ip: int = 0
    result_slot: Optional[str] = None
    pending_args: List[Any] = field(default_factory=list)


class _StdinReader:
    def __init__(self, text: str) -> None:
        self._lines = text.split("\n") if text else []
        self._line_i = 0
        self._tok_cache: List[str] = []
        self._tok_i = 0

    def _fill(self) -> None:
        while self._tok_i >= len(self._tok_cache) and self._line_i < len(self._lines):
            line = self._lines[self._line_i]
            self._line_i += 1
            self._tok_cache = line.split()
            self._tok_i = 0

    def read_dear(self) -> int:
        self._fill()
        if self._tok_i >= len(self._tok_cache):
            return 0
        t = self._tok_cache[self._tok_i]
        self._tok_i += 1
        try:
            return int(float(t))
        except ValueError:
            return 0

    def read_dearest(self) -> float:
        self._fill()
        if self._tok_i >= len(self._tok_cache):
            return 0.0
        t = self._tok_cache[self._tok_i]
        self._tok_i += 1
        try:
            return float(t)
        except ValueError:
            return 0.0

    def read_status(self) -> bool:
        return self.read_dear() != 0

    def read_rant_line(self) -> str:
        if self._line_i >= len(self._lines):
            return ""
        s = self._lines[self._line_i]
        self._line_i += 1
        self._tok_cache = []
        self._tok_i = 0
        return s.rstrip("\r")


class TacVM:
    def __init__(self, quads: List[Quad], *, stdin: str = "") -> None:
        self.quads = quads
        self.labels: Dict[str, int] = {}
        for i, q in enumerate(quads):
            if q.op == "LABEL" and q.res:
                self.labels[q.res] = i
        self.global_env: Dict[str, Any] = {}
        self.call_stack: List[_Frame] = []
        self.param_buffer: List[Any] = []
        self.ip = 0
        self.stdout = io.StringIO()
        self.stdin = _StdinReader(stdin)
        self.halt_ip: Optional[int] = None

    def run(self) -> str:
        if "__love_main" not in self.labels:
            raise VMError("missing __love_main label")
        self.halt_ip = len(self.quads)
        while 0 <= self.ip < len(self.quads):
            q = self.quads[self.ip]
            op = q.op
            if op == "COMMENT":
                self.ip += 1
                continue
            if op == "LABEL":
                if q.res == "__love_main" and not self.call_stack:
                    self.call_stack.append(
                        _Frame(locals={}, return_ip=self.halt_ip, result_slot=None)
                    )
                self.ip += 1
                continue
            if op == "GOTO":
                self.ip = self.labels[q.arg1]
                continue
            if op == "IF_FALSE":
                if not self._truthy(self._load(q.arg1)):
                    self.ip = self.labels[q.arg2]
                else:
                    self.ip += 1
                continue
            if op == "IF_TRUE":
                if self._truthy(self._load(q.arg1)):
                    self.ip = self.labels[q.arg2]
                else:
                    self.ip += 1
                continue
            if op == "ASSIGN":
                self._set(q.res, self._load(q.arg1))
                self.ip += 1
                continue
            if op in {
                "ADD",
                "SUB",
                "MUL",
                "DIV",
                "MOD",
                "EQ",
                "NE",
                "LT",
                "LE",
                "GT",
                "GE",
                "LAND",
                "LOR",
            }:
                a, b = self._load(q.arg1), self._load(q.arg2)
                self._set(q.res, self._binop(op, a, b))
                self.ip += 1
                continue
            if op in {"NEG", "LNOT"}:
                v = self._load(q.arg1)
                if op == "NEG":
                    self._set(q.res, -float(v) if isinstance(v, float) else -int(v))
                else:
                    self._set(q.res, 0 if self._truthy(v) else 1)
                self.ip += 1
                continue
            if op == "NOT":
                self._set(q.res, 0 if self._load(q.arg1) else 1)
                self.ip += 1
                continue
            if op == "PARAM":
                self.param_buffer.append(self._load(q.arg1))
                self.ip += 1
                continue
            if op == "CALL":
                n = int(q.arg2)
                args = self.param_buffer[-n:]
                self.param_buffer = self.param_buffer[:-n]
                tgt = q.arg1
                if tgt not in self.labels:
                    raise VMError(f"unknown function label `{tgt}`")
                self.call_stack.append(
                    _Frame(
                        locals={},
                        return_ip=self.ip + 1,
                        result_slot=q.res,
                        pending_args=args,
                    )
                )
                self.ip = self.labels[tgt]
                continue
            if op == "CALL_VOID":
                n = int(q.arg2)
                args = self.param_buffer[-n:]
                self.param_buffer = self.param_buffer[:-n]
                if q.arg1 not in self.labels:
                    raise VMError(f"unknown function label `{q.arg1}`")
                self.call_stack.append(
                    _Frame(
                        locals={},
                        return_ip=self.ip + 1,
                        result_slot=None,
                        pending_args=args,
                    )
                )
                self.ip = self.labels[q.arg1]
                continue
            if op == "RECV_PARAM":
                if not self.call_stack:
                    raise VMError("RECV_PARAM outside function")
                fr = self.call_stack[-1]
                idx = int(q.arg1)
                if idx >= len(fr.pending_args):
                    raise VMError("not enough arguments")
                fr.locals[q.res] = fr.pending_args[idx]
                self.ip += 1
                continue
            if op == "RETURN":
                val = self._load(q.arg1) if q.arg1 is not None else None
                if not self.call_stack:
                    raise VMError("return outside of frame")
                callee = self.call_stack.pop()
                slot = callee.result_slot
                if slot is not None and val is not None and self.call_stack:
                    self._set(slot, val)
                self.ip = callee.return_ip
                continue
            if op == "PRINT":
                self.stdout.write(str(self._load(q.arg1)))
                self.ip += 1
                continue
            if op == "PRINT_NL":
                self.stdout.write("\n")
                self.ip += 1
                continue
            if op == "READ_INT":
                self._set(q.res, self.stdin.read_dear())
                self.ip += 1
                continue
            if op == "READ_FLOAT":
                self._set(q.res, self.stdin.read_dearest())
                self.ip += 1
                continue
            if op == "READ_BOOL":
                self._set(q.res, self.stdin.read_status())
                self.ip += 1
                continue
            if op == "READ_LINE":
                self._set(q.res, self.stdin.read_rant_line())
                self.ip += 1
                continue
            if op == "INDEX_LOAD":
                base = self._load(q.arg1)
                idx = int(self._load(q.arg2))
                if not isinstance(base, list) or idx < 0 or idx >= len(base):
                    raise VMError("bad array index load")
                self._set(q.res, base[idx])
                self.ip += 1
                continue
            if op == "INDEX_STORE":
                base_pl = q.arg1
                base = self._load(base_pl)
                idx = int(self._load(q.arg2))
                val = self._load(q.res)
                if not isinstance(base, list):
                    raise VMError("INDEX_STORE on non-array")
                while len(base) <= idx:
                    base.append(None)
                base[idx] = val
                self.ip += 1
                continue
            if op == "ASET":
                sym = q.arg1
                idx = int(q.arg2)
                val = self._load(q.res)
                arr: Any = None
                if self.call_stack and sym in self.call_stack[-1].locals:
                    arr = self.call_stack[-1].locals[sym]
                elif sym in self.global_env:
                    arr = self.global_env[sym]
                if not isinstance(arr, list):
                    arr = []
                    self._set(sym, arr)
                while len(arr) <= idx:
                    arr.append(None)
                arr[idx] = val
                self.ip += 1
                continue
            if op == "MEMBER_LOAD":
                obj = self._load(q.arg1)
                if not isinstance(obj, dict):
                    raise VMError("MEMBER_LOAD on non-struct")
                if q.arg2 not in obj:
                    raise VMError(f"missing field `{q.arg2}`")
                self._set(q.res, obj[q.arg2])
                self.ip += 1
                continue
            if op == "MEMBER_STORE":
                obj = self._load(q.arg1)
                if not isinstance(obj, dict):
                    raise VMError("MEMBER_STORE on non-struct")
                obj[q.arg2] = self._load(q.res)
                self.ip += 1
                continue
            if op == "STRCAT":
                self._set(
                    q.res,
                    str(self._load(q.arg1)) + str(self._load(q.arg2)),
                )
                self.ip += 1
                continue

            raise VMError(f"unsupported quad op `{op}`")

        return self.stdout.getvalue()

    def _current_frame(self) -> _Frame:
        if not self.call_stack:
            raise VMError("no activation frame")
        return self.call_stack[-1]

    def _set(self, name: Optional[str], val: Any) -> None:
        if name is None:
            return
        if self.call_stack:
            self.call_stack[-1].locals[name] = val
        else:
            self.global_env[name] = val

    @staticmethod
    def _is_temp(name: str) -> bool:
        return name.startswith("t") and name[1:].isdigit()

    def _load(self, ref: Optional[str]) -> Any:
        if ref is None:
            return None
        if self._is_literal(ref):
            return self._literal_value(ref)
        if self.call_stack and ref in self.call_stack[-1].locals:
            return self.call_stack[-1].locals[ref]
        if ref in self.global_env:
            return self.global_env[ref]
        raise VMError(f"undefined symbol `{ref}`")

    @staticmethod
    def _is_literal(ref: str) -> bool:
        if ref in {"0", "1"} and len(ref) == 1:
            return ref.isdigit()
        if re.fullmatch(r"-?\d+", ref):
            return True
        if re.fullmatch(r"-?\d+\.\d+", ref) or re.fullmatch(r"-?\d+e-?\d+", ref, re.I):
            return True
        return ref.startswith(("'", '"'))

    @staticmethod
    def _literal_value(ref: str) -> Any:
        if re.fullmatch(r"-?\d+", ref):
            return int(ref)
        if re.fullmatch(r"-?\d+\.\d+", ref) or re.fullmatch(r"-?\d+e-?\d+", ref, re.I):
            return float(ref)
        try:
            return pyast.literal_eval(ref)
        except (ValueError, SyntaxError):
            return ref

    @staticmethod
    def _truthy(v: Any) -> bool:
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return v != 0
        if isinstance(v, float):
            return v != 0.0
        if isinstance(v, str):
            return len(v) > 0
        return bool(v)

    def _binop(self, op: str, a: Any, b: Any) -> Any:
        if op in {"LAND", "LOR"}:
            ta, tb = self._truthy(a), self._truthy(b)
            return 1 if (ta and tb if op == "LAND" else ta or tb) else 0
        if op in {"EQ", "NE"} and (isinstance(a, str) or isinstance(b, str)):
            sa, sb = str(a), str(b)
            eq = sa == sb
            if op == "EQ":
                return 1 if eq else 0
            return 0 if eq else 1
        if isinstance(a, float) or isinstance(b, float):
            x, y = float(a), float(b)
            if op == "ADD":
                return x + y
            if op == "SUB":
                return x - y
            if op == "MUL":
                return x * y
            if op == "DIV":
                return x / y if y != 0 else 0.0
            if op == "MOD":
                return x % y if y != 0 else 0.0
            return int(self._cmp_float(op, x, y))
        x, y = int(a), int(b)
        if op == "ADD":
            return x + y
        if op == "SUB":
            return x - y
        if op == "MUL":
            return x * y
        if op == "DIV":
            return x // y if y != 0 else 0
        if op == "MOD":
            return x % y if y != 0 else 0
        if op == "EQ":
            return 1 if x == y else 0
        if op == "NE":
            return 1 if x != y else 0
        if op == "LT":
            return 1 if x < y else 0
        if op == "LE":
            return 1 if x <= y else 0
        if op == "GT":
            return 1 if x > y else 0
        if op == "GE":
            return 1 if x >= y else 0
        raise VMError(f"bad binop {op}")

    @staticmethod
    def _cmp_float(op: str, x: float, y: float) -> int:
        if op == "EQ":
            return 1 if x == y else 0
        if op == "NE":
            return 1 if x != y else 0
        if op == "LT":
            return 1 if x < y else 0
        if op == "LE":
            return 1 if x <= y else 0
        if op == "GT":
            return 1 if x > y else 0
        if op == "GE":
            return 1 if x >= y else 0
        return 0


def run_tac_quads(quads: List[Quad], *, stdin: str = "") -> str:
    vm = TacVM(quads, stdin=stdin)
    return vm.run()
