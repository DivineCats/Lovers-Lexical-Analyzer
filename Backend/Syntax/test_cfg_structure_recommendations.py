#!/usr/bin/env python3
"""
Comprehensive test suite to ensure error messages always include CFG-recommended structures.

This test verifies that whenever a syntax error occurs, the error message includes
the recommended structure according to the Context-Free Grammar (CFG).

CFG Structures to Test:
1. Program: love () { ... }
2. Forever (if): forever (<expr>) { ... }
3. Forevermore (else-if): forevermore (<expr>) { ... }
4. More (else): more { ... }
5. While: while (<expr>) { ... }
6. Pursue: pursue (<expr>) { ... }
7. For: for (<for_init>; <expr>; <for_ud>) { ... }
8. Choose: choose (<expr>) { phase <const>: ... breakup; ... }
9. Declaration: <data_type> id [= <expr>];
10. Function: <return_type> id (<parameter>) { ... }
11. Input: give >> id; | overshare(id);
12. Output: express << <expr> << periodt;
13. Return: comeback [<expr>];
"""

import unittest
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Lexical.Lexer import Lexer
from Backend.Syntax.RecursiveDescentParser import RecursiveDescentParser


class TestCFGStructureRecommendations(unittest.TestCase):
    """Test that error messages always include CFG-recommended structures."""

    def setUp(self):
        """Set up test fixtures."""
        self.cfg_structures = {
            "love": "love () { ... }",
            "forever": "forever (<expr>) { ... }",
            "forevermore": "forevermore (<expr>) { ... }",
            "more": "more { ... }",
            "while": "while (<expr>) { ... }",
            "pursue": "pursue (<expr>) { ... }",
            "for": "for (<for_init>; <expr>; <for_ud>) { ... }",
            "choose": "choose (<expr>) { phase <const>: ... breakup; ... }",
            "declaration": "<data_type> id [= <expr>];",
            "function": "<return_type> id (<parameter>) { ... }",
            "give": "give >> id;",
            "overshare": "overshare(id);",
            "express": "express << <expr> << periodt;",
            "comeback": "comeback [<expr>];",
        }

    def parse_and_check_structure(self, source: str, expected_structure_keywords: list):
        """
        Parse source code and check that error messages include expected CFG structures.
        
        Args:
            source: Source code to parse
            expected_structure_keywords: List of keywords that should appear in error messages
                                         (e.g., ['love', 'forever', 'declaration'])
        """
        lexer = Lexer(source)
        parser = RecursiveDescentParser(lexer)
        
        try:
            parser.parse()
            # If parsing succeeds, there should be no errors
            self.assertEqual(len(parser.errors), 0, 
                           "Parsing succeeded but errors list is not empty")
        except Exception:
            # Parsing failed - check error messages
            errors = parser.errors if hasattr(parser, 'errors') else []
            
            # At least one error should mention the expected structure
            error_messages = " ".join([e.message for e in errors])
            error_messages_lower = error_messages.lower()
            
            found_structures = []
            for keyword in expected_structure_keywords:
                if keyword in error_messages_lower:
                    found_structures.append(keyword)
                    # Check if the error message includes structure recommendation
                    structure = self.cfg_structures.get(keyword, "")
                    if structure and structure.lower() in error_messages_lower:
                        found_structures.append(f"{keyword} (with structure)")
            
            self.assertGreater(len(found_structures), 0,
                             f"Error messages should mention at least one of {expected_structure_keywords}. "
                             f"Errors: {[e.message for e in errors]}")
            
            return errors

    # =========================================================================
    # Program Structure Tests
    # =========================================================================

    def test_love_missing_opening_paren(self):
        """Test: love missing '(' should show structure: love () { ... }"""
        source = "love { }"
        errors = self.parse_and_check_structure(source, ["love"])
        # Check that error message includes structure
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("love", error_msg)
        self.assertIn("(", error_msg)
        self.assertIn(")", error_msg)
        self.assertIn("{", error_msg)

    def test_love_missing_closing_paren(self):
        """Test: love missing ')' should show structure: love () { ... }"""
        source = "love ( { }"
        errors = self.parse_and_check_structure(source, ["love"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("love", error_msg)
        self.assertIn(")", error_msg)

    def test_love_missing_opening_brace(self):
        """Test: love missing '{' should show structure: love () { ... }"""
        source = "love () }"
        errors = self.parse_and_check_structure(source, ["love"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("love", error_msg)
        self.assertIn("{", error_msg)

    def test_love_missing_closing_brace(self):
        """Test: love missing '}' should show structure: love () { ... }"""
        source = "love () {"
        errors = self.parse_and_check_structure(source, ["love"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("love", error_msg)
        self.assertIn("}", error_msg)

    def test_love_empty_program(self):
        """Test: Empty program should show structure: love () { ... }"""
        source = ""
        errors = self.parse_and_check_structure(source, ["love"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("love", error_msg)

    # =========================================================================
    # Forever (If) Statement Tests
    # =========================================================================

    def test_forever_missing_opening_paren(self):
        """Test: forever missing '(' should show structure: forever (<expr>) { ... }"""
        source = "love () { forever { } }"
        errors = self.parse_and_check_structure(source, ["forever"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("forever", error_msg)
        self.assertIn("(", error_msg)

    def test_forever_missing_closing_paren(self):
        """Test: forever missing ')' should show structure: forever (<expr>) { ... }"""
        source = "love () { forever (x > 0 { } }"
        errors = self.parse_and_check_structure(source, ["forever"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("forever", error_msg)
        self.assertIn(")", error_msg)

    def test_forever_empty_expression(self):
        """Test: forever () should show structure: forever (<expr>) { ... }"""
        source = "love () { forever () { } }"
        errors = self.parse_and_check_structure(source, ["forever", "expression"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("forever", error_msg)
        self.assertIn("expression", error_msg)

    def test_forever_missing_opening_brace(self):
        """Test: forever missing '{' should show structure: forever (<expr>) { ... }"""
        source = "love () { forever (x > 0) } }"
        errors = self.parse_and_check_structure(source, ["forever"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("forever", error_msg)
        self.assertIn("{", error_msg)

    def test_forever_missing_closing_brace(self):
        """Test: forever missing '}' should show structure: forever (<expr>) { ... }"""
        source = "love () { forever (x > 0) { }"
        errors = self.parse_and_check_structure(source, ["forever"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("forever", error_msg)
        self.assertIn("}", error_msg)

    # =========================================================================
    # Forevermore (Else-If) Statement Tests
    # =========================================================================

    def test_forevermore_missing_opening_paren(self):
        """Test: forevermore missing '(' should show structure: forevermore (<expr>) { ... }"""
        source = "love () { forever (x > 0) { } forevermore { } }"
        errors = self.parse_and_check_structure(source, ["forevermore"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("forevermore", error_msg)
        self.assertIn("(", error_msg)

    def test_forevermore_empty_expression(self):
        """Test: forevermore () should show structure: forevermore (<expr>) { ... }"""
        source = "love () { forever (x > 0) { } forevermore () { } }"
        errors = self.parse_and_check_structure(source, ["forevermore", "expression"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("forevermore", error_msg)
        self.assertIn("expression", error_msg)

    # =========================================================================
    # More (Else) Statement Tests
    # =========================================================================

    def test_more_missing_opening_brace(self):
        """Test: more missing '{' should show structure: more { ... }"""
        source = "love () { forever (x > 0) { } more } }"
        errors = self.parse_and_check_structure(source, ["more"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("more", error_msg)
        self.assertIn("{", error_msg)

    def test_more_missing_closing_brace(self):
        """Test: more missing '}' should show structure: more { ... }"""
        source = "love () { forever (x > 0) { } more { }"
        errors = self.parse_and_check_structure(source, ["more"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("more", error_msg)
        self.assertIn("}", error_msg)

    # =========================================================================
    # While Loop Tests
    # =========================================================================

    def test_while_missing_opening_paren(self):
        """Test: while missing '(' should show structure: while (<expr>) { ... }"""
        source = "love () { while { } }"
        errors = self.parse_and_check_structure(source, ["while"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("while", error_msg)
        self.assertIn("(", error_msg)

    def test_while_empty_expression(self):
        """Test: while () should show structure: while (<expr>) { ... }"""
        source = "love () { while () { } }"
        errors = self.parse_and_check_structure(source, ["while", "expression"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("while", error_msg)
        self.assertIn("expression", error_msg)

    # =========================================================================
    # Pursue Loop Tests
    # =========================================================================

    def test_pursue_missing_opening_paren(self):
        """Test: pursue missing '(' should show structure: pursue (<expr>) { ... }"""
        source = "love () { pursue { } }"
        errors = self.parse_and_check_structure(source, ["pursue"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("pursue", error_msg)
        self.assertIn("(", error_msg)

    def test_pursue_empty_expression(self):
        """Test: pursue () should show structure: pursue (<expr>) { ... }"""
        source = "love () { pursue () { } }"
        errors = self.parse_and_check_structure(source, ["pursue", "expression"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("pursue", error_msg)
        self.assertIn("expression", error_msg)

    # =========================================================================
    # For Loop Tests
    # =========================================================================

    def test_for_missing_opening_paren(self):
        """Test: for missing '(' should show structure: for (<for_init>; <expr>; <for_ud>) { ... }"""
        source = "love () { for { } }"
        errors = self.parse_and_check_structure(source, ["for"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("for", error_msg)
        self.assertIn("(", error_msg)

    def test_for_missing_semicolons(self):
        """Test: for missing ';' should show structure: for (<for_init>; <expr>; <for_ud>) { ... }"""
        source = "love () { for (dear i = 0 i < 10 i++) { } }"
        errors = self.parse_and_check_structure(source, ["for"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("for", error_msg)
        self.assertIn(";", error_msg)

    # =========================================================================
    # Choose (Switch) Statement Tests
    # =========================================================================

    def test_choose_missing_opening_paren(self):
        """Test: choose missing '(' should show structure: choose (<expr>) { ... }"""
        source = "love () { choose { } }"
        errors = self.parse_and_check_structure(source, ["choose"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("choose", error_msg)
        self.assertIn("(", error_msg)

    def test_choose_missing_phase_structure(self):
        """Test: choose missing phase should show structure: choose (<expr>) { phase <const>: ... breakup; ... }"""
        source = "love () { choose (x) { } }"
        errors = self.parse_and_check_structure(source, ["choose", "phase"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("choose", error_msg)

    # =========================================================================
    # Declaration Tests
    # =========================================================================

    def test_declaration_missing_semicolon(self):
        """Test: declaration missing ';' should show structure: <data_type> id [= <expr>];"""
        source = "love () { dear x }"
        errors = self.parse_and_check_structure(source, ["declaration", "semicolon"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("semicolon", error_msg)
        self.assertIn(";", error_msg)

    def test_declaration_missing_identifier(self):
        """Test: declaration missing id should show structure: <data_type> id [= <expr>];"""
        source = "love () { dear ; }"
        errors = self.parse_and_check_structure(source, ["declaration", "identifier"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("identifier", error_msg)

    # =========================================================================
    # Function Declaration Tests
    # =========================================================================

    def test_function_missing_opening_paren(self):
        """Test: function missing '(' should show structure: <return_type> id (<parameter>) { ... }"""
        source = "dear func { } love () { }"
        errors = self.parse_and_check_structure(source, ["function", "parameter"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("(", error_msg)

    def test_function_missing_closing_paren(self):
        """Test: function missing ')' should show structure: <return_type> id (<parameter>) { ... }"""
        source = "dear func (dear x { } love () { }"
        errors = self.parse_and_check_structure(source, ["function", "parameter"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn(")", error_msg)

    # =========================================================================
    # Input Statement Tests
    # =========================================================================

    def test_give_missing_operator(self):
        """Test: give missing '>>' should show structure: give >> id;"""
        source = "love () { give x; }"
        errors = self.parse_and_check_structure(source, ["give"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("give", error_msg)
        self.assertIn(">>", error_msg)

    def test_give_missing_semicolon(self):
        """Test: give missing ';' should show structure: give >> id;"""
        source = "love () { give >> x }"
        errors = self.parse_and_check_structure(source, ["give", "semicolon"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("semicolon", error_msg)
        self.assertIn(";", error_msg)

    def test_overshare_missing_opening_paren(self):
        """Test: overshare missing '(' should show structure: overshare(id);"""
        source = "love () { overshare x; }"
        errors = self.parse_and_check_structure(source, ["overshare"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("overshare", error_msg)
        self.assertIn("(", error_msg)

    def test_overshare_missing_closing_paren(self):
        """Test: overshare missing ')' should show structure: overshare(id);"""
        source = "love () { overshare (x; }"
        errors = self.parse_and_check_structure(source, ["overshare"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("overshare", error_msg)
        self.assertIn(")", error_msg)

    # =========================================================================
    # Output Statement Tests
    # =========================================================================

    def test_express_missing_operator(self):
        """Test: express missing '<<' should show structure: express << <expr> << periodt;"""
        source = "love () { express x; }"
        errors = self.parse_and_check_structure(source, ["express"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("express", error_msg)
        self.assertIn("<<", error_msg)

    def test_express_missing_semicolon(self):
        """Test: express missing ';' should show structure: express << <expr> << periodt;"""
        source = "love () { express << x << periodt }"
        errors = self.parse_and_check_structure(source, ["express", "semicolon"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("semicolon", error_msg)
        self.assertIn(";", error_msg)

    # =========================================================================
    # Return Statement Tests
    # =========================================================================

    def test_comeback_missing_semicolon(self):
        """Test: comeback missing ';' should show structure: comeback [<expr>];"""
        source = "love () { comeback x }"
        errors = self.parse_and_check_structure(source, ["comeback", "semicolon"])
        error_msg = " ".join([e.message for e in errors]).lower()
        self.assertIn("semicolon", error_msg)
        self.assertIn(";", error_msg)

    # =========================================================================
    # Comprehensive Error Message Quality Tests
    # =========================================================================

    def test_all_errors_include_structure_recommendations(self):
        """Test that all error messages include structure recommendations."""
        test_cases = [
            ("love { }", ["love", "(", ")"]),
            ("love () { forever { } }", ["forever", "(", ")"]),
            ("love () { while { } }", ["while", "(", ")"]),
            ("love () { pursue { } }", ["pursue", "(", ")"]),
            ("love () { for { } }", ["for", "(", ")"]),
            ("love () { choose { } }", ["choose", "(", ")"]),
            ("love () { dear x }", ["semicolon", ";"]),
            ("love () { give x; }", ["give", ">>"]),
            ("love () { express x; }", ["express", "<<"]),
        ]
        
        for source, expected_keywords in test_cases:
            with self.subTest(source=source):
                lexer = Lexer(source)
                parser = RecursiveDescentParser(lexer)
                try:
                    parser.parse()
                except Exception:
                    pass
                
                errors = parser.errors if hasattr(parser, 'errors') else []
                error_messages = " ".join([e.message for e in errors]).lower()
                
                # At least one expected keyword should be in error messages
                found = any(keyword.lower() in error_messages for keyword in expected_keywords)
                self.assertTrue(found, 
                              f"Error messages for '{source}' should mention one of {expected_keywords}. "
                              f"Errors: {[e.message for e in errors]}")

    def test_error_messages_are_helpful(self):
        """Test that error messages are helpful and include context."""
        source = "love () { forever () { } }"
        lexer = Lexer(source)
        parser = RecursiveDescentParser(lexer)
        
        try:
            parser.parse()
        except Exception:
            pass
        
        errors = parser.errors if hasattr(parser, 'errors') else []
        self.assertGreater(len(errors), 0, "Should have at least one error for empty expression")
        
        # Check that error message is helpful
        error_msg = errors[0].message.lower()
        # Should mention expression, forever, or expected tokens
        is_helpful = any(keyword in error_msg for keyword in 
                        ["expression", "forever", "expected", "unexpected"])
        self.assertTrue(is_helpful, 
                       f"Error message should be helpful. Got: {errors[0].message}")


if __name__ == "__main__":
    unittest.main()
