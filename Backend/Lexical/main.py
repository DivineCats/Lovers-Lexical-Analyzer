import os
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS

from Backend.Lexical import Lexer, tokens_as_rows, tokenize_with_errors
from Backend.Lexical.Lexer import LexerError
from Backend.Syntax import parse_with_errors_parserv2, create_error_context
from Backend.Semantic import analyze_semantics


RUN_SESSIONS = {}


debug = os.environ.get("FLASK_DEBUG", "0") == "1"

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/lex": {"origins": "*"},
        r"/validate": {"origins": "*"},
        r"/run": {"origins": "*"},
        r"/run/start": {"origins": "*"},
        r"/run/input": {"origins": "*"},
        r"/tac": {"origins": "*"},
    },
)


@app.get("/")
def root_health():
    return jsonify({"ok": True, "service": "lovers-lexical-analyzer"}), 200


@app.get("/health")
def health():
    return jsonify({"ok": True, "status": "healthy"}), 200


@app.get("/compiler")
def compiler():
    return jsonify({"ok": True}), 200

@app.post("/lex")
def lex():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400

    try:
        tokens, errors = tokenize_with_errors(source)
        payload = {"rows": tokens_as_rows(tokens)}
        if errors:
            payload["error"] = errors[0]
            payload["errors"] = errors
        return jsonify(payload), 200
    except LexerError as exc:
        # Return partial tokens with the error so UI can show stream + terminal error.
        rows = tokens_as_rows(getattr(exc, "tokens", []) or [])
        return jsonify({"rows": rows, "error": f"Lexing failed: {exc}"}), 200
    except Exception as exc:
        return jsonify({"error": f"Lexing failed: {exc}"}), 400

    return jsonify({"rows": tokens_as_rows(tokens)})


@app.post("/validate")
def validate():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    # Supported parser types:
    # - "parserv2": LL(1) Table-Driven (default)
    # - "rd": legacy alias to parserv2 (kept for UI compatibility)
    parser_type = payload.get("parser", "parserv2")
    
    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400

    if not source.strip():
        return jsonify({
            "ok": False,
            "message": "A main program is needed in order to run.",
            "code": "ERR_EMPTY"
        }), 400

    # First run lexical analysis
    try:
        tokens, lex_errors = tokenize_with_errors(source)
        if lex_errors:
            return jsonify({
                "ok": False,
                "message": lex_errors[0],
                "code": "ERR_LEXICAL",
                "errors": [{"message": e, "code": "ERR_LEXICAL"} for e in lex_errors]
            }), 200
    except LexerError as exc:
        return jsonify({
            "ok": False,
            "message": str(exc),
            "code": "ERR_LEXICAL"
        }), 200

    # Then run syntax analysis - choose parser based on request
    # Both 'parserv2' and legacy 'rd' alias map to the LL(1) parser.
    tree, syntax_errors = parse_with_errors_parserv2(source)
    
    if syntax_errors:
        errors_list = []
        for err in syntax_errors:
            error_detail = {
                "ok": False,
                "message": err.message,
                "code": "ERR_SYNTAX",
                "line": err.line,
                "column": err.column,
                "expected": err.expected,
                "found": err.found,
                "context": create_error_context(source, err.line, err.column)
            }
            errors_list.append(error_detail)
        
        return jsonify({
            "ok": False,
            "message": syntax_errors[0].message,
            "code": "ERR_SYNTAX",
            "line": syntax_errors[0].line,
            "column": syntax_errors[0].column,
            "expected": syntax_errors[0].expected,
            "errors": errors_list,
            "parser": parser_type  # Include which parser was used
        }), 200

    semantic_errors = analyze_semantics(tokens)
    if semantic_errors:
        semantic_payload = [e.to_dict() for e in semantic_errors]
        return jsonify({
            "ok": False,
            "message": semantic_payload[0]["message"],
            "code": "ERR_SEMANTIC",
            "semantic_errors": semantic_payload,
            "parser": parser_type,
        }), 200

    # ICG (TAC generation): surface codegen failures as semantic-tab errors so Run / Output stays clean.
    from Backend.Syntax.parsetv2 import parse_with_ast
    from Backend.IR.tac import TacGenError, generate_tac_quads
    from Backend.IR.runtime_messages import humanize_icg_message

    program, ast_errors = parse_with_ast(tokens, source_code=source)
    if ast_errors:
        raw = str(ast_errors[0])
        friendly = humanize_icg_message(raw)
        return jsonify({
            "ok": False,
            "message": friendly,
            "code": "ERR_SEMANTIC",
            "semantic_errors": [{
                "message": friendly,
                "line": 1,
                "column": 1,
                "code": "ERR_ICG",
            }],
            "parser": parser_type,
            "detail": raw,
        }), 200

    if program is None:
        return jsonify({
            "ok": False,
            "message": "Program build failed after semantic analysis.",
            "code": "ERR_SEMANTIC",
            "semantic_errors": [{
                "message": "Program build failed after semantic analysis.",
                "line": 1,
                "column": 1,
                "code": "ERR_ICG",
            }],
            "parser": parser_type,
        }), 200

    try:
        generate_tac_quads(program)
    except TacGenError as exc:
        raw = str(exc)
        friendly = humanize_icg_message(raw)
        return jsonify({
            "ok": False,
            "message": friendly,
            "code": "ERR_SEMANTIC",
            "semantic_errors": [{
                "message": friendly,
                "line": 1,
                "column": 1,
                "code": "ERR_ICG",
            }],
            "parser": parser_type,
            "detail": raw,
        }), 200

    return jsonify({
        "ok": True,
        "message": f"Syntax OK - No errors found (using {parser_type} parser)",
        "parser": parser_type,
    }), 200


