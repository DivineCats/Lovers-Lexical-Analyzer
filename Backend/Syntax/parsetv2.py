# Simple LL(1) Table-Driven Parser for Lovers Language
# A simplified parser similar to your senior's approach
# 
# Now with AST building capability!
# 
# Usage:
#   - parse(tokens, build_ast=False) -> (log_messages, error_message, syntax_valid)
#   - parse(tokens, build_ast=True) -> (ast, error_message)
# 
# Note: Full AST building during pure LL(1) table-driven parsing is complex.
# This implementation uses a hybrid approach:
#   1. Validates syntax with LL(1) table-driven parser (fast, simple)
#   2. Builds AST using RecursiveDescentParser (complete, reliable)
# 
# This gives you the best of both worlds: simple validation + complete AST.

from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field

# Import AST classes from SimpleRecursiveDescentParser
# try:
#     from Backend.Syntax.SimpleRecursiveDescentParser import (
#         ASTNode, Program, Namespace, MainFunction,
#         Declaration, MultiDeclaration,
#         Function, Parameter, FunctionBody,
#         Statement, AssignmentStatement, FunctionCallStatement,
#         UnaryStatement, InputStatement, OutputStatement, ReturnStatement,
#         IfStatement, ElifClause, WhileStatement, DoWhileStatement,
#         ForStatement, ForInit, ForUpdate, SwitchStatement, CaseClause,
#         Expression, BinaryExpression, UnaryExpression,
#         IdentifierExpression, FunctionCallExpression,
#         LiteralExpression, ParenthesizedExpression
#     )
# except ImportError:
#     # Fallback: define minimal AST classes if import fails
#     @dataclass
#     class ASTNode:
#         line: int = 1
#         column: int = 1
    
 #     @dataclass
 #     class Program(ASTNode):
 #         namespace: Optional[Any] = None
 #         global_declarations: List[Any] = field(default_factory=list)
 #         sub_functions: List[Any] = field(default_factory=list)
 #         main_function: Optional[Any] = None


from Backend.Syntax.AST import (
    ASTNode,
    Program,
    Namespace,
    MainFunction,
    Declaration,
    MultiDeclaration,
    Function,
    Parameter,
    FunctionBody,
    Statement,
    AssignmentStatement,
    FunctionCallStatement,
    UnaryStatement,
    InputStatement,
    OutputStatement,
    ReturnStatement,
    IfStatement,
    ElifClause,
    WhileStatement,
    DoWhileStatement,
    ForStatement,
    ForInit,
    ForUpdate,
    SwitchStatement,
    CaseClause,
    Expression,
    BinaryExpression,
    UnaryExpression,
    IdentifierExpression,
    FunctionCallExpression,
    LiteralExpression,
    ParenthesizedExpression,
)


class ParserError(Exception):
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line if line is not None else None
        self.column = column

    def __str__(self):
        # Format: "Unexpected Token: <token> (line X, col Y)\nExpected: <list>"
        # Location is already included in the message, so just return it
        return self.message


# Token normalization: convert token kinds to grammar terminal names
def normalize_token(token_kind: str) -> str:
    """Convert token kind to grammar terminal name."""
    # Map uppercase operators/delimiters to their symbols
    token_map = {
        "LPAREN": "(",
        "RPAREN": ")",
        "LBRACE": "{",
        "RBRACE": "}",
        "LBRACKET": "[",
        "RBRACKET": "]",
        "SEMICOLON": ";",
        "COMMA": ",",
        "COLON": ":",
        "DOT": ".",
        "PLUS": "+",
        "MINUS": "-",
        "STAR": "*",
        "SLASH": "/",
        "PERCENT": "%",
        "ASSIGN": "=",
        "OP_DOT_ASSIGN": ".=",
        "LT": "<",
        "GT": ">",
        "OP_EQ": "==",
        "OP_DOT_EQ": ".==",
        "OP_NEQ": "!=",
        "OP_LTE": "<=",
        "OP_GTE": ">=",
        "OP_AND": "&&",
        "OP_OR": "||",
        "OP_INC": "++",
        "OP_DEC": "--",
        "OP_LSHIFT": "<<",
        "OP_RSHIFT": ">>",
        "OP_PLUS_ASSIGN": "+=",
        "OP_MINUS_ASSIGN": "-=",
        "OP_MUL_ASSIGN": "*=",
        "OP_DIV_ASSIGN": "/=",
        "OP_MOD_ASSIGN": "%=",
        "OP_SCOPE": "::",
        "NOT": "!",
    }
    
    # If it's a mapped token, return the symbol
    if token_kind in token_map:
        return token_map[token_kind]
    
    # If it's already lowercase (keywords, id, literals), return as-is
    if token_kind.islower():
        return token_kind
    
    # For identifiers
    if token_kind.startswith("id") or token_kind == "ID" or token_kind == "IDENTIFIER":
        return "id"
    
    # For literals
    if token_kind in ["DEAR_LIT", "INT_LIT"]:
        return "dear_lit"
    if token_kind in ["DEAREST_LIT", "FLOAT_LIT"]:
        return "dearest_lit"
    if token_kind in ["RANT_LIT", "STRING_LIT"]:
        return "rant_lit"
    if token_kind in ["GREENFLAG", "TRUE", "BOOL_LIT"]:
        return "greenflag"
    if token_kind in ["REDFLAG", "FALSE"]:
        return "redflag"
    
    # Default: lowercase it
    return token_kind.lower()


