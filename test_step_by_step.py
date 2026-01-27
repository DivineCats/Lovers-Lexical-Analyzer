from Backend.Syntax.SimpleRecursiveDescentParser import parse_with_errors_simple_rd

# Test step by step to find where the error is lost
print("Test 1: Just foreerore")
source1 = """love () {
    foreerore (x) { }
}"""
program1, errors1 = parse_with_errors_simple_rd(source1)
print(f'  Errors: {len(errors1)}, Program is None: {program1 is None}')

print("\nTest 2: foreerore after forever")
source2 = """love () {
    forever (x) { }
    foreerore (x) { }
}"""
program2, errors2 = parse_with_errors_simple_rd(source2)
print(f'  Errors: {len(errors2)}, Program is None: {program2 is None}')

print("\nTest 3: foreerore after forevermore")
source3 = """love () {
    forever (x) { }
    forevermore (x) { }
    foreerore (x) { }
}"""
program3, errors3 = parse_with_errors_simple_rd(source3)
print(f'  Errors: {len(errors3)}, Program is None: {program3 is None}')

print("\nTest 4: Full file")
source4 = """love () {
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
program4, errors4 = parse_with_errors_simple_rd(source4)
print(f'  Errors: {len(errors4)}, Program is None: {program4 is None}')
if errors4:
    for e in errors4:
        print(f'    {e.message}')
