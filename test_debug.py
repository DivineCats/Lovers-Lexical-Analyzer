import traceback
from Backend.Syntax import parse_with_errors_rd

source = """
        love() {
            dear x;
            x = 5;
        }
        """

try:
    program, errors = parse_with_errors_rd(source)
    print(f'Success: {program is not None}')
    print(f'Errors: {len(errors)}')
    for e in errors:
        print(f'Error: {e.message}')
except Exception as e:
    traceback.print_exc()