# Production table (CFG): CFG.py. LL(1) table: First_Follow.py
from Backend.Syntax.First_Follow import build_parsing_table

# Global parsing table
_parsing_table = None


def initialize_parser():
    """
    Initialize (or refresh) the parser by building the parsing table.

    The LL(1) table is derived from `cfg_productions.PRODUCTION_LIST`, which is
    your single source of truth for the grammar. To ensure the backend always
    follows the latest CFG, we rebuild the table each time we initialize.
    """
    global _parsing_table
    _parsing_table = build_parsing_table()


# Tokens that are shown quoted in expected-token messages
_DELIMITER_TOKENS = frozenset(['(', ')', '{', '}', '[', ']', ';', ',', ':'])

# Closing delimiters and their matching open (for context-aware expected set)
_CLOSING_TO_OPEN = {')': '(', ']': '[', '}': '{'}

# Epsilon production as stored in the parsing table (matches First_Follow)
_EPSILON_RULE = ['null']


def _is_epsilon_rule(rule) -> bool:
    """True if the production RHS is epsilon (null or λ)."""
    return rule == _EPSILON_RULE or rule == ['λ']


def _pending_opens_in_stack(remaining_stack: list) -> set:
    """
    Return the set of opening delimiters that are still pending (unmatched) in
    the remaining stack. Only then is it valid to suggest the matching closer.
    """
    pending = set()
    open_count = {'(': 0, '[': 0, '{': 0}
    close_count = {')': 0, ']': 0, '}': 0}
    for sym in remaining_stack:
        if sym in open_count:
            open_count[sym] += 1
        if sym in close_count:
            close_count[sym] += 1
    if open_count['('] > close_count[')']:
        pending.add('(')
    if open_count['['] > close_count[']']:
        pending.add('[')
    if open_count['{'] > close_count['}']:
        pending.add('{')
    return pending


def get_all_expected_terminals(remaining_stack, parsing_table):
    """
    Recursive Expected Set Discovery: build the set of expected terminals from
    the current parser stack so error messages are 'farsighted'.

    - Takes the remaining sequence (stack with next-to-process at index 0).
    - Recursively expands the top symbol:
      - Terminal: add it to Expected and stop that branch.
      - Non-terminal: add all lookahead terminals that could trigger a rule
        (parsing_table[nt].keys()). If the non-terminal has an ε production,
        'see through' and recursively check the next symbol on the stack.
    - Returns a set of terminal strings (e.g. {'+', '-', 'id'}), not non-terminal names.
    - Closing delimiters ')', ']', '}' are only included if the matching
      '(', '[', '{' appears (unmatched) in the remaining stack, so we never
      suggest "expected ')'" when there is no open parenthesis.
    """
    if not remaining_stack:
        return set()
    top = remaining_stack[0]
    if top == "$":
        return get_all_expected_terminals(remaining_stack[1:], parsing_table)
    if top not in parsing_table:
        # Terminal: add it and stop this branch
        return {top}
    # Non-terminal: collect all lookahead terminals that trigger a rule
    raw_expected = set(parsing_table[top].keys())
    has_epsilon = any(_is_epsilon_rule(rule) for rule in parsing_table[top].values())
    if has_epsilon and len(remaining_stack) > 1:
        # See through ε and recurse on the rest of the stack
        raw_expected |= get_all_expected_terminals(remaining_stack[1:], parsing_table)
    # Only suggest closing delimiters when we're actually inside the matching open,
    # or when that closer is on the stack (parser already consumed the open and is waiting to match it).
    pending_opens = _pending_opens_in_stack(remaining_stack)
    closers_on_stack = {sym for sym in remaining_stack if sym in _CLOSING_TO_OPEN}
    expected = set()
    for t in raw_expected:
        if t in _CLOSING_TO_OPEN:
            if _CLOSING_TO_OPEN[t] in pending_opens or t in closers_on_stack:
                expected.add(t)
        else:
            expected.add(t)
    return expected


