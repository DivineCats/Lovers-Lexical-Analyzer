# CFG Production Table for Lovers Language
# Single source of truth: all productions in one map.
# Used by parsetv2.py for reference; LL(1) parsing table is built from this grammar.
#
# Format: PRODUCTION_LIST[num] = (lhs, rhs)  where rhs is list of symbols.
# λ (epsilon) is represented as ["λ"].

from typing import Dict, List, Tuple

# Production number -> (lhs, rhs). rhs is list of symbols; ["λ"] = epsilon.
# Top-level: <top_decls_opt> (boundaries blocks, globals, sub-functions in any order), then love () { body }.
# 136 base productions; paren-only rules 200..218 (expressions inside ( ) so ; is never valid).
PRODUCTION_LIST: Dict[int, Tuple[str, List[str]]] = {
    1: ("<program>", ["<top_decls_opt>", "love", "(", ")", "{", "<body_func>", "}"]),
    2: ("<top_decls_opt>", ["<top_decl>", "<top_decls_opt>"]),
    3: ("<top_decls_opt>", ["λ"]),
    4: ("<top_decl>", ["boundaries", "id", "{", "<boundaries_decls_opt>", "}"]),
    5: ("<top_decl>", ["<data_type>", "id", "<top_after_id>"]),
    6: ("<top_decl>", ["const", "<data_type>", "id", "=", "<expr_ar>", ";"]),
    7: ("<top_decl>", ["avoidant", "id", "(", "<parameter>", ")", "{", "<body_func>", "}"]),
    8: ("<top_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]),
    9: ("<top_after_id>", ["[", "<array_size>", "]", "<array_assign>", "<multi_decl>", ";"]),
    10: ("<multi_decl>", [",", "id", "<array_decl>", "<var_initial>", "<multi_decl>"]),
    11: ("<multi_decl>", ["λ"]),
    12: ("<var_initial>", ["=", "<expr_ar>"]),
    13: ("<var_initial>", ["=", "<init_value>"]),
    14: ("<var_initial>", ["λ"]),
    15: ("<init_value>", ["<simple_val>"]),
    16: ("<init_value>", ["{", "<array_lit_list>", "}"]),
    17: ("<array_lit_list>", ["<init_value>", "<more_array_lit>"]),
    18: ("<more_array_lit>", [",", "<init_value>", "<more_array_lit>"]),
    19: ("<more_array_lit>", ["λ"]),
    20: ("<data_type>", ["dear"]),
    21: ("<data_type>", ["dearest"]),
    22: ("<data_type>", ["rant"]),
    23: ("<data_type>", ["status"]),
    24: ("<parameter>", ["<function_parameter>", "<multi_parameter>"]),
    25: ("<parameter>", ["λ"]),
    26: ("<function_parameter>", ["<data_type>", "id", "<param_array_decl>"]),
    27: ("<multi_parameter>", [",", "<function_parameter>", "<multi_parameter>"]),
    28: ("<multi_parameter>", ["λ"]),
    29: ("<body_func>", ["<local_decl_list>", "<statements>"]),
    30: ("<local_decl_list>", ["<local_decl>", "<local_decl_list>"]),
    31: ("<local_decl_list>", ["λ"]),
    32: ("<local_decl>", ["<data_type>", "id", "<decl_tail>"]),
    33: ("<statements>", ["id", "<id_suffix>", "<statements>"]),
    34: ("<statements>", ["<input_state>", "<statements>"]),
    35: ("<statements>", ["<output_state>", "<statements>"]),
    36: ("<statements>", ["<conditional_state>", "<statements>"]),
    37: ("<statements>", ["<loop_state>", "<statements>"]),
    38: ("<statements>", ["<comeback_state>", "<statements>"]),
    39: ("<statements>", ["<choose_state>", "<statements>"]),
    40: ("<statements>", ["<unary_state>", "<statements>"]),
    41: ("<statements>", ["λ"]),
    #500: ("<statements>", ["<local_decl>", "<statements>"]), for declaration after ng statements
    42: ("<id_suffix>", ["[", "<expr>", "]", "<id_suffix>"]),

    # Keep these lines exactly as they are:
    43: ("<id_suffix>", ["<assign_ops>", "<assign_values>", ";"]),
    44: ("<id_suffix>", ["(", "<arguments>", ")", ";"]),
    45: ("<id_suffix>", ["<unary_ops>", ";"]),
    46: ("<unary_state>", ["<unary_ops>", "id", ";"]),
    47: ("<unary_ops>", ["++"]),
    48: ("<unary_ops>", ["--"]),
    49: ("<arguments>", ["<paren_expr>", "<more_arguments>"]),
    50: ("<arguments>", ["λ"]),
    51: ("<more_arguments>", [",", "<paren_expr>", "<more_arguments>"]),
    52: ("<more_arguments>", ["λ"]),
    53: ("<assign_ops>", ["="]),
    54: ("<assign_ops>", ["+="]),
    55: ("<assign_ops>", ["-="]),
    56: ("<assign_ops>", ["*="]),
    57: ("<assign_ops>", ["/="]),
    58: ("<assign_ops>", ["%="]),
    59: ("<assign_values>", ["<expr_ar>"]),
    60: ("<input_state>", ["give", ">>", "id", "<input_tail>", "<more_input_ids>", ";"]),
    61: ("<input_state>", ["overshare", "(", "id", ")", ";"]),
    62: ("<output_state>", ["express", "<<", "<output_values>", "<more_output_tail>", ";"]),
    63: ("<more_output_tail>", ["<<", "<output_values>", "<more_output_tail>"]),
    64: ("<more_output_tail>", ["λ"]),
    65: ("<output_values>", ["<expr>"]),
    66: ("<output_values>", ["periodt"]),
    67: ("<comeback_state>", ["comeback", "<expr_opt>", ";"]),
    68: ("<expr>", ["<log_expr>"]),
    69: ("<expr_opt>", ["<expr>"]),
    70: ("<expr_opt>", ["λ"]),
    71: ("<expr_ar>", ["<term>", "<expr_next>"]),
    72: ("<expr_next>", ["+", "<term>", "<expr_next>"]),
    73: ("<expr_next>", ["-", "<term>", "<expr_next>"]),
    74: ("<expr_next>", ["λ"]),
    75: ("<term>", ["<factor>", "<term_next>"]),
    76: ("<term_next>", ["*", "<factor>", "<term_next>"]),
    77: ("<term_next>", ["/", "<factor>", "<term_next>"]),
    78: ("<term_next>", ["%", "<factor>", "<term_next>"]),
    79: ("<term_next>", ["λ"]),
    80: ("<factor>", ["(", "<paren_expr>", ")"]),
    81: ("<factor>", ["id", "<factor_tail>"]),
    82: ("<factor>", ["dear_lit"]),
    83: ("<factor>", ["dearest_lit"]),
    84: ("<factor>", ["rant_lit"]),
    85: ("<factor>", ["<status_lit>"]),
    86: ("<status_lit>", ["greenflag"]),
    87: ("<status_lit>", ["redflag"]),
    88: ("<factor>", ["-", "<factor>"]),
    299: ("<factor>", ["+", "<factor>"]),
    89: ("<rel_expr>", ["<expr_ar>", "<rel_next>"]),
    90: ("<rel_next>", ["<rel_op>", "<expr_ar>", "<rel_next>"]),
    91: ("<rel_next>", ["λ"]),
    92: ("<rel_op>", ["=="]),
    93: ("<rel_op>", ["!="]),
    94: ("<rel_op>", ["<"]),
    95: ("<rel_op>", ["<="]),
    96: ("<rel_op>", [">"]),
    97: ("<rel_op>", [">="]),
    98: ("<log_expr>", ["<and_expr>", "<log_next>"]),
    99: ("<log_next>", ["||", "<and_expr>", "<log_next>"]),
    100: ("<log_next>", ["λ"]),
    101: ("<and_expr>", ["<rel_expr>", "<and_next>"]),
    102: ("<and_next>", ["&&", "<rel_expr>", "<and_next>"]),
    103: ("<and_next>", ["λ"]),
    104: ("<conditional_state>", ["forever", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>", "<more_opt>"]),
    105: ("<forevermore_lst>", ["forevermore", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>"]),
    106: ("<forevermore_lst>", ["λ"]),
    107: ("<more_opt>", ["more", "{", "<body_func>", "}"]),
    108: ("<more_opt>", ["λ"]),
    109: ("<loop_state>", ["<pursue_stmt>"]),
    110: ("<loop_state>", ["<while_stmt>"]),
    111: ("<loop_state>", ["<for_stmt>"]),
    112: ("<pursue_stmt>", ["pursue", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    113: ("<while_stmt>", ["while", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    114: ("<for_stmt>", ["for", "(", "<for_init>", ";", "<expr>", ";", "<for_ud>", ")", "{", "<body_func>", "}"]),
    115: ("<for_init>", ["<data_type>", "id", "=", "<expr_ar>"]),
    116: ("<for_init>", ["id", "=", "<expr_ar>"]),
    117: ("<for_ud>", ["id", "<assign_ops>", "<expr>"]),
    118: ("<for_ud>", ["id", "<unary_ops>"]),
    119: ("<for_ud>", ["<unary_ops>", "id"]),
    120: ("<choose_state>", ["choose", "(", "<expr>", ")", "{", "<phase_lst>", "<bareminimum_opt>", "}"]),
    121: ("<phase_lst>", ["phase", "<choose_const>", ":", "<body_func>", "breakup", ";", "<phase_lst_next>"]),
    122: ("<phase_lst_next>", ["<phase_lst>"]),
    123: ("<phase_lst_next>", ["λ"]),
    124: ("<choose_const>", ["dear_lit"]),
    125: ("<choose_const>", ["rant_lit"]),
    126: ("<bareminimum_opt>", ["bareminimum", ":", "<body_func>", "breakup", ";"]),
    127: ("<bareminimum_opt>", ["λ"]),
    131: ("<array_decl>", ["[", "<array_size>", "]", "<array_decl>"]),
    132: ("<array_decl>", ["λ"]),  # (If not already there as the terminator)
    135: ("<more_input_ids>", [">>", "id", "<input_tail>", "<more_input_ids>"]),
    136: ("<more_input_ids>", ["λ"]),
    # =======================================================================
    # PARENTHESIS-ONLY EXPRESSION HIERARCHY
    # These rules mirror the main expression logic but are strictly for use
    # inside ( ) so that "; " is never valid lookahead.
    # =======================================================================
    200: ("<paren_expr>", ["<paren_log_expr>"]),
    201: ("<paren_log_expr>", ["<paren_and_expr>", "<paren_log_next>"]),
    202: ("<paren_log_next>", ["||", "<paren_and_expr>", "<paren_log_next>"]),
    203: ("<paren_log_next>", ["λ"]),
    204: ("<paren_and_expr>", ["<paren_rel_expr>", "<paren_and_next>"]),
    205: ("<paren_and_next>", ["&&", "<paren_rel_expr>", "<paren_and_next>"]),
    206: ("<paren_and_next>", ["λ"]),
    207: ("<paren_rel_expr>", ["<paren_expr_ar>", "<paren_rel_next>"]),
    208: ("<paren_rel_next>", ["<rel_op>", "<paren_expr_ar>", "<paren_rel_next>"]),
    209: ("<paren_rel_next>", ["λ"]),
    210: ("<paren_expr_ar>", ["<paren_term>", "<paren_expr_next>"]),
    211: ("<paren_expr_next>", ["+", "<paren_term>", "<paren_expr_next>"]),
    212: ("<paren_expr_next>", ["-", "<paren_term>", "<paren_expr_next>"]),
    213: ("<paren_expr_next>", ["λ"]),
    214: ("<paren_term>", ["<factor>", "<paren_term_next>"]),
    215: ("<paren_term_next>", ["*", "<factor>", "<paren_term_next>"]),
    216: ("<paren_term_next>", ["/", "<factor>", "<paren_term_next>"]),
    217: ("<paren_term_next>", ["%", "<factor>", "<paren_term_next>"]),
    218: ("<paren_term_next>", ["λ"]),
    300: ("<boundaries_decls_opt>", ["<top_decl>", "<boundaries_decls_opt>"]),
    301: ("<boundaries_decls_opt>", ["λ"]),
    320: ("<factor_tail>", ["[", "<expr>", "]", "<factor_tail>"]),

     # 2. Function Call: ( args )
    321: ("<factor_tail>", ["(", "<arguments>", ")"]),

    # 3. Post-Increment / Decrement
    322: ("<factor_tail>", ["++"]),
    323: ("<factor_tail>", ["--"]),

    # 4. Empty (It was just a plain variable)
    324: ("<factor_tail>", ["λ"]),
    330: ("<param_array_decl>", ["[", "]", "<param_array_decl>"]),
    331: ("<param_array_decl>", ["λ"]),
    325: ("<factor_tail>", ["::", "id", "<factor_tail>"]),
    340: ("<id_suffix>", ["::", "id", "<id_suffix>"]),
    350: ("<input_tail>", ["[", "<expr>", "]", "<input_tail>"]), 
    351: ("<input_tail>", ["λ"]),
    133: ("<array_size>", ["dear_lit"]), # Allows numbers like [5]
    134: ("<array_size>", ["λ"]),        # Allows empty like []
    360: ("<factor>", ["++", "id"]), 
    361: ("<factor>", ["--", "id"]),
    362: ("<statements>", ["<break_state>", "<statements>"]),
    364: ("<break_state>", ["breakup", ";"]),
    355: ("<scalar_assign>", ["=", "<expr_ar>"]),
    366: ("<scalar_assign>", ["λ"]),  # Allow empty: dear x;
    367: ("<array_assign>", ["=", "{", "<array_lit_list>", "}"]),
    368: ("<array_assign>", ["λ"]),  # Allow empty: dear x[];
    370: ("<top_after_id>", ["<scalar_assign>", "<multi_decl>", ";"]),
    371: ("<decl_tail>", ["[", "<array_size>", "]", "<array_assign>", "<multi_decl>", ";"]),
    372: ("<decl_tail>", ["<scalar_assign>", "<multi_decl>", ";"]),
    367: ("<array_assign>", ["=", "<array_source>"]),
    380: ("<array_source>", ["{", "<array_lit_list>", "}"]),
381: ("<array_source>", ["id"]),

# Defines SIMPLE VALUES (The "Whitelist")
# Used to ban "1+1" inside arrays, allowing only raw data.
450: ("<simple_val>", ["dear_lit"]),    
451: ("<simple_val>", ["dearest_lit"]), 
452: ("<simple_val>", ["rant_lit"]),    
453: ("<simple_val>", ["greenflag"]),   
454: ("<simple_val>", ["redflag"]),     
455: ("<simple_val>", ["id"]),          
456: ("<simple_val>", ["-", "dear_lit"]),       # Allow negative ints
457: ("<simple_val>", ["-", "dearest_lit"]),    # Allow negative floats
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
