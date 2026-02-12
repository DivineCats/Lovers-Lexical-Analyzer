# LL(1) Parser Limit Test Cases — Lovers Language

## Spec vs grammar (for QA)

The language spec says global/local declarations must use "literals only." The **current CFG** ([CFG.py](../Backend/Syntax/CFG.py)) differs:

- **dear / dearest:** Use `<dear_init_expr>` and `<dearest_init_expr>`, which **allow arithmetic** (e.g. `dear x = 5+5;` is **valid**). Invalid cases for declarations therefore use other errors (missing `;`, wrong token, etc.).
- **rant:** `<rant_init_val>` = `rant_lit` | `id` only — no `+` or other operators. So `rant s = "a" + "b";` is **invalid**; expected after the first value are `,` or `;`.
- **status:** `<status_init_expr>` allows `greenflag`, `redflag`, `id`, `(`, `not` — richer than literal-only.

Expected Tokens below are derived from the LL(1) FIRST/FOLLOW sets implied by this grammar.

---

## 1. Global Declarations

Tests the top-level declaration rules and (where applicable) strict literal vs expression inits.

### Valid examples

**1.1** Literal-only dear with multi-declaration:
```lovers
dear x = 1, y = 2;
love () { }
```

**1.2** Single rant literal:
```lovers
rant s = "hi";
love () { }
```

**1.3** Dear with arithmetic (allowed by current grammar):
```lovers
dear x = 5 + 5;
love () { }
```

### Invalid examples

**1.4** Missing semicolon after global declaration  
Snippet:
```lovers
dear x = 10
love () { }
```
- **Line:** 1  
- **Token where parser fails:** `love` (or EOF, depending on scanner; first token that is not valid after `<dear_multi>`).  
- **Expected Tokens:** `;`  
- **Reason:** After `10`, parser expects `<dear_init_expr_next>` then `<dear_multi>` then `;`. So the next terminal must be `;` (or `,` if more ids). Here the next token is `love`, so failure is at `love`. Expected: `;`.

**1.5** Rant declaration with expression (binary operator not allowed in `<rant_init_val>`)  
Snippet:
```lovers
rant s = "a" + "b";
love () { }
```
- **Line:** 1  
- **Token where parser fails:** `+`  
- **Expected Tokens:** `,`, `;`  
- **Reason:** `<rant_init_val>` is only `rant_lit` or `id`. After `"a"` we are in `<rant_multi>`; the parser expects `,` (more ids) or `;` (end). So at `+`: Expected Tokens: `,`, `;`.

**1.6** Wrong token after identifier (invalid keyword)  
Snippet:
```lovers
dear x equals 10;
love () { }
```
- **Line:** 1  
- **Token where parser fails:** `equals`  
- **Expected Tokens:** `(`, `=`, `,`, `;`, `[`  
- **Reason:** After `dear` `id` we have `<dear_after_id>`. FIRST(&lt;dear_tail&gt;) = `=`, `,`, `;`, `[` and we also have `(` for function. So at `equals`: Expected Tokens: `(`, `=`, `,`, `;`, `[`.

---

## 2. Local Statements (inside `love() { ... }`)

Tests mixing strict declarations with flexible assignments inside the main function body.

### Valid examples

**2.1** Local declaration then assignment with expression:
```lovers
love () {
  dear a = 1;
  a = 5 + 5;
}
```

**2.2** Multiple local declarations and one assignment:
```lovers
love () {
  dear x = 10;
  rant s = "hi";
  x = x + 1;
}
```

**2.3** Local declaration without init, then assignment:
```lovers
love () {
  dear a, b;
  a = 1;
  b = 2;
}
```

### Invalid examples

**2.4** Rant declaration with expression inside function  
Snippet:
```lovers
love () {
  rant s = "a" + "b";
}
```
- **Line:** 2  
- **Token where parser fails:** `+`  
- **Expected Tokens:** `,`, `;`  
- **Reason:** Same as 1.5: `<rant_init_val>` is `rant_lit` | `id` only. After `"a"`, expected: `,` or `;`.

**2.5** Missing semicolon on assignment  
Snippet:
```lovers
love () {
  dear x = 1;
  x = 2
}
```
- **Line:** 3  
- **Token where parser fails:** `}`  
- **Expected Tokens:** `;`  
- **Reason:** After `<assign_values>`, parser expects `;` from `<id_suffix>`. So at `}`: Expected Tokens: `;`.

**2.6** Statement starting with invalid keyword  
Snippet:
```lovers
love () {
  dear x = 1;
  if (x) { }
}
```
- **Line:** 3  
- **Token where parser fails:** `if`  
- **Expected Tokens:** `id`, `give`, `overshare`, `express`, `forever`, `pursue`, `while`, `for`, `comeback`, `choose`, `++`, `--`, `breakup`, or end of body  
- **Reason:** `<statements>` FIRST set: statements start with one of those terminals (or λ). `if` is not in the language; keyword for condition is `forever`. So at `if`: Expected Tokens: `id`, `give`, `overshare`, `express`, `forever`, `pursue`, `while`, `for`, `comeback`, `choose`, `++`, `--`, `breakup`.

---

## 3. Conditional Logic

Tests `forever` / `forevermore` / `more` and nested/empty blocks.

### Valid examples

**3.1** Simple forever with block:
```lovers
love () {
  dear x = 0;
  forever (x < 1) { express << x; }
}
```

