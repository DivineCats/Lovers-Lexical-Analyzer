#!/usr/bin/env python3
"""Test cases for error recovery - copy and paste these into your test."""

# ============================================================================
# TEST CASE 1: Missing Semicolons (Most Common Error)
# ============================================================================
test_case_1 = """
love main() {
    dear x = 10
    dearest y = 20.5
    rant name = "hello"
    
    x = y + 10
    express << x << periodt;
}
"""

# ============================================================================
# TEST CASE 2: Multiple Independent Errors
# ============================================================================
test_case_2 = """
love main() {
    dear x = 10
    dearest y = 20.5
    rant z = "test"
    
    x = y + z
    express << x << periodt;
    
    forever (x > 5) {
        express << "x is big" << periodt;
    }
}
"""

# ============================================================================
# TEST CASE 3: Missing Braces
# ============================================================================
test_case_3 = """
love main() {
    dear x = 10;
    forever (x > 5) {
        express << x << periodt;
    // Missing closing brace
"""

# ============================================================================
# TEST CASE 4: Wrong Operators
# ============================================================================
test_case_4 = """
love main() {
    dear x = 10;
    dear y = 20;
    
    if (x == y) {  // Wrong: should be forever
        express << "equal" << periodt;
    }
}
"""

# ============================================================================
# TEST CASE 5: Reserved Word as Identifier
# ============================================================================
test_case_5 = """
love main() {
    dear love = 10;  // Error: 'love' is reserved
    dearest forever = 20.5;  // Error: 'forever' is reserved
    rant while = "test";  // Error: 'while' is reserved
    
    express << love << periodt;
}
"""

# ============================================================================
# TEST CASE 6: Missing Parentheses
# ============================================================================
test_case_6 = """
love main() {
    dear x = 10;
    
    forever x > 5 {  // Missing parentheses
        express << x << periodt;
    }
}
"""

# ============================================================================
# TEST CASE 7: Incomplete Declarations
# ============================================================================
test_case_7 = """
love main() {
    dear x  // Missing = and value
    dearest y =  // Missing value
    rant z  // Missing = and value
    
    express << x << periodt;
}
"""

# ============================================================================
# TEST CASE 8: Multiple Errors in Nested Structures
# ============================================================================
test_case_8 = """
love main() {
    dear x = 10
    dear y = 20
    
    forever (x > y) {
        dear z = x + y
        express << z << periodt;
        
        if (z > 30) {  // Wrong: should be forever
            express << "big" << periodt;
        }
    }
}
"""

# ============================================================================
# TEST CASE 9: Function Call Errors
# ============================================================================
test_case_9 = """
love main() {
    dear x = 10;
    
    func(x, y, z  // Missing closing parenthesis
    express << x << periodt;
}
"""

# ============================================================================
# TEST CASE 10: Array Declaration Errors
# ============================================================================
test_case_10 = """
love main() {
    dear arr[10];  // Missing proper array syntax
    dear arr2[] = {1, 2, 3  // Missing closing brace
    express << arr[0] << periodt;
}
"""

# ============================================================================
# TEST CASE 11: Mixed Errors - Realistic Scenario
# ============================================================================
test_case_11 = """
boundaries math {
    dear x = 10
    dearest y = 20.5
    
    love calculate() {
        dear result = x + y
        express << result << periodt;
        comeback result;
    }
}

love main() {
    dear a = 5
    dearest b = 10.5
    rant msg = "hello"
    
    a = b + 5
    express << a << periodt;
    
    forever (a > 10) {
        express << "big" << periodt;
        a = a - 1
    }
    
    comeback 0;
}
"""

# ============================================================================
# TEST CASE 12: Expression Errors
# ============================================================================
test_case_12 = """
love main() {
    dear x = 10;
    dear y = 20;
    
    x = x +  // Missing right operand
    y = * y;  // Missing left operand
    express << x << periodt;
}
"""

# ============================================================================
# TEST CASE 13: String/Output Errors
# ============================================================================
test_case_13 = """
love main() {
    rant name = "John
    rant msg = 'hello'  // Wrong quotes
    
    express << name << periodt;
    express << msg << periodt;
}
"""

# ============================================================================
# TEST CASE 14: Loop Errors
# ============================================================================
test_case_14 = """
love main() {
    dear i = 0;
    
    while (i < 10) {  // Wrong: should be 'forever'
        express << i << periodt;
        i = i + 1  // Missing semicolon
    }
    
    for (dear j = 0; j < 5; j++) {  // Wrong: should be 'for' with proper syntax
        express << j << periodt;
    }
}
"""

# ============================================================================
# TEST CASE 15: Return Statement Errors
# ============================================================================
test_case_15 = """
love main() {
    dear x = 10;
    
    comeback  // Missing value
    comeback x  // Missing semicolon
    comeback 0;
}
"""

# ============================================================================
# ALL TEST CASES (for easy copying)
# ============================================================================
ALL_TEST_CASES = {
    "Test 1: Missing Semicolons": test_case_1,
    "Test 2: Multiple Independent Errors": test_case_2,
    "Test 3: Missing Braces": test_case_3,
    "Test 4: Wrong Operators": test_case_4,
    "Test 5: Reserved Word as Identifier": test_case_5,
    "Test 6: Missing Parentheses": test_case_6,
    "Test 7: Incomplete Declarations": test_case_7,
    "Test 8: Multiple Errors in Nested Structures": test_case_8,
    "Test 9: Function Call Errors": test_case_9,
    "Test 10: Array Declaration Errors": test_case_10,
    "Test 11: Mixed Errors - Realistic": test_case_11,
    "Test 12: Expression Errors": test_case_12,
    "Test 13: String/Output Errors": test_case_13,
    "Test 14: Loop Errors": test_case_14,
    "Test 15: Return Statement Errors": test_case_15,
}

if __name__ == "__main__":
    print("=" * 70)
    print("ERROR RECOVERY TEST CASES")
    print("=" * 70)
    print("\nAvailable test cases:\n")
    for name, code in ALL_TEST_CASES.items():
        print(f"{name}:")
        print("-" * 70)
        print(code)
        print()
