Cfg mapping for the Lovers language
====================================

This file captures the context‑free grammar you provided and maps the terminals to the tokens emitted by the lexer / expected by the parser.

Token/terminal mapping
----------------------
- `dear` → `KEYWORD_TYPE_INT`
- `dearest` → `KEYWORD_TYPE_FLOAT`
- `rant` → `KEYWORD_TYPE_STRING`
- `status` → `KEYWORD_TYPE_BOOL`
- `const` → `KEYWORD_CONST`
- `give` → `KEYWORD_IO_GIVE`
- `express` → `KEYWORD_IO_EXPRESS`
- `overshare` → `KEYWORD_IO_OVERSHARE`
- `forever` → `KEYWORD_IF`
- `forevermore` → `KEYWORD_ELSEIF`
- `more` → `KEYWORD_ELSE`
- `choose` → `KEYWORD_SWITCH`
- `phase` → `KEYWORD_CASE`
- `bareminimum` → `KEYWORD_DEFAULT`
- `for` → `KEYWORD_FOR`
- `while` → `KEYWORD_WHILE`
- `pursue` → `KEYWORD_DO_WHILE`
- `breakup` → `KEYWORD_BREAK`
- `moveon` → `KEYWORD_CONTINUE`
- `love` → `KEYWORD_MAIN` (parsed as `love ( ) { ... }`)
- `periodt` → `KEYWORD_ENDL`
- `boundaries` → `KEYWORD_NAMESPACE`
- `comeback` → `KEYWORD_RETURN`
- Boolean literals: `greenflag` → `BOOL_LITERAL_TRUE`, `redflag` → `BOOL_LITERAL_FALSE`
- Identifiers: `IDENTIFIER`
- Literals: `INT_LITERAL`, `FLOAT_LITERAL`, `STRING_LITERAL`
- Punctuation: `(` `)` `{` `}` `[` `]` `;` `,` `:`
- Operators:
  - Assignment: `=` `+=` `-=` `*=` `/=` `%=` (`ASSIGN`, `OP_PLUS_ASSIGN`, etc.)
  - Arithmetic: `+` `-` `*` `/` `%` (`PLUS`, `MINUS`, `STAR`, `SLASH`, `PERCENT`)
  - Logical: `&&` `||` `!` (`OP_AND`, `OP_OR`, `BANG`)
  - Relational: `>` `<` `>=` `<=` `==` `!=` (`GT`, `LT`, `OP_GTE`, `OP_LTE`, `OP_EQ`, `OP_NEQ`)
  - Shift: `<<` `>>` (`OP_LSHIFT`, `OP_RSHIFT`)
  - Unary increment/decrement: `++` `--` (`OP_INC`, `OP_DEC`)

