# CFG Production Table for Lovers Language
# Single source of truth: all productions in one map.
# Used by parsetv2.py for reference; LL(1) parsing table is built from this grammar.
#
# Format: PRODUCTION_LIST[num] = (lhs, rhs)  where rhs is list of symbols.
# λ (epsilon) is represented as ["λ"].

from typing import Dict, List, Tuple

# Production number -> (lhs, rhs). rhs is list of symbols; ["λ"] = epsilon.
# Top-level: <top_decls_opt> then love () { body }. Declarations are STRICT TYPED:
#   dear/dearest/rant/status each have *_tail rules that expect only the matching literal type.

PRODUCTION_LIST: Dict[int, Tuple[str, List[str]]] = {
    1: ("<program>", ["<top_decls_opt>", "love", "(", ")", "{", "<body_func>", "}"]),
    2: ("<top_decls_opt>", ["<top_decl>", "<top_decls_opt>"]),
    3: ("<top_decls_opt>", ["λ"]),
    
    # ==========================================
    # 1. TOP-LEVEL DECLARATIONS (STRICT TYPED)
    # ==========================================
    # After "dear id" / "dearest id" etc.: ( parameter ) { body } = function, else _tail = variable
    # Type name: id or literals (same logic for dear, dearest, rant, status)
    389: ("<dearest_name>", ["id"]),
    390: ("<dearest_name>", ["dear_lit"]),
    391: ("<dearest_name>", ["dearest_lit"]),
    396: ("<dear_name>", ["id"]),
    397: ("<dear_name>", ["dear_lit"]),
    398: ("<dear_name>", ["dearest_lit"]),
    399: ("<rant_name>", ["id"]),
    400: ("<rant_name>", ["rant_lit"]),
    401: ("<status_name>", ["id"]),
    402: ("<status_name>", ["greenflag"]),
    403: ("<status_name>", ["redflag"]),
    4: ("<top_decl>", ["dear", "<dear_name>", "<dear_after_id>"]),
    5: ("<top_decl>", ["dearest", "<dearest_name>", "<dearest_after_id>"]),
    6: ("<top_decl>", ["rant", "<rant_name>", "<rant_after_id>"]),
    7: ("<top_decl>", ["status", "<status_name>", "<status_after_id>"]),
    8: ("<top_decl>", ["boundaries", "id", "{", "<boundaries_decls_opt>", "}"]),
    9: ("<top_decl>", ["avoidant", "id", "(", "<parameter>", ")", "{", "<body_func>", "}"]),

    # Return-type functions: type id ( parameter ) { body_func }
    218: ("<dear_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]),
    219: ("<dear_after_id>", ["<dear_tail>"]),
    220: ("<dearest_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]),
    221: ("<dearest_after_id>", ["<dearest_tail>"]),
    222: ("<rant_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]),
    223: ("<rant_after_id>", ["<rant_tail>"]),
    224: ("<status_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]),
    225: ("<status_after_id>", ["<status_tail>"]),
    # const <data-type> <identifier> = <value/expression> ; (factored so LL(1) chooses by data-type)
    10: ("<top_decl>", ["const", "<const_decl>"]),
    404: ("<const_decl>", ["dear", "<dear_name>", "=", "<dear_expr>", ";"]),
    405: ("<const_decl>", ["dearest", "<dearest_name>", "=", "<dearest_expr>", ";"]),
    406: ("<const_decl>", ["rant", "<rant_name>", "=", "<rant_expr>", ";"]),
    407: ("<const_decl>", ["status", "<status_name>", "=", "<status_lit>", ";"]),

    # A. DEAR (Integer) - Type-specific init expr: expected (, +, ++, -, --, dear_lit, id
    14: ("<dear_tail>", ["=", "<dear_expr>", "<dear_multi>", ";"]),
    15: ("<dear_tail>", ["<dear_multi>", ";"]),
    16: ("<dear_tail>", ["[", "<dear_array_after_lbracket>"]),
    380: ("<dear_array_after_lbracket>", ["]", "=", "<dear_array_source>", ";"]),
    381: ("<dear_array_after_lbracket>", ["<dear_expr>", "]", "<dear_array_assign>", "<dear_multi>", ";"]),
    17: ("<dear_multi>", [",", "id", "<dear_init_opt>", "<dear_multi>"]),
    18: ("<dear_multi>", ["λ"]),
    19: ("<dear_init_opt>", ["=", "<dear_expr>"]),
    20: ("<dear_init_opt>", ["λ"]),

    # B. DEAREST (Float) - Uses <dearest_expr> (No %, bitwise). Array size = <dear_expr>
    21: ("<dearest_tail>", ["=", "<dearest_expr>", "<dearest_multi>", ";"]),
    22: ("<dearest_tail>", ["<dearest_multi>", ";"]),
    23: ("<dearest_tail>", ["[", "<dearest_array_after_lbracket>"]),
    382: ("<dearest_array_after_lbracket>", ["]", "=", "<dearest_array_source>", ";"]),
    383: ("<dearest_array_after_lbracket>", ["<dear_expr>", "]", "<dearest_array_assign>", "<dearest_multi>", ";"]),
    24: ("<dearest_multi>", [",", "id", "<dearest_init_opt>", "<dearest_multi>"]),
    25: ("<dearest_multi>", ["λ"]),
    26: ("<dearest_init_opt>", ["=", "<dearest_expr>"]),
    27: ("<dearest_init_opt>", ["λ"]),

   # C. RANT (String) - Uses <rant_expr> (Concat only). Array size = <dear_expr>
    28: ("<rant_tail>", ["=", "<rant_expr>", "<rant_multi>", ";"]),
    29: ("<rant_tail>", ["<rant_multi>", ";"]),
    30: ("<rant_tail>", ["[", "<rant_array_after_lbracket>"]),
    384: ("<rant_array_after_lbracket>", ["]", "=", "<rant_array_source>", ";"]),
    385: ("<rant_array_after_lbracket>", ["<dear_expr>", "]", "<rant_array_assign>", "<rant_multi>", ";"]),
    31: ("<rant_multi>", [",", "id", "<rant_init_opt>", "<rant_multi>"]),
    32: ("<rant_multi>", ["λ"]),
    33: ("<rant_init_opt>", ["=", "<rant_expr>"]),
    34: ("<rant_init_opt>", ["λ"]),
    259: ("<rant_init_val>", ["rant_lit"]),
    260: ("<rant_init_val>", ["id"]),

    # D. STATUS (Boolean) - Uses <status_expr> (Logic + Relational). Array size = <dear_expr>
    35: ("<status_tail>", ["=", "<status_expr>", "<status_multi>", ";"]),
    36: ("<status_tail>", ["<status_multi>", ";"]),
    37: ("<status_tail>", ["[", "<status_array_after_lbracket>"]),
    386: ("<status_array_after_lbracket>", ["]", "=", "<status_array_source>", ";"]),
    387: ("<status_array_after_lbracket>", ["<dear_expr>", "]", "<status_array_assign>", "<status_multi>", ";"]),
    38: ("<status_multi>", [",", "id", "<status_init_opt>", "<status_multi>"]),
    39: ("<status_multi>", ["λ"]),
    40: ("<status_init_opt>", ["=", "<status_expr>"]),
    41: ("<status_init_opt>", ["λ"]),
    261: ("<status_init_expr>", ["<status_lit>"]),
    262: ("<status_init_expr>", ["id"]),
    263: ("<status_init_expr>", ["(", "<paren_expr>", ")"]),
    264: ("<status_init_expr>", ["not", "<status_init_expr>"]),
    42: ("<status_lit>", ["greenflag"]),
    43: ("<status_lit>", ["redflag"]),

    # DEAR init expr (restricted factor: dear_lit, id, (, +, -, ++, --)
    226: ("<dear_init_expr>", ["<dear_init_term>", "<dear_init_expr_next>"]),
    227: ("<dear_init_expr_next>", ["+", "<dear_init_term>", "<dear_init_expr_next>"]),
    228: ("<dear_init_expr_next>", ["-", "<dear_init_term>", "<dear_init_expr_next>"]),
    229: ("<dear_init_expr_next>", ["λ"]),
    230: ("<dear_init_term>", ["<dear_init_factor>", "<dear_init_term_next>"]),
    231: ("<dear_init_term_next>", ["*", "<dear_init_factor>", "<dear_init_term_next>"]),
    232: ("<dear_init_term_next>", ["/", "<dear_init_factor>", "<dear_init_term_next>"]),
    233: ("<dear_init_term_next>", ["%", "<dear_init_factor>", "<dear_init_term_next>"]),
    234: ("<dear_init_term_next>", ["λ"]),
    235: ("<dear_init_factor>", ["(", "<paren_expr>", ")"]),
    236: ("<dear_init_factor>", ["id", "<factor_tail>"]),
    237: ("<dear_init_factor>", ["dear_lit"]),
    238: ("<dear_init_factor>", ["-", "<dear_init_factor>"]),
    239: ("<dear_init_factor>", ["+", "<dear_init_factor>"]),
    240: ("<dear_init_factor>", ["++", "id"]),
    241: ("<dear_init_factor>", ["--", "id"]),

    # DEAREST init expr (restricted factor: dearest_lit, dear_lit, id, (, +, -, ++, --)
    242: ("<dearest_init_expr>", ["<dearest_init_term>", "<dearest_init_expr_next>"]),
    243: ("<dearest_init_expr_next>", ["+", "<dearest_init_term>", "<dearest_init_expr_next>"]),
    244: ("<dearest_init_expr_next>", ["-", "<dearest_init_term>", "<dearest_init_expr_next>"]),
    245: ("<dearest_init_expr_next>", ["λ"]),
    246: ("<dearest_init_term>", ["<dearest_init_factor>", "<dearest_init_term_next>"]),
    247: ("<dearest_init_term_next>", ["*", "<dearest_init_factor>", "<dearest_init_term_next>"]),
    248: ("<dearest_init_term_next>", ["/", "<dearest_init_factor>", "<dearest_init_term_next>"]),
    249: ("<dearest_init_term_next>", ["%", "<dearest_init_factor>", "<dearest_init_term_next>"]),
    250: ("<dearest_init_term_next>", ["λ"]),
    251: ("<dearest_init_factor>", ["(", "<paren_expr>", ")"]),
    252: ("<dearest_init_factor>", ["id", "<factor_tail>"]),
    253: ("<dearest_init_factor>", ["dearest_lit"]),
    254: ("<dearest_init_factor>", ["dear_lit"]),
    255: ("<dearest_init_factor>", ["-", "<dearest_init_factor>"]),
    256: ("<dearest_init_factor>", ["+", "<dearest_init_factor>"]),
    257: ("<dearest_init_factor>", ["++", "id"]),
    258: ("<dearest_init_factor>", ["--", "id"]),

    44: ("<boundaries_decls_opt>", ["<top_decl>", "<boundaries_decls_opt>"]),
    45: ("<boundaries_decls_opt>", ["λ"]),

    # ==========================================
    # 2. FUNCTIONS & LOCAL DECLARATIONS (STRICT TYPED)
    # ==========================================
    46: ("<body_func>", ["<local_decl_list>", "<statements>"]),
    47: ("<local_decl_list>", ["<local_decl>", "<local_decl_list>"]),
    48: ("<local_decl_list>", ["λ"]),
    49: ("<local_decl>", ["dear", "<dear_name>", "<dear_tail>"]),
    50: ("<local_decl>", ["dearest", "<dearest_name>", "<dearest_tail>"]),
    51: ("<local_decl>", ["rant", "<rant_name>", "<rant_tail>"]),
    52: ("<local_decl>", ["status", "<status_name>", "<status_tail>"]),

    # ==========================================
    # 3. ASSIGNMENT LOGIC
    # ==========================================
    # SCALAR: Used in statements (id = expr ;)
    53: ("<scalar_assign>", ["=", "<expr_ar>"]),
    54: ("<scalar_assign>", ["λ"]),

    # ARRAY: Strict Source (List or ID) - generic still used by init_value elsewhere
    55: ("<array_assign>", ["=", "<array_source>"]),
    56: ("<array_assign>", ["λ"]),
    57: ("<array_source>", ["{", "<array_lit_list>", "}"]),
    58: ("<array_source>", ["id"]),

    # TYPE-SPECIFIC ARRAY INITIALIZERS (rant_lit|id, dear_lit|id|-dear_lit, etc.)
    # RANT: rant_lit or id only
    336: ("<rant_array_source>", ["{", "<rant_array_lit_list>", "}"]),

    338: ("<rant_array_lit_list>", ["<rant_array_elem>", "<more_rant_array_lit>"]),
    339: ("<rant_array_elem>", ["rant_lit"]),
    340: ("<rant_array_elem>", ["id"]),
    341: ("<more_rant_array_lit>", [",", "<rant_array_elem>", "<more_rant_array_lit>"]),
    342: ("<more_rant_array_lit>", ["λ"]),
    # DEAR: dear_lit, id, or -dear_lit
    343: ("<dear_array_source>", ["{", "<dear_array_lit_list>", "}"]),
    
    345: ("<dear_array_lit_list>", ["<dear_array_elem>", "<more_dear_array_lit>"]),
    346: ("<dear_array_elem>", ["dear_lit"]),
    347: ("<dear_array_elem>", ["id"]),
    348: ("<dear_array_elem>", ["-", "dear_lit"]),
    349: ("<more_dear_array_lit>", [",", "<dear_array_elem>", "<more_dear_array_lit>"]),
    350: ("<more_dear_array_lit>", ["λ"]),
    # DEAREST: dearest_lit, dear_lit, id, -dearest_lit, -dear_lit
    351: ("<dearest_array_source>", ["{", "<dearest_array_lit_list>", "}"]),
    
    353: ("<dearest_array_lit_list>", ["<dearest_array_elem>", "<more_dearest_array_lit>"]),
    354: ("<dearest_array_elem>", ["dearest_lit"]),
    355: ("<dearest_array_elem>", ["dear_lit"]),
    356: ("<dearest_array_elem>", ["id"]),
    357: ("<dearest_array_elem>", ["-", "<dearest_neg_lit>"]),
    358: ("<dearest_neg_lit>", ["dearest_lit"]),
    359: ("<dearest_neg_lit>", ["dear_lit"]),
    360: ("<more_dearest_array_lit>", [",", "<dearest_array_elem>", "<more_dearest_array_lit>"]),
    361: ("<more_dearest_array_lit>", ["λ"]),
    # STATUS: greenflag, redflag, id
    362: ("<status_array_source>", ["{", "<status_array_lit_list>", "}"]),
    
    364: ("<status_array_lit_list>", ["<status_array_elem>", "<more_status_array_lit>"]),
    365: ("<status_array_elem>", ["greenflag"]),
    366: ("<status_array_elem>", ["redflag"]),
    367: ("<status_array_elem>", ["id"]),
    368: ("<more_status_array_lit>", [",", "<status_array_elem>", "<more_status_array_lit>"]),
    369: ("<more_status_array_lit>", ["λ"]),
    # Type-specific array assign (optional = source)
    370: ("<dear_array_assign>", ["=", "<dear_array_source>"]),
    371: ("<dear_array_assign>", ["λ"]),
    372: ("<dearest_array_assign>", ["=", "<dearest_array_source>"]),
    373: ("<dearest_array_assign>", ["λ"]),
    374: ("<rant_array_assign>", ["=", "<rant_array_source>"]),
    375: ("<rant_array_assign>", ["λ"]),
    376: ("<status_array_assign>", ["=", "<status_array_source>"]),
    377: ("<status_array_assign>", ["λ"]),

    # ==========================================
    # 4. INITIALIZATION & VALUES
    # ==========================================
    59: ("<var_initial>", ["=", "<expr_ar>"]),
    60: ("<var_initial>", ["=", "<init_value>"]),
    61: ("<var_initial>", ["λ"]),

    # ARRAY LIST: Strict Simple Values Only (No Math inside {})
    62: ("<init_value>", ["<simple_val>"]),
    63: ("<init_value>", ["{", "<array_lit_list>", "}"]),
    64: ("<array_lit_list>", ["<init_value>", "<more_array_lit>"]),
    65: ("<more_array_lit>", [",", "<init_value>", "<more_array_lit>"]),
    66: ("<more_array_lit>", ["λ"]),

    # Simple Values Whitelist (for array literals etc.)
    67: ("<simple_val>", ["dear_lit"]),
    68: ("<simple_val>", ["dearest_lit"]),
    69: ("<simple_val>", ["rant_lit"]),
    70: ("<simple_val>", ["greenflag"]),
    71: ("<simple_val>", ["redflag"]),
    72: ("<simple_val>", ["id"]),
    73: ("<simple_val>", ["-", "dear_lit"]),
    74: ("<simple_val>", ["-", "dearest_lit"]),
    75: ("<simple_val>", ["λ"]),

    # ==========================================
    # 5. DATA TYPES & PARAMETERS
    # ==========================================
    76: ("<data_type>", ["dear"]),
    77: ("<data_type>", ["dearest"]),
    78: ("<data_type>", ["rant"]),
    79: ("<data_type>", ["status"]),

    80: ("<parameter>", ["<function_parameter>", "<multi_parameter>"]),
    81: ("<parameter>", ["λ"]),
    82: ("<function_parameter>", ["<data_type>", "id", "<param_array_decl>"]),
    83: ("<multi_parameter>", [",", "<function_parameter>", "<multi_parameter>"]),
    84: ("<multi_parameter>", ["λ"]),
    85: ("<param_array_decl>", ["[", "]", "<param_array_decl>"]),
    86: ("<param_array_decl>", ["λ"]),
    87: ("<array_decl>", ["[", "<array_size>", "]", "<array_decl>"]),
    88: ("<array_decl>", ["λ"]),
    89: ("<array_size>", ["dear_lit"]),
    90: ("<array_size>", ["λ"]),

    # ==========================================
    # 6. STATEMENTS
    # ==========================================
    91: ("<statements>", ["id", "<id_suffix>", "<statements>"]),
    92: ("<statements>", ["<input_state>", "<statements>"]),
    93: ("<statements>", ["<output_state>", "<statements>"]),
    94: ("<statements>", ["<conditional_state>", "<statements>"]),
    95: ("<statements>", ["<loop_state>", "<statements>"]),
    96: ("<statements>", ["<comeback_state>", "<statements>"]),
    97: ("<statements>", ["<choose_state>", "<statements>"]),
    98: ("<statements>", ["<unary_state>", "<statements>"]),
    99: ("<statements>", ["<break_state>", "<statements>"]),
    100: ("<statements>", ["λ"]),

    # ==========================================
    # 7. ID SUFFIXES & UNARY
    # ==========================================
    # Array index: dedicated nonterminal (semicolon not part of it; can tailor later)
    388: ("<array_index_expr>", ["<expr>"]),
    101: ("<id_suffix>", ["[", "<array_index_expr>", "]", "<id_suffix>"]),
    102: ("<id_suffix>", ["<assign_ops>", "<assign_values>", ";"]),
    103: ("<id_suffix>", ["(", "<arguments>", ")", ";"]),
    104: ("<id_suffix>", ["<unary_ops>", ";"]),
    105: ("<id_suffix>", ["::", "id", "<id_suffix>"]),

    106: ("<unary_state>", ["<unary_ops>", "id", ";"]),
    107: ("<unary_ops>", ["++"]),
    108: ("<unary_ops>", ["--"]),

    109: ("<assign_ops>", ["="]),
    110: ("<assign_ops>", ["+="]),
    111: ("<assign_ops>", ["-="]),
    112: ("<assign_ops>", ["*="]),
    113: ("<assign_ops>", ["/="]),
    114: ("<assign_ops>", ["%="]),

    # ASSIGNMENT: Strict Arithmetic Only (Prevents x = y == z)
    115: ("<assign_values>", ["<assign_rhs_expr>"]),
    116: ("<arguments>", ["<paren_expr>", "<more_arguments>"]),
    117: ("<arguments>", ["λ"]),
    118: ("<more_arguments>", [",", "<paren_expr>", "<more_arguments>"]),
    119: ("<more_arguments>", ["λ"]),

    # ==========================================
    # 8. I/O & CONTROL FLOW
    # ==========================================
    120: ("<input_state>", ["give", ">>", "id", "<input_tail>", "<more_input_ids>", ";"]),
    121: ("<input_state>", ["overshare", "(", "id", ")", ";"]),
    122: ("<input_tail>", ["[", "<array_index_expr>", "]", "<input_tail>"]),
    123: ("<input_tail>", ["λ"]),
    124: ("<more_input_ids>", [">>", "id", "<input_tail>", "<more_input_ids>"]),
    125: ("<more_input_ids>", ["λ"]),

    126: ("<output_state>", ["express", "<<", "<output_values>", "<more_output_tail>", ";"]),
    127: ("<more_output_tail>", ["<<", "<output_values>", "<more_output_tail>"]),
    128: ("<more_output_tail>", ["λ"]),
    129: ("<output_values>", ["<expr>"]),
    130: ("<output_values>", ["periodt"]),

    131: ("<comeback_state>", ["comeback", "<expr_opt>", ";"]),
    132: ("<break_state>", ["breakup", ";"]),

    # ==========================================
    # 9. LOOPS & CONDITIONS
    # ==========================================
    133: ("<conditional_state>", ["forever", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>", "<more_opt>"]),
    134: ("<forevermore_lst>", ["forevermore", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>"]),
    135: ("<forevermore_lst>", ["λ"]),
    136: ("<more_opt>", ["more", "{", "<body_func>", "}"]),
    137: ("<more_opt>", ["λ"]),

    138: ("<loop_state>", ["<pursue_stmt>"]),
    139: ("<loop_state>", ["<while_stmt>"]),
    140: ("<loop_state>", ["<for_stmt>"]),

    141: ("<pursue_stmt>", ["pursue", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    142: ("<while_stmt>", ["while", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    143: ("<for_stmt>", ["for", "(", "<for_init>", ";", "<expr>", ";", "<for_ud>", ")", "{", "<body_func>", "}"]),

    144: ("<for_init>", ["<data_type>", "id", "=", "<expr_ar>"]),
    145: ("<for_init>", ["id", "=", "<expr_ar>"]),

    146: ("<for_ud>", ["id", "<assign_ops>", "<expr>"]),
    147: ("<for_ud>", ["id", "<unary_ops>"]),
    148: ("<for_ud>", ["<unary_ops>", "id"]),

    149: ("<choose_state>", ["choose", "(", "<expr>", ")", "{", "<phase_lst>", "<bareminimum_opt>", "}"]),
    150: ("<phase_lst>", ["phase", "<choose_const>", ":", "<body_func>", "breakup", ";", "<phase_lst_next>"]),
    151: ("<phase_lst_next>", ["<phase_lst>"]),
    152: ("<phase_lst_next>", ["λ"]),
    153: ("<choose_const>", ["dear_lit"]),
    154: ("<bareminimum_opt>", ["bareminimum", ":", "<body_func>", "breakup", ";"]),
    155: ("<bareminimum_opt>", ["λ"]),

    # ==========================================
    # 10. EXPRESSIONS (MAIN HIERARCHY)
    # ==========================================
    156: ("<expr>", ["<log_expr>"]),
    157: ("<expr_opt>", ["<expr>"]),
    158: ("<expr_opt>", ["λ"]),

    159: ("<log_expr>", ["<and_expr>", "<log_next>"]),
    160: ("<log_next>", ["||", "<and_expr>", "<log_next>"]),
    161: ("<log_next>", ["λ"]),

    162: ("<and_expr>", ["<rel_expr>", "<and_next>"]),
    163: ("<and_next>", ["&&", "<rel_expr>", "<and_next>"]),
    164: ("<and_next>", ["λ"]),

    165: ("<rel_expr>", ["<expr_ar>", "<rel_next>"]),
    166: ("<rel_next>", ["<rel_op>", "<expr_ar>", "<rel_next>"]),
    167: ("<rel_next>", ["λ"]),
    168: ("<rel_op>", ["=="]),
    169: ("<rel_op>", ["!="]),
    170: ("<rel_op>", ["<"]),
    171: ("<rel_op>", ["<="]),
    172: ("<rel_op>", [">"]),
    173: ("<rel_op>", [">="]),

    174: ("<expr_ar>", ["<term>", "<expr_next>"]),
    175: ("<expr_next>", ["+", "<term>", "<expr_next>"]),
    176: ("<expr_next>", ["-", "<term>", "<expr_next>"]),
    177: ("<expr_next>", ["λ"]),

    178: ("<term>", ["<factor>", "<term_next>"]),
    179: ("<term_next>", ["*", "<factor>", "<term_next>"]),
    180: ("<term_next>", ["/", "<factor>", "<term_next>"]),
    181: ("<term_next>", ["%", "<factor>", "<term_next>"]),
    182: ("<term_next>", ["λ"]),

    # ==========================================
    # 11. FACTORS & TAILS
    # ==========================================
    183: ("<factor>", ["(", "<paren_expr>", ")"]),
    184: ("<factor>", ["id", "<factor_tail>"]),
    185: ("<factor>", ["dear_lit"]),
    186: ("<factor>", ["dearest_lit"]),
    187: ("<factor>", ["rant_lit"]),
    188: ("<factor>", ["<status_lit>"]),
    189: ("<factor>", ["-", "<factor>"]),
    190: ("<factor>", ["+", "<factor>"]),
    191: ("<factor>", ["++", "id"]),
    192: ("<factor>", ["--", "id"]),

    193: ("<factor_tail>", ["[", "<array_index_expr>", "]", "<factor_tail>"]),
    194: ("<factor_tail>", ["(", "<arguments>", ")"]),
    195: ("<factor_tail>", ["++"]),
    196: ("<factor_tail>", ["--"]),
    197: ("<factor_tail>", ["::", "id", "<factor_tail>"]),
    198: ("<factor_tail>", ["λ"]),

    # ==========================================
    # 12. PARENTHESIS-ONLY HIERARCHY
    # ==========================================
    199: ("<paren_expr>", ["<paren_log_expr>"]),
    200: ("<paren_log_expr>", ["<paren_and_expr>", "<paren_log_next>"]),
    201: ("<paren_log_next>", ["||", "<paren_and_expr>", "<paren_log_next>"]),
    202: ("<paren_log_next>", ["λ"]),
    203: ("<paren_and_expr>", ["<paren_rel_expr>", "<paren_and_next>"]),
    204: ("<paren_and_next>", ["&&", "<paren_rel_expr>", "<paren_and_next>"]),
    205: ("<paren_and_next>", ["λ"]),
    206: ("<paren_rel_expr>", ["<paren_expr_ar>", "<paren_rel_next>"]),
    207: ("<paren_rel_next>", ["<rel_op>", "<paren_expr_ar>", "<paren_rel_next>"]),
    208: ("<paren_rel_next>", ["λ"]),
    209: ("<paren_expr_ar>", ["<paren_term>", "<paren_expr_next>"]),
    210: ("<paren_expr_next>", ["+", "<paren_term>", "<paren_expr_next>"]),
    211: ("<paren_expr_next>", ["-", "<paren_term>", "<paren_expr_next>"]),
    212: ("<paren_expr_next>", ["λ"]),
    213: ("<paren_term>", ["<factor>", "<paren_term_next>"]),
    214: ("<paren_term_next>", ["*", "<factor>", "<paren_term_next>"]),
    215: ("<paren_term_next>", ["/", "<factor>", "<paren_term_next>"]),
    216: ("<paren_term_next>", ["%", "<factor>", "<paren_term_next>"]),
    217: ("<paren_term_next>", ["λ"]),

    # Assignment RHS: comparison and logical allowed; == and != prohibited (prevents x = y == z)
    265: ("<assign_rhs_expr>", ["<assign_rhs_log_expr>"]),
    266: ("<assign_rhs_log_expr>", ["<assign_rhs_and_expr>", "<assign_rhs_log_next>"]),
    267: ("<assign_rhs_log_next>", ["||", "<assign_rhs_and_expr>", "<assign_rhs_log_next>"]),
    268: ("<assign_rhs_log_next>", ["λ"]),
    269: ("<assign_rhs_and_expr>", ["<assign_rhs_rel_expr>", "<assign_rhs_and_next>"]),
    270: ("<assign_rhs_and_next>", ["&&", "<assign_rhs_rel_expr>", "<assign_rhs_and_next>"]),
    271: ("<assign_rhs_and_next>", ["λ"]),
    272: ("<assign_rhs_rel_expr>", ["<expr_ar>", "<assign_rhs_rel_next>"]),
    273: ("<assign_rhs_rel_next>", ["<assign_rhs_rel_op>", "<expr_ar>", "<assign_rhs_rel_next>"]),
    274: ("<assign_rhs_rel_next>", ["λ"]),
    275: ("<assign_rhs_rel_op>", ["<"]),
    276: ("<assign_rhs_rel_op>", ["<="]),
    277: ("<assign_rhs_rel_op>", [">"]),
    278: ("<assign_rhs_rel_op>", [">="]),
    378: ("<assign_rhs_rel_op>", ["=="]),
    379: ("<assign_rhs_rel_op>", ["!="]),
    # ==========================================
    # TAILORED EXPRESSIONS (C++ MIMIC)
    # ==========================================
    # A. INTEGER (dear) - Math + Bitwise
    279: ("<dear_expr>", ["<dear_term>", "<dear_next>"]),
    280: ("<dear_next>", ["+", "<dear_term>", "<dear_next>"]),
    281: ("<dear_next>", ["-", "<dear_term>", "<dear_next>"]),
    282: ("<dear_next>", ["<<", "<dear_term>", "<dear_next>"]),
    283: ("<dear_next>", [">>", "<dear_term>", "<dear_next>"]),
    
  
    
    287: ("<dear_next>", ["λ"]),
    288: ("<dear_term>", ["<dear_factor>", "<dear_term_next>"]),
    289: ("<dear_term_next>", ["*", "<dear_factor>", "<dear_term_next>"]),
    290: ("<dear_term_next>", ["/", "<dear_factor>", "<dear_term_next>"]),
    291: ("<dear_term_next>", ["%", "<dear_factor>", "<dear_term_next>"]),
    292: ("<dear_term_next>", ["λ"]),
    293: ("<dear_factor>", ["(", "<dear_expr>", ")"]),
    294: ("<dear_factor>", ["dear_lit"]),
    295: ("<dear_factor>", ["id"]),
    296: ("<dear_factor>", ["-", "<dear_factor>"]),
    297: ("<dear_factor>", ["+", "<dear_factor>"]),
   

    # B. FLOAT (dearest) - Same arithmetic as dear: +, -, *, /, %, <<, >>
    299: ("<dearest_expr>", ["<dearest_term>", "<dearest_next>"]),
    300: ("<dearest_next>", ["+", "<dearest_term>", "<dearest_next>"]),
    301: ("<dearest_next>", ["-", "<dearest_term>", "<dearest_next>"]),
    393: ("<dearest_next>", ["<<", "<dearest_term>", "<dearest_next>"]),
    394: ("<dearest_next>", [">>", "<dearest_term>", "<dearest_next>"]),
    302: ("<dearest_next>", ["λ"]),
    303: ("<dearest_term>", ["<dearest_factor>", "<dearest_term_next>"]),
    304: ("<dearest_term_next>", ["*", "<dearest_factor>", "<dearest_term_next>"]),
    305: ("<dearest_term_next>", ["/", "<dearest_factor>", "<dearest_term_next>"]),
    395: ("<dearest_term_next>", ["%", "<dearest_factor>", "<dearest_term_next>"]),
    306: ("<dearest_term_next>", ["λ"]),
    307: ("<dearest_factor>", ["(", "<dearest_expr>", ")"]),
    308: ("<dearest_factor>", ["dearest_lit"]),
    309: ("<dearest_factor>", ["id"]),
    392: ("<dearest_factor>", ["dear_lit"]),
    310: ("<dearest_factor>", ["-", "<dearest_factor>"]),

    # C. STRING (rant) - Concat only
    311: ("<rant_expr>", ["<rant_term>", "<rant_next>"]),
    312: ("<rant_next>", ["+", "<rant_term>", "<rant_next>"]),
    313: ("<rant_next>", ["λ"]),
    314: ("<rant_term>", ["<rant_factor>"]),
    315: ("<rant_factor>", ["(", "<rant_expr>", ")"]),
    316: ("<rant_factor>", ["rant_lit"]),
    317: ("<rant_factor>", ["id"]),

    # D. BOOLEAN (status) - Logic + Relational; uses status_int_compare (dear_expr comparisons)
    318: ("<status_expr>", ["<status_and>", "<status_or_next>"]),
    319: ("<status_or_next>", ["||", "<status_and>", "<status_or_next>"]),
    320: ("<status_or_next>", ["λ"]),
    321: ("<status_and>", ["<status_factor>", "<status_and_next>"]),
    322: ("<status_and_next>", ["&&", "<status_factor>", "<status_and_next>"]),
    323: ("<status_and_next>", ["λ"]),
    324: ("<status_factor>", ["(", "<status_expr>", ")"]),
    325: ("<status_factor>", ["not", "<status_factor>"]),
    326: ("<status_factor>", ["<status_lit>"]),
    327: ("<status_factor>", ["id"]),
    328: ("<status_factor>", ["<status_int_compare>"]),

    # E. Integer comparison (used inside status_factor for x > y etc.)
    329: ("<status_int_compare>", ["<dear_expr>", "<status_int_compare_next>"]),
    330: ("<status_int_compare_next>", ["<rel_op>", "<dear_expr>"]),
    331: ("<status_int_compare_next>", ["λ"]),

    # Assignment RHS: comparison and logical allowed; == and != prohibited (prevents x = y == z)
}


# By nonterminal: lhs -> list of RHS (each RHS is list of symbols). Easy lookup.
CFG_BY_NONTERMINAL: Dict[str, List[List[str]]] = {}
for _num, (lhs, rhs) in PRODUCTION_LIST.items():
    if lhs not in CFG_BY_NONTERMINAL:
        CFG_BY_NONTERMINAL[lhs] = []
    CFG_BY_NONTERMINAL[lhs].append(rhs)


def get_productions(lhs: str) -> List[List[str]]:
    """Return all RHS alternatives for nonterminal lhs."""
    return CFG_BY_NONTERMINAL.get(lhs, [])


def is_epsilon(rhs: List[str]) -> bool:
    """True if RHS is epsilon (λ or null)."""
    return rhs in (["λ"], ["null"]) or (len(rhs) == 1 and rhs[0] in ("λ", "null"))