def _build_full_expected_set(top, stack, parsing_table):
    """
    Build the set of expected terminals at this position from the parsing table only.
    No blocking or masking: expected = exactly what the CFG/table allows for the current stack top.
    """
    expected = set()
    if top in parsing_table:
        expected |= set(parsing_table[top].keys())
    elif top != "$":
        expected.add(top)
    return expected


def _get_context_aware_expected_set(top, stack, lookahead, parsing_table, last_consumed_token=None):
    """
    Build the set of expected terminals at this position using Recursive Expected
    Set Discovery. The remaining sequence is [top] + stack in process order
    (stack is stored with next-to-pop at the end, so we use [top] + reversed(stack)).
    Error messages become 'farsighted' by seeing through ε and collecting terminals
    from the whole remaining rule.
    """
    # Remaining sequence: next to process is top, then rest of stack (next-to-pop first)
    if stack:
        remaining_stack = [top] + list(reversed(stack))
    else:
        remaining_stack = [top]
    return get_all_expected_terminals(remaining_stack, parsing_table)


def _format_expected_tokens(expected_set):
    """Format expected set as a single string for 'Expected Token: ...'."""
    if not expected_set:
        return "none"
    sorted_tokens = sorted(expected_set)
    formatted = [f"'{t}'" if t in _DELIMITER_TOKENS else t for t in sorted_tokens]
    return ", ".join(formatted)


