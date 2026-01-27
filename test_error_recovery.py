#!/usr/bin/env python3
"""Simple test script for error recovery functionality."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Syntax import parse_with_errors, create_error_context

def test_error_recovery():
    """Test error recovery with multiple syntax errors."""
    
    # Test code with multiple errors
    test_source = """
boundaries test {
    dear x = 10
    dearest y = 20.5
    rant name = "hello"
    
    love main() {
        dear a = 5
        dear b = 10
        express << a << periodt;
        
        forever (a > b) {
            express << "a is greater" << periodt;
        }
        
        comeback 0;
    }
}
"""
    
    print("=" * 60)
    print("Testing Parser (stops on first error)")
    print("=" * 60)
    print("\nTest Source:")
    print(test_source)
    print("\n" + "=" * 60)
    print("Parsing (stops on first error)...")
    print("=" * 60)
    
    tree, errors = parse_with_errors(test_source)
    
    if errors:
        print(f"\nFound {len(errors)} error(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"Error {i}:")
            print(f"  {error}")
            context = create_error_context(test_source, error.line, error.column)
            print(context)
            print()
    else:
        print("\n✓ No errors found!")
        if tree:
            print("✓ Parsing successful!")
    
    # Test with known errors
    print("\n" + "=" * 60)
    print("Testing with intentional errors...")
    print("=" * 60)
    
    error_source = """
love main() {
    dear x = 10
    dearest y = 20.5
    rant z = "test"
    
    x = y + z
    express << x << periodt;
}
"""
    
    print("\nError Source (missing semicolons):")
    print(error_source)
    
    tree2, errors2 = parse_with_errors(error_source)
    
    print(f"\nFound {len(errors2)} error(s):\n")
    for i, error in enumerate(errors2, 1):
        print(f"Error {i}:")
        print(f"  {error}")
        context = create_error_context(error_source, error.line, error.column)
        print(context)
        print()

if __name__ == "__main__":
    test_error_recovery()
