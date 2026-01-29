# CFG Production Table for Lovers Language
# Single source of truth: all productions in one map.
# Used by parsetv2.py for reference; LL(1) parsing table is built from this grammar.
#
# Format: PRODUCTION_LIST[num] = (lhs, rhs)  where rhs is list of symbols.
# λ (epsilon) is represented as ["λ"].

from typing import Dict, List, Tuple

# Production number -> (lhs, rhs). rhs is list of symbols; ["λ"] = epsilon.
# NOTE: Top-level structure is:
#   zero or more top-level items (globals, functions, or boundaries blocks) in any order
#   mandatory main function: love () { body }
#   Productions 1-137; no legacy/unused nonterminals.
PRODUCTION_LIST: Dict[int, Tuple[str, List[str]]] = {
    1: ("<program>", ["<top_decls_opt>", "love", "(", ")", "{", "<body_func>", "}"]),
     # Top-level list: each item is a global, function, or boundaries block (any order)
    2: ("<top_decls_opt>", ["<top_decl>", "<top_decls_opt>"]),
    3: ("<top_decls_opt>", ["λ"]),
    4: ("<top_decl>", ["<data_type>", "id", "<top_after_id>"]),
    5: ("<top_decl>", ["const", "<data_type>", "id", "=", "<expr>", ";"]),
    6: ("<top_decl>", ["avoidant", "id", "(", "<parameter>", ")", "{", "<body_func>", "}"]),
    7: ("<top_decl>", ["boundaries", "id", "{", "<top_decls_opt>", "}"]),
    8: ("<top_after_id>", ["(", "<parameter>", ")", "{", "<body_func>", "}"]),
    9: ("<top_after_id>", ["<array_decl>", "<var_initial>", "<multi_decl>", ";"]),
    10: ("<multi_decl>", [",", "id", "<array_decl>", "<var_initial>", "<multi_decl>"]),
    11: ("<multi_decl>", ["λ"]),
    12: ("<var_initial>", ["=", "<expr>"]),
    13: ("<var_initial>", ["=", "<init_value>"]),
    14: ("<var_initial>", ["λ"]),
    15: ("<init_value>", ["<expr>"]),
    16: ("<init_value>", ["{", "<array_lit_list>", "}"]),
    17: ("<array_lit_list>", ["<init_value>", "<more_array_lit>"]),
    18: ("<more_array_lit>", [",", "<init_value>", "<more_array_lit>"]),
    19: ("<more_array_lit>", ["λ"]),
    20: ("<data_type>", ["dear"]),
    21: ("<data_type>", ["dearest"]),
    22: ("<data_type>", ["rant"]),
    23: ("<data_type>", ["status"]),
    24: ("<return_type>", ["<data_type>"]),
    25: ("<parameter>", ["<function_parameter>", "<multi_parameter>"]),
    26: ("<parameter>", ["λ"]),
    27: ("<function_parameter>", ["<data_type>", "id", "<array_decl>"]),
    28: ("<multi_parameter>", [",", "<function_parameter>", "<multi_parameter>"]),
    29: ("<multi_parameter>", ["λ"]),
    30: ("<body_func>", ["<local_decl_list>", "<statements>"]),
    31: ("<local_decl_list>", ["<local_decl>", "<local_decl_list>"]),
    32: ("<local_decl_list>", ["λ"]),
    33: ("<local_decl>", ["<data_type>", "id", "<array_decl>", "<var_initial>", "<multi_decl>", ";"]),
    34: ("<statements>", ["id", "<id_suffix>", "<statements>"]),
    35: ("<statements>", ["<input_state>", "<statements>"]),
    36: ("<statements>", ["<output_state>", "<statements>"]),
    37: ("<statements>", ["<conditional_state>", "<statements>"]),
    38: ("<statements>", ["<loop_state>", "<statements>"]),
    39: ("<statements>", ["<comeback_state>", "<statements>"]),
    40: ("<statements>", ["<choose_state>", "<statements>"]),
    41: ("<statements>", ["<unary_state>", "<statements>"]),
    42: ("<statements>", ["λ"]),
    43: ("<id_suffix>", ["<index_array>", "<assign_ops>", "<assign_values>", ";"]),
    44: ("<id_suffix>", ["<assign_ops>", "<assign_values>", ";"]),
    45: ("<id_suffix>", ["(", "<arguments>", ")", ";"]),
    46: ("<id_suffix>", ["<unary_ops>", ";"]),
    47: ("<unary_state>", ["<unary_ops>", "id", ";"]),
    48: ("<unary_ops>", ["++"]),
    49: ("<unary_ops>", ["--"]),
    50: ("<arguments>", ["<expr>", "<more_arguments>"]),
    51: ("<arguments>", ["λ"]),
    52: ("<more_arguments>", [",", "<expr>", "<more_arguments>"]),
    53: ("<more_arguments>", ["λ"]),
    54: ("<assign_ops>", ["="]),
    55: ("<assign_ops>", ["+="]),
    56: ("<assign_ops>", ["-="]),
    57: ("<assign_ops>", ["*="]),
    58: ("<assign_ops>", ["/="]),
    59: ("<assign_ops>", ["%="]),
    60: ("<assign_values>", ["<expr>"]),
    # Input: support one or more identifiers in a single 'give' statement:
    #   give >> x;
    #   give >> x >> y >> z;
    61: ("<input_state>", ["give", ">>", "id", "<more_input_ids>", ";"]),
    62: ("<input_state>", ["overshare", "(", "id", ")", ";"]),
    # Output: require at least one '<< value' before ';'
    #   express << <output_values> << <output_values> ... ;
    63: ("<output_state>", ["express", "<<", "<output_values>", "<more_output_tail>", ";"]),
    64: ("<more_output_tail>", ["<<", "<output_values>", "<more_output_tail>"]),
    65: ("<more_output_tail>", ["λ"]),
    66: ("<output_values>", ["<expr>"]),
    67: ("<output_values>", ["periodt"]),
    68: ("<comeback_state>", ["comeback", "<expr_opt>", ";"]),
    69: ("<expr>", ["<log_expr>"]),
    70: ("<expr_opt>", ["<expr>"]),
    71: ("<expr_opt>", ["λ"]),
    72: ("<expr_ar>", ["<term>", "<expr_next>"]),
    73: ("<expr_next>", ["+", "<term>", "<expr_next>"]),
    74: ("<expr_next>", ["-", "<term>", "<expr_next>"]),
    75: ("<expr_next>", ["λ"]),
    76: ("<term>", ["<factor>", "<term_next>"]),
    77: ("<term_next>", ["*", "<factor>", "<term_next>"]),
    78: ("<term_next>", ["/", "<factor>", "<term_next>"]),
    79: ("<term_next>", ["%", "<factor>", "<term_next>"]),
    80: ("<term_next>", ["λ"]),
    81: ("<factor>", ["(", "<expr>", ")"]),
    # Factor can be an identifier, optionally followed by a function-call suffix.
    # This makes the grammar LL(1)-friendly by ensuring there is only ONE
    # production for `<factor>` that starts with `id`.
    82: ("<factor>", ["id", "<call_opt>"]),
    83: ("<factor>", ["dear_lit"]),
    84: ("<factor>", ["dearest_lit"]),
    85: ("<factor>", ["rant_lit"]),
    86: ("<factor>", ["<status_lit>"]),
    87: ("<status_lit>", ["greenflag"]),
    88: ("<status_lit>", ["redflag"]),
    # Optional function-call suffix for factors that start with `id`.
    # Handles: `id`, `id(args)`, and `id::id(args)`.
    89: ("<call_opt>", ["<boundaries_suffix>", "(", "<arguments>", ")"]),
    90: ("<rel_expr>", ["<expr_ar>", "<rel_next>"]),
    91: ("<rel_next>", ["<rel_op>", "<expr_ar>", "<rel_next>"]),
    92: ("<rel_next>", ["λ"]),
    93: ("<rel_op>", ["=="]),
    94: ("<rel_op>", ["!="]),
    95: ("<rel_op>", ["<"]),
    96: ("<rel_op>", ["<="]),
    97: ("<rel_op>", [">"]),
    98: ("<rel_op>", [">="]),
    99: ("<log_expr>", ["<and_expr>", "<log_next>"]),
    100: ("<log_next>", ["||", "<and_expr>", "<log_next>"]),
    101: ("<log_next>", ["λ"]),
    102: ("<and_expr>", ["<rel_expr>", "<and_next>"]),
    103: ("<and_next>", ["&&", "<rel_expr>", "<and_next>"]),
    104: ("<and_next>", ["λ"]),
    105: ("<conditional_state>", ["forever", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>", "<more_opt>"]),
    106: ("<forevermore_lst>", ["forevermore", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>"]),
    107: ("<forevermore_lst>", ["λ"]),
    108: ("<more_opt>", ["more", "{", "<body_func>", "}"]),
    109: ("<more_opt>", ["λ"]),
    110: ("<loop_state>", ["<pursue_stmt>"]),
    111: ("<loop_state>", ["<while_stmt>"]),
    112: ("<loop_state>", ["<for_stmt>"]),
    113: ("<pursue_stmt>", ["pursue", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    114: ("<while_stmt>", ["while", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    115: ("<for_stmt>", ["for", "(", "<for_init>", ";", "<expr>", ";", "<for_ud>", ")", "{", "<body_func>", "}"]),
    116: ("<for_init>", ["<data_type>", "id", "=", "<expr>"]),
    117: ("<for_init>", ["id", "=", "<expr>"]),
    118: ("<for_ud>", ["id", "<assign_ops>", "<expr>"]),
    119: ("<for_ud>", ["id", "<unary_ops>"]),
    120: ("<for_ud>", ["<unary_ops>", "id"]),
    121: ("<choose_state>", ["choose", "(", "<expr>", ")", "{", "<phase_lst>", "<bareminimum_opt>", "}"]),
    122: ("<phase_lst>", ["phase", "<choose_const>", ":", "<body_func>", "breakup", ";", "<phase_lst_next>"]),
    123: ("<phase_lst_next>", ["<phase_lst>"]),
    124: ("<phase_lst_next>", ["λ"]),
    125: ("<choose_const>", ["dear_lit"]),
    126: ("<choose_const>", ["rant_lit"]),
    127: ("<bareminimum_opt>", ["bareminimum", ":", "<body_func>", "breakup", ";"]),
    128: ("<bareminimum_opt>", ["λ"]),
    129: ("<call_opt>", ["λ"]),
    130: ("<boundaries_suffix>", ["::", "id"]),
    131: ("<boundaries_suffix>", ["λ"]),
    132: ("<array_decl>", ["[", "]", "<array_decl>"]),
    133: ("<array_decl>", ["λ"]),
    134: ("<index_array>", ["[", "<expr_ar>", "]", "<index_array>"]),
    135: ("<index_array>", ["λ"]),
   
    # A single top-level declaration:
    #   - typed function:    <data_type> id "(" parameter ")" "{" body_func "}"
    #   - global variable:   <data_type> id <array_decl> <var_initial> <multi_decl> ";"
    #   - const global var:  const <data_type> id "=" <expr> ";"
    #   - void function:     avoidant id "(" parameter ")" "{" body_func "}"
    #   - boundaries block: boundaries id "{" top_decls_opt "}" (any order with above)

    # Additional identifiers for 'give' input: >> id >> id >> ...
    136: ("<more_input_ids>", [">>", "id", "<more_input_ids>"]),
    137: ("<more_input_ids>", ["λ"]),
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
