from flask import Flask, jsonify, request
from flask_cors import CORS

from Backend.Lexical import Lexer, tokens_as_rows, tokenize_with_errors
from Backend.Lexical.Lexer import LexerError
from Backend.Syntax import parse_with_errors, parse_with_errors_rd, parse_with_errors_simple_rd, create_error_context

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
    parser_type = payload.get("parser", "lark")  # "lark", "rd" (recursive descent), or "simple_rd" (simple recursive descent)
    
    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400

    if not source.strip():
        return jsonify({
            "ok": False,
            "message": "Source is empty",
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
    if parser_type == "rd":
        # Use Recursive Descent Parser
        tree, syntax_errors = parse_with_errors_rd(source)
    elif parser_type == "simple_rd":
        # Use Simple Recursive Descent Parser (top-down, left-to-right with own AST)
        tree, syntax_errors = parse_with_errors_simple_rd(source)
    else:
        # Use Lark parser (default) - stops on first error
        tree, syntax_errors = parse_with_errors(source)
    
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
