# Why You're Seeing 2 Errors Instead of 1

## Your Code:
```lovers
love () {
    ran name[] = {"Jhin", "John"};
}
```

## What's Happening:

### Error 1: "Unexpected token 'name'" (Line 3)
**This is the REAL error** - but the message could be clearer.

**Root Cause:**
- You typed `ran` but the correct keyword is `rant` (for string type)
- The lexer tokenizes `ran` as an **identifier** (`id`), not as a keyword
- The parser expects a **type keyword** (`dear`, `dearest`, `rant`, `status`) before the variable name
- When it sees `ran` (identifier) followed by `name` (identifier), it's confused
- It reports: "Unexpected token 'name'" because it expected an operator or semicolon after `ran`

**What the parser sees:**
```
ran    → ID (identifier) ❌ Should be RANT (keyword)
name   → ID (identifier) 
[]     → Array brackets
=      → Assignment
```

**The parser's confusion:**
- It sees: `identifier identifier [] = ...`
- This is invalid syntax (can't have two identifiers in a row)
- So it reports the error on `name` (the second identifier)

### Error 2: "Unexpected token '}'" (Line 5)
**This is a CASCADING ERROR** - a false positive from error recovery.

**What happens:**
1. Parser hits Error 1 on line 3
2. Error recovery kicks in and tries to find a "synchronization point"
3. It skips ahead looking for a safe place to resume parsing
4. When it reaches the closing brace `}` on line 5, the parser is still in a confused state
5. It doesn't recognize the `}` as closing the `love () {` block because the previous statement wasn't parsed correctly
6. So it reports: "Unexpected token '}'"

**This is why it's cascading:**
- The `}` is actually correct syntax
- The error only appears because the parser got confused by Error 1
- Without Error 1, the `}` would be perfectly valid

## The Fix:

I've improved the cascading error filter to detect and remove these false positives. The filter now:

1. **Checks if an error is on a closing brace** after a previous error nearby
2. **Verifies the line is mostly just the brace** (not real code)
3. **Removes it if it's clearly a recovery artifact**

## Expected Result After Fix:

You should now see **only 1 error**:
- ✅ "Unexpected token 'name'" (or better: a message about `ran` not being a valid type)

The second error about `}` should be filtered out as a cascading error.

## Better Error Message (Future Improvement):

Ideally, the error message should be:
- ❌ Current: "Unexpected token 'name'"
- ✅ Better: "Expected type keyword (dear/dearest/rant/status) but found identifier 'ran'. Did you mean 'rant'?"

This would make it clearer that `ran` is the problem, not `name`.
