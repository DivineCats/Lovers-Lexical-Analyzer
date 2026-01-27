from Backend.Syntax.SimpleRecursiveDescentParser import SimpleRecursiveDescentParser, ParseError
from Backend.Lexical.Lexer import Lexer

# Test 3 scenario - why isn't it being caught?
source = """love () {
    forever (x) { }
    forevermore (x) { }
    foreerore (x) { }
}"""

lexer = Lexer(source)
parser = SimpleRecursiveDescentParser(lexer)

print("Testing why foreerore isn't caught after forevermore...")
try:
    program = parser.parse()
    print(f'SUCCESS: Program parsed successfully: {program is not None}')
    print(f'Errors in parser.errors: {len(parser.errors)}')
    for e in parser.errors:
        print(f'  {e.message}')
    
    # Check what statements were parsed
    if program and program.main_function and program.main_function.body:
        print(f'\nStatements parsed: {len(program.main_function.body.statements)}')
        for i, stmt in enumerate(program.main_function.body.statements):
            stmt_type = type(stmt).__name__
            print(f'  Statement {i}: {stmt_type}')
            if hasattr(stmt, 'identifier'):
                print(f'    Identifier: {stmt.identifier}')
except ParseError as e:
    print(f'ERROR RAISED: {e.message}')
    print(f'Errors in parser.errors: {len(parser.errors)}')
    for err in parser.errors:
        print(f'  {err.message}')