def parse(token_list=None, build_ast=False):
    """
    Parse tokens using LL(1) table-driven parser.
    
    Args:
        token_list: List of tokens (Token objects or tuples). If None, tries to use global token variable.
        build_ast: If True, builds and returns AST. If False, only validates syntax.
    
    Returns:
        If build_ast=False: Tuple of (log_messages, error_message, syntax_valid)
        If build_ast=True: Tuple of (ast, error_message) where ast is Program or None
    """
    initialize_parser()
    
    # Try to get tokens from global scope if not provided
    if token_list is None:
        try:
            # Try importing from Lexer module
            import sys
            if 'token' in globals():
                token_list = globals()['token']
            else:
                # Try to import from Backend.Lexical.Lexer
                from Backend.Lexical.Lexer import token
                token_list = token
        except:
            pass
    
    if not token_list:
        raise ParserError("Syntax Error: No tokens provided.")
    
    # Filter out NEWLINE tokens (they're not part of the grammar)
    filtered_tokens = []
    for tok in token_list:
        if hasattr(tok, 'kind'):
            if tok.kind not in ["NEWLINE", "EOF"]:
                filtered_tokens.append(tok)
        elif isinstance(tok, tuple) and len(tok) > 0:
            if tok[0] not in ["NEWLINE", "EOF"]:
                filtered_tokens.append(tok)
        else:
            filtered_tokens.append(tok)
    
    # Add EOF marker at the end if not present
    if filtered_tokens:
        last_token = filtered_tokens[-1]
        last_kind = last_token.kind if hasattr(last_token, 'kind') else (last_token[0] if isinstance(last_token, tuple) else None)
        if last_kind != "EOF":
            from Backend.Lexical.Lexer import Token
            last_line = last_token.line if hasattr(last_token, 'line') else (last_token[-2] if isinstance(last_token, tuple) and len(last_token) >= 3 else 1)
            # EOF position = after last line (so "unexpected EOF" reports line 3 when last content is on line 2)
            eof_token = Token(kind="EOF", lexeme="", line=last_line + 1, column=1)
            filtered_tokens.append(eof_token)
    
    token_list = filtered_tokens
    
    # If building AST, use AST-building parser
    if build_ast:
        return parse_with_ast(token_list)
    
    # Original validation-only parser
    # Stack order: $ at bottom, <program> on top (so $ is popped last)
    stack = ["$", "<program>"]
    current_token_index = 0
    log_messages = []
    error_message = []
    syntax_valid = False
    
    def get_lookahead():
        """Safely retrieve the current token and its position."""
        if current_token_index < len(token_list):
            token_data = token_list[current_token_index]
            
            # Handle Token objects
            if hasattr(token_data, 'kind'):
                curr_token = token_data.kind
                line = getattr(token_data, 'line', None)
                column = getattr(token_data, 'column', None)
            # Handle token objects with 'type' attribute
            elif hasattr(token_data, 'type'):
                curr_token = token_data.type
                line = getattr(token_data, 'line', None)
                column = getattr(token_data, 'column', None)
            # Handle token tuples
            elif isinstance(token_data, tuple):
                if len(token_data) >= 3:
                    curr_token = token_data[0]
                    line = token_data[-2] if len(token_data) >= 3 else None
                    column = token_data[-1] if len(token_data) >= 3 else None
                else:
                    return "$", None, None
            else:
                return "$", None, None
            
            # Normalize token
            normalized = normalize_token(curr_token)
            
            # Handle EOF - convert to "$" for parser
            if normalized == "eof" or curr_token == "EOF":
                return "$", line, column
            
            # Handle identifiers
            if normalized == "id" or (isinstance(curr_token, str) and (curr_token.startswith("id") or curr_token == "ID" or curr_token == "IDENTIFIER")):
                return "id", line, column
            
            return normalized, line, column
        return "$", None, None
    
    try:
        while stack:
            top = stack.pop()
            lookahead, line, column = get_lookahead()
            
            # Debugging logs
            log_messages.append(f"Stack Top: {top}, Lookahead: {lookahead} (Line {line}, Column {column})")
            
            if top == "$":
                if lookahead == "$":
                    # Successfully parsed
                    error_message.append("Input accepted: Syntactically correct.")
                    syntax_valid = True
                    break
                else:
                    # More tokens after end marker - this shouldn't happen in normal flow
                    # But if it does, show what was unexpected
                    raise ParserError(f"Unexpected Token: {lookahead} (line {line}, col {column})\nExpected Token: <end of input>", line, column)
            
            if lookahead == "$" and top != "$":
                # End of input reached - user is still typing (incremental parsing).
                # Instead of treating this as a normal unexpected token, surface it
                # explicitly as an end-of-input (EOF) situation so the higher-level
                # error formatter can show "unexpected end of input" rather than
                # picking an arbitrary first expected token.
                expected_set = _get_context_aware_expected_set(top, stack, lookahead, _parsing_table)
                expected_str = _format_expected_tokens(expected_set)
                raise ParserError(
                    f"Unexpected Token: $EOF (line {line}, col {column})\nExpected Token: {expected_str}",
                    line, column
                )
            
            # Terminal match
            if top == lookahead:
                log_messages.append(f"Matched: {lookahead} (Line {line}, Column {column})")
                current_token_index += 1
            # Nonterminal: use parsing table
            elif top in _parsing_table:
                rule = _parsing_table[top].get(lookahead)
                if rule:
                    if rule == ['null']:  # Epsilon production
                        log_messages.append(f"Skipping {top} (Epsilon Production)")
                    else:
                        log_messages.append(f"Applying Rule: {top} -> {' '.join(rule)}")
                        # Push rule in reverse order
                        stack.extend(reversed(rule))
                else:
                    expected_set = _get_context_aware_expected_set(top, stack, lookahead, _parsing_table)
                    expected_str = _format_expected_tokens(expected_set)
                    raise ParserError(
                        f"Unexpected Token: {lookahead} (line {line}, col {column})\nExpected Token: {expected_str}",
                        line, column
                    )
            else:
                # Terminal mismatch - show full expected set (stack + expr continuation)
                if top == "id" and lookahead in ("}", ";", "\n", "$"):
                    msg = f"Invalid Token after data type (line {line}, col {column})\nExpected Token: identifier"
                else:
                    expected_set = _get_context_aware_expected_set(top, stack, lookahead, _parsing_table)
                    expected_str = _format_expected_tokens(expected_set)
                    msg = f"Unexpected Token: {lookahead} (line {line}, col {column})\nExpected Token: {expected_str}"
                raise ParserError(msg, line, column)
        
        # Final check - if we've consumed all tokens but stack is empty, we're done
        # If there are remaining tokens, that's an error
        if not stack and current_token_index < len(token_list):
            remaining_token, rem_line, rem_col = get_lookahead()
            if remaining_token != "$":
                raise ParserError(
                    f"Unexpected Token: {remaining_token} (line {rem_line}, col {rem_col})\nExpected Token: <end of input>",
                    rem_line, rem_col
                )
        
        # If we still have items on stack and reached end of input, show what's expected
        # This handles the case where user is still typing (incremental parsing)
        # This case is already handled above in the "lookahead == $ and top != $" check
        # So we don't need to duplicate it here
    
    except ParserError as e:
        error_message.append(str(e))
        syntax_valid = False
    except Exception as e:
        error_message.append(f"Unexpected error: {str(e)}")
        syntax_valid = False
    
    return log_messages, error_message, syntax_valid


