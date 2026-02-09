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
    
    # Top-Level Declarations
    4: ("<top_decl>", ["boundaries", "id", "{", "<boundaries_decls_opt>", "}"]),
    5: ("<top_decl>", ["<data_type>", "id", "<top_after_id>"]), 
    
    # CONSTANT: Strict Arithmetic Only (No boolean logic allowed)
    6: ("<top_decl>", ["const", "<data_type>", "id", "=", "<expr_ar>", ";"]), 
    
    7: ("<top_decl>", ["avoidant", "id", "(", "<parameter>", ")", "{", "<body_func>", "}"]),
    
    # Global Variable Split (Array vs Scalar)
    8: ("<top_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]), 
    9: ("<top_after_id>", ["[", "<array_size>", "]", "<array_assign>", "<multi_decl>", ";"]), 
    10: ("<top_after_id>", ["<scalar_assign>", "<multi_decl>", ";"]), 

    11: ("<boundaries_decls_opt>", ["<top_decl>", "<boundaries_decls_opt>"]),
    12: ("<boundaries_decls_opt>", ["λ"]),

    # ==========================================
    # 2. FUNCTIONS & LOCAL DECLARATIONS
    # ==========================================
    13: ("<body_func>", ["<local_decl_list>", "<statements>"]),
    14: ("<local_decl_list>", ["<local_decl>", "<local_decl_list>"]),
    15: ("<local_decl_list>", ["λ"]),

    # Local Variable Split
    16: ("<local_decl>", ["<data_type>", "id", "<decl_tail>"]),
    17: ("<decl_tail>", ["[", "<array_size>", "]", "<array_assign>", "<multi_decl>", ";"]), 
    18: ("<decl_tail>", ["<scalar_assign>", "<multi_decl>", ";"]), 

    # Multi-Declaration Support
    19: ("<multi_decl>", [",", "id", "<array_decl>", "<var_initial>", "<multi_decl>"]),
    20: ("<multi_decl>", ["λ"]),

    # ==========================================
    # 3. ASSIGNMENT LOGIC
    # ==========================================
    # SCALAR: Strict Arithmetic Only (No boolean logic allowed)
    21: ("<scalar_assign>", ["=", "<expr_ar>"]),
    22: ("<scalar_assign>", ["λ"]),

    # ARRAY: Strict Source (List or ID)
    23: ("<array_assign>", ["=", "<array_source>"]),
    24: ("<array_assign>", ["λ"]),
    25: ("<array_source>", ["{", "<array_lit_list>", "}"]),
    26: ("<array_source>", ["id"]),

    # ==========================================
    # 4. INITIALIZATION & VALUES
    # ==========================================
    # INIT: Strict Arithmetic Only
    27: ("<var_initial>", ["=", "<expr_ar>"]),       
    28: ("<var_initial>", ["=", "<init_value>"]), 
    29: ("<var_initial>", ["λ"]),

    # ARRAY LIST: Strict Simple Values Only (No Math inside {})
    30: ("<init_value>", ["<simple_val>"]),
    31: ("<init_value>", ["{", "<array_lit_list>", "}"]),
    32: ("<array_lit_list>", ["<init_value>", "<more_array_lit>"]),
    33: ("<more_array_lit>", [",", "<init_value>", "<more_array_lit>"]),
    34: ("<more_array_lit>", ["λ"]),

    # Simple Values Whitelist
    35: ("<simple_val>", ["dear_lit"]),
    36: ("<simple_val>", ["dearest_lit"]),
    37: ("<simple_val>", ["rant_lit"]),
    38: ("<simple_val>", ["greenflag"]),
    39: ("<simple_val>", ["redflag"]),
    40: ("<simple_val>", ["id"]),
    41: ("<simple_val>", ["-", "dear_lit"]),
    42: ("<simple_val>", ["-", "dearest_lit"]),

    # ==========================================
    # 5. DATA TYPES & PARAMETERS
    # ==========================================
    43: ("<data_type>", ["dear"]),
    44: ("<data_type>", ["dearest"]),
    45: ("<data_type>", ["rant"]),
    46: ("<data_type>", ["status"]),

    47: ("<parameter>", ["<function_parameter>", "<multi_parameter>"]),
    48: ("<parameter>", ["λ"]),
    49: ("<function_parameter>", ["<data_type>", "id", "<param_array_decl>"]),
    50: ("<multi_parameter>", [",", "<function_parameter>", "<multi_parameter>"]),
    51: ("<multi_parameter>", ["λ"]),
    52: ("<param_array_decl>", ["[", "]", "<param_array_decl>"]),
    53: ("<param_array_decl>", ["λ"]),
    54: ("<array_decl>", ["[", "<array_size>", "]", "<array_decl>"]),
    55: ("<array_decl>", ["λ"]),
    56: ("<array_size>", ["dear_lit"]),
    57: ("<array_size>", ["λ"]),

    # ==========================================
    # 6. STATEMENTS
    # ==========================================
    58: ("<statements>", ["id", "<id_suffix>", "<statements>"]),
    59: ("<statements>", ["<input_state>", "<statements>"]),
    60: ("<statements>", ["<output_state>", "<statements>"]),
    61: ("<statements>", ["<conditional_state>", "<statements>"]),
    62: ("<statements>", ["<loop_state>", "<statements>"]),
    63: ("<statements>", ["<comeback_state>", "<statements>"]),
    64: ("<statements>", ["<choose_state>", "<statements>"]),
    65: ("<statements>", ["<unary_state>", "<statements>"]),
    66: ("<statements>", ["<break_state>", "<statements>"]),
    67: ("<statements>", ["λ"]),

    # ==========================================
    # 7. ID SUFFIXES & UNARY
    # ==========================================
    68: ("<id_suffix>", ["[", "<expr>", "]", "<id_suffix>"]),  
    69: ("<id_suffix>", ["<assign_ops>", "<assign_values>", ";"]), 
    70: ("<id_suffix>", ["(", "<arguments>", ")", ";"]), 
    71: ("<id_suffix>", ["<unary_ops>", ";"]), 
    72: ("<id_suffix>", ["::", "id", "<id_suffix>"]), 

    73: ("<unary_state>", ["<unary_ops>", "id", ";"]),
    74: ("<unary_ops>", ["++"]),
    75: ("<unary_ops>", ["--"]),

    76: ("<assign_ops>", ["="]),
    77: ("<assign_ops>", ["+="]),
    78: ("<assign_ops>", ["-="]),
    79: ("<assign_ops>", ["*="]),
    80: ("<assign_ops>", ["/="]),
    81: ("<assign_ops>", ["%="]),
    
    # ASSIGNMENT: Strict Arithmetic Only (Prevents x = y == z)
    82: ("<assign_values>", ["<expr_ar>"]),

    83: ("<arguments>", ["<paren_expr>", "<more_arguments>"]),
    84: ("<arguments>", ["λ"]),
    85: ("<more_arguments>", [",", "<paren_expr>", "<more_arguments>"]),
    86: ("<more_arguments>", ["λ"]),

    # ==========================================
    # 8. I/O & CONTROL FLOW
    # ==========================================
    87: ("<input_state>", ["give", ">>", "id", "<input_tail>", "<more_input_ids>", ";"]),
    88: ("<input_state>", ["overshare", "(", "id", ")", ";"]),
    89: ("<input_tail>", ["[", "<expr>", "]", "<input_tail>"]),
    90: ("<input_tail>", ["λ"]),
    91: ("<more_input_ids>", [">>", "id", "<input_tail>", "<more_input_ids>"]),
    92: ("<more_input_ids>", ["λ"]),

    93: ("<output_state>", ["express", "<<", "<output_values>", "<more_output_tail>", ";"]),
    94: ("<more_output_tail>", ["<<", "<output_values>", "<more_output_tail>"]),
    95: ("<more_output_tail>", ["λ"]),
    96: ("<output_values>", ["<expr>"]),
    97: ("<output_values>", ["periodt"]),

    98: ("<comeback_state>", ["comeback", "<expr_opt>", ";"]),
    99: ("<break_state>", ["breakup", ";"]),

    # ==========================================
    # 9. LOOPS & CONDITIONS
    # ==========================================
    100: ("<conditional_state>", ["forever", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>", "<more_opt>"]),
    101: ("<forevermore_lst>", ["forevermore", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>"]),
    102: ("<forevermore_lst>", ["λ"]),
    103: ("<more_opt>", ["more", "{", "<body_func>", "}"]),
    104: ("<more_opt>", ["λ"]),

    105: ("<loop_state>", ["<pursue_stmt>"]),
    106: ("<loop_state>", ["<while_stmt>"]),
    107: ("<loop_state>", ["<for_stmt>"]),

    108: ("<pursue_stmt>", ["pursue", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    109: ("<while_stmt>", ["while", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    110: ("<for_stmt>", ["for", "(", "<for_init>", ";", "<expr>", ";", "<for_ud>", ")", "{", "<body_func>", "}"]),
    
    # FOR INIT: Strict Arithmetic Only
    111: ("<for_init>", ["<data_type>", "id", "=", "<expr_ar>"]),
    112: ("<for_init>", ["id", "=", "<expr_ar>"]),
    
    113: ("<for_ud>", ["id", "<assign_ops>", "<expr>"]),
    114: ("<for_ud>", ["id", "<unary_ops>"]),
    115: ("<for_ud>", ["<unary_ops>", "id"]),

    116: ("<choose_state>", ["choose", "(", "<expr>", ")", "{", "<phase_lst>", "<bareminimum_opt>", "}"]),
    117: ("<phase_lst>", ["phase", "<choose_const>", ":", "<body_func>", "breakup", ";", "<phase_lst_next>"]),
    118: ("<phase_lst_next>", ["<phase_lst>"]),
    119: ("<phase_lst_next>", ["λ"]),
    120: ("<choose_const>", ["dear_lit"]),
    121: ("<choose_const>", ["rant_lit"]),
    122: ("<bareminimum_opt>", ["bareminimum", ":", "<body_func>", "breakup", ";"]),
    123: ("<bareminimum_opt>", ["λ"]),

    # ==========================================
    # 10. EXPRESSIONS (MAIN HIERARCHY)
    # ==========================================
    124: ("<expr>", ["<log_expr>"]),
    125: ("<expr_opt>", ["<expr>"]),
    126: ("<expr_opt>", ["λ"]),

    127: ("<log_expr>", ["<and_expr>", "<log_next>"]),
    128: ("<log_next>", ["||", "<and_expr>", "<log_next>"]),
    129: ("<log_next>", ["λ"]),

    130: ("<and_expr>", ["<rel_expr>", "<and_next>"]),
    131: ("<and_next>", ["&&", "<rel_expr>", "<and_next>"]),
    132: ("<and_next>", ["λ"]),

    133: ("<rel_expr>", ["<expr_ar>", "<rel_next>"]),
    134: ("<rel_next>", ["<rel_op>", "<expr_ar>", "<rel_next>"]),
    135: ("<rel_next>", ["λ"]),
    136: ("<rel_op>", ["=="]),
    137: ("<rel_op>", ["!="]),
    138: ("<rel_op>", ["<"]),
    139: ("<rel_op>", ["<="]),
    140: ("<rel_op>", [">"]),
    141: ("<rel_op>", [">="]),

    142: ("<expr_ar>", ["<term>", "<expr_next>"]),
    143: ("<expr_next>", ["+", "<term>", "<expr_next>"]),
    144: ("<expr_next>", ["-", "<term>", "<expr_next>"]),
    145: ("<expr_next>", ["λ"]),

    146: ("<term>", ["<factor>", "<term_next>"]),
    147: ("<term_next>", ["*", "<factor>", "<term_next>"]),
    148: ("<term_next>", ["/", "<factor>", "<term_next>"]),
    149: ("<term_next>", ["%", "<factor>", "<term_next>"]),
    150: ("<term_next>", ["λ"]),

    # ==========================================
    # 11. FACTORS & TAILS
    # ==========================================
    151: ("<factor>", ["(", "<paren_expr>", ")"]),
    152: ("<factor>", ["id", "<factor_tail>"]),
    153: ("<factor>", ["dear_lit"]),
    154: ("<factor>", ["dearest_lit"]),
    155: ("<factor>", ["rant_lit"]),
    156: ("<factor>", ["<status_lit>"]),
    157: ("<factor>", ["-", "<factor>"]),
    158: ("<factor>", ["+", "<factor>"]),
    159: ("<factor>", ["++", "id"]),
    160: ("<factor>", ["--", "id"]),

    161: ("<status_lit>", ["greenflag"]),
    162: ("<status_lit>", ["redflag"]),

    163: ("<factor_tail>", ["[", "<expr>", "]", "<factor_tail>"]),
    164: ("<factor_tail>", ["(", "<arguments>", ")"]),
    165: ("<factor_tail>", ["++"]),
    166: ("<factor_tail>", ["--"]),
    167: ("<factor_tail>", ["::", "id", "<factor_tail>"]),
    168: ("<factor_tail>", ["λ"]),

    # ==========================================
    # 12. PARENTHESIS-ONLY HIERARCHY
    # ==========================================
    169: ("<paren_expr>", ["<paren_log_expr>"]),
    170: ("<paren_log_expr>", ["<paren_and_expr>", "<paren_log_next>"]),
    171: ("<paren_log_next>", ["||", "<paren_and_expr>", "<paren_log_next>"]),
    172: ("<paren_log_next>", ["λ"]),
    173: ("<paren_and_expr>", ["<paren_rel_expr>", "<paren_and_next>"]),
    174: ("<paren_and_next>", ["&&", "<paren_rel_expr>", "<paren_and_next>"]),
    175: ("<paren_and_next>", ["λ"]),
    176: ("<paren_rel_expr>", ["<paren_expr_ar>", "<paren_rel_next>"]),
    177: ("<paren_rel_next>", ["<rel_op>", "<paren_expr_ar>", "<paren_rel_next>"]),
    178: ("<paren_rel_next>", ["λ"]),
    179: ("<paren_expr_ar>", ["<paren_term>", "<paren_expr_next>"]),
    180: ("<paren_expr_next>", ["+", "<paren_term>", "<paren_expr_next>"]),
    181: ("<paren_expr_next>", ["-", "<paren_term>", "<paren_expr_next>"]),
    182: ("<paren_expr_next>", ["λ"]),
    183: ("<paren_term>", ["<factor>", "<paren_term_next>"]),
    184: ("<paren_term_next>", ["*", "<factor>", "<paren_term_next>"]),
    185: ("<paren_term_next>", ["/", "<factor>", "<paren_term_next>"]),
    186: ("<paren_term_next>", ["%", "<factor>", "<paren_term_next>"]),
    187: ("<paren_term_next>", ["λ"]),
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
