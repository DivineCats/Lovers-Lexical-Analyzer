# CFG Production Table for Lovers Language
# Single source of truth: all productions in one map.
# Used by parsetv2.py for reference; LL(1) parsing table is built from this grammar.
#
# Format: PRODUCTION_LIST[num] = (lhs, rhs)  where rhs is list of symbols.
# λ (epsilon) is represented as ["λ"].

from typing import Dict, List, Tuple

# Production number -> (lhs, rhs). rhs is list of symbols; ["λ"] = epsilon.
# NOTE: Top-level structure is:
#   optional boundaries block
#   zero or more top-level declarations (globals or sub-functions)
#   mandatory main function: love () { body }
PRODUCTION_LIST: Dict[int, Tuple[str, List[str]]] = {
    1: ("<program>", ["<boundaries_opt>", "<top_decls_opt>", "love", "(", ")", "{", "<body_func>", "}"]),
    2: ("<boundaries_opt>", ["boundaries", "id", "{", "<top_decls_opt>", "}"]),
    3: ("<boundaries_opt>", ["λ"]),
    # Legacy nonterminals (<global_declaration>, <sub_func>) are no longer used
    # from <program>. They are kept for reference but not part of the LL(1) path.
    4: ("<global_declaration>", ["<declaration>", "<global_declaration>"]),
    5: ("<global_declaration>", ["λ"]),
    6: ("<sub_func>", ["<return_type>", "id", "(", "<parameter>", ")", "{", "<body_func>", "}", "<sub_func>"]),
    7: ("<sub_func>", ["avoidant", "id", "(", "<parameter>", ")", "{", "<body_func>", "}", "<sub_func>"]),
    8: ("<sub_func>", ["λ"]),
    9: ("<declaration>", ["<data_type>", "id", "<array_decl>", "<var_initial>", "<multi_decl>", ";"]),
    10: ("<declaration>", ["<data_type>", "id", ";"]),
    11: ("<declaration>", ["<const_decl>", "<data_type>", "id", "=", "<expr>", ";"]),
    12: ("<multi_decl>", [",", "id", "<array_decl>", "<var_initial>", "<multi_decl>"]),
    13: ("<multi_decl>", ["λ"]),
    14: ("<const_decl>", ["const"]),
    15: ("<const_decl>", ["λ"]),
    16: ("<var_initial>", ["=", "<expr>"]),
    17: ("<var_initial>", ["=", "<init_value>"]),
    18: ("<var_initial>", ["λ"]),
    19: ("<init_value>", ["<expr>"]),
    20: ("<init_value>", ["{", "<array_lit_list>", "}"]),
    21: ("<array_lit_list>", ["<init_value>", "<more_array_lit>"]),
    22: ("<more_array_lit>", [",", "<init_value>", "<more_array_lit>"]),
    23: ("<more_array_lit>", ["λ"]),
    24: ("<data_type>", ["dear"]),
    25: ("<data_type>", ["dearest"]),
    26: ("<data_type>", ["rant"]),
    27: ("<data_type>", ["status"]),
    28: ("<return_type>", ["<data_type>"]),
    29: ("<parameter>", ["<function_parameter>", "<multi_parameter>"]),
    30: ("<parameter>", ["λ"]),
    31: ("<function_parameter>", ["<data_type>", "id", "<array_decl>"]),
    32: ("<multi_parameter>", [",", "<function_parameter>", "<multi_parameter>"]),
    33: ("<multi_parameter>", ["λ"]),
    34: ("<body_func>", ["<local_decl_list>", "<statements>"]),
    35: ("<local_decl_list>", ["<local_decl>", "<local_decl_list>"]),
    36: ("<local_decl_list>", ["λ"]),
    37: ("<local_decl>", ["<data_type>", "id", "<array_decl>", "<var_initial>", "<multi_decl>", ";"]),
    38: ("<statements>", ["id", "<id_suffix>", "<statements>"]),
    39: ("<statements>", ["<input_state>", "<statements>"]),
    40: ("<statements>", ["<output_state>", "<statements>"]),
    41: ("<statements>", ["<conditional_state>", "<statements>"]),
    42: ("<statements>", ["<loop_state>", "<statements>"]),
    43: ("<statements>", ["<comeback_state>", "<statements>"]),
    44: ("<statements>", ["<choose_state>", "<statements>"]),
    45: ("<statements>", ["<unary_state>", "<statements>"]),
    46: ("<statements>", ["λ"]),
    47: ("<id_suffix>", ["<index_array>", "<assign_ops>", "<assign_values>", ";"]),
    48: ("<id_suffix>", ["<assign_ops>", "<assign_values>", ";"]),
    49: ("<id_suffix>", ["(", "<arguments>", ")", ";"]),
    50: ("<id_suffix>", ["<unary_ops>", ";"]),
    51: ("<unary_state>", ["<unary_ops>", "id", ";"]),
    52: ("<unary_ops>", ["++"]),
    53: ("<unary_ops>", ["--"]),
    54: ("<arguments>", ["<expr>", "<more_arguments>"]),
    55: ("<arguments>", ["λ"]),
    56: ("<more_arguments>", [",", "<expr>", "<more_arguments>"]),
    57: ("<more_arguments>", ["λ"]),
    58: ("<assign_ops>", ["="]),
    59: ("<assign_ops>", ["+="]),
    60: ("<assign_ops>", ["-="]),
    61: ("<assign_ops>", ["*="]),
    62: ("<assign_ops>", ["/="]),
    63: ("<assign_ops>", ["%="]),
    64: ("<assign_values>", ["<expr>"]),
    # Input: support one or more identifiers in a single 'give' statement:
    #   give >> x;
    #   give >> x >> y >> z;
    65: ("<input_state>", ["give", ">>", "id", "<more_input_ids>", ";"]),
    66: ("<input_state>", ["overshare", "(", "id", ")", ";"]),
    67: ("<output_state>", ["express", "<more_output>", ";"]),
    68: ("<more_output>", ["<<", "<output_values>", "<more_output>"]),
    69: ("<more_output>", ["λ"]),
    70: ("<output_values>", ["<expr>"]),
    71: ("<output_values>", ["periodt"]),
    73: ("<comeback_state>", ["comeback", "<expr_opt>", ";"]),
    74: ("<expr>", ["<log_expr>"]),
    75: ("<expr_opt>", ["<expr>"]),
    76: ("<expr_opt>", ["λ"]),
    77: ("<expr_ar>", ["<term>", "<expr_next>"]),
    78: ("<expr_next>", ["+", "<term>", "<expr_next>"]),
    79: ("<expr_next>", ["-", "<term>", "<expr_next>"]),
    80: ("<expr_next>", ["λ"]),
    81: ("<term>", ["<factor>", "<term_next>"]),
    82: ("<term_next>", ["*", "<factor>", "<term_next>"]),
    83: ("<term_next>", ["/", "<factor>", "<term_next>"]),
    84: ("<term_next>", ["%", "<factor>", "<term_next>"]),
    85: ("<term_next>", ["λ"]),
    86: ("<factor>", ["(", "<expr>", ")"]),
    # Factor can be an identifier, optionally followed by a function-call suffix.
    # This makes the grammar LL(1)-friendly by ensuring there is only ONE
    # production for `<factor>` that starts with `id`.
    87: ("<factor>", ["id", "<call_opt>"]),
    88: ("<factor>", ["dear_lit"]),
    89: ("<factor>", ["dearest_lit"]),
    90: ("<factor>", ["rant_lit"]),
    91: ("<factor>", ["<status_lit>"]),
    92: ("<status_lit>", ["greenflag"]),
    93: ("<status_lit>", ["redflag"]),
    # Optional function-call suffix for factors that start with `id`.
    # Handles: `id`, `id(args)`, and `id::id(args)`.
    94: ("<call_opt>", ["<boundaries_suffix>", "(", "<arguments>", ")"]),
    95: ("<rel_expr>", ["<expr_ar>", "<rel_next>"]),
    96: ("<rel_next>", ["<rel_op>", "<expr_ar>", "<rel_next>"]),
    97: ("<rel_next>", ["λ"]),
    98: ("<rel_op>", ["=="]),
    99: ("<rel_op>", ["!="]),
    100: ("<rel_op>", ["<"]),
    101: ("<rel_op>", ["<="]),
    102: ("<rel_op>", [">"]),
    103: ("<rel_op>", [">="]),
    104: ("<log_expr>", ["<and_expr>", "<log_next>"]),
    105: ("<log_next>", ["||", "<and_expr>", "<log_next>"]),
    106: ("<log_next>", ["λ"]),
    107: ("<and_expr>", ["<rel_expr>", "<and_next>"]),
    108: ("<and_next>", ["&&", "<rel_expr>", "<and_next>"]),
    109: ("<and_next>", ["λ"]),
    110: ("<conditional_state>", ["forever", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>", "<more_opt>"]),
    111: ("<forevermore_lst>", ["forevermore", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>"]),
    112: ("<forevermore_lst>", ["λ"]),
    113: ("<more_opt>", ["more", "{", "<body_func>", "}"]),
    114: ("<more_opt>", ["λ"]),
    115: ("<loop_state>", ["<pursue_stmt>"]),
    116: ("<loop_state>", ["<while_stmt>"]),
    117: ("<loop_state>", ["<for_stmt>"]),
    118: ("<pursue_stmt>", ["pursue", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    119: ("<while_stmt>", ["while", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    120: ("<for_stmt>", ["for", "(", "<for_init>", ";", "<expr>", ";", "<for_ud>", ")", "{", "<body_func>", "}"]),
    121: ("<for_init>", ["<data_type>", "id", "=", "<expr>"]),
    122: ("<for_init>", ["id", "=", "<expr>"]),
    123: ("<for_ud>", ["id", "<assign_ops>", "<expr>"]),
    124: ("<for_ud>", ["id", "<unary_ops>"]),
    125: ("<for_ud>", ["<unary_ops>", "id"]),
    126: ("<choose_state>", ["choose", "(", "<expr>", ")", "{", "<phase_lst>", "<bareminimum_opt>", "}"]),
    127: ("<phase_lst>", ["phase", "<choose_const>", ":", "<body_func>", "breakup", ";", "<phase_lst_next>"]),
    128: ("<phase_lst_next>", ["<phase_lst>"]),
    129: ("<phase_lst_next>", ["λ"]),
    130: ("<choose_const>", ["num_lit"]),
    131: ("<choose_const>", ["string_lit"]),
    132: ("<bareminimum_opt>", ["bareminimum", ":", "<body_func>", "breakup", ";"]),
    133: ("<bareminimum_opt>", ["λ"]),
    134: ("<call_opt>", ["λ"]),
    135: ("<boundaries_suffix>", ["::", "id"]),
    136: ("<boundaries_suffix>", ["λ"]),
    137: ("<array_decl>", ["[", "]", "<array_decl>"]),
    138: ("<array_decl>", ["λ"]),
    139: ("<index_array>", ["[", "<expr_ar>", "]", "<index_array>"]),
    140: ("<index_array>", ["λ"]),
    # Top-level declaration list (globals + sub-functions) before love()
    141: ("<top_decls_opt>", ["<top_decl>", "<top_decls_opt>"]),
    142: ("<top_decls_opt>", ["λ"]),
    # A single top-level declaration:
    #   - typed function:    <data_type> id "(" parameter ")" "{" body_func "}"
    #   - global variable:   <data_type> id <array_decl> <var_initial> <multi_decl> ";"
    #   - const global var:  const <data_type> id "=" <expr> ";"
    #   - void function:     avoidant id "(" parameter ")" "{" body_func "}"
    143: ("<top_decl>", ["<data_type>", "id", "<top_after_id>"]),
    144: ("<top_decl>", ["const", "<data_type>", "id", "=", "<expr>", ";"]),
    145: ("<top_decl>", ["avoidant", "id", "(", "<parameter>", ")", "{", "<body_func>", "}"]),
    146: ("<top_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]),
    147: ("<top_after_id>", ["<array_decl>", "<var_initial>", "<multi_decl>", ";"]),
    # Additional identifiers for 'give' input: >> id >> id >> ...
    148: ("<more_input_ids>", [">>", "id", "<more_input_ids>"]),
    149: ("<more_input_ids>", ["λ"]),
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
