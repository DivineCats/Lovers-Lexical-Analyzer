#!/usr/bin/env python3
"""Quick test script - paste your test case here and run."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Syntax import parse_with_full_recovery, create_error_context

# ============================================================================
# PASTE YOUR TEST CASE HERE
# ============================================================================
test_source = """
love main() {
    dear x = 10
    dearest y = 20.5
    rant z = "test"
    
    x = y + z
    express << x << periodt;
}
"""

# ============================================================================
# RUN THE TEST
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("ERROR RECOVERY TEST")
    print("=" * 70)
    print("\nSource Code:")
    print(test_source)
    print("\n" + "=" * 70)
    print("Results:")
    print("=" * 70)
    
    tree, errors = parse_with_full_recovery(test_source)
    
    if errors:
        print(f"\n✓ Found {len(errors)} error(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"{'='*70}")
            print(f"ERROR {i}:")
            print(f"{'='*70}")
            print(f"{error}\n")
            context = create_error_context(test_source, error.line, error.column)
            print(context)
            print()
    else:
        print("\n✓ No errors found!")
        if tree:
            print("✓ Parsing successful!")
            print("\nParse tree structure:")
            print(tree.pretty()[:500] + "..." if len(tree.pretty()) > 500 else tree.pretty())
