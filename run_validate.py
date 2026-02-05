import sys
from pathlib import Path

# Ensure project root is on sys.path so `Backend` can be imported when run from anywhere.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Lexical import Lexer, tokenize_with_errors
from Backend.Lexical.Lexer import LexerError
from Backend.Syntax import parse_with_errors_parserv2, create_error_context
from Backend.Syntax.errors import SyntaxError as ParserSyntaxError


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python run_validate.py <source_file> [--tree]")
        return 1

    src_path = Path(sys.argv[1])
    show_tree = "--tree" in sys.argv
    
    if not src_path.exists():
        print(f"File not found: {src_path}")
        return 1

    source = src_path.read_text(encoding="utf-8")
    
    # Phase 1: Lexical Analysis
    print("=" * 50)
    print("Phase 1: Lexical Analysis")
    print("=" * 50)
    
    try:
        tokens, lex_errors = tokenize_with_errors(source)
        if lex_errors:
            print("Lexical errors:")
            for e in lex_errors:
                print(" -", e)
            return 1
        print("Lexing successful!")
        print(f"  Tokens generated: {len(tokens)}")
    except LexerError as exc:
        print(f"Lexing failed: {exc}")
        return 1
    except Exception as exc:
        print(f"Lexing failed: {exc}")
        return 1

    # Phase 2: Syntax Analysis
    print()
    print("=" * 50)
    print("Phase 2: Syntax Analysis")
    print("=" * 50)
    
    try:
        tree, syntax_errors = parse_with_errors_parserv2(source)
        
        if syntax_errors:
            print("Syntax errors:")
            for err in syntax_errors:
                print()
                print(f" - {err}")
                # Show error context
                context = create_error_context(source, err.line, err.column)
                print()
                print(context)
            return 1
        
        print("Parsing successful!")
        
        if show_tree and tree:
            print()
            print("Parse Tree:")
            print("-" * 40)
            print(tree.pretty())
        
        return 0
        
    except ParserSyntaxError as exc:
        print(f"Parsing failed: {exc}")
        context = create_error_context(source, exc.line, exc.column)
        print()
        print(context)
        return 1
    except Exception as exc:
        print(f"Parsing failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
