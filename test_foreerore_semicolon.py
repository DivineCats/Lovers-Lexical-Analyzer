from Backend.Syntax.SimpleRecursiveDescentParser import SimpleRecursiveDescentParser, ParseError
from Backend.Lexical.Lexer import Lexer

# Test if function call parsing catches the error when it expects semicolon but finds brace
source = """love () {
    foreerore (age <= 12) {
        express << "test";
    }
}"""

lexer = Lexer(source)
parser = SimpleRecursiveDescentParser(lexer)

print("Testing if function call parsing catches the error...")
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
