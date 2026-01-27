# CFG Structure Recommendations - Errors Found

## Summary

After analyzing the parser code, I found that **some error messages include CFG structure recommendations, but many are missing them**.

## ✅ Error Messages WITH CFG Structure Recommendations

### 1. Program Structure (`love`)
- ✅ Missing `(`: "Complete structure: love () { ... }"
- ✅ Missing `)`: "Complete structure: love () { ... }"
- ✅ Missing `{`: "Complete structure: love () { ... }"

### 2. Forever Statement (`forever`)
- ✅ Empty expression: "Complete structure: forever (<expr>) { ... }"
- ✅ Missing `)`: "Complete structure: forever (<expr>) { ... }"
- ✅ Missing `{`: "Complete structure: forever (<expr>) { ... }"
- ✅ Missing `}`: "Complete structure: forever (<expr>) { ... }"

### 3. More Statement (`more`)
- ✅ Missing `{`: "Complete structure: more { ... }"

### 4. Express Statement (`express`)
- ✅ Missing `<<`: "Complete structure: express << <expr> << periodt;"
- ✅ Missing expression: "Complete structure: express << <expr> << periodt;"

---

## ❌ Error Messages MISSING CFG Structure Recommendations

### 1. While Statement (`while`)
**Location:** `_parse_while_statement()` (line ~2440)
**Current:** Uses generic `_consume()` calls without context
**Missing:**
- Missing `(`: Should show "Complete structure: while (<expr>) { ... }"
- Missing `)`: Should show "Complete structure: while (<expr>) { ... }"
- Missing `{`: Should show "Complete structure: while (<expr>) { ... }"
- Missing `}`: Should show "Complete structure: while (<expr>) { ... }"
- Empty expression: Should show "Complete structure: while (<expr>) { ... }"

### 2. Pursue Statement (`pursue`)
**Location:** `_parse_do_while_statement()` (line ~2458)
**Current:** Uses generic `_consume()` calls without context
**Missing:**
- Missing `(`: Should show "Complete structure: pursue (<expr>) { ... }"
- Missing `)`: Should show "Complete structure: pursue (<expr>) { ... }"
- Missing `{`: Should show "Complete structure: pursue (<expr>) { ... }"
- Missing `}`: Should show "Complete structure: pursue (<expr>) { ... }"
- Empty expression: Should show "Complete structure: pursue (<expr>) { ... }"

### 3. For Statement (`for`)
**Location:** `_parse_for_statement()` (line ~2476)
**Current:** Uses generic `_consume()` calls without context
**Missing:**
- Missing `(`: Should show "Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }"
- Missing `;`: Should show "Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }"
- Missing `)`: Should show "Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }"
- Missing `{`: Should show "Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }"
- Missing `}`: Should show "Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }"

### 4. Choose Statement (`choose`)
**Location:** `_parse_switch_statement()` (line ~2587)
**Current:** Uses generic `_consume()` calls without context
**Missing:**
- Missing `(`: Should show "Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }"
- Missing `)`: Should show "Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }"
- Missing `{`: Should show "Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }"
- Missing `}`: Should show "Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }"
- Missing `phase`: Should show "Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }"

### 5. Give Statement (`give`)
**Location:** `_parse_input_statement()` (line ~2060)
**Current:** "Expected '>>' after 'give'"
**Missing:**
- Missing `>>`: Should show "Complete structure: give >> id;"

### 6. Overshare Statement (`overshare`)
**Location:** `_parse_input_statement()` (line ~2075)
**Current:** "Expected identifier in overshare"
**Missing:**
- Missing `(`: Should show "Complete structure: overshare(id);"
- Missing `)`: Should show "Complete structure: overshare(id);"
- Missing identifier: Should show "Complete structure: overshare(id);"

### 7. Comeback Statement (`comeback`)
**Location:** `_parse_return_statement()` (line ~2160)
**Current:** Uses generic `_consume()` calls
**Missing:**
- Missing `;`: Should show "Complete structure: comeback [<expr>];"

### 8. Forevermore Statement (`forevermore`)
**Location:** `_parse_if_statement()` (line ~2340)
**Current:** Uses generic error messages
**Missing:**
- Missing `(`: Should show "Complete structure: forevermore (<expr>) { ... }"
- Missing `)`: Should show "Complete structure: forevermore (<expr>) { ... }"
- Missing `{`: Should show "Complete structure: forevermore (<expr>) { ... }"
- Missing `}`: Should show "Complete structure: forevermore (<expr>) { ... }"
- Empty expression: Should show "Complete structure: forevermore (<expr>) { ... }"

### 9. Declaration Statements
**Location:** `_parse_declaration()` (line ~1630)
**Current:** Generic semicolon/identifier errors
**Missing:**
- Missing `;`: Should show "Complete structure: <data_type> id [= <expr>];"
- Missing identifier: Should show "Complete structure: <data_type> id [= <expr>];"

### 10. Function Declarations
**Location:** `_parse_sub_function()` (line ~1020)
**Current:** Generic parameter/brace errors
**Missing:**
- Missing `(`: Should show "Complete structure: <return_type> id (<parameter>) { ... }"
- Missing `)`: Should show "Complete structure: <return_type> id (<parameter>) { ... }"
- Missing `{`: Should show "Complete structure: <return_type> id (<parameter>) { ... }"
- Missing `}`: Should show "Complete structure: <return_type> id (<parameter>) { ... }"

---

## Recommendations

### Priority 1 (High): Core Control Flow Statements
1. **while** - Very common, needs structure recommendations
2. **pursue** - Common loop, needs structure recommendations
3. **for** - Complex structure, needs structure recommendations
4. **choose** - Complex structure, needs structure recommendations

### Priority 2 (Medium): Input/Output Statements
5. **give** - Common input, needs structure recommendations
6. **overshare** - Common input, needs structure recommendations
7. **comeback** - Common return, needs structure recommendations

### Priority 3 (Low): Other Statements
8. **forevermore** - Less common, but should have structure recommendations
9. **declaration** - Common, but errors are usually clear
10. **function** - Less common, but should have structure recommendations

---

## Test Coverage

The test suite `test_cfg_structure_recommendations.py` includes tests for all these scenarios, but they will fail until the error messages are updated to include CFG structure recommendations.

---

## Next Steps

1. Update error messages in `_parse_while_statement()` to include "Complete structure: while (<expr>) { ... }"
2. Update error messages in `_parse_do_while_statement()` to include "Complete structure: pursue (<expr>) { ... }"
3. Update error messages in `_parse_for_statement()` to include "Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }"
4. Update error messages in `_parse_switch_statement()` to include "Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }"
5. Update error messages in `_parse_input_statement()` to include structure recommendations
6. Update error messages in `_parse_return_statement()` to include structure recommendations
7. Update error messages for `forevermore` to include structure recommendations
8. Update error messages for declarations and functions to include structure recommendations

---

## Status

- ✅ **18 error messages** already include CFG structure recommendations
- ❌ **~40+ error messages** are missing CFG structure recommendations
- 📝 **Test suite created** to verify all error messages include structure recommendations