class ASTBuilder:
    """Helper class to build AST nodes during LL(1) parsing."""
    
    def __init__(self, token_list):
        self.token_list = token_list
        self.current_index = 0
        self.ast_stack = []  # Stack to build AST nodes
        self.value_stack = []  # Stack to store intermediate values
    
    def get_current_token(self):
        """Get current token with position."""
        if self.current_index < len(self.token_list):
            token_data = self.token_list[self.current_index]
            
            if hasattr(token_data, 'kind'):
                return token_data.kind, getattr(token_data, 'lexeme', ''), getattr(token_data, 'line', 1), getattr(token_data, 'column', 1)
            elif hasattr(token_data, 'type'):
                return token_data.type, getattr(token_data, 'value', ''), getattr(token_data, 'line', 1), getattr(token_data, 'column', 1)
            elif isinstance(token_data, tuple):
                if len(token_data) >= 3:
                    return token_data[0], token_data[1] if len(token_data) > 1 else '', token_data[-2] if len(token_data) >= 3 else 1, token_data[-1] if len(token_data) >= 3 else 1
            return None, '', 1, 1
        return None, '', 1, 1
    
    def consume_token(self):
        """Consume current token and advance."""
        if self.current_index < len(self.token_list):
            self.current_index += 1
    
    def get_token_value(self):
        """Get the lexeme/value of current token."""
        _, value, _, _ = self.get_current_token()
        return value


def parse_with_ast(token_list, source_code=None):
    """
    Parse tokens and build AST using LL(1) table-driven parser.
    
    Note: Full AST building during pure LL(1) table-driven parsing is complex.
    This implementation uses a hybrid approach:
    1. Validates syntax with LL(1) table-driven parser (fast, simple)
    2. Builds AST using SimpleRecursiveDescentParser (complete, reliable)
    
    This gives you the best of both worlds: simple validation + complete AST.
    
    Args:
        token_list: List of tokens
        source_code: Optional source code string (preferred for accurate AST building)
    
    Returns:
        Tuple of (ast, error_message) where ast is Program or None
    """
    initialize_parser()
    
    # First validate syntax with LL(1) parser.
    # For now we do not build a full AST here; we only reuse the
    # shared AST classes to return a minimal Program node on success.
    log_messages, error_msg, syntax_valid = parse(token_list, build_ast=False)
    if not syntax_valid:
        # error_msg is a list of formatted error strings
        return None, error_msg
    
    # Syntax is valid – build a complete AST from the token stream.
    try:
        from Backend.Syntax.AST import RecursiveDescentAstBuilder, AstBuildError

        builder = RecursiveDescentAstBuilder(token_list)
        program = builder.parse_program()
        return program, []
    except Exception as e:
        # If AST building fails even though syntax validation passed,
        # surface a readable message (caller may fall back to validation-only).
        if e.__class__.__name__ == "AstBuildError":
            return None, [str(e)]
        return None, [f"AST build failed: {str(e)}"]