**3.2** forever → forevermore → more chain:
```lovers
love () {
  dear n = 2;
  forever (n == 1) { express << periodt; }
  forevermore (n == 2) { express << periodt; }
  more { express << periodt; }
}
```

**3.3** Deeply nested forever and empty block:
```lovers
love () {
  forever (greenflag) {
    forever (redflag) { }
  }
}
```

### Invalid examples

**3.4** Wrong keyword (e.g. `if` instead of `forever`)  
Snippet:
```lovers
love () {
  if (greenflag) { }
}
```
- **Line:** 2  
- **Token where parser fails:** `if`  
- **Expected Tokens:** `id`, `give`, `overshare`, `express`, `forever`, `pursue`, `while`, `for`, `comeback`, `choose`, `++`, `--`, `breakup`  
- **Reason:** Conditionals start with `forever`. At `if`: Expected Tokens: as in 2.6 (statement starters); notably `forever` is expected for a conditional.

**3.5** forever without opening parenthesis  
Snippet:
```lovers
love () {
  forever greenflag) { }
}
```
- **Line:** 2  
- **Token where parser fails:** `greenflag`  
- **Expected Tokens:** `(`  
- **Reason:** `<conditional_state>` is `forever` `(` `<expr>` `)` `{` ... So after `forever`: Expected Tokens: `(`.

**3.6** Missing closing brace on forever block  
Snippet:
```lovers
love () {
  forever (greenflag) {
    dear x = 1;
}
```
- **Line:** 4  
- **Token where parser fails:** `}` (the one that closes `love`) or EOF  
- **Expected Tokens:** `}`  
- **Reason:** After `<body_func>` of the forever block, parser expects `}`. If we have only one `}` and it is taken to close the forever block, then the next token is EOF and we are inside `love`; parser expects another `}` for `love`. So at that `}` or EOF: Expected Tokens: `}` (for the forever block or for `love` depending on position). Concretely: after `dear x = 1;` we have statements then `}` for forever; then `<forevermore_lst>`, `<more_opt>`, then `}` for love. So the first `}` closes the forever block; then we need `}` for love. If the snippet has only one `}`, failure is at EOF: Expected Tokens: `}`.

---

## 4. Arrays

Tests strict array declaration (`dear list[10];`) and flexible array access/assignment in statements.

### Valid examples

**4.1** Array declaration with literal size, no initializer:
```lovers
dear list[10];
love () { }
```

**4.2** Array declaration with initializer list:
```lovers
dear list[3] = { 1, 2, 3 };
love () { }
```

**4.3** Array element assignment with expression in body:
```lovers
dear list[5];
dear x = 1;
love () {
  list[0] = x + 1;
}
```

### Invalid examples

**4.4** Array size non-literal (identifier instead of dear_lit)  
Snippet:
```lovers
dear list[n];
love () { }
```
- **Line:** 1  
- **Token where parser fails:** `n`  
- **Expected Tokens:** `dear_lit`, `]`  
- **Reason:** `<array_size>` is `dear_lit` or λ. After `[`, parser expects `<array_size>`: either a constant integer or `]`. So at `n` (id): Expected Tokens: `dear_lit`, `]`.

**4.5** Missing `]` in array declaration  
Snippet:
```lovers
dear list[10
love () { }
```
- **Line:** 1  
- **Token where parser fails:** `love` (or newline / next token)  
- **Expected Tokens:** `]`  
- **Reason:** After `<array_size>` (e.g. `10`), parser expects `]`. So at next token: Expected Tokens: `]`.

**4.6** Invalid array initializer (expression instead of simple list)  
Snippet:
```lovers
dear list[2] = { 1 + 0, 2 };
love () { }
```
- **Line:** 1  
- **Token where parser fails:** `+`  
- **Expected Tokens:** (from `<array_lit_list>` / `<init_value>`: `<simple_val>` then more with `,`) — so after `1`, expected: `,`, `}`.  
- **Reason:** `<array_source>` is `{` `<array_lit_list>` `}` and `<array_lit_list>` uses `<init_value>`, which is `<simple_val>` or `{` ... `<simple_val>` is dear_lit, dearest_lit, rant_lit, greenflag, redflag, id, or `-` dear_lit/dearest_lit — no binary `+`. So at `+`: Expected Tokens: `,`, `}`.

---

## Summary table (invalid cases)

| #   | Category           | Failure token | Expected Tokens |
|-----|--------------------|---------------|-----------------|
| 1.4 | Global Declarations| `love`        | `;`             |
| 1.5 | Global Declarations| `+`           | `,`, `;`        |
| 1.6 | Global Declarations| `equals`      | `(`, `=`, `,`, `;`, `[` |
| 2.4 | Local Statements   | `+`           | `,`, `;`        |
| 2.5 | Local Statements   | `}`           | `;`             |
| 2.6 | Local Statements   | `if`          | `id`, `give`, `express`, `forever`, ... |
| 3.4 | Conditional Logic  | `if`          | `forever`, ...  |
| 3.5 | Conditional Logic  | `greenflag`   | `(`             |
| 3.6 | Conditional Logic  | EOF or `}`    | `}`             |
| 4.4 | Arrays             | `n`           | `dear_lit`, `]` |
| 4.5 | Arrays             | next after 10 | `]`             |
| 4.6 | Arrays             | `+`           | `,`, `}`        |

Use this document to drive limit tests and to verify that the parser reports the same **Expected Tokens** at each failure point (e.g. from the LL(1) table or error-reporting logic).
