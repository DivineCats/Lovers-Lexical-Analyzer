# CFG Production Table for Lovers Language
# Single source of truth: all productions in one map.
# Used by parsetv2.py for reference; LL(1) parsing table is built from this grammar.
#
# Format: PRODUCTION_LIST is a list of (lhs, rhs) where rhs is list of symbols.
# λ (epsilon) is represented as ["λ"].

from typing import Dict, List, Tuple

# Each item is (lhs, rhs). rhs is list of symbols; ["λ"] = epsilon. First production is start symbol.
# Top-level: <top_decls_opt> then love () { body }. Declarations are STRICT TYPED:
#   dear/dearest/rant/status each have *_tail rules that expect only the matching literal type.

PRODUCTION_LIST: List[Tuple[str, List[str]]] = [
    ("<program>", ["<top_decls_opt>", "love", "(", ")", "{", "<body_func>", "}"]),
    ("<top_decls_opt>", ["<top_decl>", "<top_decls_opt>"]),
    ("<top_decls_opt>", ["λ"]),
    
    # ==========================================
    # 1. TOP-LEVEL DECLARATIONS (STRICT TYPED)
    # ==========================================
    # After "dear id" / "dearest id" etc.: ( parameter ) { body } = function, else _tail = variable
    # All data types: only id after type (no literals as name)
    # status isolated like const: one production for keyword, then dedicated nonterminal
    ("<top_decl>", ["dear", "id", "<dear_after_id>"]),
    ("<top_decl>", ["dearest", "id", "<dearest_after_id>"]),
    ("<top_decl>", ["rant", "id", "<rant_after_id>"]),
    ("<top_decl>", ["status", "<status_top_decl>"]),
    ("<status_top_decl>", ["id", "<status_after_id>"]),
    ("<top_decl>", ["boundaries", "id", "{", "<boundaries_decls_opt>", "}"]),
    ("<top_decl>", ["avoidant", "id", "(", "<parameter>", ")", "{", "<body_func>", "}"]),

    # Return-type functions: type id ( parameter ) { typed_func_body } (must end with comeback)
    ("<dear_after_id>", ["(", "<parameter>", ")", "{", "<typed_func_body>", "}"]),
    ("<dear_after_id>", ["<dear_tail>"]),
    ("<dearest_after_id>", ["(", "<parameter>", ")", "{", "<typed_func_body>", "}"]),
    ("<dearest_after_id>", ["<dearest_tail>"]),
    ("<rant_after_id>", ["(", "<parameter>", ")", "{", "<typed_func_body>", "}"]),
    ("<rant_after_id>", ["<rant_tail>"]),
    ("<status_after_id>", ["(", "<parameter>", ")", "{", "<typed_func_body>", "}"]),
    ("<status_after_id>", ["<status_tail>"]),
    # const <data-type> <identifier> = <value/expression> ; (factored so LL(1) chooses by data-type)
    ("<top_decl>", ["const", "<const_decl>"]),
    ("<const_decl>", ["dear", "id", "=", "<dear_expr>", ";"]),
    ("<const_decl>", ["dearest", "id", "=", "<dearest_expr>", ";"]),
    ("<const_decl>", ["rant", "id", "=", "<rant_expr>", ";"]),
    ("<const_decl>", ["status", "id", "=", "<status_lit>", ";"]),

    # A. DEAR (Integer) - Type-specific init expr: expected (, +, ++, -, --, dear_lit, id
    ("<dear_tail>", ["=", "<dear_expr>", "<dear_multi>", ";"]),
    ("<dear_tail>", ["<dear_multi>", ";"]),
    ("<dear_tail>", ["[", "<dear_array_after_lbracket>"]),
    ("<dear_array_after_lbracket>", ["]", "<dear_array_empty_dims_tail>"]),
    ("<dear_array_empty_dims_tail>", ["[", "]", "<dear_array_empty_dims_tail>"]),
    ("<dear_array_empty_dims_tail>", ["=", "<dear_array_source>", ";"]),
    ("<dear_array_after_lbracket>", ["<dear_expr>", "]", "<dear_array_dim_tail>"]),
    ("<dear_array_dim_tail>", ["[", "<dear_expr>", "]", "<dear_array_dim_tail>"]),
    ("<dear_array_dim_tail>", ["<dear_array_assign>", "<dear_multi>", ";"]),
    ("<dear_multi>", [",", "id", "<dear_init_opt>", "<dear_multi>"]),
    ("<dear_multi>", ["λ"]),
    ("<dear_init_opt>", ["=", "<dear_expr>"]),
    ("<dear_init_opt>", ["λ"]),

    # B. DEAREST (Float) - Uses <dearest_expr> (No %, bitwise). Array size = <dear_expr>
    ("<dearest_tail>", ["=", "<dearest_expr>", "<dearest_multi>", ";"]),
    ("<dearest_tail>", ["<dearest_multi>", ";"]),
    ("<dearest_tail>", ["[", "<dearest_array_after_lbracket>"]),
    ("<dearest_array_after_lbracket>", ["]", "<dearest_array_empty_dims_tail>"]),
    ("<dearest_array_empty_dims_tail>", ["[", "]", "<dearest_array_empty_dims_tail>"]),
    ("<dearest_array_empty_dims_tail>", ["=", "<dearest_array_source>", ";"]),
    ("<dearest_array_after_lbracket>", ["<dear_expr>", "]", "<dearest_array_dim_tail>"]),
    ("<dearest_array_dim_tail>", ["[", "<dear_expr>", "]", "<dearest_array_dim_tail>"]),
    ("<dearest_array_dim_tail>", ["<dearest_array_assign>", "<dearest_multi>", ";"]),
    ("<dearest_multi>", [",", "id", "<dearest_init_opt>", "<dearest_multi>"]),
    ("<dearest_multi>", ["λ"]),
    ("<dearest_init_opt>", ["=", "<dearest_expr>"]),
    ("<dearest_init_opt>", ["λ"]),

   # C. RANT (String) - Uses <rant_expr> (Concat only). Array size = <dear_expr>
    ("<rant_tail>", ["=", "<rant_expr>", "<rant_multi>", ";"]),
    ("<rant_tail>", ["<rant_multi>", ";"]),
    ("<rant_tail>", ["[", "<rant_array_after_lbracket>"]),
    ("<rant_array_after_lbracket>", ["]", "<rant_array_empty_dims_tail>"]),
    ("<rant_array_empty_dims_tail>", ["[", "]", "<rant_array_empty_dims_tail>"]),
    ("<rant_array_empty_dims_tail>", ["=", "<rant_array_source>", ";"]),
    ("<rant_array_after_lbracket>", ["<dear_expr>", "]", "<rant_array_dim_tail>"]),
    ("<rant_array_dim_tail>", ["[", "<dear_expr>", "]", "<rant_array_dim_tail>"]),
    ("<rant_array_dim_tail>", ["<rant_array_assign>", "<rant_multi>", ";"]),
    ("<rant_multi>", [",", "id", "<rant_init_opt>", "<rant_multi>"]),
    ("<rant_multi>", ["λ"]),
    ("<rant_init_opt>", ["=", "<rant_expr>"]),
    ("<rant_init_opt>", ["λ"]),
    ("<rant_init_val>", ["rant_lit"]),
    ("<rant_init_val>", ["id"]),

    # D. STATUS (Boolean) - Uses <status_expr> (Logic + Relational). Array size = <dear_expr>
    ("<status_tail>", ["=", "<status_expr>", "<status_multi>", ";"]),
    ("<status_tail>", ["<status_multi>", ";"]),
    ("<status_tail>", ["[", "<status_array_after_lbracket>"]),
    ("<status_array_after_lbracket>", ["]", "<status_array_empty_dims_tail>"]),
    ("<status_array_empty_dims_tail>", ["[", "]", "<status_array_empty_dims_tail>"]),
    ("<status_array_empty_dims_tail>", ["=", "<status_array_source>", ";"]),
    ("<status_array_after_lbracket>", ["<dear_expr>", "]", "<status_array_dim_tail>"]),
    ("<status_array_dim_tail>", ["[", "<dear_expr>", "]", "<status_array_dim_tail>"]),
    ("<status_array_dim_tail>", ["<status_array_assign>", "<status_multi>", ";"]),
    ("<status_multi>", [",", "id", "<status_init_opt>", "<status_multi>"]),
    ("<status_multi>", ["λ"]),
    ("<status_init_opt>", ["=", "<status_expr>"]),
    ("<status_init_opt>", ["λ"]),
    ("<status_init_expr>", ["<status_lit>"]),
    ("<status_init_expr>", ["id"]),
    ("<status_init_expr>", ["(", "<paren_expr>", ")"]),
    ("<status_init_expr>", ["not", "<status_init_expr>"]),
    ("<status_lit>", ["greenflag"]),
    ("<status_lit>", ["redflag"]),

    # DEAR init expr (restricted factor: dear_lit, id, (, +, -, ++, --)
    ("<dear_init_expr>", ["<dear_init_term>", "<dear_init_expr_next>"]),
    ("<dear_init_expr_next>", ["+", "<dear_init_term>", "<dear_init_expr_next>"]),
    ("<dear_init_expr_next>", ["-", "<dear_init_term>", "<dear_init_expr_next>"]),
    ("<dear_init_expr_next>", ["λ"]),
    ("<dear_init_term>", ["<dear_init_factor>", "<dear_init_term_next>"]),
    ("<dear_init_term_next>", ["*", "<dear_init_factor>", "<dear_init_term_next>"]),
    ("<dear_init_term_next>", ["/", "<dear_init_factor>", "<dear_init_term_next>"]),
    ("<dear_init_term_next>", ["%", "<dear_init_factor>", "<dear_init_term_next>"]),
    ("<dear_init_term_next>", ["λ"]),
    ("<dear_init_factor>", ["(", "<paren_expr>", ")"]),
    ("<dear_init_factor>", ["id", "<factor_tail>"]),
    ("<dear_init_factor>", ["dear_lit"]),
    ("<dear_init_factor>", ["-", "<dear_init_factor>"]),
    ("<dear_init_factor>", ["+", "<dear_init_factor>"]),
    ("<dear_init_factor>", ["++", "id"]),
    ("<dear_init_factor>", ["--", "id"]),

    # DEAREST init expr (restricted factor: dearest_lit, dear_lit, id, (, +, -, ++, --)
    ("<dearest_init_expr>", ["<dearest_init_term>", "<dearest_init_expr_next>"]),
    ("<dearest_init_expr_next>", ["+", "<dearest_init_term>", "<dearest_init_expr_next>"]),
    ("<dearest_init_expr_next>", ["-", "<dearest_init_term>", "<dearest_init_expr_next>"]),
    ("<dearest_init_expr_next>", ["λ"]),
    ("<dearest_init_term>", ["<dearest_init_factor>", "<dearest_init_term_next>"]),
    ("<dearest_init_term_next>", ["*", "<dearest_init_factor>", "<dearest_init_term_next>"]),
    ("<dearest_init_term_next>", ["/", "<dearest_init_factor>", "<dearest_init_term_next>"]),
    ("<dearest_init_term_next>", ["%", "<dearest_init_factor>", "<dearest_init_term_next>"]),
    ("<dearest_init_term_next>", ["λ"]),
    ("<dearest_init_factor>", ["(", "<paren_expr>", ")"]),
    ("<dearest_init_factor>", ["id", "<factor_tail>"]),
    ("<dearest_init_factor>", ["dearest_lit"]),
    ("<dearest_init_factor>", ["dear_lit"]),
    ("<dearest_init_factor>", ["-", "<dearest_init_factor>"]),
    ("<dearest_init_factor>", ["+", "<dearest_init_factor>"]),
    ("<dearest_init_factor>", ["++", "id"]),
    ("<dearest_init_factor>", ["--", "id"]),

    ("<boundaries_decls_opt>", ["<top_decl>", "<boundaries_decls_opt>"]),
    ("<boundaries_decls_opt>", ["λ"]),

    # ==========================================
    # 2. FUNCTIONS & LOCAL DECLARATIONS (STRICT TYPED)
    # ==========================================
    ("<body_func>", ["<local_decl_list>", "<statements>"]),
    ("<phase_body>", ["<local_decl_list>", "<phase_statements>"]),
    ("<typed_func_body>", ["<local_decl_list>", "<statements>"]),
    ("<local_decl_list>", ["<local_decl>", "<local_decl_list>"]),
    ("<local_decl_list>", ["λ"]),
    ("<local_decl>", ["dear", "id", "<dear_tail>"]),
    ("<local_decl>", ["dearest", "id", "<dearest_tail>"]),
    ("<local_decl>", ["rant", "id", "<rant_tail>"]),
    ("<local_decl>", ["status", "<status_local_decl>"]),
    ("<status_local_decl>", ["id", "<status_tail>"]),

    # ==========================================
    # 3. ASSIGNMENT LOGIC
    # ==========================================
    # SCALAR: Used in statements (id = expr ;)
    ("<scalar_assign>", ["=", "<expr_ar>"]),
    ("<scalar_assign>", ["λ"]),

    # ARRAY: Strict Source (List or ID) - generic still used by init_value elsewhere
    ("<array_assign>", ["=", "<array_source>"]),
    ("<array_assign>", ["λ"]),
    ("<array_source>", ["{", "<array_lit_list>", "}"]),
    ("<array_lit_list>", ["λ"]),
    ("<array_source>", ["id"]),

    # TYPE-SPECIFIC ARRAY INITIALIZERS (rant_lit|id, dear_lit|id|-dear_lit, etc.)
    # RANT: rant_lit or id only
    ("<rant_array_source>", ["{", "<rant_array_lit_list>", "}"]),
    ("<rant_array_lit_list>", ["λ"]),

    ("<rant_array_lit_list>", ["<rant_array_elem>", "<more_rant_array_lit>"]),
    ("<rant_array_elem>", ["rant_lit"]),
    ("<rant_array_elem>", ["id", "<factor_tail>"]),
    ("<rant_array_elem>", ["{", "<rant_array_lit_list>", "}"]),
    ("<more_rant_array_lit>", [",", "<rant_array_elem>", "<more_rant_array_lit>"]),
    ("<more_rant_array_lit>", ["λ"]),
    # DEAR: dear_lit, dearest_lit, id, greenflag, redflag, -dear_lit, -dearest_lit (consistent with dear)
    ("<dear_array_source>", ["{", "<dear_array_lit_list>", "}"]),
    ("<dear_array_lit_list>", ["λ"]),
    
    ("<dear_array_lit_list>", ["<dear_array_elem>", "<more_dear_array_lit>"]),
    ("<dear_array_elem>", ["dear_lit"]),
    ("<dear_array_elem>", ["id", "<factor_tail>"]),
    ("<dear_array_elem>", ["-", "<dear_array_neg_lit>"]),
    ("<dear_array_neg_lit>", ["dear_lit"]),
    ("<dear_array_neg_lit>", ["dearest_lit"]),
    ("<dear_array_elem>", ["greenflag"]),
    ("<dear_array_elem>", ["redflag"]),
    ("<dear_array_elem>", ["dearest_lit"]),
    ("<dear_array_elem>", ["{", "<dear_array_lit_list>", "}"]),
    ("<more_dear_array_lit>", [",", "<dear_array_elem>", "<more_dear_array_lit>"]),
    ("<more_dear_array_lit>", ["λ"]),
    # DEAREST: dearest_lit, dear_lit, id, greenflag, redflag, -dearest_lit, -dear_lit (consistent with dearest)
    ("<dearest_array_source>", ["{", "<dearest_array_lit_list>", "}"]),
    ("<dearest_array_lit_list>", ["λ"]),
    
    ("<dearest_array_lit_list>", ["<dearest_array_elem>", "<more_dearest_array_lit>"]),
    ("<dearest_array_elem>", ["dearest_lit"]),
    ("<dearest_array_elem>", ["dear_lit"]),
    ("<dearest_array_elem>", ["id", "<factor_tail>"]),
    ("<dearest_array_elem>", ["-", "<dearest_neg_lit>"]),
    ("<dearest_array_elem>", ["greenflag"]),
    ("<dearest_array_elem>", ["redflag"]),
    ("<dearest_array_elem>", ["{", "<dearest_array_lit_list>", "}"]),
    ("<dearest_neg_lit>", ["dearest_lit"]),
    ("<dearest_neg_lit>", ["dear_lit"]),
    ("<more_dearest_array_lit>", [",", "<dearest_array_elem>", "<more_dearest_array_lit>"]),
    ("<more_dearest_array_lit>", ["λ"]),
    # STATUS: greenflag, redflag, dear_lit, dearest_lit, id (consistent with status)
    ("<status_array_source>", ["{", "<status_array_lit_list>", "}"]),
    ("<status_array_lit_list>", ["λ"]),
    
    ("<status_array_lit_list>", ["<status_array_elem>", "<more_status_array_lit>"]),
    ("<status_array_elem>", ["greenflag"]),
    ("<status_array_elem>", ["redflag"]),
    ("<status_array_elem>", ["id", "<factor_tail>"]),
    ("<status_array_elem>", ["dear_lit"]),
    ("<status_array_elem>", ["dearest_lit"]),
    ("<status_array_elem>", ["{", "<status_array_lit_list>", "}"]),
    ("<more_status_array_lit>", [",", "<status_array_elem>", "<more_status_array_lit>"]),
    ("<more_status_array_lit>", ["λ"]),
    # Type-specific array assign (optional = source)
    ("<dear_array_assign>", ["=", "<dear_array_source>"]),
    ("<dear_array_assign>", ["λ"]),
    ("<dearest_array_assign>", ["=", "<dearest_array_source>"]),
    ("<dearest_array_assign>", ["λ"]),
    ("<rant_array_assign>", ["=", "<rant_array_source>"]),
    ("<rant_array_assign>", ["λ"]),
    ("<status_array_assign>", ["=", "<status_array_source>"]),
    ("<status_array_assign>", ["λ"]),

    # ==========================================
    # 4. INITIALIZATION & VALUES
    # ==========================================
    ("<var_initial>", ["=", "<expr_ar>"]),
    ("<var_initial>", ["=", "<init_value>"]),
    ("<var_initial>", ["λ"]),

    # ARRAY LIST: Strict Simple Values Only (No Math inside {})
    ("<init_value>", ["<simple_val>"]),
    ("<init_value>", ["{", "<array_lit_list>", "}"]),
    ("<array_lit_list>", ["<init_value>", "<more_array_lit>"]),
    ("<more_array_lit>", [",", "<init_value>", "<more_array_lit>"]),
    ("<more_array_lit>", ["λ"]),

    # Simple Values Whitelist (for array literals etc.)
    ("<simple_val>", ["dear_lit"]),
    ("<simple_val>", ["dearest_lit"]),
    ("<simple_val>", ["rant_lit"]),
    ("<simple_val>", ["greenflag"]),
    ("<simple_val>", ["redflag"]),
    ("<simple_val>", ["id"]),
    ("<simple_val>", ["-", "dear_lit"]),
    ("<simple_val>", ["-", "dearest_lit"]),
    ("<simple_val>", ["λ"]),

    # ==========================================
    # 5. DATA TYPES & PARAMETERS
    # ==========================================
    ("<data_type>", ["dear"]),
    ("<data_type>", ["dearest"]),
    ("<data_type>", ["rant"]),
    ("<data_type>", ["status"]),

    ("<parameter>", ["<function_parameter>", "<multi_parameter>"]),
    ("<parameter>", ["λ"]),
    ("<function_parameter>", ["<data_type>", "id", "<param_array_decl>"]),
    ("<multi_parameter>", [",", "<function_parameter>", "<multi_parameter>"]),
    ("<multi_parameter>", ["λ"]),
    ("<param_array_decl>", ["[", "]", "<param_array_decl>"]),
    ("<param_array_decl>", ["λ"]),
    ("<array_decl>", ["[", "<array_size>", "]", "<array_decl>"]),
    ("<array_decl>", ["λ"]),
    ("<array_size>", ["dear_lit"]),
    ("<array_size>", ["λ"]),

    # ==========================================
    # 6. STATEMENTS
    # ==========================================
    ("<statements>", ["id", "<id_suffix>", "<statements>"]),
    ("<statements>", ["<input_state>", "<statements>"]),
    ("<statements>", ["<output_state>", "<statements>"]),
    ("<statements>", ["<conditional_state>", "<statements>"]),
    ("<statements>", ["<loop_state>", "<statements>"]),
    ("<statements>", ["<comeback_state>", "<statements>"]),
    ("<statements>", ["<choose_state>", "<statements>"]),
    ("<statements>", ["<unary_state>", "<statements>"]),
    ("<statements>", ["<break_state>", "<statements>"]),
    ("<statements>", ["<local_decl>", "<statements>"]),  # declaration anywhere
    ("<statements>", ["λ"]),

    # Phase/case body: statements without breakup (for choose phase/bareminimum)
    ("<phase_statements>", ["id", "<id_suffix>", "<phase_statements>"]),
    ("<phase_statements>", ["<input_state>", "<phase_statements>"]),
    ("<phase_statements>", ["<output_state>", "<phase_statements>"]),
    ("<phase_statements>", ["<conditional_state>", "<phase_statements>"]),
    ("<phase_statements>", ["<loop_state>", "<phase_statements>"]),
    ("<phase_statements>", ["<comeback_state>", "<phase_statements>"]),
    ("<phase_statements>", ["<choose_state>", "<phase_statements>"]),
    ("<phase_statements>", ["<unary_state>", "<phase_statements>"]),
    ("<phase_statements>", ["<local_decl>", "<phase_statements>"]),
    ("<phase_statements>", ["λ"]),

    # ==========================================
    # 7. ID SUFFIXES & UNARY
    # ==========================================
    # Array index: dedicated nonterminal (semicolon not part of it; can tailor later)
    ("<array_index_expr>", ["<expr>"]),
    ("<id_suffix>", ["[", "<array_index_expr>", "]", "<id_suffix>"]),
    ("<id_suffix>", ["<assign_ops>", "<assign_values>", ";"]),
    ("<id_suffix>", ["(", "<arguments>", ")", ";"]),
    ("<id_suffix>", ["<unary_ops>", ";"]),
    ("<id_suffix>", ["::", "id", "<id_suffix>"]),

    ("<unary_state>", ["<unary_ops>", "id", ";"]),
    ("<unary_ops>", ["++"]),
    ("<unary_ops>", ["--"]),

    ("<assign_ops>", ["="]),
    ("<assign_ops>", ["+="]),
    ("<assign_ops>", ["-="]),
    ("<assign_ops>", ["*="]),
    ("<assign_ops>", ["/="]),
    ("<assign_ops>", ["%="]),

    # ASSIGNMENT: Strict Arithmetic Only (Prevents x = y == z)
    ("<assign_values>", ["<assign_rhs_expr>"]),
    ("<arguments>", ["<paren_expr>", "<more_arguments>"]),
    ("<arguments>", ["λ"]),
    ("<more_arguments>", [",", "<paren_expr>", "<more_arguments>"]),
    ("<more_arguments>", ["λ"]),

    # ==========================================
    # 8. I/O & CONTROL FLOW
    # ==========================================
    ("<input_state>", ["give", ">>", "id", "<input_tail>", "<more_input_ids>", ";"]),
    ("<input_state>", ["overshare", "(", "id", ")", ";"]),
    ("<input_tail>", ["[", "<array_index_expr>", "]", "<input_tail>"]),
    ("<input_tail>", ["λ"]),
    ("<more_input_ids>", [">>", "id", "<input_tail>", "<more_input_ids>"]),
    ("<more_input_ids>", ["λ"]),

    ("<output_state>", ["express", "<<", "<output_values>", "<more_output_tail>", ";"]),
    ("<more_output_tail>", ["<<", "<output_values>", "<more_output_tail>"]),
    ("<more_output_tail>", ["λ"]),
    ("<output_values>", ["<expr>"]),
    ("<output_values>", ["periodt"]),

    ("<comeback_state>", ["comeback", "<expr_opt>", ";"]),
    ("<break_state>", ["breakup", ";"]),

    # ==========================================
    # 9. LOOPS & CONDITIONS
    # ==========================================
    ("<conditional_state>", ["forever", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>", "<more_opt>"]),
    ("<forevermore_lst>", ["forevermore", "(", "<expr>", ")", "{", "<body_func>", "}", "<forevermore_lst>"]),
    ("<forevermore_lst>", ["λ"]),
    ("<more_opt>", ["more", "{", "<body_func>", "}"]),
    ("<more_opt>", ["λ"]),

    ("<loop_state>", ["<pursue_stmt>"]),
    ("<loop_state>", ["<while_stmt>"]),
    ("<loop_state>", ["<for_stmt>"]),

    ("<pursue_stmt>", ["pursue", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    ("<while_stmt>", ["while", "(", "<expr>", ")", "{", "<body_func>", "}"]),
    ("<for_stmt>", ["for", "(", "<for_init>", ";", "<expr>", ";", "<for_ud>", ")", "{", "<body_func>", "}"]),

    ("<for_init>", ["<data_type>", "id", "=", "<expr_ar>"]),
    ("<for_init>", ["id", "=", "<expr_ar>"]),

    # Factored so LL(1): id assign_ops expr vs id unary_ops both start with id → id for_ud_tail
    ("<for_ud>", ["id", "<for_ud_tail>"]),
    ("<for_ud_tail>", ["<assign_ops>", "<expr>"]),
    ("<for_ud_tail>", ["<unary_ops>"]),
    ("<for_ud>", ["<unary_ops>", "id"]),

    ("<choose_state>", ["choose", "(", "<expr>", ")", "{", "<phase_lst>", "<bareminimum_opt>", "}"]),
    ("<phase_lst>", ["phase", "<choose_const>", ":", "<phase_body>", "breakup", ";", "<phase_lst_next>"]),
    ("<phase_lst_next>", ["<phase_lst>"]),
    ("<phase_lst_next>", ["λ"]),
    ("<choose_const>", ["dear_lit"]),
    ("<bareminimum_opt>", ["bareminimum", ":", "<phase_body>", "breakup", ";"]),
    ("<bareminimum_opt>", ["λ"]),

    # ==========================================
    # 10. EXPRESSIONS (MAIN HIERARCHY)
    # ==========================================
    ("<expr>", ["<log_expr>"]),
    ("<expr_opt>", ["<expr>"]),
    ("<expr_opt>", ["λ"]),

    ("<log_expr>", ["<and_expr>", "<log_next>"]),
    ("<log_next>", ["||", "<and_expr>", "<log_next>"]),
    ("<log_next>", ["λ"]),

    ("<and_expr>", ["<rel_expr>", "<and_next>"]),
    ("<and_next>", ["&&", "<rel_expr>", "<and_next>"]),
    ("<and_next>", ["λ"]),

    ("<rel_expr>", ["<expr_ar>", "<rel_next>"]),
    ("<rel_next>", ["<rel_op>", "<expr_ar>", "<rel_next>"]),
    ("<rel_next>", ["λ"]),
    ("<rel_op>", ["=="]),
    ("<rel_op>", ["!="]),
    ("<rel_op>", ["<"]),
    ("<rel_op>", ["<="]),
    ("<rel_op>", [">"]),
    ("<rel_op>", [">="]),

    ("<expr_ar>", ["<term>", "<expr_next>"]),
    ("<expr_next>", ["+", "<term>", "<expr_next>"]),
    ("<expr_next>", ["-", "<term>", "<expr_next>"]),
    ("<expr_next>", ["λ"]),

    ("<term>", ["<factor>", "<term_next>"]),
    ("<term_next>", ["*", "<factor>", "<term_next>"]),
    ("<term_next>", ["/", "<factor>", "<term_next>"]),
    ("<term_next>", ["%", "<factor>", "<term_next>"]),
    ("<term_next>", ["λ"]),

    # ==========================================
    # 11. FACTORS & TAILS
    # ==========================================
    ("<factor>", ["(", "<paren_expr>", ")"]),
    ("<factor>", ["id", "<factor_tail>"]),
    ("<factor>", ["dear_lit"]),
    ("<factor>", ["dearest_lit"]),
    ("<factor>", ["rant_lit"]),
    ("<factor>", ["<status_lit>"]),
    ("<factor>", ["-", "<factor>"]),
    ("<factor>", ["+", "<factor>"]),
    ("<factor>", ["++", "id"]),
    ("<factor>", ["--", "id"]),
    # Logical NOT in general expr (forever/while/choose conditions, etc.)
    ("<factor>", ["!", "<factor>"]),

    ("<factor_tail>", ["[", "<array_index_expr>", "]", "<factor_tail>"]),
    ("<factor_tail>", ["(", "<arguments>", ")"]),
    ("<factor_tail>", ["++"]),
    ("<factor_tail>", ["--"]),
    ("<factor_tail>", ["::", "id", "<factor_tail>"]),
    ("<factor_tail>", ["λ"]),

    # ==========================================
    # 12. PARENTHESIS-ONLY HIERARCHY
    # ==========================================
    ("<paren_expr>", ["<paren_log_expr>"]),
    ("<paren_log_expr>", ["<paren_and_expr>", "<paren_log_next>"]),
    ("<paren_log_next>", ["||", "<paren_and_expr>", "<paren_log_next>"]),
    ("<paren_log_next>", ["λ"]),
    ("<paren_and_expr>", ["<paren_rel_expr>", "<paren_and_next>"]),
    ("<paren_and_next>", ["&&", "<paren_rel_expr>", "<paren_and_next>"]),
    ("<paren_and_next>", ["λ"]),
    ("<paren_rel_expr>", ["<paren_expr_ar>", "<paren_rel_next>"]),
    ("<paren_rel_next>", ["<rel_op>", "<paren_expr_ar>", "<paren_rel_next>"]),
    ("<paren_rel_next>", ["λ"]),
    ("<paren_expr_ar>", ["<paren_term>", "<paren_expr_next>"]),
    ("<paren_expr_next>", ["+", "<paren_term>", "<paren_expr_next>"]),
    ("<paren_expr_next>", ["-", "<paren_term>", "<paren_expr_next>"]),
    ("<paren_expr_next>", ["λ"]),
    ("<paren_term>", ["<factor>", "<paren_term_next>"]),
    ("<paren_term_next>", ["*", "<factor>", "<paren_term_next>"]),
    ("<paren_term_next>", ["/", "<factor>", "<paren_term_next>"]),
    ("<paren_term_next>", ["%", "<factor>", "<paren_term_next>"]),
    ("<paren_term_next>", ["λ"]),

    # Assignment RHS: comparison and logical allowed; == and != prohibited (prevents x = y == z)
    ("<assign_rhs_expr>", ["<assign_rhs_log_expr>"]),
    ("<assign_rhs_log_expr>", ["<assign_rhs_and_expr>", "<assign_rhs_log_next>"]),
    ("<assign_rhs_log_next>", ["||", "<assign_rhs_and_expr>", "<assign_rhs_log_next>"]),
    ("<assign_rhs_log_next>", ["λ"]),
    ("<assign_rhs_and_expr>", ["<assign_rhs_rel_expr>", "<assign_rhs_and_next>"]),
    ("<assign_rhs_and_next>", ["&&", "<assign_rhs_rel_expr>", "<assign_rhs_and_next>"]),
    ("<assign_rhs_and_next>", ["λ"]),
    ("<assign_rhs_rel_expr>", ["<expr_ar>", "<assign_rhs_rel_next>"]),
    ("<assign_rhs_rel_next>", ["<assign_rhs_rel_op>", "<expr_ar>", "<assign_rhs_rel_next>"]),
    ("<assign_rhs_rel_next>", ["λ"]),
    ("<assign_rhs_rel_op>", ["<"]),
    ("<assign_rhs_rel_op>", ["<="]),
    ("<assign_rhs_rel_op>", [">"]),
    ("<assign_rhs_rel_op>", [">="]),
    ("<assign_rhs_rel_op>", ["=="]),
    ("<assign_rhs_rel_op>", ["!="]),
    # ==========================================
    # TAILORED EXPRESSIONS (C++ MIMIC)
    # ==========================================
    # A. INTEGER (dear) - Math + Bitwise; allow id assign_ops expr (C++ style) in expression
    ("<dear_expr>", ["id", "<dear_expr_id_tail>"]),
    ("<dear_expr>", ["<dear_term_not_id>", "<dear_next>"]),
    ("<dear_expr_id_tail>", ["<assign_ops>", "<dear_expr>"]),
    ("<dear_expr_id_tail>", ["<factor_tail>", "<dear_tail_after_factor>"]),
    ("<dear_tail_after_factor>", ["<dear_term_next>", "<dear_next>"]),
    ("<dear_next>", ["+", "<dear_term>", "<dear_next>"]),
    ("<dear_next>", ["-", "<dear_term>", "<dear_next>"]),
    ("<dear_next>", ["<<", "<dear_term>", "<dear_next>"]),
    ("<dear_next>", [">>", "<dear_term>", "<dear_next>"]),
    
  
    
    ("<dear_next>", ["λ"]),
    ("<dear_term>", ["<dear_factor>", "<dear_term_next>"]),
    ("<dear_term_next>", ["*", "<dear_factor>", "<dear_term_next>"]),
    ("<dear_term_next>", ["/", "<dear_factor>", "<dear_term_next>"]),
    ("<dear_term_next>", ["%", "<dear_factor>", "<dear_term_next>"]),
    ("<dear_term_next>", ["λ"]),
    ("<dear_factor>", ["(", "<dear_expr>", ")"]),
    ("<dear_factor>", ["dear_lit"]),
    ("<dear_factor>", ["id", "<factor_tail>"]),
    ("<dear_factor>", ["greenflag"]),
    ("<dear_factor>", ["redflag"]),
    ("<dear_factor>", ["-", "<dear_factor>"]),
    ("<dear_factor>", ["+", "<dear_factor>"]),
    ("<dear_factor>", ["++", "id"]),
    ("<dear_factor>", ["--", "id"]),
   

    # B. FLOAT (dearest) - Same arithmetic as dear; allow id assign_ops expr in expression
    ("<dearest_expr>", ["id", "<dearest_expr_id_tail>"]),
    ("<dearest_expr>", ["<dearest_term_not_id>", "<dearest_next>"]),
    ("<dearest_expr_id_tail>", ["<assign_ops>", "<dearest_expr>"]),
    ("<dearest_expr_id_tail>", ["<factor_tail>", "<dearest_tail_after_factor>"]),
    ("<dearest_tail_after_factor>", ["<dearest_term_next>", "<dearest_next>"]),
    ("<dearest_term_not_id>", ["<dearest_factor_not_id>", "<dearest_term_next>"]),
    ("<dearest_factor_not_id>", ["(", "<dearest_expr>", ")"]),
    ("<dearest_factor_not_id>", ["dearest_lit"]),
    ("<dearest_factor_not_id>", ["dear_lit"]),
    ("<dearest_factor_not_id>", ["greenflag"]),
    ("<dearest_factor_not_id>", ["redflag"]),
    ("<dearest_factor_not_id>", ["-", "<dearest_factor_not_id>"]),
    ("<dearest_factor_not_id>", ["+", "<dearest_factor_not_id>"]),
    ("<dearest_factor_not_id>", ["++", "id"]),
    ("<dearest_factor_not_id>", ["--", "id"]),
    ("<dearest_next>", ["+", "<dearest_term>", "<dearest_next>"]),
    ("<dearest_next>", ["-", "<dearest_term>", "<dearest_next>"]),

    ("<dearest_next>", ["λ"]),
    ("<dearest_term>", ["<dearest_factor>", "<dearest_term_next>"]),
    ("<dearest_term_next>", ["*", "<dearest_factor>", "<dearest_term_next>"]),
    ("<dearest_term_next>", ["/", "<dearest_factor>", "<dearest_term_next>"]),
    ("<dearest_term_next>", ["λ"]),
    ("<dearest_factor>", ["(", "<dearest_expr>", ")"]),
    ("<dearest_factor>", ["dearest_lit"]),
    ("<dearest_factor>", ["id", "<factor_tail>"]),
    ("<dearest_factor>", ["dear_lit"]),
    ("<dearest_factor>", ["greenflag"]),
    ("<dearest_factor>", ["redflag"]),
    ("<dearest_factor>", ["-", "<dearest_factor>"]),
    ("<dearest_factor>", ["++", "id"]),
    ("<dearest_factor>", ["--", "id"]),

    # C. STRING (rant) - Concat only
    ("<rant_expr>", ["<rant_term>", "<rant_next>"]),
    ("<rant_next>", ["+", "<rant_term>", "<rant_next>"]),
    ("<rant_next>", ["λ"]),
    ("<rant_term>", ["<rant_factor>"]),
    ("<rant_factor>", ["(", "<rant_expr>", ")"]),
    ("<rant_factor>", ["rant_lit"]),
    ("<rant_factor>", ["id"]),

    # D. BOOLEAN (status) - Logic + Relational; uses status_int_compare (dear_expr comparisons)
    ("<status_expr>", ["<status_and>", "<status_or_next>"]),
    ("<status_or_next>", ["||", "<status_and>", "<status_or_next>"]),
    ("<status_or_next>", ["λ"]),
    ("<status_and>", ["<status_factor>", "<status_and_next>"]),
    ("<status_and_next>", ["&&", "<status_factor>", "<status_and_next>"]),
    ("<status_and_next>", ["λ"]),
    ("<status_factor>", ["not", "<status_factor>"]),
    ("<status_factor>", ["!", "<status_factor>"]),
    ("<status_factor>", ["<status_lit>"]),
    ("<status_factor>", ["<status_int_compare>"]),
    ("<status_factor>", ["dear_lit"]),
    # id: after status_int_compare so table[status_factor][id] = id status_factor_after_id (enables id, id>expr)
    ("<status_factor>", ["id", "<status_factor_after_id>"]),
    ("<status_factor_after_id>", ["λ"]),
    ("<status_factor_after_id>", ["<rel_op>", "<dear_expr>"]),

    # E. Integer comparison: left side cannot be bare id (so id uses status_factor_after_id; (x>5), 5>y use this)
    ("<dear_expr_not_id>", ["<dear_term_not_id>", "<dear_next>"]),
    ("<dear_term_not_id>", ["<dear_factor_not_id>", "<dear_term_next>"]),
    ("<dear_factor_not_id>", ["(", "<dear_expr>", ")"]),
    ("<dear_factor_not_id>", ["dear_lit"]),
    ("<dear_factor_not_id>", ["greenflag"]),
    ("<dear_factor_not_id>", ["redflag"]),
    ("<dear_factor_not_id>", ["-", "<dear_factor_not_id>"]),
    ("<dear_factor_not_id>", ["+", "<dear_factor_not_id>"]),
    ("<dear_factor_not_id>", ["++", "id"]),
    ("<dear_factor_not_id>", ["--", "id"]),
    ("<status_int_compare>", ["<dear_expr_not_id>", "<status_int_compare_next>"]),
    ("<status_int_compare_next>", ["<rel_op>", "<dear_expr>"]),
    ("<status_int_compare_next>", ["λ"]),
    # ( status_expr ) after status_int_compare so table[status_factor]["("] = ( status_expr ) for (x>5)
    ("<status_factor>", ["(", "<status_expr>", ")"]),

    # Assignment RHS: comparison and logical allowed; == and != prohibited (prevents x = y == z)
]


# By nonterminal: lhs -> list of RHS (each RHS is list of symbols). Easy lookup.
CFG_BY_NONTERMINAL: Dict[str, List[List[str]]] = {}
for (lhs, rhs) in PRODUCTION_LIST:
    if lhs not in CFG_BY_NONTERMINAL:
        CFG_BY_NONTERMINAL[lhs] = []
    CFG_BY_NONTERMINAL[lhs].append(rhs)


def get_productions(lhs: str) -> List[List[str]]:
    """Return all RHS alternatives for nonterminal lhs."""
    return CFG_BY_NONTERMINAL.get(lhs, [])


def is_epsilon(rhs: List[str]) -> bool:
    """True if RHS is epsilon (λ or null)."""
    return rhs in (["λ"], ["null"]) or (len(rhs) == 1 and rhs[0] in ("λ", "null"))
