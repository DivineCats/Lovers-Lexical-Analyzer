from Backend.Syntax.SimpleRecursiveDescentParser import SimpleRecursiveDescentParser, ParseError
from Backend.Lexical.Lexer import Lexer

# Test the exact scenario from the full file
source = """love () {
    forever (age <= 1) {
        express << "test";
    } 
    forevermore (age <= 4) {
        express << "test";
    } 
    foreerore (age <= 12) {
        express << "test";
    }
}"""

lexer = Lexer(source)
parser = SimpleRecursiveDescentParser(lexer)

print("Testing foreerore detection...")
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
