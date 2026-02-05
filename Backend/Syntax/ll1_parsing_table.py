"""
LL(1) parsing table builder for the Lovers language.

This module *derives* the LL(1) table from `cfg_productions.PRODUCTION_LIST`,
so the CFG in `cfg_productions.py` is the **single source of truth**.

`parsetv2.py` still uses a table-driven LL(1) parser, but you only need to
maintain the grammar once, in `cfg_productions.py`.
"""

from typing import Dict, List, Set

from Backend.Syntax.CFG import PRODUCTION_LIST, is_epsilon


Symbol = str
RHS = List[Symbol]
ParsingTable = Dict[Symbol, Dict[Symbol, RHS]]


EPSILON = "λ"
EPSILON_RULE: RHS = ["null"]  # parsetv2 treats ['null'] as epsilon
END_MARKER = "$"

# Exposed FIRST/FOLLOW maps for visualization and debugging.
# These are populated the first time build_parsing_table() is called.
FIRST_SETS: Dict[Symbol, Set[Symbol]] = {}
FOLLOW_SETS: Dict[Symbol, Set[Symbol]] = {}


def _nonterminals() -> Set[Symbol]:
    """All LHS symbols (nonterminals) in the grammar."""
    return set(lhs for lhs, _ in PRODUCTION_LIST.values())


def _all_symbols() -> Set[Symbol]:
    """All symbols that appear anywhere on RHS."""
    symbols: Set[Symbol] = set()
    for _, rhs in PRODUCTION_LIST.items():
        symbols.update(rhs)
    return symbols


def _terminals(nonterms: Set[Symbol]) -> Set[Symbol]:
    """Symbols that are not nonterminals and not epsilon/null."""
    terms: Set[Symbol] = set()
    for _, (lhs, rhs) in PRODUCTION_LIST.items():
        for sym in rhs:
            if sym not in nonterms and sym not in (EPSILON, "null"):
                terms.add(sym)
    return terms


def _first_sets(nonterms: Set[Symbol], terms: Set[Symbol]) -> Dict[Symbol, Set[Symbol]]:
    """
    Compute FIRST sets for all symbols (nonterminals + terminals).
    FIRST(a) for terminals is {a}, FIRST(λ) = {λ}.
    """
    first: Dict[Symbol, Set[Symbol]] = {nt: set() for nt in nonterms}

    # Terminals and epsilon
    for t in terms | {EPSILON}:
        first[t] = {t}

    changed = True
    while changed:
        changed = False
        for _, (lhs, rhs) in PRODUCTION_LIST.items():
            before = len(first[lhs])

            if is_epsilon(rhs):
                first[lhs].add(EPSILON)
            else:
                nullable_prefix = True
                for sym in rhs:
                    sym_first = first.get(sym, {sym})
                    first[lhs].update(sym_first - {EPSILON})
                    if EPSILON not in sym_first:
                        nullable_prefix = False
                        break
                if nullable_prefix:
                    first[lhs].add(EPSILON)

            if len(first[lhs]) > before:
                changed = True

    return first


def _first_of_sequence(seq: RHS, first: Dict[Symbol, Set[Symbol]]) -> Set[Symbol]:
    """FIRST for a sequence of symbols α = X1 X2 ... Xn."""
    if not seq:
        return {EPSILON}

    result: Set[Symbol] = set()
    nullable_prefix = True
    for sym in seq:
        sym_first = first.get(sym, {sym})
        result.update(sym_first - {EPSILON})
        if EPSILON not in sym_first:
            nullable_prefix = False
            break
    if nullable_prefix:
        result.add(EPSILON)
    return result


def _follow_sets(nonterms: Set[Symbol], first: Dict[Symbol, Set[Symbol]]) -> Dict[Symbol, Set[Symbol]]:
    """
    Compute FOLLOW sets for all nonterminals.
    Standard algorithm: distribute FIRST of suffix and FOLLOW(lhs).
    """
    follow: Dict[Symbol, Set[Symbol]] = {nt: set() for nt in nonterms}

    # Start symbol (production 1) gets end marker
    start_lhs, _ = PRODUCTION_LIST[1]
    follow[start_lhs].add(END_MARKER)

    changed = True
    while changed:
        changed = False
        for _, (lhs, rhs) in PRODUCTION_LIST.items():
            for i, B in enumerate(rhs):
                if B not in nonterms:
                    continue

                beta = rhs[i + 1 :]
                first_beta = _first_of_sequence(beta, first)

                before = len(follow[B])

                # FIRST(beta) \ {ε} ⊆ FOLLOW(B)
                follow[B].update(first_beta - {EPSILON})

                # If beta ⇒* ε, then FOLLOW(lhs) ⊆ FOLLOW(B)
                if not beta or EPSILON in first_beta or is_epsilon(beta):
                    follow[B].update(follow[lhs])

                if len(follow[B]) > before:
                    changed = True

    return follow


def build_parsing_table() -> ParsingTable:
    """
    Build the LL(1) parsing table M[A, a] from the CFG in PRODUCTION_LIST.

    For each production A → α:
      1. For each terminal a ∈ FIRST(α) \ {ε}, set M[A, a] = α.
      2. If ε ∈ FIRST(α), then for each b ∈ FOLLOW(A), set M[A, b] = ε.

    Epsilon productions are encoded as ['null'] to match parsetv2.py's
    expectation.
    """
    nonterms = _nonterminals()
    terms = _terminals(nonterms)
    first = _first_sets(nonterms, terms)
    follow = _follow_sets(nonterms, first)

    # Expose FIRST/FOLLOW so other tools/UI can visualize them without
    # recomputing. We copy into the module-level dicts to keep them in sync
    # with the current grammar.
    global FIRST_SETS, FOLLOW_SETS
    FIRST_SETS = {k: set(v) for k, v in first.items()}
    FOLLOW_SETS = {k: set(v) for k, v in follow.items()}

    table: ParsingTable = {nt: {} for nt in nonterms}

    for _, (lhs, rhs) in PRODUCTION_LIST.items():
        first_alpha = _first_of_sequence(rhs, first)

        # 1. Terminals in FIRST(α) (except ε)
        for a in first_alpha - {EPSILON}:
            table[lhs][a] = rhs if not is_epsilon(rhs) else EPSILON_RULE

        # 2. If ε ∈ FIRST(α), terminals in FOLLOW(lhs)
        if EPSILON in first_alpha or is_epsilon(rhs):
            for b in follow[lhs]:
                if b == END_MARKER:
                    # parsetv2 handles '$' separately as end-of-input
                    continue
                table[lhs][b] = EPSILON_RULE
    
    return table
