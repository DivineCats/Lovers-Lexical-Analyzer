"""
Run Lovers source via AST → TAC → virtual machine (no tree-walking interpreter).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from Backend.Interpreter.interpreter import analyze_and_build_program
from Backend.IR.tac import TacGenError, generate_tac_quads
from Backend.IR.vm import TacVM, VMError


def run_lovers_source(
    source: str, *, stdin: str = ""
) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    """
    Full pipeline: lex → syntax → semantic → AST → ICG → TAC VM.

    Returns (stdout, stderr, None) on success, or (None, None, error_dict).
    On VM / ICG failure after a successful parse: (partial_stdout or "", None, {...}).
    """
    program, err = analyze_and_build_program(source)
    if err is not None:
        return None, None, err
    assert program is not None
    try:
        quads = generate_tac_quads(program)
    except TacGenError as exc:
        return None, None, {"phase": "icg", "message": str(exc)}
    vm = TacVM(quads, stdin=stdin)
    try:
        out = vm.run()
    except VMError as exc:
        return vm.stdout.getvalue(), None, {"phase": "runtime", "message": str(exc)}
    return out or "", "", None
