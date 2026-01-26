# Error Recovery Implementation Plan

## Overview
Implement comprehensive error recovery in the Lovers language parser to detect **all syntax errors** in a single pass, rather than stopping at the first error.

## Current State
- Parser uses Lark with Earley algorithm
- `parse_safe()` method exists but stops at first error
- Error handling is sophisticated with readable messages
- Grammar is complex with many rules (program structure, functions, statements, expressions)

## Goals
1. **Detect all syntax errors** in one parse attempt
2. **Continue parsing** after each error to find subsequent errors
3. **Maintain error quality** - preserve helpful error messages and context
4. **Minimize false positives** - avoid cascading errors from recovery

## Strategy: Multi-Pass Error Recovery with Panic Mode

### Phase 1: Error Recovery Parser (Core Implementation)

#### 1.1 Create `ErrorRecoveryParser` Class
- **Location**: `Parser.py` (new class or extend existing `Parser`)
- **Approach**: Implement panic-mode recovery with synchronization points
- **Key Methods**:
  - `parse_with_recovery()`: Main entry point for error recovery
  - `_recover_from_error()`: Handle recovery at error location
  - `_find_sync_point()`: Find next safe point to resume parsing
  - `_collect_all_errors()`: Iteratively parse and collect errors

#### 1.2 Synchronization Points (Resume Points)
Define tokens/rules where parsing can safely resume:
- **Statement-level**: `SEMICOLON`, `LBRACE`, `RBRACE`
- **Keyword-level**: `LOVE`, `FOREVER`, `WHILE`, `FOR`, `PURSUE`, `CHOOSE`, `COMEBACK`
- **Declaration-level**: `DEAR`, `DEAREST`, `RANT`, `STATUS`, `AVOIDANT`
- **Expression-level**: `RPAREN`, `RBRACKET`, `COMMA`

#### 1.3 Recovery Algorithm
```
1. Parse until first error
2. Record error with position
3. Find synchronization point:
   a. Look ahead for sync tokens (semicolon, brace, keyword)
   b. Skip tokens until sync point found
   c. If no sync point, skip to next line
4. Resume parsing from sync point
5. Repeat until EOF or max errors reached
6. Return all collected errors
```

### Phase 2: Token-Level Recovery Strategies

#### 2.1 Common Error Patterns (Heuristics)
Detect and suggest fixes for:
- **Missing semicolons**: Insert `;` and continue
- **Missing brackets**: Insert `}` or `)` based on context
- **Missing commas**: Insert `,` in argument/declaration lists
- **Unclosed strings**: Skip to next line or quote
- **Unclosed comments**: Skip to next line

#### 2.2 Token Insertion/Deletion
- **Insert expected tokens** when context is clear (e.g., missing `;` after statement)
- **Delete unexpected tokens** when they're clearly wrong (e.g., extra `;`)
- **Track insertions/deletions** to avoid cascading errors

### Phase 3: Grammar-Level Enhancements

#### 3.1 Error Productions (Optional)
Add error rules to grammar.lark for common patterns:
```lark
// Example: Allow error recovery in statements
statement: normal_statement
         | error_statement  // Catch-all for malformed statements

error_statement: ID error_tokens SEMICOLON  // Skip until semicolon
```

**Note**: This requires grammar modification and may be complex. Consider Phase 1 first.

### Phase 4: Implementation Details

#### 4.1 Error Recovery Parser Structure
```python
class ErrorRecoveryParser:
    def __init__(self, base_parser: Parser):
        self.base_parser = base_parser
        self.max_errors = 100  # Prevent infinite loops
        self.sync_tokens = {SEMICOLON, LBRACE, RBRACE, ...}
        self.sync_keywords = {LOVE, FOREVER, WHILE, ...}
    
    def parse_with_recovery(self, source: str) -> Tuple[Optional[Tree], List[SyntaxError]]:
        errors = []
        tokens = list(self._tokenize(source))
        current_pos = 0
        
        while current_pos < len(tokens):
            try:
                # Try to parse from current position
                result = self._parse_from_position(tokens, current_pos)
                if result.success:
                    return result.tree, errors
                else:
                    errors.append(result.error)
                    current_pos = self._recover_from_error(tokens, current_pos, result.error)
            except Exception as e:
                # Fallback error handling
                errors.append(self._create_error(e, current_pos))
                current_pos = self._skip_to_next_line(tokens, current_pos)
        
        return None, errors
```

