# Solution: Typo Recovery for `more` Keyword in If Statements

## Problem
When user types `moe` instead of `more`, the parser generates 3 errors:
1. ✅ Correct: "Unexpected identifier 'moe'. Did you mean 'more'?"
2. ❌ Cascading: "Missing semicolon" (because parser doesn't recognize `moe` as a keyword)
3. ❌ Cascading: "Expected '}' to close function" (because parser lost track of structure)

**Expected:** Only 1 error (the typo)

## Root Cause
In `_parse_if_statement()`, the code checks:
```python
if self._match("more"):
    self._consume("more")
    # ... parse else clause
```

When `moe` is encountered:
- `self._match("more")` returns `False` (because `moe` is an `id` token, not `more`)
- The else clause is skipped
- Later, `moe {` is seen as an invalid statement, causing cascading errors

## Solution

### Approach: Typo Detection and Recovery in If Statement Parsing

Modify `_parse_if_statement()` to:
1. Check if current token is an identifier that looks like a typo for `more`
2. If it is, report the typo error but continue parsing as if it were `more`
3. This prevents cascading errors

### Implementation

**Location:** `_parse_if_statement()` method, around line 1940-1942

**Current Code:**
```python
# Parse else clause
else_body = None
if self._match("more"):
    self._consume("more")
    self._consume("LBRACE")
    # ... rest of else parsing
```

**New Code:**
```python
# Parse else clause
else_body = None
# Check for "more" keyword or typo
if self._match("more"):
    self._consume("more")
    self._consume("LBRACE")
    # ... rest of else parsing
elif self._match("id"):
    # Check if this identifier is a typo for "more"
    current_token = self._current_token()
    suggestion = self._find_similar_keyword(current_token.lexeme)
    if suggestion == "more":
        # It's a typo for "more" - report error but continue parsing
        error = ParseError(
            f"Unexpected identifier '{current_token.lexeme}'. Did you mean 'more'?",
            current_token
        )
        self.errors.append(error)
        # Advance past the typo and continue as if it were "more"
        self._advance()  # Skip the typo identifier
        # Check if next token is LBRACE (expected after "more")
        if self._match("LBRACE"):
            self._consume("LBRACE")
            self._skip_whitespace()
            # Parse the else body with recovery
            try:
                else_body = self._parse_function_body()
            except ParseError:
                else_body = self._parse_function_body_with_recovery()
            self._consume("RBRACE")
        else:
            # Typo but wrong structure - report additional error
            next_token = self._current_token()
            if next_token:
                error2 = ParseError(
                    f"Expected '{{' after 'more', found '{next_token.lexeme}'",
                    next_token
                )
                self.errors.append(error2)
```

## Benefits

1. **Single Error Report:** Only reports the typo error, not cascading errors
2. **Graceful Recovery:** Continues parsing after the typo, maintaining structure
3. **Better UX:** User sees one clear error message instead of confusing cascading errors
4. **Maintains Parsing Context:** Parser doesn't lose track of function structure

## Testing

Test case:
```python
love () {
    forever (num > 0) {
        express << "Positive." << periodt;
    } 
    forevermore (num < 0) {
        express << "Negative." << periodt;
    } 
    moe {  # Typo: should be "more"
        express << "Zero." << periodt;
    }
}
```

**Expected Result:**
- ✅ 1 error: "Unexpected identifier 'moe'. Did you mean 'more'?"
- ✅ Parser continues and successfully parses the rest
- ✅ No cascading errors

## Alternative: Also Handle in Error Recovery

We could also improve the error recovery in `_parse_function_body_with_recovery()` to detect when an identifier followed by `{` is likely a typo for `more` in the context of an if statement chain. However, the solution above is cleaner because it handles it at the source (in `_parse_if_statement()`).