Grammar
---------------------
1.  `<program> → <boundaries_opt> <global_declaration> love main ( ) { <body_func> }`
2.  `<boundaries_opt> → boundaries id { <global_dec> }`
3.  `<boundaries_opt> → λ`
4.  `<global_declaration> → <declaration_list>`
5.  `<global_declaration> → <function_def> <global_declaration>`
6.  `<global_declaration> → λ`
7.  `<declaration_list> → <declaration> <global_declaration>`
8.  `<declaration_list> → λ`
9.  `<declaration> → <data type> id <array_decl> <var_initial> <multi_decl> ;`
10. `<declaration> → <data type> id ;`
11. `<declaration> → <const_decl> <data type> id = <expr> ;`
12. `<multi_decl> → , id <array_decl> <var_initial> <multi_decl>`
13. `<multi_decl> → λ`
14. `<const_decl> → const`
15. `<const_decl> → λ`
16. `<var_initial> → = <expr>`
17. `<var_initial> → λ`
18. `<data type> → dear`
19. `<data type> → dearest`
20. `<data type> → rant`
21. `<data type> → status`
22. `<array_func> → <func_tail>`
23. `<array_func> → <array_decl> <array_initialization>`
24. `<func_tail> → ( <param> ) <array_decl>`
25. `<param> → <func_param> <multi_param>`
26. `<param> → λ`
27. `<func_param> → <data_type> id <array_decl>`
28. `<multi_param> → , <func_param> <multi_param>`
29. `<multi_param> → λ`
30. `<array_decl> → [ <expr> ] <array_decl>`
31. `<array_decl> → [ ] <array_decl>`
32. `<array_decl> → λ`
33. `<index_array> → [ <array_values> ] <index_multi>`
34. `<index_multi> → [ <array_values> ] <index_multi>`
35. `<index_multi> → λ`
36. `<array_values> → <expr>`
37. `<array_initialization> → = { <array_elements> }`
38. `<array_initialization> → = <expr>`
39. `<array_initialization> → λ`
40. `<array_elements> → <array_values>`
41. `<array_elements> → <array_values> , <array_elements>`
42. `<literals> → dear_lit`
43. `<literals> → dearest_lit`
44. `<literals> → rant_lit`
45. `<literals> → <status>`
46. `<status> → greenflag`
47. `<status> → redflag`
48. `<function_def> → <return_type> id ( <param> ) { <body_func> }`
49. `<function_def> → λ`
50. `<body_func> → <statements>`
51. `<body_func> → λ`
52. `<return_type> → <data_type>`
53. `<statements> → id <assign-call-state> <statements>`
54. `<statements> → <input_state> <statements>`
55. `<statements> → <output_state> <statements>`
56. `<statements> → <conditional_state> <statements>`
57. `<statements> → <loop_state> <statements>`
58. `<statements> → <comeback_state> <statements>`
59. `<statements> → <choose_state> <statements>`
60. `<statements> → <unary_state> <statements>`
61. `<statements> → <local_decl> <statements>`
62. `<statements> → λ`
63. `<local_decl> → <declaration>`
64. `<loop_block> → <statements>`
65. `<assign-call-state> → <index_array> <assign_ops> <assign_values> ;`
66. `<assign-call-state> → <assign_ops> <assign_values> ;`
67. `<assign-call-state> → ( <arguments> ) ;`
68. `<assign-call-state> → <unary_ops> ;`
69. `<arguments> → <expr> <arg_tail>`
70. `<arguments> → λ`
71. `<arg_tail> → , <expr> <arg_tail>`
72. `<arg_tail> → λ`
73. `<assign_ops> → =`
74. `<assign_ops> → +=`
75. `<assign_ops> → -=`
76. `<assign_ops> → *=`
77. `<assign_ops> → /=`
78. `<assign_ops> → %=`
79. `<assign_values> → <expr>`
80. `<assign_values> → { <array_elements> }`
81. `<expr> → <term> <expr_tail>`
82. `<expr_tail> → <add_ops> <term> <expr_tail>`
83. `<expr_tail> → λ`
84. `<term> → <factor> <term_tail>`
85. `<term_tail> → <mul_ops> <factor> <term_tail>`
86. `<term_tail> → λ`
87. `<factor> → id <ident_tail>`
88. `<factor> → <literals>`
89. `<factor> → ( <expr> )`
90. `<factor> → <unary_ops> id`
91. `<ident_tail> → [ <expr> ]`
92. `<ident_tail> → <unary_ops>`
93. `<ident_tail> → ( <arguments> )`
94. `<ident_tail> → λ`
95. `<unary_ops> → ++`
96. `<unary_ops> → --`
97. `<add_ops> → +`
98. `<add_ops> → -`
99. `<mul_ops> → *`
100. `<mul_ops> → /`
101. `<mul_ops> → %`
102. `<input_state> → give >> id ;`
103. `<input_state> → overshare ( id ) ;`
104. `<output_state> → express <output_chain> ;`
105. `<output_chain> → << <output_values> <output_chain>`
106. `<output_chain> → << <output_values>`
107. `<output_values> → <expr>`
108. `<output_values> → periodt`
109. `<conditional_state> → forever ( <condi> ) { <condi_body> } <forevermore_statement> <more_case>`
110. `<condi> → <condi_or>`
111. `<condi_or> → <condi_and> <or_tail>`
112. `<or_tail> → **`
113. `<or_tail> → λ`
114. `<condi_and> → <rel_expr> <and_tail>`
115. `<and_tail> → && <rel_expr> <and_tail>`
116. `<and_tail> → λ`
117. `<rel_expr> → <expr> <rel_ops> <expr>`
118. `<rel_expr> → <expr>`
119. `<rel_ops> → >`
120. `<rel_ops> → <`
121. `<rel_ops> → >=`
122. `<rel_ops> → <=`
123. `<rel_ops> → !=`
124. `<rel_ops> → ==`
125. `<condi_body> → <statements>`
126. `<forevermore_statement> → forevermore ( <condi> ) { <condi_body> } <forevermore_statement>`
127. `<forevermore_statement> → λ`
128. `<more_case> → more { <condi_body> }`
129. `<more_case> → λ`
130. `<loop_state> → <for_state>`
131. `<loop_state> → <while_state>`
132. `<loop_state> → <pursue_state>`
133. `<for_state> → for ( <loop_init> ; <condi> ; <update> ) { <loop_body> }`
134. `<loop_init> → <data type> id = <expr>`
135. `<loop_init> → id = <expr>`
136. `<update> → id <unary_ops>`
137. `<update> → <unary_ops> id`
138. `<while_state> → while ( <condi> ) { <loop_body> }`
139. `<pursue_state> → pursue ( <condi> ) { <loop_body> }`
140. `<loop_body> → <statements>`
141. `<loop_body> → <cf_state>`
142. `<choose_state> → choose ( <expr> ) { <cases> <bareminimum_case> }`
143. `<cases> → phase <literals> : <choose_block> <breakup_case> <cases>`
144. `<cases> → λ`
145. `<choose_block> → <statements>`
146. `<breakup_case> → breakup ;`
147. `<breakup_case> → λ`
148. `<bareminimum_case> → bareminimum : <choose_block> <breakup_case>`
149. `<bareminimum_case> → λ`
150. `<cf_state> → breakup ;`
151. `<cf_state> → moveon ;`
152. `<comeback_state> → comeback <return_values> ;`
153. `<return_values> → <expr>`
154. `<return_values> → λ`
155. `<unary_state> → <unary_ops> id`
