from Backend.Syntax.SimpleRecursiveDescentParser import parse_with_errors_simple_rd
import sys

# Test just "foreerore"
source1 = """love () {
    foreerore (age <= 12) {
        express << "test";
    }
}"""

print("=== Test 1: foreerore ===", file=sys.stderr)
program1, errors1 = parse_with_errors_simple_rd(source1)
print(f'Errors: {len(errors1)}', file=sys.stderr)
for e in errors1:
    print(f'  {e.message} (line {e.line}, col {e.column})', file=sys.stderr)

# Test just "exprss"
source2 = """love () {
    exprss << "test";
}"""

print("\n=== Test 2: exprss ===", file=sys.stderr)
program2, errors2 = parse_with_errors_simple_rd(source2)
print(f'Errors: {len(errors2)}', file=sys.stderr)
for e in errors2:
    print(f'  {e.message} (line {e.line}, col {e.column})', file=sys.stderr)
