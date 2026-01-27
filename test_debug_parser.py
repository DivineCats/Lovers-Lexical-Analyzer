from Backend.Lexical.Lexer import Lexer
from Backend.Syntax.SimpleRecursiveDescentParser import SimpleRecursiveDescentParser, ParseError

source = """love () {
    exprss << "test";
}"""

lexer = Lexer(source)
parser = SimpleRecursiveDescentParser(lexer)

# Print all tokens
print("Tokens:")
for i, token in enumerate(lexer.tokens):
    print(f"  {i}: {token.kind} = '{token.lexeme}'")

# Try to parse
try:
    program = parser.parse()
    print(f"\nParsing succeeded! Program: {program}")
except ParseError as e:
    print(f"\nParseError raised: {e.message}")
    print(f"  Line: {e.line}, Column: {e.column}")
    print(f"  Errors in parser.errors: {len(parser.errors)}")
    for err in parser.errors:
        print(f"    - {err.message}")
