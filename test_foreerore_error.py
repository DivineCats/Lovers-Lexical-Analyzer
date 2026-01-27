from Backend.Syntax.SimpleRecursiveDescentParser import parse_with_errors_simple_rd

source = """love () {
    forever (age <= 1) {
        express << "test";
    }
    foreerore (age <= 12) {
        express << "test";
    }
}"""

program, errors = parse_with_errors_simple_rd(source)
print(f'Errors: {len(errors)}')
for e in errors:
    print(f'  {e.message} (line {e.line}, col {e.column})')
print(f'Program is None: {program is None}')