def parse_with_errors_parserv2(source: str):
    """
    Parse source code using the LL(1) table-driven parser.
    
    Args:
        source: Source code to parse
        
    Returns:
        Tuple of (tree, errors) where:
        - tree: None (this parser doesn't build an AST)
        - errors: List of SyntaxError objects
    """
    from Backend.Lexical.Lexer import Lexer
    from Backend.Syntax.errors import SyntaxError
    
    # Tokenize the source
    lexer = Lexer(source)
    try:
        tokens, lex_errors = lexer.scan_tokens_collect_errors()
        if lex_errors:
            # Convert lexical errors to syntax errors
            errors = []
            for lex_error in lex_errors:
                errors.append(SyntaxError(
                    message=f"Lexical error: {lex_error}",
                    line=1,
                    column=1,
                    expected=[],
                    found="",
                    raw_message=lex_error
                ))
            return None, errors
    except Exception as e:
        errors = [SyntaxError(
            message=f"Lexical analysis failed: {str(e)}",
            line=1,
            column=1,
            expected=[],
            found="",
            raw_message=str(e)
        )]
        return None, errors
    
    # Parse tokens - try to build AST
    errors = []
    try:
        # Try to build AST (pass source code for accurate AST building)
        ast, ast_errors = parse_with_ast(tokens, source_code=source)
        
        if ast_errors:
            # If AST building had errors, fall back to validation only
            log_messages, error_messages, syntax_valid = parse(tokens, build_ast=False)
            
            if syntax_valid:
                # Syntax is valid but AST building failed
                # Return None for AST but no syntax errors
                return None, []
            else:
                # Syntax errors - convert to SyntaxError objects
                for error_msg in error_messages:
                    # Try to extract line and column from error message
                    line = 1
                    column = 1
                    expected = []
                    found = ""
                    
                    # Parse error message format: "message (Line X, Column Y)" or "(line X, col Y)"
                    import re
                    match = re.search(r'Line (\d+), Column (\d+)', error_msg)
                    if match:
                        line = int(match.group(1))
                        column = int(match.group(2))
                    # New format: "Unexpected Token: ... (line X, col Y)"
                    match = re.search(r'\(line (\d+), col (\d+)\)', error_msg)
                    if match:
                        line = int(match.group(1))
                        column = int(match.group(2))
                    
                    # Parse new format: "Unexpected Token: <token> (line X, col Y)\nExpected: <list>"
                    # Also handle simple format: "Expected Token: <token>" (for incremental typing)
                    if error_msg.startswith("Expected Token:"):
                        # Simple format for incremental typing - just show what's expected
                        unexpected_match = None  # No unexpected token in this format
                        expected_match = re.search(r'Expected Token:\s*(.+)', error_msg)
                        if expected_match:
                            expected_str = expected_match.group(1).strip()
                            # Remove quotes if present
                            expected_str = expected_str.strip("'\"")
                            expected = [expected_str]
                            found = ""  # No unexpected token, just showing what's expected
                        # Extract line/column if present in message
                        match = re.search(r'\(line (\d+), col (\d+)\)', error_msg)
                        if match:
                            line = int(match.group(1))
                            column = int(match.group(2))
                    else:
                        unexpected_match = re.search(r'Unexpected Token:\s*(.+?)(?:\s*\(line|\n|$)', error_msg)
                        expected_match = re.search(r'Expected:\s*(.+)', error_msg)
                    
                    if unexpected_match:
                        found = unexpected_match.group(1).strip()
                        # Remove angle brackets if present, but keep the token
                        if found.startswith('<') and found.endswith('>'):
                            found = found.strip('<>')
                    
                    # Prefer "Expected Token: X" format (simple one-line)
                    expected_token_match = re.search(r'Expected Token:\s*(.+)', error_msg)
                    if expected_token_match:
                        expected = [expected_token_match.group(1).strip().strip("'\"")]
                    elif expected_match:
                        expected_str = expected_match.group(1).strip()
                        if expected_str.endswith(', ...'):
                            expected_str = expected_str[:-5]
                        expected = [t.strip().strip("'\"") for t in expected_str.split(',') if t.strip()]
                    
                    # Fallback to old format parsing if new format not found
                    if not unexpected_match:
                        found_match = re.search(r"Unexpected token '([^']+)'", error_msg)
                        if not found_match:
                            found_match = re.search(r"Unexpected symbol '([^']+)'", error_msg)
                        if found_match:
                            found = found_match.group(1)
                    
                    if not expected_match:
                        # Try old format
                        old_expected_match = re.search(r'Expected Token:\s*(.+)', error_msg)
                        if old_expected_match:
                            expected_str = old_expected_match.group(1).strip()
                            if expected_str.endswith(', ...'):
                                expected_str = expected_str[:-5]
                            expected = [t.strip().strip("'\"") for t in expected_str.split(',') if t.strip()]
                        else:
                            old_expected_match = re.search(r'expected one of: (\[.*?\]|.*?)(?:\s|$)', error_msg)
                            if old_expected_match:
                                expected_str = old_expected_match.group(1).strip().strip('[]')
                                expected = [t.strip().strip("'\"") for t in expected_str.split(',') if t.strip()]
                    
                    errors.append(SyntaxError(
                        message=error_msg,
                        line=line,
                        column=column,
                        expected=expected,
                        found=found,
                        raw_message=error_msg
                    ))
                
                return None, errors
        else:
            # AST built successfully
            return ast, []
    except ParserError as e:
        # Direct ParserError - extract line and column
        line = e.line if e.line is not None else 1
        column = e.column if e.column is not None else 1
        
        # Parse new format: "Unexpected Token: <token> (line X, col Y)\nExpected: <list>"
        expected = []
        found = ""
        import re
        
        error_str = str(e)
        unexpected_match = re.search(r'Unexpected Token:\s*(.+?)(?:\s*\(line|\n|$)', error_str)
        expected_match = re.search(r'Expected:\s*(.+)', error_str)
        
        if unexpected_match:
            found = unexpected_match.group(1).strip()
            # Remove angle brackets if present
            if found.startswith('<') and found.endswith('>'):
                found = found.strip('<>')
        
        if expected_match:
            expected_str = expected_match.group(1).strip()
            # Handle "..." for truncated lists
            if expected_str.endswith(', ...'):
                expected_str = expected_str[:-5]
            # Split by comma and clean up
            expected = [t.strip().strip("'\"") for t in expected_str.split(',') if t.strip()]
        
        # Fallback to old format if new format not found
        if not unexpected_match:
            found_match = re.search(r"Unexpected token '([^']+)'", error_str)
            if not found_match:
                found_match = re.search(r"Unexpected symbol '([^']+)'", error_str)
            if found_match:
                found = found_match.group(1)
        
        if not expected_match:
            old_expected_match = re.search(r'Expected Token:\s*(.+)', error_str)
            if old_expected_match:
                expected_str = old_expected_match.group(1).strip()
                if expected_str.endswith(', ...'):
                    expected_str = expected_str[:-5]
                expected = [t.strip().strip("'\"") for t in expected_str.split(',') if t.strip()]
            else:
                old_expected_match = re.search(r'expected one of: (\[.*?\]|.*?)(?:\s|$)', error_str)
                if old_expected_match:
                    expected_str = old_expected_match.group(1).strip().strip('[]')
                    expected = [t.strip().strip("'\"") for t in expected_str.split(',') if t.strip()]
        
        errors.append(SyntaxError(
            message=str(e),
            line=line,
            column=column,
            expected=expected,
            found=found,
            raw_message=str(e)
        ))
        return None, errors
    except Exception as e:
        errors = [SyntaxError(
            message=f"Parsing failed: {str(e)}",
            line=1,
            column=1,
            expected=[],
            found="",
            raw_message=str(e)
        )]
        return None, errors


# ============================================================================
# CONTEXT-AWARE EXPECTED TOKEN FILTERING
# ============================================================================
# The `_get_context_aware_expected_set()` function builds the expected-token
# set from the current parser state (top, stack, lookahead) so error messages
# show only tokens valid in that context. It delegates to `_build_full_expected_set()`
# in the general case and applies context rules when needed, e.g.:
#
# - At EOF after closing a top-level function (top "{" and <top_decls_opt> in stack):
#   Shows program-level tokens (love, avoidant, boundaries, const, dear, etc.)
#   and does NOT show '}' (valid only after <top_decls_opt> inside a boundaries block).
#
# - After statement keywords (express, give, forever, etc.):
#   Only shows tokens that start/continue statements; does NOT show expression
#   operators (+, -, *, /, etc.) unless inside an expression.
#
# - Inside expressions:
#   Shows expression operators when appropriate and delimiters that end expressions.
#
# This makes error messages more concise and helpful by showing only tokens
# that actually lead to valid, complete statements or expressions.
# ============================================================================
