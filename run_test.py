#!/usr/bin/env python3
"""Interactive test runner for error recovery."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Syntax import parse_with_full_recovery, create_error_context
from test_cases import ALL_TEST_CASES

def run_test(test_name: str, source: str):
    """Run a single test case."""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)
    print("\nSource Code:")
    print(source)
    print("\n" + "=" * 70)
    print("Parsing with error recovery...")
    print("=" * 70)
    
    tree, errors = parse_with_full_recovery(source)
    
    if errors:
        print(f"\n✓ Found {len(errors)} error(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"{'─'*70}")
            print(f"ERROR {i}:")
            print(f"{'─'*70}")
            print(f"{error}\n")
            context = create_error_context(source, error.line, error.column)
            print(context)
            print()
    else:
        print("\n✓ No errors found!")
        if tree:
            print("✓ Parsing successful!")
    
    return len(errors)

def main():
    """Main test runner."""
    print("=" * 70)
    print("ERROR RECOVERY TEST RUNNER")
    print("=" * 70)
    print("\nAvailable test cases:")
    print()
    
    test_list = list(ALL_TEST_CASES.items())
    for i, (name, _) in enumerate(test_list, 1):
        print(f"  {i:2d}. {name}")
    
    print(f"\n  {len(test_list) + 1:2d}. Run ALL tests")
    print(f"  {len(test_list) + 2:2d}. Custom test (paste your code)")
    print()
    
    try:
        choice = input("Select test case (number): ").strip()
        
        if choice == str(len(test_list) + 1):
            # Run all tests
            print("\n" + "=" * 70)
            print("RUNNING ALL TESTS")
            print("=" * 70)
            total_errors = 0
            for name, source in test_list:
                errors = run_test(name, source)
                total_errors += errors
                input("\nPress Enter to continue to next test...")
            print(f"\n{'='*70}")
            print(f"SUMMARY: Total errors found across all tests: {total_errors}")
            print(f"{'='*70}")
            
        elif choice == str(len(test_list) + 2):
            # Custom test
            print("\n" + "=" * 70)
            print("CUSTOM TEST")
            print("=" * 70)
            print("\nPaste your test code (end with empty line + Ctrl+D or Ctrl+Z):")
            print("(Or type 'exit' to cancel)")
            print()
            
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip().lower() == 'exit':
                        print("Cancelled.")
                        return
                    lines.append(line)
                except EOFError:
                    break
            
            if lines:
                custom_source = '\n'.join(lines)
                run_test("Custom Test", custom_source)
            else:
                print("No code provided.")
                
        else:
            # Run specific test
            test_num = int(choice)
            if 1 <= test_num <= len(test_list):
                name, source = test_list[test_num - 1]
                run_test(name, source)
            else:
                print("Invalid choice!")
                
    except (ValueError, KeyboardInterrupt):
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
