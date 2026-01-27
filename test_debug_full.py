from Backend.Syntax.SimpleRecursiveDescentParser import SimpleRecursiveDescentParser, ParseError
from Backend.Lexical.Lexer import Lexer

source = """love () {
    foreerore (age <= 12) {
        express << "test";
    }
}"""

lexer = Lexer(source)
parser = SimpleRecursiveDescentParser(lexer)

try:
    program = parser.parse()
    print(f'Parsed successfully: {program is not None}')
    print(f'Errors in parser.errors: {len(parser.errors)}')
    for e in parser.errors:
        print(f'  {e.message}')
except ParseError as e:
    print(f'ParseError raised: {e.message}')
    print(f'Errors in parser.errors: {len(parser.errors)}')
    for err in parser.errors:
        print(f'  {err.message}')
