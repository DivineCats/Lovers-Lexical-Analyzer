from Backend.Syntax.SimpleRecursiveDescentParser import parse_with_errors_simple_rd
import sys

source = """love () {
    dear age;

    express << "Enter your age: ";
    give >> age;

    express << "You entered " << age << ". You are ";

    forever (age <= 1) {
        express << "a Baby." << periodt;
    } 
    forevermore (age <= 4) {
        express << "a Toddler." << periodt;
    } 
    foreerore (age <= 12) {
        express << "a Child." << periodt;
    } 
    forevermore (age <= 17) {
        express << "a Teenager." << periodt;
    } 
    forevermore (age <= 59) {
        express << "an Adult." << periodt;
    } 
    more {
        exprss << "a Senior Citizen." << periodt;
    }
}"""

print("Parsing...", file=sys.stderr)
program, errors = parse_with_errors_simple_rd(source)
print(f'Errors: {len(errors)}', file=sys.stderr)
for e in errors:
    print(f'  {e.message} (line {e.line}, col {e.column})', file=sys.stderr)
print(f'Program is None: {program is None}', file=sys.stderr)