#### 4.2 Token Stream Management
- **Tokenize once**: Pre-tokenize entire source
- **Position tracking**: Track current position in token stream
- **Line/column mapping**: Maintain accurate error positions

#### 4.3 Error Deduplication
- **Prevent duplicate errors**: Same error at same position
- **Merge similar errors**: Multiple errors in same statement
- **Prioritize errors**: Show most critical errors first

### Phase 5: Integration Points

#### 5.1 Update `parse_safe()` Method
- **Option A**: Replace with recovery parser
- **Option B**: Add new method `parse_with_full_recovery()`
- **Recommendation**: Option B (backward compatible)

#### 5.2 API Changes
```python
# New method
def parse_with_full_recovery(self, source: str) -> Tuple[Optional[Tree], List[SyntaxError]]:
    """Parse with error recovery to detect all errors."""
    ...

# Keep existing for backward compatibility
def parse_safe(self, source: str) -> Tuple[Optional[Tree], List[SyntaxError]]:
    """Parse and return first error (existing behavior)."""
    ...
```

#### 5.3 Backend Integration
- Update `Backend/Lexical/main.py` to use recovery parser
- Update `run_validate.py` to show all errors
- Frontend already supports multiple errors in response

### Phase 6: Testing Strategy

#### 6.1 Test Cases
1. **Multiple independent errors**: Errors in different statements
2. **Cascading errors**: One error causing others
3. **Nested errors**: Errors in nested structures (loops, conditionals)
4. **Edge cases**: EOF errors, incomplete programs, missing braces

#### 6.2 Validation
- Compare error count with manual inspection
- Verify error positions are accurate
- Ensure no false positives from recovery

## Implementation Order

### Step 1: Basic Recovery Framework (Priority: High)
- Create `ErrorRecoveryParser` class
- Implement basic panic-mode recovery
- Test with simple multi-error cases

### Step 2: Synchronization Points (Priority: High)
- Define and implement sync tokens/keywords
- Test recovery at different statement levels

### Step 3: Token-Level Heuristics (Priority: Medium)
- Implement common error pattern detection
- Add token insertion/deletion logic

### Step 4: Error Deduplication (Priority: Medium)
- Implement error merging/deduplication
- Improve error prioritization

### Step 5: Integration & Testing (Priority: High)
- Integrate with existing API
- Update backend endpoints
- Comprehensive testing

### Step 6: Grammar Enhancements (Priority: Low)
- Consider error productions if needed
- Only if basic recovery insufficient

## Technical Considerations

### Challenges
1. **Lark's parser stops at first error**: Need custom recovery loop
2. **Token position tracking**: Maintain accurate line/column info
3. **False positives**: Recovery might introduce spurious errors
4. **Performance**: Multiple parse attempts may be slower

### Solutions
1. **Pre-tokenize**: Tokenize once, parse incrementally
2. **Position preservation**: Track positions through recovery
3. **Error confidence**: Mark errors as "recovered" vs "real"
4. **Early termination**: Stop after reasonable error count

### Performance Impact
- **Expected overhead**: 2-5x slower for error cases
- **Acceptable trade-off**: Better error reporting
- **Optimization**: Cache parse states, limit recovery depth

## Success Criteria
1. ✅ Detects all syntax errors in test cases
2. ✅ Error positions remain accurate after recovery
3. ✅ No significant performance degradation (< 5x slower)
4. ✅ Backward compatible with existing API
5. ✅ Error messages remain helpful and readable

## Alternative Approaches Considered

### Option A: Grammar Error Productions
- **Pros**: Native Lark support, clean grammar
- **Cons**: Complex grammar modifications, harder to maintain

### Option B: Incremental Parsing
- **Pros**: Very accurate, minimal false positives
- **Cons**: Complex implementation, may be slow

### Option C: Panic Mode (Selected)
- **Pros**: Simple, effective, well-understood
- **Cons**: May skip valid code, some false positives

## Next Steps
1. Review and approve this plan
2. Implement Step 1 (Basic Recovery Framework)
3. Iterate based on testing results
4. Integrate with existing codebase
