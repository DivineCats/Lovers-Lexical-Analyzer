"""
Run Lovers source via AST → TAC → virtual machine (no tree-walking interpreter).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from Backend.IR.pipeline import analyze_and_build_program
from Backend.IR.runtime_messages import humanize_runtime_message
from Backend.IR.tac import TacGenError, generate_tac_quads, tacgen_error_dict
from Backend.IR.vm import TacVM, VMError


def run_lovers_source(
    source: str, *, stdin: str = ""
) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    """
    Full pipeline: lex → syntax → semantic → AST → ICG → TAC VM.

    Returns (stdout, stderr, None) on success, or (None, None, error_dict).
    On VM / ICG failure after a successful parse: (partial_stdout or "", None, {...}).
    """
    vm, vm_err = create_vm_from_source(source, stdin=stdin)
    if vm_err is not None:
        return None, None, vm_err
    assert vm is not None
    try:
        out = vm.run()
    except VMError as exc:
        raw = str(exc)
        return vm.stdout.getvalue(), None, {
            "phase": "runtime",
            "message": humanize_runtime_message(raw),
            "detail": raw,
        }
    return out or "", "", None


def create_vm_from_source(
    source: str, *, stdin: str = "", echo_input: bool = False
) -> Tuple[Optional[TacVM], Optional[Dict[str, Any]]]:
    """
    Build TAC VM from source after analyze + TAC generation.

    Returns (vm, None) on success or (None, error_dict) on failure.
    """
    program, err = analyze_and_build_program(source)
    if err is not None:
        return None, err
    assert program is not None
    try:
        quads = generate_tac_quads(program)
    except TacGenError as exc:
        return None, tacgen_error_dict(exc)
    layouts = {sd.name: dict(sd.fields) for sd in program.struct_definitions}
    return TacVM(
        quads, stdin=stdin, echo_input=echo_input, struct_layouts=layouts
    ), None