@app.post("/run")
def run_program():
    """Lex → syntax → semantic → AST → TAC (ICG) → VM. Optional `stdin` string for input."""
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    stdin = payload.get("stdin", "")

    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400
    if not isinstance(stdin, str):
        stdin = ""

    if not source.strip():
        return jsonify({
            "ok": False,
            "message": "A main program is needed in order to run.",
            "code": "ERR_EMPTY",
        }), 400

    from Backend.IR.exec import run_lovers_source

    stdout, stderr, err = run_lovers_source(source, stdin=stdin)
    if err is not None:
        return jsonify({"ok": False, **err}), 200

    return jsonify({
        "ok": True,
        "stdout": stdout or "",
        "stderr": stderr or "",
    }), 200


@app.post("/run/start")
def run_program_start():
    """Start interactive run and pause on input (`give`) when needed."""
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    stdin = payload.get("stdin", "")
    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400
    if not isinstance(stdin, str):
        stdin = ""

    if not source.strip():
        return jsonify({
            "ok": False,
            "message": "A main program is needed in order to run.",
            "code": "ERR_EMPTY",
        }), 400

    from Backend.IR.exec import create_vm_from_source
    from Backend.IR.runtime_messages import humanize_runtime_message
    from Backend.IR.vm import VMError

    vm, err = create_vm_from_source(source, stdin=stdin, echo_input=True)
    if err is not None:
        return jsonify({"ok": False, **err}), 200
    assert vm is not None
    try:
        state = vm.run_until_input()
    except VMError as exc:
        raw = str(exc)
        return jsonify({
            "ok": False,
            "phase": "runtime",
            "message": humanize_runtime_message(raw),
            "detail": raw,
            "stdout": vm.stdout.getvalue(),
        }), 200

    if state.get("state") == "waiting_input":
        session_id = str(uuid.uuid4())
        RUN_SESSIONS[session_id] = vm
        return jsonify({
            "ok": True,
            "state": "waiting_input",
            "session_id": session_id,
            "stdout": vm.stdout.getvalue(),
            "input_kind": state.get("kind"),
        }), 200

    return jsonify({
        "ok": True,
        "state": "finished",
        "stdout": vm.stdout.getvalue(),
        "stderr": "",
    }), 200


@app.post("/run/input")
def run_program_input():
    """Continue an interactive run by supplying one line of user input."""
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id", "")
    user_input = payload.get("input", "")

    if not isinstance(session_id, str) or not session_id.strip():
        return jsonify({"ok": False, "message": "`session_id` is required."}), 400
    if not isinstance(user_input, str):
        user_input = str(user_input)

    vm = RUN_SESSIONS.get(session_id)
    if vm is None:
        return jsonify({"ok": False, "message": "Run session not found or expired."}), 404

    from Backend.IR.runtime_messages import humanize_runtime_message
    from Backend.IR.vm import VMError

    try:
        vm.provide_input(user_input)
        state = vm.run_until_input()
    except VMError as exc:
        RUN_SESSIONS.pop(session_id, None)
        raw = str(exc)
        return jsonify({
            "ok": False,
            "phase": "runtime",
            "message": humanize_runtime_message(raw),
            "detail": raw,
            "stdout": vm.stdout.getvalue(),
        }), 200

    if state.get("state") == "waiting_input":
        return jsonify({
            "ok": True,
            "state": "waiting_input",
            "session_id": session_id,
            "stdout": vm.stdout.getvalue(),
            "input_kind": state.get("kind"),
        }), 200

    RUN_SESSIONS.pop(session_id, None)
    return jsonify({
        "ok": True,
        "state": "finished",
        "stdout": vm.stdout.getvalue(),
        "stderr": "",
    }), 200


@app.post("/tac")
def tac_program():
    """Lex → syntax → semantic → AST → three-address code (ICG)."""
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")

    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400

    if not source.strip():
        return jsonify({
            "ok": False,
            "message": "A main program is needed in order to run.",
            "code": "ERR_EMPTY",
        }), 400

    from Backend.IR.tac import lovers_source_to_tac

    tac_text, err = lovers_source_to_tac(source)
    if err is not None:
        return jsonify({"ok": False, **err}), 200

    return jsonify({"ok": True, "tac": tac_text or ""}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
