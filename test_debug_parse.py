from Backend.Syntax.SimpleRecursiveDescentParser import SimpleRecursiveDescentParser, ParseError
from Backend.Lexical.Lexer import Lexer

# Test 3 scenario
source = """love () {
    forever (x) { }
    forevermore (x) { }
    foreerore (x) { }
}"""

lexer = Lexer(source)
tokens = lexer.scan_tokens()
parser = SimpleRecursiveDescentParser(lexer)

# Print tokens to see what we're parsing
print("Tokens:")
for i, token in enumerate(tokens[:30]):  # First 30 tokens
    print(f"  {i}: {token.kind} = '{token.lexeme}' (line {token.line}, col {token.column})")

print("\nParsing...")
try:
    program = parser.parse()
    print(f'SUCCESS: Program parsed successfully: {program is not None}')
    print(f'Errors in parser.errors: {len(parser.errors)}')
    for e in parser.errors:
        print(f'  {e.message}')
except ParseError as e:
    print(f'ERROR RAISED: {e.message}')
    print(f'Errors in parser.errors: {len(parser.errors)}')
    for err in parser.errors:
        print(f'  {err.message}')
