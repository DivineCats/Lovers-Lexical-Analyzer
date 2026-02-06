from flask import Flask, jsonify, request
from flask_cors import CORS

from Backend.Lexical import Lexer, tokens_as_rows, tokenize_with_errors
from Backend.Lexical.Lexer import LexerError
from Backend.Syntax import parse_with_errors_parserv2, create_error_context

app = Flask(__name__)
CORS(app, resources={r"/lex": {"origins": "*"}, r"/validate": {"origins": "*"}})

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
            "message": "Expected program to start with love () { }.",
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

    return jsonify({
        "ok": True,
        "message": f"Syntax OK - No errors found (using {parser_type} parser)",
        "parser": parser_type
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # flip debug=False for production
