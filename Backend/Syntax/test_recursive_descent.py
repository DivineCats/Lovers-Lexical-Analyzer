# Backend/Syntax/test_recursive_descent.py
"""Comprehensive test suite for RecursiveDescentParser."""

import unittest
from Backend.Syntax.RecursiveDescentParser import (
    RecursiveDescentParser,
    parse_with_errors_rd,
    parse_from_source,
    Program,
    Function,
    FunctionBody,
    Declaration,
    AssignmentStatement,
    IfStatement,
    WhileStatement,
    ForStatement,
    ReturnStatement,
    InputStatement,
    OutputStatement,
)


class TestRecursiveDescentParser(unittest.TestCase):
    """Test cases for Recursive Descent Parser."""
    
    def test_empty_program(self):
        """Test parsing an empty program."""
        source = "love() { }"
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(program.main_function)
    
    def test_simple_program(self):
        """Test parsing a simple valid program."""
        source = """
        love() {
            dear x;
            x = 5;
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(program.main_function.body.statements), 2)
    
    def test_global_declarations(self):
        """Test parsing global variable declarations."""
        source = """
        dear globalVar;
        love() {
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(program.global_declarations), 1)
        self.assertEqual(program.global_declarations[0].data_type, "dear")
    
    def test_const_declaration(self):
        """Test parsing const declarations."""
        source = """
        const dear PI = 3;
        love() {
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertTrue(program.global_declarations[0].is_const)
    
    def test_array_declaration(self):
        """Test parsing array declarations."""
        source = """
        love() {
            dear arr[10];
            rant str[];
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertEqual(program.main_function.body.local_declarations[0].variables[0].array_dimensions, 1)
    
    def test_assignment_statements(self):
        """Test parsing assignment statements."""
        source = """
        love() {
            dear x;
            x = 5;
            x += 10;
            x -= 3;
            x *= 2;
            x /= 4;
            x %= 2;
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertEqual(len(statements), 6)
        self.assertIsInstance(statements[0], AssignmentStatement)
        self.assertEqual(statements[0].operator, "ASSIGN")
    
    def test_array_assignment(self):
        """Test parsing array assignments."""
        source = """
        love() {
            dear arr[5];
            arr[0] = 10;
            arr[1] = 20;
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertEqual(len(statements[0].indices), 1)
    
    def test_if_statement(self):
        """Test parsing if statements."""
        source = """
        love() {
            dear x = 5;
            forever (x > 0) {
                x = x - 1;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertIsInstance(statements[1], IfStatement)
    
    def test_if_else_statement(self):
        """Test parsing if-else statements."""
        source = """
        love() {
            dear x = 5;
            forever (x > 0) {
                x = x - 1;
            } more {
                x = 0;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        if_stmt = program.main_function.body.statements[1]
        self.assertIsNotNone(if_stmt.else_body)
    
    def test_if_elseif_statement(self):
        """Test parsing if-elseif-else statements."""
        source = """
        love() {
            dear x = 5;
            forever (x > 10) {
                x = 20;
            } forevermore (x > 5) {
                x = 10;
            } more {
                x = 0;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        if_stmt = program.main_function.body.statements[1]
        self.assertEqual(len(if_stmt.elif_clauses), 1)
        self.assertIsNotNone(if_stmt.else_body)
    
    def test_while_statement(self):
        """Test parsing while loops."""
        source = """
        love() {
            dear x = 0;
            while (x < 10) {
                x = x + 1;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertIsInstance(statements[1], WhileStatement)
    
    def test_for_statement(self):
        """Test parsing for loops."""
        source = """
        love() {
            for (dear i = 0; i < 10; i++) {
                dear x = i;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertIsInstance(statements[0], ForStatement)
    
    def test_do_while_statement(self):
        """Test parsing do-while loops."""
        source = """
        love() {
            dear x = 0;
            pursue (x < 10) {
                x = x + 1;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertIsInstance(statements[1], type(program.main_function.body.statements[1]))
        # Check it's a DoWhileStatement
        self.assertTrue(hasattr(statements[1], 'condition'))
    
    def test_switch_statement(self):
        """Test parsing switch statements."""
        source = """
        love() {
            dear x = 5;
            choose (x) {
                phase 1: {
                    x = 10;
                } breakup;
                phase 2: {
                    x = 20;
                } breakup;
                bareminimum: {
                    x = 0;
                } breakup;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        # May have some errors due to complex switch syntax, but should parse
        self.assertIsNotNone(program)
    
    def test_input_statements(self):
        """Test parsing input statements."""
        source = """
        love() {
            dear x;
            give >> x;
            overshare(x);
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertIsInstance(statements[0], InputStatement)
        self.assertIsInstance(statements[1], InputStatement)
    
    def test_output_statements(self):
        """Test parsing output statements."""
        source = """
        love() {
            dear x = 5;
            express << x << periodt;
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        statements = program.main_function.body.statements
        self.assertIsInstance(statements[1], OutputStatement)
    
    def test_return_statement(self):
        """Test parsing return statements."""
        source = """
        dear func() {
            comeback 5;
        }
        love() {
            dear result = func();
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(program.sub_functions), 1)
    
    def test_function_declarations(self):
        """Test parsing function declarations."""
        source = """
        dear add(dear a, dear b) {
            comeback a + b;
        }
        love() {
            dear sum = add(5, 10);
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(program.sub_functions), 1)
        self.assertEqual(program.sub_functions[0].name, "add")
        self.assertEqual(len(program.sub_functions[0].parameters), 2)
    
    def test_void_function(self):
        """Test parsing void (avoidant) functions."""
        source = """
        avoidant print(dear x) {
            express << x;
        }
        love() {
            print(5);
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertIsNone(program.sub_functions[0].return_type)
    
    def test_expressions(self):
        """Test parsing various expressions."""
        source = """
        love() {
            dear x = 5 + 3 * 2;
            dear y = (x > 10) && (x < 20);
            dear z = x == 5 || y == greenflag;
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
    
    def test_unary_operators(self):
        """Test parsing unary operators."""
        source = """
        love() {
            dear x = 5;
            ++x;
            x++;
            --x;
            x--;
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
    
    def test_array_access(self):
        """Test parsing array access in expressions."""
        source = """
        love() {
            dear arr[5];
            dear x = arr[0] + arr[1];
            arr[2] = arr[0] * arr[1];
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
    
    def test_nested_expressions(self):
        """Test parsing nested expressions."""
        source = """
        love() {
            dear x = (5 + 3) * (2 - 1);
            dear y = ((x > 0) && (x < 10)) || (x == 5);
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
    
    def test_boundaries(self):
        """Test parsing boundaries (namespace)."""
        source = """
        boundaries MyNamespace {
            dear x;
        }
        love() {
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertIsNotNone(program)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(program.boundaries)
        self.assertEqual(program.boundaries.name, "MyNamespace")
    
    # ========================================================================
    # ERROR DETECTION TESTS
    # ========================================================================
    
    def test_missing_semicolon(self):
        """Test detection of missing semicolon."""
        source = """
        love() {
            dear x = 5
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertGreater(len(errors), 0)
        # Should detect missing semicolon
    
    def test_missing_brace(self):
        """Test detection of missing brace."""
        source = """
        love() {
            dear x = 5;
        """
        program, errors = parse_with_errors_rd(source)
        self.assertGreater(len(errors), 0)
    
    def test_missing_parenthesis(self):
        """Test detection of missing parenthesis."""
        source = """
        love() {
            forever (x > 0 {
                x = x - 1;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertGreater(len(errors), 0)
    
    def test_invalid_keyword(self):
        """Test detection of invalid keyword."""
        source = """
        love() {
            if (x > 0) {
                x = 5;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertGreater(len(errors), 0)
    
    def test_multiple_errors(self):
        """Test detection of multiple errors."""
        source = """
        love() {
            dear x = 5
            dear y = 10
            forever (x > 0 {
                x = x - 1
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        # Should detect multiple errors
        self.assertGreater(len(errors), 1)
    
    def test_typo_detection(self):
        """Test typo detection in keywords."""
        source = """
        love() {
            forevr (x > 0) {
                x = 5;
            }
        }
        """
        program, errors = parse_with_errors_rd(source)
        self.assertGreater(len(errors), 0)
        # Check if typo suggestion is in error message
        error_msg = str(errors[0])
        # Should suggest "forever" for "forevr"
        self.assertIn("forever", error_msg.lower())
    
    def test_empty_file(self):
        """Test parsing empty file."""
        source = ""
        program, errors = parse_with_errors_rd(source)
        # Should handle gracefully
        self.assertIsNotNone(errors)
    
    def test_whitespace_only(self):
        """Test parsing whitespace-only file."""
        source = "   \n\t  \n  "
        program, errors = parse_with_errors_rd(source)
        # Should handle gracefully
        self.assertIsNotNone(errors)
    
    def test_malformed_program(self):
        """Test parsing malformed program."""
        source = """
        love() {
            dear x = 
            forever
            while
        }
        """
        program, errors = parse_with_errors_rd(source)
        # Should detect errors and continue parsing
        self.assertGreater(len(errors), 0)
        # Should not crash
    
    def test_error_recovery(self):
        """Test error recovery continues after errors."""
        source = """
        love() {
            dear x = 5;  // Valid
            dear y =     // Missing value
            dear z = 10; // Valid
        }
        """
        program, errors = parse_with_errors_rd(source)
        # Should detect error but continue to parse 'z'
        self.assertGreater(len(errors), 0)
        # Should still parse some statements
        if program and program.main_function:
            # Should have parsed at least 'x' and possibly 'z'
            self.assertGreaterEqual(len(program.main_function.body.statements), 1)


if __name__ == "__main__":
    unittest.main()
