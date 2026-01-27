# Brace Detection Fix - Preventing False "Missing Closing Brace" Errors

## Problem

When there's a structural error (like `express <<` without an expression), the parser reports a false "Expected '}' to close 'love () {' function" error even though the closing brace exists.

**Example:**
```python
love () {
    express <<
}
```

**Current Behavior:**
- ❌ Error 1: "Unexpected token '\n' after '<<'" (correct)
- ❌ Error 2: "Expected '}' to close 'love () {' function" (FALSE - brace exists!)

**Expected Behavior:**
- ✅ Error 1: "Unexpected token '\n' after '<<'" (correct)
- ✅ No false "missing closing brace" error

## Root Cause

1. **Parser Position After Errors:**
   - When `express <<` fails (missing expression), error is recorded
   - `_parse_function_body_with_recovery()` tries to recover
   - Parser might not advance correctly to the closing brace
   - When `_parse_program()` checks for closing brace, parser is still at error location

2. **Brace Detection Logic:**
   - `_parse_program()` checks `if not self._match("RBRACE")`
   - If parser is at wrong position, it doesn't see the brace
   - Reports false "missing brace" error

3. **Cascading Error Logic:**
   - The check for `has_structural_errors` should prevent this
   - But if brace isn't found at current position, it still reports error

## Solution Implemented

### Fix 1: Improved Brace Detection in `_parse_program()` ✅

**Location:** Lines ~968-1015

**Changes:**
1. **Check current position first** - If we're already at the brace, consume it
2. **Scan ahead for matching brace** - Use `_find_matching_closing_brace()` to find it even if we're not at it
3. **Advance to brace if found** - If brace exists ahead, advance to it and consume it
4. **Only report if truly missing** - Only report "missing brace" if:
   - Brace not at current position AND
   - Brace not found ahead AND
   - No structural errors (to avoid cascading)

**Key Logic:**
```python
# Check current position first
if self._match("RBRACE"):
    # Already at brace - consume it
    self._consume("RBRACE", context="main function")
elif matching_brace_idx is not None:
    # Found brace ahead - advance to it
    self.current_index = matching_brace_idx
    self._consume("RBRACE", context="main function")
elif not self._match("RBRACE"):
    # No brace found - only report if no structural errors
    if not has_structural_errors:
        # Report missing brace
```

### Fix 2: Improved Recovery in `_parse_function_body_with_recovery()` ✅

**Location:** Lines ~1362-1368

**Changes:**
1. **Stop at closing brace during recovery** - When scanning for sync points, if we find the function body's closing brace (brace_depth == 0), stop there
2. **Don't advance past brace** - Leave parser at the brace so `_parse_program()` can consume it
3. **Proper brace depth tracking** - Track brace depth correctly during error recovery

**Key Logic:**
```python
elif current_token.kind == "RBRACE":
    if brace_depth > 0:
        brace_depth -= 1  # Nested block
    elif brace_depth == 0:
        # Function body's closing brace - stop here
        found_sync = True
        break
```

### Fix 3: Better Structural Error Detection ✅

**Location:** Lines ~974-980

**Changes:**
- Enhanced check for structural errors to include more error types
- Prevents false "missing brace" errors when we have structural errors

**Key Logic:**
```python
has_structural_errors = any(
    "expression" in e.message.lower() or 
    "unexpected token" in e.message.lower() or
    ("expected" in e.message.lower() and "brace" not in e.message.lower() and "parenthesis" not in e.message.lower())
    for e in self.errors
)
```

## Expected Result After Fix

For `love () { express << }`:
- ✅ **1 error only:** "Unexpected token '\n' after '<<'. Expected one of: ... Complete structure: express << <expr> << periodt;"
- ✅ **No "Expected '}'" error** (prevented by improved brace detection)
- ✅ Parser correctly finds and consumes the closing brace

## Test Cases

### Test Case 1: Missing Expression
```python
love () {
    express <<
}
```
**Expected:** 1 error (missing expression), no false "missing brace" error

### Test Case 2: Empty Forever Expression
```python
love () {
    forever () {
    }
}
```
**Expected:** 1 error (empty expression), no false "missing brace" error

### Test Case 3: Missing Semicolon
```python
love () {
    dear x
}
```
**Expected:** 1 error (missing semicolon), no false "missing brace" error

## Status

✅ **COMPLETE** - Improved brace detection implemented:
- Better scanning for matching braces
- Proper position tracking after errors
- Cascading error prevention
- Only reports missing brace when truly missing
