import sys
from pathlib import Path

# Ensure project root is on sys.path so `Backend` can be imported when run from anywhere.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Lexical import Lexer, tokenize_with_errors
from Backend.Lexical.Lexer import LexerError


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python run_validate.py <source_file>")
        return 1

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"File not found: {src_path}")
        return 1

    source = src_path.read_text(encoding="utf-8")
    try:
        tokens, lex_errors = tokenize_with_errors(source)
        if lex_errors:
            print("Lexical errors:")
            for e in lex_errors:
                print(" -", e)
            return 1
        print("Lexing successful!")
        return 0
    except LexerError as exc:  # pragma: no cover - defensive user feedback
        print(f"Lexing failed: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive user feedback
        print(f"Lexing failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
