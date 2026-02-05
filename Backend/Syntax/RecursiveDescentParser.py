# Backend/Syntax/RecursiveDescentParser.py
"""
Recursive Descent Parser with AST for the L.O.V.E. language.

This is an alternative parser implementation using hand-written recursive descent
parsing instead of Lark. It produces an Abstract Syntax Tree (AST) representation
of the parsed program.
"""

from __future__ import annotations

from typing import List, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass, field
import sys

# Avoid circular import by using TYPE_CHECKING
if TYPE_CHECKING:
    from Backend.Lexical.Lexer import Token, Lexer


# =============================================================================
# AST NODE CLASSES
# =============================================================================

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 1
    column: int = 1


# =============================================================================
# Program Structure
# =============================================================================

@dataclass
class Program(ASTNode):
    """Root node: boundaries_opt global_declaration sub_func love() { body_func }"""
    namespace: Optional[Namespace] = None
    global_declarations: List[Declaration] = field(default_factory=list)
    sub_functions: List[Function] = field(default_factory=list)
    main_function: MainFunction = None


@dataclass
class Namespace(ASTNode):
    """Namespace: boundaries id { ... }"""
    name: str = ""
    global_declarations: List[Declaration] = field(default_factory=list)
    sub_functions: List[Function] = field(default_factory=list)


@dataclass
class MainFunction(ASTNode):
    """Main function: love() { body_func }"""
    body: FunctionBody = None


# =============================================================================
# Declarations
# =============================================================================

@dataclass
class Declaration(ASTNode):
    """Variable declaration: data_type id [array_decl] [= expr] [multi_decl];"""
    data_type: str = ""  # "dear", "dearest", "rant", "status"
    identifier: str = ""
    array_dimensions: int = 0  # Number of [] pairs
    initial_value: Optional[Expression] = None
    is_const: bool = False
    multi_declarations: List[MultiDeclaration] = field(default_factory=list)


@dataclass
class MultiDeclaration(ASTNode):
    """Multiple declarations: , id [array_decl] [= expr]"""
    identifier: str = ""
    array_dimensions: int = 0
    initial_value: Optional[Expression] = None


# =============================================================================
# Functions
# =============================================================================

@dataclass
class Function(ASTNode):
    """Function: return_type id (parameters) { body_func }"""
    return_type: Optional[str] = None  # None for "avoidant" (void)
    name: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    body: FunctionBody = None


@dataclass
class Parameter(ASTNode):
    """Function parameter: data_type id [array_decl]"""
    data_type: str = ""
    identifier: str = ""
    array_dimensions: int = 0


@dataclass
class FunctionBody(ASTNode):
    """Function body: local_decl_list statements"""
    local_declarations: List[Declaration] = field(default_factory=list)
    statements: List[Statement] = field(default_factory=list)


# =============================================================================
# Statements
# =============================================================================

@dataclass
class Statement(ASTNode):
    """Base class for all statements."""
    pass


@dataclass
class AssignmentStatement(Statement):
    """Assignment: id [index_array] assign_op expr;"""
    identifier: str = ""
    array_indices: List[Expression] = field(default_factory=list)
    operator: str = "="  # "=", "+=", "-=", "*=", "/=", "%="
    value: Expression = None


@dataclass
class FunctionCallStatement(Statement):
    """Function call: id [::id] (arguments);"""
    identifier: str = ""
    namespace: Optional[str] = None
    arguments: List[Expression] = field(default_factory=list)


@dataclass
class UnaryStatement(Statement):
    """Unary operation: ++id; or --id; or id++; or id--;"""
    operator: str = ""  # "++" or "--"
    identifier: str = ""
    is_prefix: bool = True  # True for ++x, False for x++


@dataclass
class InputStatement(Statement):
    """Input: give >> id; or overshare(id);"""
    method: str = ""  # "give" or "overshare"
    identifier: str = ""


@dataclass
class OutputStatement(Statement):
    """Output: express << value [<< value ...] [<< periodt];"""
    values: List[Union[Expression, str]] = field(default_factory=list)  # str for "periodt"


@dataclass
class ReturnStatement(Statement):
    """Return: comeback [expr];"""
    value: Optional[Expression] = None


@dataclass
class IfStatement(Statement):
    """If: forever (expr) { body } [forevermore ...] [more { body }]"""
    condition: Expression = None
    then_body: FunctionBody = None
    elif_clauses: List[ElifClause] = field(default_factory=list)
    else_body: Optional[FunctionBody] = None


@dataclass
class ElifClause(ASTNode):
    """Else-if: forevermore (expr) { body }"""
    condition: Expression = None
    body: FunctionBody = None


@dataclass
class WhileStatement(Statement):
    """While: while (expr) { body }"""
    condition: Expression = None
    body: FunctionBody = None


@dataclass
class DoWhileStatement(Statement):
    """Do-while: pursue (expr) { body }"""
    condition: Expression = None
    body: FunctionBody = None


@dataclass
class ForStatement(Statement):
    """For: for (init; condition; update) { body }"""
    init: Optional[ForInit] = None
    condition: Optional[Expression] = None
    update: Optional[ForUpdate] = None
    body: FunctionBody = None


@dataclass
class ForInit(ASTNode):
    """For initialization: [data_type] id = expr"""
    data_type: Optional[str] = None
    identifier: str = ""
    value: Expression = None


@dataclass
class ForUpdate(ASTNode):
    """For update: id assign_op expr | id unary_op | unary_op id"""
    identifier: str = ""
    operator: str = ""  # "=", "+=", "-=", "*=", "/=", "%=", "++", "--"
    value: Optional[Expression] = None  # None for unary operations
    is_prefix: bool = True  # For unary operations


@dataclass
class SwitchStatement(Statement):
    """Switch: choose (expr) { phase ... [bareminimum ...] }"""
    expression: Expression = None
    cases: List[CaseClause] = field(default_factory=list)
    default_case: Optional[FunctionBody] = None


@dataclass
class CaseClause(ASTNode):
    """Case: phase const : body breakup;"""
    value: Union[int, float, str] = None  # Literal value
    body: FunctionBody = None


# =============================================================================
# Expressions
# =============================================================================

@dataclass
class Expression(ASTNode):
    """Base class for all expressions."""
    pass


@dataclass
class BinaryExpression(Expression):
    """Binary operation: left op right"""
    operator: str = ""
    left: Expression = None
    right: Expression = None


@dataclass
class UnaryExpression(Expression):
    """Unary operation: op expr"""
    operator: str = ""
    operand: Expression = None


@dataclass
class IdentifierExpression(Expression):
    """Identifier: id [index_array]"""
    name: str = ""
    array_indices: List[Expression] = field(default_factory=list)


@dataclass
class FunctionCallExpression(Expression):
    """Function call in expression: id [::id] (arguments)"""
    identifier: str = ""
    namespace: Optional[str] = None
    arguments: List[Expression] = field(default_factory=list)


@dataclass
class LiteralExpression(Expression):
    """Literal: int, float, string, or bool"""
    value: Union[int, float, str, bool] = None
    literal_type: str = ""  # "int", "float", "string", "bool"


@dataclass
class ParenthesizedExpression(Expression):
    """Parenthesized: (expr)"""
    expression: Expression = None


# =============================================================================
# RECURSIVE DESCENT PARSER
# =============================================================================

class ParseError(Exception):
    """Exception raised when parsing fails."""
    def __init__(self, message: str, token: Optional["Token"] = None):
        super().__init__(message)
        self.message = message
        self.token = token
        self.line = token.line if token else 1
        self.column = token.column if token else 1


class RecursiveDescentParser:
    """
    Hand-written Recursive Descent Parser for L.O.V.E. language.
    
    The grammar is designed for LL(1) parsing with right-recursion for expressions.
    """
    
    # Keywords that can start statements
    STATEMENT_KEYWORDS = {
        "give", "overshare", "express", "forever", "while", 
        "pursue", "for", "comeback", "choose"
    }
    
    # All language keywords for typo detection
    ALL_KEYWORDS = {
        "love", "boundaries", "const", "avoidant", "comeback",
        "dear", "dearest", "rant", "status", "forever", "forevermore",
        "more", "choose", "phase", "bareminimum", "for", "while",
        "pursue", "breakup", "give", "express", "overshare", "periodt",
        "greenflag", "redflag", "moveon"
    }
    
    # Maximum iterations for error recovery to prevent infinite loops
    MAX_RECOVERY_ITERATIONS = 1000
    
    def __init__(self, lexer: "Lexer"):
        """
        Initialize parser with a lexer.
        
        Args:
            lexer: Lexer instance that produces tokens
        """
        # Import here to avoid circular dependency
        from Backend.Lexical.Lexer import Token, Lexer as LexerType
        self.lexer = lexer
        self.tokens: List["Token"] = []
        self.current_index = 0
        self.errors: List[ParseError] = []
    
    def parse(self) -> Program:
        """
        Parse the program and return the AST.
        
        Returns:
            Program AST node
            
        Raises:
            ParseError: If parsing fails
        """
        # Import here to avoid circular dependency
        from Backend.Lexical.Lexer import Token
        
        # Tokenize the entire source
        self.tokens = []
        try:
            self.tokens = self.lexer.scan_tokens()
        except Exception as e:
            raise ParseError(f"Lexical error: {e}")
        
        # Filter out NEWLINE tokens (like Lark's custom lexer does)
        # But keep them for now to help with debugging - we'll skip them during parsing
        # Actually, let's keep them but skip them in parsing methods
        
        # Ensure EOF token exists
        if not self.tokens or self.tokens[-1].kind != "EOF":
            eof_token = Token(kind="EOF", lexeme="", line=self.tokens[-1].line if self.tokens else 1, column=1)
            self.tokens.append(eof_token)
        
        self.current_index = 0
        self.errors = []
        
        # Skip any leading whitespace
        self._skip_whitespace()
        
        # Parse program
        program = self._parse_program()
        
        # Check for errors
        if self.errors:
            error_msg = "\n".join([f"Line {e.line}:{e.column} - {e.message}" for e in self.errors])
            raise ParseError(f"Parse errors:\n{error_msg}")
        
        return program
    
    def parse_with_recovery(self) -> tuple[Optional[Program], List[ParseError]]:
        """
        Parse the program with error recovery to collect multiple errors.
        
        Returns:
            Tuple of (program, errors) where program may be None if parsing failed,
            and errors is a list of all ParseError objects found.
        """
        # Import here to avoid circular dependency
        from Backend.Lexical.Lexer import Token
        
        # Tokenize the entire source
        self.tokens = []
        try:
            self.tokens = self.lexer.scan_tokens()
        except Exception as e:
            error = ParseError(f"Lexical error: {e}", None)
            return None, [error]
        
        # Ensure EOF token exists
        if not self.tokens or self.tokens[-1].kind != "EOF":
            eof_token = Token(kind="EOF", lexeme="", line=self.tokens[-1].line if self.tokens else 1, column=1)
            self.tokens.append(eof_token)
        
        self.current_index = 0
        self.errors = []
        
        # Skip any leading whitespace
        self._skip_whitespace()
        
        # Try to parse with recovery
        program = None
        try:
            program = self._parse_program_with_recovery()
        except ParseError:
            # ParseError is already handled and added to self.errors
            # Re-raise to let recovery mechanism handle it
            raise
        except (AttributeError, KeyError, IndexError, TypeError) as e:
            # Common parser errors that should be caught and reported
            error = ParseError(
                f"Internal parser error: {type(e).__name__}: {e}",
                self._current_token()
            )
            self.errors.append(error)
        except Exception as e:
            # Unexpected critical errors - re-raise to avoid hiding bugs
            raise
        
        # Debug: Print errors collected
        if len(self.errors) > 0:
            print(f"[DEBUG parse_with_recovery] Collected {len(self.errors)} errors:", file=sys.stderr)
            for i, err in enumerate(self.errors, 1):
                print(f"  Error {i}: Line {err.line}:{err.column} - {err.message[:80]}", file=sys.stderr)
        
        return program, self.errors
    
    # =========================================================================
    # Token Management
    # =========================================================================
    
    def _current_token(self) -> Optional["Token"]:
        """Get current token."""
        if self.current_index < len(self.tokens):
            return self.tokens[self.current_index]
        return None
    
    def _peek_token(self, offset: int = 1) -> Optional["Token"]:
        """Peek at token ahead."""
        idx = self.current_index + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None
    
    def _advance(self) -> Optional["Token"]:
        """Advance to next token."""
        if self.current_index < len(self.tokens):
            self.current_index += 1
        return self._current_token()
    
    def _match(self, expected_kind: str) -> bool:
        """Check if current token matches expected kind."""
        token = self._current_token()
        if token and token.kind == expected_kind:
            return True
        return False
    
    def _find_similar_keyword(self, word: str, max_distance: int = 2) -> Optional[str]:
        """
        Find a keyword similar to the given word (for typo detection).
        Uses Levenshtein distance.
        
        Args:
            word: The word to find similar keywords for
            max_distance: Maximum edit distance to consider
            
        Returns:
            The most similar keyword, or None if none found
        """
        word_lower = word.lower()
        
        # Exact match
        if word_lower in self.ALL_KEYWORDS:
            return word_lower
        
        # Calculate Levenshtein distance
        def levenshtein(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein(s2, s1)
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            return previous_row[-1]
        
        best_match = None
        best_distance = max_distance + 1
        
        for keyword in self.ALL_KEYWORDS:
            distance = levenshtein(word_lower, keyword)
            if distance < best_distance:
                best_distance = distance
                best_match = keyword
        
        return best_match if best_match else None
    
    def _consume(self, expected_kind: str, error_msg: Optional[str] = None, context: Optional[str] = None, recover: bool = False) -> Optional["Token"]:
        """
        Consume token of expected kind with enhanced error messages.
        
        Args:
            expected_kind: Expected token kind
            error_msg: Custom error message
            context: Context about what we're parsing (e.g., "statement", "expression", "declaration")
            recover: If True, record error and return None instead of raising (for error recovery)
            
        Returns:
            The consumed token, or None if recover=True and token doesn't match
            
        Raises:
            ParseError: If token doesn't match and recover=False
        """
        token = self._current_token()
        if not token:
            msg = error_msg or f"Unexpected end of input, expected {expected_kind}"
            error = ParseError(msg, self.tokens[-1] if self.tokens else None)
            if recover:
                self.errors.append(error)
                return None
            raise error
        
        if token.kind == expected_kind:
            self._advance()
            return token
        
        # Build enhanced error message
        found_lexeme = token.lexeme
        found_kind = token.kind
        
        # If we found an identifier that looks like a keyword typo
        suggestion = None
        if found_kind == "id" and found_lexeme:
            suggestion = self._find_similar_keyword(found_lexeme)
        
        # Build the error message
        if error_msg:
            msg = error_msg
        else:
            # Create a user-friendly message
            possible_terminals = []
            if context:
                # Get all possible terminals based on CFG structure
                possible_terminals = self._get_all_possible_terminals(context)
                if possible_terminals:
                    # Format the possible terminals nicely
                    terminal_names = [self._format_expected_token(t).strip("'") for t in possible_terminals]
                    terminals_str = ", ".join(terminal_names)
                    msg = f"Unexpected token '{found_lexeme}' while parsing {context}. Expected one of: {terminals_str}"
                else:
                    # Fallback to CFG suggestion
                    context_suggestion = self._get_cfg_suggestion(context, expected_kind)
                    if context_suggestion:
                        msg = f"Unexpected token '{found_lexeme}' while parsing {context}. {context_suggestion}"
                    else:
                        msg = f"Unexpected token '{found_lexeme}' while parsing {context}"
            else:
                msg = f"Unexpected token '{found_lexeme}'"
            
            # Add what was expected (if not already included in possible_terminals list)
            if not possible_terminals:
                expected_display = self._format_expected_token(expected_kind)
                msg += f". Expected {expected_display}"
            
            # Add suggestion if we found a similar keyword
            if suggestion and suggestion != found_lexeme.lower():
                msg += f". Did you mean '{suggestion}'?"
        
        error = ParseError(msg, token)
        self.errors.append(error)
        
        if recover:
            return None
        raise error
    
    def _get_cfg_suggestion(self, context: str, expected_kind: str) -> Optional[str]:
        """
        Suggest all possible terminals that can come next based on CFG structure.
        
        Args:
            context: Current parsing context (e.g., "output statement", "after <<", "id_suffix")
            expected_kind: The expected token kind
            
        Returns:
            A suggestion string listing all possible terminals, or None
        """
        context_lower = context.lower()
        
        # After << in output statement: can be <expr> or periodt (Rule 71, 72)
        if "after <<" in context_lower or ("output" in context_lower and expected_kind in ["periodt", "id", "LPAREN", "dear_lit", "dearest_lit", "rant_lit", "greenflag", "redflag"]):
            return "Expected an expression or 'periodt'"
        
        # After express: must be << (Rule 68)
        if "output statement" in context_lower and expected_kind == "OP_LSHIFT":
            return "Expected '<<' (output operator)"
        
        # After identifier in statement: can be various things (Rule 48-51)
        if "id_suffix" in context_lower or ("statement" in context_lower and expected_kind in ["LPAREN", "ASSIGN", "OP_PLUS_ASSIGN", "OP_MINUS_ASSIGN", "OP_MUL_ASSIGN", "OP_DIV_ASSIGN", "OP_MOD_ASSIGN", "OP_INC", "OP_DEC", "LBRACKET", "SEMICOLON"]):
            return "Expected '(', '=', '+=', '-=', '*=', '/=', '%=', '++', '--', '[', or ';'"
        
        # After identifier in function call: can be arguments or empty (Rule 50)
        if "arguments" in context_lower or (expected_kind == "RPAREN" and self._peek_token(-1) and self._peek_token(-1).kind == "LPAREN"):
            return "Expected an expression or ')'"
        
        # In expression: can be various terminals (Rule 74-106)
        if "expression" in context_lower:
            return "Expected an expression (identifier, literal, '(', or function call)"
        
        # After data type in declaration: must be identifier (Rule 9, 37)
        if "declaration" in context_lower and expected_kind == "id":
            return "Expected an identifier"
        
        # After identifier in declaration: can be array_decl, =, or ; (Rule 9)
        if "declaration" in context_lower and expected_kind in ["LBRACKET", "ASSIGN", "SEMICOLON"]:
            return "Expected '[', '=', or ';'"
        
        # In statement list: can be various statements (Rule 38-46)
        if "statement" in context_lower and "id_suffix" not in context_lower:
            return "Expected a statement (express, give, overshare, forever, while, pursue, for, comeback, choose, identifier, or unary operator)"
        
        # In declaration: can be data types (Rule 24-27)
        if "declaration" in context_lower and expected_kind in ["dear", "dearest", "rant", "status"]:
            return "Expected a data type (dear, dearest, rant, or status)"
        
        return None
    
    def _get_all_possible_terminals(self, context: str) -> List[str]:
        """
        Get all possible terminal tokens that can come next based on CFG structure.
        
        Args:
            context: Current parsing context/state
            
        Returns:
            List of possible terminal token kinds
        """
        context_lower = context.lower()
        possible = []
        
        # After << in output: expr or periodt (Rule 71, 72)
        if "after <<" in context_lower or ("output" in context_lower and "after" in context_lower):
            possible.extend(["periodt", "id", "LPAREN", "dear_lit", "dearest_lit", "rant_lit", "greenflag", "redflag", "MINUS", "NOT"])
            return possible
        
        # After express: must be <<
        if "output statement" in context_lower and "after express" in context_lower:
            return ["OP_LSHIFT"]
        
        # After identifier in statement: id_suffix options (Rule 48-51)
        if "id_suffix" in context_lower or ("statement" in context_lower and "after id" in context_lower):
            possible.extend(["LPAREN", "ASSIGN", "OP_PLUS_ASSIGN", "OP_MINUS_ASSIGN", "OP_MUL_ASSIGN", 
                           "OP_DIV_ASSIGN", "OP_MOD_ASSIGN", "OP_INC", "OP_DEC", "LBRACKET", "SEMICOLON"])
            return possible
        
        # In expression: can start with various terminals
        if "expression" in context_lower:
            possible.extend(["id", "LPAREN", "dear_lit", "dearest_lit", "rant_lit", "greenflag", "redflag", "MINUS", "NOT"])
            return possible
        
        # After data type: identifier
        if "declaration" in context_lower and "after data_type" in context_lower:
            return ["id"]
        
        # In statement list
        if "statement" in context_lower:
            possible.extend(["express", "give", "overshare", "forever", "while", "pursue", "for", 
                           "comeback", "choose", "id", "OP_INC", "OP_DEC"])
            return possible
        
        return possible
    
    def _find_sync_point(self) -> bool:
        """
        Find synchronization point after an error (panic mode recovery).
        Skips tokens until we find a safe point to resume parsing.
        
        Returns:
            True if sync point found, False if we've reached EOF
        """
        # Sync points: semicolon, closing brace, keywords that start statements
        sync_tokens = {"SEMICOLON", "RBRACE", "LBRACE"}
        sync_keywords = {"love", "give", "overshare", "express", "forever", "while", 
                        "pursue", "for", "comeback", "choose", "dear", "dearest", 
                        "rant", "status", "avoidant"}
        
        while self._current_token() and self._current_token().kind != "EOF":
            token = self._current_token()
            
            # Check for sync tokens
            if token.kind in sync_tokens:
                # Found a sync point - don't consume it, let the caller handle it
                return True
            
            # Check for sync keywords
            if token.kind in sync_keywords or (token.kind == "id" and token.lexeme.lower() in sync_keywords):
                return True
            
            # Skip this token
            self._advance()
            self._skip_whitespace()
        
        return False
    
    def _analyze_brace_balance(self, start_index: Optional[int] = None) -> dict:
        """
        Analyze brace and parenthesis balance from current position (or start_index) to end.
        
        Returns a dictionary with:
        - brace_depth: net brace depth (positive = more opening braces)
        - paren_depth: net parenthesis depth
        - bracket_depth: net bracket depth
        - has_closing_brace: True if there's a closing brace that could match
        - has_closing_paren: True if there's a closing paren that could match
        
        Args:
            start_index: Optional starting token index (defaults to current_index)
            
        Returns:
            Dictionary with balance information
        """
        if start_index is None:
            start_index = self.current_index
        
        brace_depth = 0
        paren_depth = 0
        bracket_depth = 0
        has_closing_brace = False
        has_closing_paren = False
        has_closing_bracket = False
        
        # Look ahead from start_index
        for i in range(start_index, len(self.tokens)):
            token = self.tokens[i]
            if token.kind == "EOF":
                break
            
            if token.kind == "LBRACE":
                brace_depth += 1
            elif token.kind == "RBRACE":
                brace_depth -= 1
                if brace_depth == 0:
                    has_closing_brace = True
            elif token.kind == "LPAREN":
                paren_depth += 1
            elif token.kind == "RPAREN":
                paren_depth -= 1
                if paren_depth == 0:
                    has_closing_paren = True
            elif token.kind == "LBRACKET":
                bracket_depth += 1
            elif token.kind == "RBRACKET":
                bracket_depth -= 1
                if bracket_depth == 0:
                    has_closing_bracket = True
        
        return {
            "brace_depth": brace_depth,
            "paren_depth": paren_depth,
            "bracket_depth": bracket_depth,
            "has_closing_brace": has_closing_brace or brace_depth <= 0,
            "has_closing_paren": has_closing_paren or paren_depth <= 0,
            "has_closing_bracket": has_closing_bracket or bracket_depth <= 0,
            "unbalanced_braces": brace_depth > 0,
            "unbalanced_parens": paren_depth > 0,
            "unbalanced_brackets": bracket_depth > 0
        }
    
    def _find_matching_closing_brace(self, start_index: Optional[int] = None) -> Optional[int]:
        """
        Find the index of the matching closing brace for the brace at start_index.
        Uses brace depth tracking to find the matching brace.
        
        Args:
            start_index: Index of opening brace token (defaults to current_index)
            
        Returns:
            Index of matching closing brace, or None if not found
        """
        if start_index is None:
            start_index = self.current_index
        
        # If current token is not LBRACE, look for it
        if start_index < len(self.tokens) and self.tokens[start_index].kind != "LBRACE":
            # Look forward for next LBRACE
            for i in range(start_index, len(self.tokens)):
                if self.tokens[i].kind == "LBRACE":
                    start_index = i
                    break
            else:
                return None
        
        if start_index >= len(self.tokens) or self.tokens[start_index].kind != "LBRACE":
            return None
        
        # Track depth to find matching closing brace
        depth = 1
        for i in range(start_index + 1, len(self.tokens)):
            token = self.tokens[i]
            if token.kind == "LBRACE":
                depth += 1
            elif token.kind == "RBRACE":
                depth -= 1
                if depth == 0:
                    return i
            elif token.kind == "EOF":
                break
        
        return None
    
    def _format_expected_token(self, token_kind: str) -> str:
        """Format expected token kind for display."""
        # Map token kinds to readable names
        token_display = {
            "id": "an identifier",
            "express": "'express'",
            "give": "'give'",
            "overshare": "'overshare'",
            "forever": "'forever'",
            "while": "'while'",
            "for": "'for'",
            "pursue": "'pursue'",
            "comeback": "'comeback'",
            "choose": "'choose'",
            "periodt": "'periodt'",
            "LPAREN": "'('",
            "RPAREN": "')'",
            "LBRACE": "'{'",
            "RBRACE": "'}'",
            "LBRACKET": "'['",
            "RBRACKET": "']'",
            "SEMICOLON": "';'",
            "COMMA": "','",
            "ASSIGN": "'='",
            "dear_lit": "an integer literal",
            "dearest_lit": "a float literal",
            "rant_lit": "a string literal",
            "greenflag": "'greenflag'",
            "redflag": "'redflag'",
            "MINUS": "'-'",
            "NOT": "'!'",
            "OP_LSHIFT": "'<<'",
            "OP_PLUS_ASSIGN": "'+='",
            "OP_MINUS_ASSIGN": "'-='",
            "OP_MUL_ASSIGN": "'*='",
            "OP_DIV_ASSIGN": "'/='",
            "OP_MOD_ASSIGN": "'%='",
            "OP_INC": "'++'",
            "OP_DEC": "'--'",
        }
        return token_display.get(token_kind, f"'{token_kind}'")
    
    def _consume_optional(self, expected_kind: str) -> Optional["Token"]:
        """Try to consume token, return None if not found."""
        if self._match(expected_kind):
            return self._consume(expected_kind)
        return None
    
    def _skip_whitespace(self):
        """Skip NEWLINE and other whitespace tokens."""
        while self._match("NEWLINE"):
            self._advance()
    
    # =========================================================================
    # Program Structure
    # =========================================================================
    
    def _parse_program(self) -> Program:
        """Parse: boundaries_opt global_declaration sub_func love() { body_func }"""
        line = self._current_token().line if self._current_token() else 1
        col = self._current_token().column if self._current_token() else 1
        
        # Parse optional namespace
        namespace = self._parse_namespace()
        
        # Parse global declarations
        global_decls = []
        while self._match("dear") or self._match("dearest") or self._match("rant") or \
              self._match("status") or self._match("const"):
            global_decls.append(self._parse_declaration())
        
        # Parse sub functions
        sub_funcs = []
        while self._match("dear") or self._match("dearest") or self._match("rant") or \
              self._match("status") or self._match("avoidant"):
            sub_funcs.append(self._parse_sub_function())
        
        # Parse main function
        self._consume("love", "Expected 'love' keyword for main function")
        
        # Check if structure is incomplete and provide helpful suggestion
        if not self._match("LPAREN"):
            next_token = self._current_token()
            if next_token:
                msg = f"Expected '(' after 'love'. Complete structure: love () {{ ... }}"
            else:
                msg = "Expected '(' after 'love'. Complete structure: love () { ... }"
            error = ParseError(msg, next_token)
            self.errors.append(error)
            raise error
        
        self._consume("LPAREN", context="main function after love")
        
        if not self._match("RPAREN"):
            next_token = self._current_token()
            msg = f"Expected ')' after '('. Complete structure: love () {{ ... }}"
            error = ParseError(msg, next_token)
            self.errors.append(error)
            raise error
        
        self._consume("RPAREN", context="main function")
        self._skip_whitespace()  # Skip whitespace after )
        
        if not self._match("LBRACE"):
            next_token = self._current_token()
            if next_token and next_token.kind != "EOF":
                msg = f"Expected '{{' after 'love ()'. Found '{next_token.lexeme}' instead. Complete structure: love () {{ ... }}"
            else:
                msg = "Expected '{' after 'love ()'. Complete structure: love () { ... }"
            error = ParseError(msg, next_token)
            self.errors.append(error)
            raise error
        
        self._consume("LBRACE", context="main function")
        self._skip_whitespace()  # Skip newlines after opening brace
        
        # Store the position of the opening brace for better error messages
        # Find the LBRACE token we just consumed
        opening_brace_index = None
        for i in range(self.current_index - 1, -1, -1):
            if i < len(self.tokens) and self.tokens[i].kind == "LBRACE":
                opening_brace_index = i
                break
        
        # Try to parse function body - use recovery if there are errors
        try:
            main_body = self._parse_function_body()
        except ParseError:
            # If there were errors in the body, use recovery mode
            # This helps prevent false "missing closing brace" errors
            main_body = self._parse_function_body_with_recovery()
            # Don't raise - continue to check for closing brace
            # After recovery, make sure we advance past any remaining tokens
            # to reach the closing brace if it exists
            self._skip_whitespace()
        
        # Check for missing closing brace with improved detection
        # First, try to find the matching closing brace even if we're not at it
        matching_brace_idx = None
        if opening_brace_index is not None:
            matching_brace_idx = self._find_matching_closing_brace(opening_brace_index)
        
        # Check if we already have errors about structural issues
        has_structural_errors = any(
            "expression" in e.message.lower() or 
            "unexpected token" in e.message.lower() or
            ("expected" in e.message.lower() and "brace" not in e.message.lower() and "parenthesis" not in e.message.lower())
            for e in self.errors
        )
        
        # Check current position first
        if self._match("RBRACE"):
            # We're already at the closing brace - consume it normally
            self._consume("RBRACE", context="main function")
        elif matching_brace_idx is not None:
            # Found matching brace ahead - advance to it and consume it
            # This handles cases where parser is at wrong position after errors
            if self.current_index < matching_brace_idx:
                # We're before the brace - advance to it
                self.current_index = matching_brace_idx
                # Now we should be at the brace
                if self._match("RBRACE"):
                    self._consume("RBRACE", context="main function")
                else:
                    # Something went wrong - brace should be here
                    # Don't report error if we have structural errors (cascading)
                    if not has_structural_errors:
                        next_token = self._current_token()
                        msg = f"Expected '}}' to close 'love () {{' function. Found '{next_token.lexeme if next_token else 'end of input'}' instead. Complete structure: love () {{ ... }}"
                        error = ParseError(msg, next_token)
                        self.errors.append(error)
                        raise error
        elif not self._match("RBRACE"):
            # No matching brace found AND not at current position
            # This is a real missing brace error
            next_token = self._current_token()
            
            # Only report if we don't have structural errors (to avoid cascading)
            if not has_structural_errors:
                if next_token and next_token.kind != "EOF":
                    msg = f"Expected '}}' to close 'love () {{' function. Found '{next_token.lexeme}' instead. Complete structure: love () {{ ... }}"
                else:
                    msg = "Expected '}' to close 'love () {' function. Reached end of input. Complete structure: love () { ... }"
                error = ParseError(msg, next_token)
                self.errors.append(error)
                raise error
            # Otherwise, don't report (likely cascading from structural error)
            # Return what we have so far
            return Program(
                namespace=namespace,
                global_declarations=global_decls,
                sub_functions=sub_funcs,
                main_function=main_func,
                line=line,
                column=col
            )
        else:
            # Normal case - brace is there, consume it
            self._consume("RBRACE", context="main function")
        
        main_func = MainFunction(body=main_body, line=line, column=col)
        
        return Program(
            namespace=namespace,
            global_declarations=global_decls,
            sub_functions=sub_funcs,
            main_function=main_func,
            line=line,
            column=col
        )
    
    def _parse_program_with_recovery(self) -> Optional[Program]:
        """
        Parse program with error recovery to collect multiple errors.
        """
        line = self._current_token().line if self._current_token() else 1
        col = self._current_token().column if self._current_token() else 1
        
        # Parse optional namespace (with recovery)
        namespace = None
        try:
            namespace = self._parse_namespace()
        except ParseError:
            # Error already recorded, try to recover
            self._find_sync_point()
        
        # Parse global declarations (with recovery)
        global_decls = []
        while not self._match("EOF"):
            self._skip_whitespace()
            if self._match("dear") or self._match("dearest") or self._match("rant") or \
               self._match("status") or self._match("const"):
                try:
                    global_decls.append(self._parse_declaration())
                except ParseError:
                    # Error recorded, skip to next declaration or function
                    if not self._find_sync_point():
                        break
            elif self._match("dear") or self._match("dearest") or self._match("rant") or \
                 self._match("status") or self._match("avoidant") or self._match("love"):
                # Start of function or main - break
                break
            else:
                break
        
        # Parse sub functions (with recovery)
        sub_funcs = []
        while not self._match("EOF"):
            self._skip_whitespace()
            if self._match("dear") or self._match("dearest") or self._match("rant") or \
               self._match("status") or self._match("avoidant"):
                try:
                    sub_funcs.append(self._parse_sub_function())
                except ParseError:
                    # Error recorded, skip to next function or main
                    if not self._find_sync_point():
                        break
            elif self._match("love"):
                # Start of main function - break
                break
            else:
                break
        
        # Parse main function (with recovery)
        main_func = None
        try:
            # Try to consume "love" - check for typo first
            if self._match("id"):
                # Might be a typo for "love"
                suggestion = self._find_similar_keyword(self._current_token().lexeme)
                if suggestion == "love":
                    # It's a typo - record error and continue
                    token = self._current_token()
                    msg = f"Unexpected identifier '{token.lexeme}'. Did you mean 'love'?"
                    error = ParseError(msg, token)
                    self.errors.append(error)
                    self._advance()  # Skip the typo
                elif not self._match("love"):
                    # Not love and not a typo - record error and try to recover
                    token = self._current_token()
                    msg = f"Expected 'love' keyword for main function, found '{token.lexeme}'"
                    error = ParseError(msg, token)
                    self.errors.append(error)
                    if not self._find_sync_point():
                        return None
            elif not self._match("love"):
                # Expected love but didn't find it
                token = self._current_token()
                if token:
                    msg = f"Expected 'love' keyword for main function, found '{token.lexeme}'"
                    error = ParseError(msg, token)
                    self.errors.append(error)
                if not self._find_sync_point():
                    return None
            
            # Consume love if we have it
            if self._match("love"):
                self._consume("love")
                
                # Check if structure is incomplete and provide helpful suggestion
                self._skip_whitespace()
                if not self._match("LPAREN"):
                    next_token = self._current_token()
                    if next_token and next_token.kind != "EOF":
                        msg = f"Expected '(' after 'love'. Complete structure: love () {{ ... }}"
                    else:
                        msg = "Expected '(' after 'love'. Complete structure: love () { ... }"
                    error = ParseError(msg, next_token)
                    self.errors.append(error)
                    # Don't raise - let recovery continue
            
            # Try to parse main function structure - use recovery mode
            # After detecting typo for "love", we should still try to parse the function
            # Skip whitespace in case there are newlines
            self._skip_whitespace()
            
            # Debug: Check what token we're at after skipping "loe"
            current = self._current_token()
            if current:
                print(f"[DEBUG _parse_program_with_recovery] After 'loe' typo, current token: {current.kind} '{current.lexeme}' (line {current.line})", file=sys.stderr)
            
            # Try to parse () { } structure - use try/except for each part
            if self._match("LPAREN"):
                print(f"[DEBUG _parse_program_with_recovery] Found LPAREN, continuing to parse function", file=sys.stderr)
                try:
                    self._consume("LPAREN")
                except ParseError:
                    # Error recorded, try to continue anyway
                    pass
                
                self._skip_whitespace()
                try:
                    self._consume("RPAREN")
                except ParseError:
                    # Error recorded, try to continue
                    pass
                
                self._skip_whitespace()
                if self._match("LBRACE"):
                    print(f"[DEBUG _parse_program_with_recovery] Found LBRACE, entering function body", file=sys.stderr)
                    try:
                        self._consume("LBRACE")
                        self._skip_whitespace()
                        # Parse function body with recovery (this will collect multiple errors)
                        # This is the key - it should detect expess error here
                        # Even if there are errors, we want to continue parsing to find more
                        main_body = self._parse_function_body_with_recovery()
                        self._skip_whitespace()
                        if self._match("RBRACE"):
                            try:
                                self._consume("RBRACE")
                                main_func = MainFunction(body=main_body, line=line, column=col)
                            except ParseError:
                                # Error recorded, but we still have the body
                                main_func = MainFunction(body=main_body, line=line, column=col)
                        else:
                            # Missing closing brace for main function
                            next_token = self._current_token()
                            if next_token and next_token.kind != "EOF":
                                msg = f"Expected '}}' to close 'love () {{' function. Found '{next_token.lexeme}' instead"
                            else:
                                msg = "Expected '}' to close 'love () {' function. Reached end of input"
                            error = ParseError(msg, next_token)
                            self.errors.append(error)
                            # Still create the function with the body we parsed
                            main_func = MainFunction(body=main_body, line=line, column=col)
                    except ParseError as e:
                        # Error in function body already recorded
                        print(f"[DEBUG _parse_program_with_recovery] Exception in function body: {e}", file=sys.stderr)
                        # But we should still try to create a body if we can
                        # The errors are already in self.errors, so we can continue
                        try:
                            # Try to parse body again (errors already recorded)
                            main_body = self._parse_function_body_with_recovery()
                            main_func = MainFunction(body=main_body, line=line, column=col)
                        except:
                            # If we can't parse body at all, create empty body
                            # Errors are already recorded
                            main_body = FunctionBody(
                                local_declarations=[],
                                statements=[],
                                line=line,
                                column=col
                            )
                            main_func = MainFunction(body=main_body, line=line, column=col)
                else:
                    # Missing opening brace after love ()
                    next_token = self._current_token()
                    if next_token and next_token.kind != "EOF":
                        msg = f"Expected '{{' after 'love ()'. Found '{next_token.lexeme}' instead. Complete structure: love () {{ ... }}"
                    else:
                        msg = "Expected '{' after 'love ()'. Complete structure: love () { ... }"
                    error = ParseError(msg, next_token)
                    self.errors.append(error)
                    # Try to continue parsing anyway (might find more errors)
                    # But we can't create a proper function without the opening brace
            else:
                # No LPAREN found after love
                print(f"[DEBUG _parse_program_with_recovery] No LPAREN found after 'love'. Current token: {self._current_token().kind if self._current_token() else 'None'}", file=sys.stderr)
        except ParseError:
            # Error already recorded
            pass
        
        if main_func is None:
            return None
        
        # Check if there's unexpected code after the main function
        # (should only be EOF after love () { ... })
        self._skip_whitespace()
        next_token = self._current_token()
        if next_token and next_token.kind != "EOF":
            # There's code after the main function - this is invalid
            # Check if it looks like it should be inside the function body
            if (next_token.kind in ["dear", "dearest", "rant", "status"] or
                next_token.kind == "id" or
                next_token.kind in ["express", "give", "overshare", "forever", "while", "pursue", "for", "comeback", "choose"]):
                msg = f"Unexpected code after 'love () {{ ... }}' function. Code like '{next_token.lexeme}' should be inside the function body. Did you accidentally close the function too early?"
            else:
                msg = f"Unexpected token '{next_token.lexeme}' after 'love () {{ ... }}' function. Only EOF expected after main function."
            error = ParseError(msg, next_token)
            self.errors.append(error)
        
        return Program(
            namespace=namespace,
            global_declarations=global_decls,
            sub_functions=sub_funcs,
            main_function=main_func,
            line=line,
            column=col
        )
    
    def _parse_function_body_with_recovery(self) -> FunctionBody:
        """Parse function body with error recovery."""
        token = self._current_token()
        
        # Debug: Log entry
        if token:
            print(f"[DEBUG _parse_function_body_with_recovery] Entering function body at token: {token.kind} '{token.lexeme}' (line {token.line})", file=sys.stderr)
        
        # Parse local declarations (with recovery)
        local_decls = []
        while self._match("dear") or self._match("dearest") or \
              self._match("rant") or self._match("status"):
            try:
                local_decls.append(self._parse_local_declaration())
                self._skip_whitespace()
            except ParseError:
                # Error recorded, skip to next declaration or statement
                if not self._find_sync_point():
                    break
        
        # Parse statements (with recovery)
        statements = []
        max_iterations = self.MAX_RECOVERY_ITERATIONS
        iteration = 0
        
        # Track brace depth to know when we've reached the function body's closing brace
        # We start at depth 0 (we're inside the function body's opening brace)
        # Note: When statements parse nested blocks (like forever { ... }), they consume
        # the braces internally, so we won't see them here. But during error recovery,
        # we might skip tokens and see braces, so we need to track them.
        brace_depth = 0
        
        while not self._match("EOF") and iteration < max_iterations:
            iteration += 1
            self._skip_whitespace()
            
            # Check if we've reached the function body's closing brace
            # (only stop if brace_depth == 0, meaning we're at the top level)
            if self._match("RBRACE") and brace_depth == 0:
                break
            
            current_token = self._current_token()
            if current_token:
                print(f"[DEBUG _parse_function_body_with_recovery] Attempting to parse statement: {current_token.kind} '{current_token.lexeme}' (line {current_token.line})", file=sys.stderr)
            
            # Try to parse a statement
            # Note: When statements parse successfully (e.g., forever { ... }), they consume
            # their own braces internally, so we stay at brace_depth == 0.
            # We only need to track depth during error recovery when we skip tokens.
            try:
                stmt = self._parse_statement()
                if stmt:
                    statements.append(stmt)
                    self._skip_whitespace()
                    # After successfully parsing a statement, we're back at top level
                    # (brace_depth should still be 0, but reset it to be safe)
                    brace_depth = 0
                else:
                    # No statement could be parsed - might be an error
                    # Don't skip immediately - the error might have been recorded in _parse_statement
                    # Just advance to next token to avoid infinite loop
                    if self._current_token():
                        self._advance()
                    else:
                        break
            except ParseError as e:
                # Error already recorded in self.errors - this is good!
                print(f"[DEBUG _parse_function_body_with_recovery] Caught ParseError. Error count in self.errors: {len(self.errors)}", file=sys.stderr)
                print(f"[DEBUG _parse_function_body_with_recovery] Error message: {e.message[:60]}", file=sys.stderr)
                # Verify the error is actually in self.errors
                if len(self.errors) == 0:
                    print(f"[DEBUG _parse_function_body_with_recovery] WARNING: Error was raised but NOT in self.errors! Adding it now.", file=sys.stderr)
                    self.errors.append(e)
                
                # Check if the error is about a structural issue (expression, braces, etc.)
                # vs a missing semicolon. Don't report "missing semicolon" if error was structural.
                error_message_lower = e.message.lower()
                # Check if this is a typo error - if so, skip to sync point without generating more errors
                error_is_typo = "did you mean" in error_message_lower
                error_is_structural = (
                    "expression" in error_message_lower or
                    "unexpected token" in error_message_lower or
                    "expected" in error_message_lower and "semicolon" not in error_message_lower or
                    "brace" in error_message_lower or
                    "parenthesis" in error_message_lower or
                    "missing" in error_message_lower and "semicolon" not in error_message_lower
                )
                error_is_about_semicolon = "semicolon" in error_message_lower
                
                # Now we need to recover by skipping to the next statement
                # Look for semicolon (statement end) - this is the best sync point
                found_sync = False
                
                # Look for semicolon (statement end) - this is the best sync point
                # Track the position where we started looking (for missing semicolon error)
                sync_start_token = self._current_token()
                found_semicolon = False
                
                # Check if sync_start_token is a statement starter (doesn't need semicolon before it)
                statement_starters = {"forever", "while", "for", "pursue", "choose", "express", "give", "overshare", "comeback"}
                sync_is_statement_starter = (
                    sync_start_token and 
                    (sync_start_token.kind in statement_starters or 
                     (sync_start_token.kind == "id" and sync_start_token.lexeme.lower() in statement_starters))
                )
                
                # Track brace depth to avoid stopping at nested closing braces
                # Use the outer loop's brace_depth variable, starting from its current value
                # Since we're recovering from an error, we might be inside a nested block.
                
                # If this is a typo error, skip the typo token first to avoid generating more errors
                if error_is_typo and self._current_token() and self._current_token().kind == "id":
                    # Skip the typo identifier token
                    self._advance()
                    self._skip_whitespace()
                
                while self._current_token() and self._current_token().kind != "EOF":
                    current_token = self._current_token()
                    
                    # Track brace depth as we scan during recovery (update outer loop's brace_depth)
                    if current_token.kind == "LBRACE":
                        brace_depth += 1
                    elif current_token.kind == "RBRACE":
                        if brace_depth > 0:
                            # This is closing a nested block, continue looking
                            brace_depth -= 1
                        elif brace_depth == 0:
                            # This is the function body's closing brace - stop here
                            # Don't advance, let the outer loop handle it
                            found_sync = True
                            break
                    
                    # Look for sync points at top level (brace_depth == 0)
                    if current_token.kind == "SEMICOLON" and brace_depth == 0:
                        # Found semicolon at top level - consume it and continue to next statement
                        print(f"[DEBUG _parse_function_body_with_recovery] Found semicolon, consuming and continuing", file=sys.stderr)
                        self._advance()
                        found_sync = True
                        found_semicolon = True
                        break
                    elif current_token.kind in {"express", "give", "overshare", "forever", 
                                                "while", "pursue", "for", "comeback", "choose"} and brace_depth == 0:
                        # Found next statement keyword at top level
                        # Only report missing semicolon error if:
                        # 1. We haven't already found/reported one
                        # 2. The original error was NOT about a structural issue (expression, braces, etc.)
                        # 3. The sync_start_token is NOT a statement starter (statement starters don't need semicolons before them)
                        # 4. The original error was NOT already about a semicolon
                        # 5. The original error was NOT a typo error (prioritize typo completion first)
                        should_report_missing_semicolon = (
                            not found_semicolon and 
                            sync_start_token and 
                            not error_is_structural and 
                            not error_is_about_semicolon and
                            not sync_is_statement_starter and
                            not error_is_typo  # Don't report additional errors after typo
                        )
                        if should_report_missing_semicolon:
                            missing_semicolon_error = ParseError(
                                f"Missing semicolon. Expected ';' before '{current_token.lexeme}'",
                                sync_start_token
                            )
                            self.errors.append(missing_semicolon_error)
                            print(f"[DEBUG _parse_function_body_with_recovery] Added missing semicolon error before keyword. Total errors: {len(self.errors)}", file=sys.stderr)
                        # Stop here (don't consume, let next iteration handle it)
                        found_sync = True
                        break
                    elif current_token.kind in {"more", "forevermore"} and brace_depth == 0:
                        # These are part of a forever/forevermore chain, not new statements
                        # Skip past the entire block (more { ... } or forevermore (...) { ... })
                        # to find the end of the chain
                        if current_token.kind == "more":
                            # Skip "more" and its block
                            self._advance()  # Skip "more"
                            self._skip_whitespace()
                            if self._match("LBRACE"):
                                self._advance()  # Skip "{"
                                # Skip the body until we find the closing brace
                                block_depth = 1
                                while block_depth > 0 and self._current_token() and self._current_token().kind != "EOF":
                                    if self._current_token().kind == "LBRACE":
                                        block_depth += 1
                                    elif self._current_token().kind == "RBRACE":
                                        block_depth -= 1
                                    self._advance()
                                self._skip_whitespace()
                        elif current_token.kind == "forevermore":
                            # Skip "forevermore (expr) { ... }"
                            self._advance()  # Skip "forevermore"
                            self._skip_whitespace()
                            if self._match("LPAREN"):
                                # Skip until matching RPAREN
                                self._advance()
                                paren_depth = 1
                                while paren_depth > 0 and self._current_token() and self._current_token().kind != "EOF":
                                    if self._current_token().kind == "LPAREN":
                                        paren_depth += 1
                                    elif self._current_token().kind == "RPAREN":
                                        paren_depth -= 1
                                    self._advance()
                                self._skip_whitespace()
                                if self._match("LBRACE"):
                                    self._advance()  # Skip "{"
                                    # Skip the body until we find the closing brace
                                    block_depth = 1
                                    while block_depth > 0 and self._current_token() and self._current_token().kind != "EOF":
                                        if self._current_token().kind == "LBRACE":
                                            block_depth += 1
                                        elif self._current_token().kind == "RBRACE":
                                            block_depth -= 1
                                        self._advance()
                                    self._skip_whitespace()
                        # After skipping the block, we've finished the forever chain
                        # Continue to next iteration of outer loop (which will check for RBRACE)
                        found_sync = True
                        break
                    elif current_token.kind == "id" and brace_depth == 0:
                        # Check if this identifier might be a typo for "more" or "forevermore"
                        peek = self._peek_token()
                        if peek and (peek.kind == "LBRACE" or peek.kind == "LPAREN"):
                            suggestion = self._find_similar_keyword(current_token.lexeme)
                            if suggestion in {"more", "forevermore"}:
                                # It's a typo for "more" or "forevermore" - report error and skip
                                typo_error = ParseError(
                                    f"Unexpected identifier '{current_token.lexeme}'. Did you mean '{suggestion}'?",
                                    current_token
                                )
                                self.errors.append(typo_error)
                                # Skip the typo and its block (same logic as above)
                                self._advance()  # Skip the typo identifier
                                if suggestion == "more":
                                    # Handle as "more { ... }"
                                    if self._match("LBRACE"):
                                        self._advance()  # Skip "{"
                                        block_depth = 1
                                        while block_depth > 0 and self._current_token() and self._current_token().kind != "EOF":
                                            if self._current_token().kind == "LBRACE":
                                                block_depth += 1
                                            elif self._current_token().kind == "RBRACE":
                                                block_depth -= 1
                                            self._advance()
                                        self._skip_whitespace()
                                elif suggestion == "forevermore":
                                    # Handle as "forevermore (expr) { ... }"
                                    if self._match("LPAREN"):
                                        self._advance()
                                        paren_depth = 1
                                        while paren_depth > 0 and self._current_token() and self._current_token().kind != "EOF":
                                            if self._current_token().kind == "LPAREN":
                                                paren_depth += 1
                                            elif self._current_token().kind == "RPAREN":
                                                paren_depth -= 1
                                            self._advance()
                                        self._skip_whitespace()
                                        if self._match("LBRACE"):
                                            self._advance()
                                            block_depth = 1
                                            while block_depth > 0 and self._current_token() and self._current_token().kind != "EOF":
                                                if self._current_token().kind == "LBRACE":
                                                    block_depth += 1
                                                elif self._current_token().kind == "RBRACE":
                                                    block_depth -= 1
                                                self._advance()
                                            self._skip_whitespace()
                                found_sync = True
                                break
                    
                    # Skip this token and continue looking
                    self._advance()
                    self._skip_whitespace()
                
                if not found_sync:
                    # No sync point found - reached EOF
                    # If we didn't find a semicolon, report missing semicolon error
                    # Only if:
                    # 1. We haven't already reported one
                    # 2. The original error was NOT about a structural issue
                    # 3. The sync_start_token is NOT a statement starter
                    # 4. The original error was NOT already about a semicolon
                    # 5. The original error was NOT a typo error (prioritize typo completion first)
                    should_report_missing_semicolon = (
                        not found_semicolon and 
                        sync_start_token and 
                        not error_is_structural and 
                        not error_is_about_semicolon and
                        not sync_is_statement_starter and
                        not error_is_typo  # Don't report additional errors after typo
                    )
                    if should_report_missing_semicolon:
                        missing_semicolon_error = ParseError(
                            f"Missing semicolon. Expected ';' before end of input",
                            sync_start_token
                        )
                        self.errors.append(missing_semicolon_error)
                        print(f"[DEBUG _parse_function_body_with_recovery] Added missing semicolon error at EOF. Total errors: {len(self.errors)}", file=sys.stderr)
                    break
        
        # Before returning, make sure we're positioned correctly
        # If we're at the closing brace, DON'T advance past it - let _parse_program() consume it
        # This ensures proper brace tracking
        self._skip_whitespace()
        
        print(f"[DEBUG _parse_function_body_with_recovery] Exiting function body. Collected {len(self.errors)} total errors so far", file=sys.stderr)
        print(f"[DEBUG _parse_function_body_with_recovery] Current token: {self._current_token().kind if self._current_token() else 'None'}", file=sys.stderr)
        return FunctionBody(
            local_declarations=local_decls,
            statements=statements,
            line=token.line if token else 1,
            column=token.column if token else 1
        )
    
    def _parse_namespace(self) -> Optional[Namespace]:
        """Parse: boundaries id { global_declaration sub_func }"""
        if not self._match("boundaries"):
            return None
        
        token = self._consume("boundaries")
        name_token = self._consume("id", "Expected identifier after 'boundaries'")
        self._consume("LBRACE")
        self._skip_whitespace()  # Skip newlines after opening brace
        
        # Parse global declarations
        global_decls = []
        while self._match("dear") or self._match("dearest") or self._match("rant") or \
              self._match("status") or self._match("const"):
            global_decls.append(self._parse_declaration())
            self._skip_whitespace()
        
        # Parse sub functions
        sub_funcs = []
        while self._match("dear") or self._match("dearest") or self._match("rant") or \
              self._match("status") or self._match("avoidant"):
            sub_funcs.append(self._parse_sub_function())
            self._skip_whitespace()
        
        self._consume("RBRACE")
        
        return Namespace(
            name=name_token.lexeme,
            global_declarations=global_decls,
            sub_functions=sub_funcs,
            line=token.line,
            column=token.column
        )
    
    def _parse_sub_function(self) -> Function:
        """Parse: return_type id (parameter) { body_func } | avoidant id (parameter) { body_func }"""
        token = self._current_token()
        
        if self._match("avoidant"):
            self._consume("avoidant")
            return_type = None
        else:
            return_type = self._parse_data_type()
        
        name_token = self._consume("id", "Expected function name. Complete structure: <return_type> id (<parameter>) { ... }")
        self._consume("LPAREN", "Expected '(' after function name. Complete structure: <return_type> id (<parameter>) { ... }")
        parameters = self._parse_parameters()
        self._consume("RPAREN", "Expected ')' to close function parameters. Complete structure: <return_type> id (<parameter>) { ... }")
        self._consume("LBRACE", "Expected '{' after function parameters. Complete structure: <return_type> id (<parameter>) { ... }")
        self._skip_whitespace()  # Skip newlines after opening brace
        body = self._parse_function_body()
        self._consume("RBRACE", "Expected '}' to close function body. Complete structure: <return_type> id (<parameter>) { ... }")
        
        return Function(
            return_type=return_type,
            name=name_token.lexeme,
            parameters=parameters,
            body=body,
            line=token.line if token else 1,
            column=token.column if token else 1
        )
    
    # =========================================================================
    # Declarations
    # =========================================================================
    
    def _parse_declaration(self) -> Declaration:
        """
        Parse declaration according to CFG:
        - Rule 9: <data_type> id <array_decl> <var_initial> <multi_decl>;
        - Rule 10: <data_type> id;
        - Rule 11: <const_decl> <data_type> id = <expr> ;
        """
        token = self._current_token()
        
        # Check for const (Rule 11)
        is_const = False
        if self._match("const"):
            self._consume("const")
            is_const = True
            # Const declaration: const data_type id = expr;
            data_type = self._parse_data_type()
            id_token = self._consume("id", "Expected identifier. Complete structure: const <data_type> id = <expr>;")
            self._consume("ASSIGN", "Expected '=' in const declaration. Complete structure: const <data_type> id = <expr>;")
            initial_value = self._parse_expression()
            self._consume("SEMICOLON", "Expected semicolon after declaration. Complete structure: const <data_type> id = <expr>;")
            
            return Declaration(
                data_type=data_type,
                identifier=id_token.lexeme,
                array_dimensions=0,
                initial_value=initial_value,
                is_const=True,
                multi_declarations=[],
                line=token.line if token else 1,
                column=token.column if token else 1
            )
        
        # Parse data type
        data_type = self._parse_data_type()
        
        # Parse identifier
        id_token = self._consume("id", "Expected identifier. Complete structure: <data_type> id [= <expr>];")
        
        # Check for Rule 10: <data_type> id; (simple declaration)
        if self._match("SEMICOLON"):
            self._consume("SEMICOLON")
            return Declaration(
                data_type=data_type,
                identifier=id_token.lexeme,
                array_dimensions=0,
                initial_value=None,
                is_const=False,
                multi_declarations=[],
                line=token.line if token else 1,
                column=token.column if token else 1
            )
        
        # Rule 9: <data_type> id <array_decl> <var_initial> <multi_decl>;
        # Parse array dimensions
        array_dims = self._parse_array_declaration()
        
        # Parse initial value
        initial_value = None
        if self._match("ASSIGN"):
            self._consume("ASSIGN")
            # Check if it's an array literal or expression
            if self._match("LBRACE"):
                # Array literal: = { ... }
                self._consume("LBRACE")
                array_values = []
                if not self._match("RBRACE"):
                    array_values.append(self._parse_init_value())
                    while self._match("COMMA"):
                        self._consume("COMMA")
                        array_values.append(self._parse_init_value())
                self._consume("RBRACE")
                # For now, store as expression (could create ArrayLiteralExpression)
                initial_value = array_values[0] if array_values else None
            else:
                initial_value = self._parse_expression()
        
        # Parse multi declarations
        multi_decls = []
        while self._match("COMMA"):
            self._consume("COMMA")
            multi_id = self._consume("id", "Expected identifier after comma. Complete structure: <data_type> id [= <expr>], id2 [= <expr>];")
            multi_dims = self._parse_array_declaration()
            multi_init = None
            if self._match("ASSIGN"):
                self._consume("ASSIGN")
                if self._match("LBRACE"):
                    self._consume("LBRACE")
                    array_vals = []
                    if not self._match("RBRACE"):
                        array_vals.append(self._parse_init_value())
                        while self._match("COMMA"):
                            self._consume("COMMA")
                            array_vals.append(self._parse_init_value())
                    self._consume("RBRACE")
                    multi_init = array_vals[0] if array_vals else None
                else:
                    multi_init = self._parse_expression()
            multi_decls.append(MultiDeclaration(
                identifier=multi_id.lexeme,
                array_dimensions=multi_dims,
                initial_value=multi_init,
                line=multi_id.line,
                column=multi_id.column
            ))
        
        self._consume("SEMICOLON", "Expected semicolon after declaration. Complete structure: <data_type> id [= <expr>];")
        self._skip_whitespace()  # Skip newlines after semicolon
        
        return Declaration(
            data_type=data_type,
            identifier=id_token.lexeme,
            array_dimensions=array_dims,
            initial_value=initial_value,
            is_const=is_const,
            multi_declarations=multi_decls,
            line=token.line if token else 1,
            column=token.column if token else 1
        )
    
    def _parse_init_value(self) -> Expression:
        """Parse: <expr> | { <array_lit_list> }"""
        if self._match("LBRACE"):
            # Array literal - for now parse as expression
            # This is a simplification; could create ArrayLiteralExpression
            self._consume("LBRACE")
            values = []
            if not self._match("RBRACE"):
                values.append(self._parse_expression())
                while self._match("COMMA"):
                    self._consume("COMMA")
                    values.append(self._parse_expression())
            self._consume("RBRACE")
            # Return first value as placeholder (should be ArrayLiteralExpression)
            return values[0] if values else None
        else:
            return self._parse_expression()
    
    def _parse_data_type(self) -> str:
        """Parse: dear | dearest | rant | status"""
        if self._match("dear"):
            self._consume("dear")
            return "dear"
        elif self._match("dearest"):
            self._consume("dearest")
            return "dearest"
        elif self._match("rant"):
            self._consume("rant")
            return "rant"
        elif self._match("status"):
            self._consume("status")
            return "status"
        else:
            raise ParseError("Expected data type (dear, dearest, rant, status)", self._current_token())
    
    def _parse_array_declaration(self) -> int:
        """Parse: [] [] ... (returns count of [] pairs)"""
        count = 0
        while self._match("LBRACKET"):
            self._consume("LBRACKET")
            self._consume("RBRACKET")
            count += 1
        return count
    
    def _parse_parameters(self) -> List[Parameter]:
        """Parse: function_parameter [multi_parameter] | empty"""
        params = []
        
        if not (self._match("dear") or self._match("dearest") or 
                self._match("rant") or self._match("status")):
            return params
        
        # Parse first parameter
        params.append(self._parse_function_parameter())
        
        # Parse additional parameters
        while self._match("COMMA"):
            self._consume("COMMA")
            params.append(self._parse_function_parameter())
        
        return params
    
    def _parse_function_parameter(self) -> Parameter:
        """Parse: data_type id [array_decl]"""
        token = self._current_token()
        data_type = self._parse_data_type()
        id_token = self._consume("id", "Expected parameter name")
        array_dims = self._parse_array_declaration()
        
        return Parameter(
            data_type=data_type,
            identifier=id_token.lexeme,
            array_dimensions=array_dims,
            line=token.line if token else 1,
            column=token.column if token else 1
        )
    
    # =========================================================================
    # Function Body
    # =========================================================================
    
    def _parse_function_body(self) -> FunctionBody:
        """Parse: local_decl_list statements"""
        # Skip any leading whitespace/newlines
        self._skip_whitespace()
        
        token = self._current_token()
        
        # Parse local declarations
        local_decls = []
        while self._match("dear") or self._match("dearest") or \
              self._match("rant") or self._match("status"):
            local_decls.append(self._parse_local_declaration())
            self._skip_whitespace()
        
        # Parse statements
        statements = []
        while not self._match("RBRACE") and not self._match("EOF"):
            self._skip_whitespace()
            if self._match("RBRACE"):
                break
            
            # Try to parse a statement
            try:
                stmt = self._parse_statement()
                if stmt:
                    statements.append(stmt)
                    self._skip_whitespace()
                else:
                    # No statement could be parsed - this shouldn't happen if _parse_statement raises errors
                    break
            except ParseError:
                # Error already recorded in self.errors, re-raise it
                raise
        
        return FunctionBody(
            local_declarations=local_decls,
            statements=statements,
            line=token.line if token else 1,
            column=token.column if token else 1
        )
    
    def _parse_local_declaration(self) -> Declaration:
        """Parse: data_type id [array_decl] [= expr] [multi_decl];"""
        # Same as global declaration
        return self._parse_declaration()
    
    # =========================================================================
    # Statements
    # =========================================================================
    
    def _parse_statement(self) -> Optional[Statement]:
        """
        Parse any statement.
        Returns None if no statement can be parsed, raises ParseError if there's an unexpected token.
        """
        token = self._current_token()
        if not token:
            return None
        
        # Skip whitespace
        if self._match("NEWLINE"):
            self._skip_whitespace()
            token = self._current_token()
            if not token:
                return None
        
        # Check for different statement types
        # First check for exact keyword matches
        if self._match("give") or self._match("overshare"):
            return self._parse_input_statement()
        elif self._match("express"):
            return self._parse_output_statement()
        elif self._match("forever"):
            return self._parse_if_statement()
        elif self._match("while"):
            return self._parse_while_statement()
        elif self._match("pursue"):
            return self._parse_do_while_statement()
        elif self._match("for"):
            return self._parse_for_statement()
        elif self._match("comeback"):
            return self._parse_return_statement()
        elif self._match("choose"):
            return self._parse_switch_statement()
        elif self._match("id"):
            # Check if this identifier is a typo for a statement keyword
            suggestion = self._find_similar_keyword(token.lexeme)
            if suggestion == "forever":
                # Typo for "forever" (if statement) - report error and stop parsing
                # Don't continue parsing to avoid cascading errors
                error = ParseError(
                    f"Unexpected identifier '{token.lexeme}'. Did you mean 'forever'?",
                    token
                )
                self.errors.append(error)
                # Raise error to stop parsing - let recovery skip to next sync point
                raise error
            elif suggestion == "choose":
                # Typo for "choose" (switch statement) - report error and stop parsing
                # Don't continue parsing to avoid cascading errors
                error = ParseError(
                    f"Unexpected identifier '{token.lexeme}'. Did you mean 'choose'?",
                    token
                )
                self.errors.append(error)
                # Raise error to stop parsing - let recovery skip to next sync point
                raise error
            else:
                # Not a typo for a statement keyword, treat as regular identifier statement
                peek = self._peek_token()
                print(f"[DEBUG _parse_statement] Calling _parse_id_statement for '{token.lexeme}'. Peek token: {peek.kind if peek else 'None'} '{peek.lexeme if peek else ''}'", file=sys.stderr)
                return self._parse_id_statement()
        elif self._match("OP_INC") or self._match("OP_DEC"):
            return self._parse_unary_statement()
        else:
            # We have a token but it's not a valid statement starter
            # Create a helpful error message
            if token.kind == "id":
                # It's an identifier - might be a typo
                suggestion = self._find_similar_keyword(token.lexeme)
                if suggestion:
                    msg = f"Unexpected identifier '{token.lexeme}'. Did you mean '{suggestion}'?"
                else:
                    msg = f"Unexpected identifier '{token.lexeme}'. Expected a statement keyword (express, give, forever, while, etc.)"
            else:
                # Other unexpected token
                expected_keywords = ", ".join(sorted(self.STATEMENT_KEYWORDS))
                msg = f"Unexpected token '{token.lexeme}'. Expected a statement keyword: {expected_keywords}"
            
            error = ParseError(msg, token)
            print(f"[DEBUG _parse_statement] Adding error to self.errors. Count before: {len(self.errors)}", file=sys.stderr)
            self.errors.append(error)
            print(f"[DEBUG _parse_statement] Count after: {len(self.errors)}. Error message: {msg[:60]}", file=sys.stderr)
            raise error
    
    def _parse_id_statement(self) -> Statement:
        """
        Parse: id id_suffix
        According to CFG:
        - Rule 48: <index_array> <assign_ops> <assign_values>;
        - Rule 49: <assign_ops> <assign_values> ;
        - Rule 50: (<arguments>);
        - Rule 51: <unary_ops> ;
        """
        token = self._consume("id")
        identifier = token.lexeme
        
        # Check for common typos: if identifier is followed by <<, it might be a typo for "express"
        peek = self._peek_token()
        print(f"[DEBUG _parse_id_statement] After consuming '{identifier}', peek token: {peek.kind if peek else 'None'} '{peek.lexeme if peek else ''}'", file=sys.stderr)
        if peek and peek.kind == "OP_LSHIFT":
            # This looks like it should be an output statement
            # An identifier followed by << is not a valid statement - it should be "express <<"
            print(f"[DEBUG _parse_id_statement] Found identifier '{identifier}' followed by OP_LSHIFT", file=sys.stderr)
            suggestion = self._find_similar_keyword(identifier)
            print(f"[DEBUG _parse_id_statement] Suggestion for '{identifier}': {suggestion}", file=sys.stderr)
            if suggestion == "express":
                msg = f"Unexpected identifier '{identifier}'. Did you mean '{suggestion}'? (Found '<<' which suggests an output statement)"
            else:
                # Even if not detected as typo, id << is not valid - suggest express
                msg = f"Unexpected identifier '{identifier}'. Did you mean 'express'? (Found '<<' which suggests an output statement)"
            error = ParseError(msg, token)
            print(f"[DEBUG _parse_id_statement] Creating error and adding to self.errors. Current error count: {len(self.errors)}", file=sys.stderr)
            self.errors.append(error)
            print(f"[DEBUG _parse_id_statement] Error count after append: {len(self.errors)}. Raising error...", file=sys.stderr)
            raise error
        
        # Parse id_suffix according to CFG
        # Check for Rule 50: (<arguments>);
        if self._match("LPAREN"):
            # Function call: id (<arguments>);
            namespace = None
            # Check for namespace (boundaries_suffix) - but this comes before LPAREN in func_call
            # Actually, func_call is: id <boundaries_suffix> (<arguments>)
            # But in id_suffix, it's just: (<arguments>);
            self._consume("LPAREN")
            arguments = self._parse_arguments()
            self._consume("RPAREN")
            self._consume("SEMICOLON")
            
            return FunctionCallStatement(
                identifier=identifier,
                namespace=namespace,
                arguments=arguments,
                line=token.line,
                column=token.column
            )
        
        # Check for Rule 51: <unary_ops> ;
        if self._match("OP_INC") or self._match("OP_DEC"):
            # Unary operation: id++ or id--
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            self._consume("SEMICOLON")
            
            return UnaryStatement(
                operator=operator,
                identifier=identifier,
                is_prefix=False,
                line=token.line,
                column=token.column
            )
        
        # Parse index_array (Rule 48: <index_array> <assign_ops> <assign_values>;)
        # or Rule 49: <assign_ops> <assign_values> ;
        array_indices = []
        if self._match("LBRACKET"):
            # Rule 48: has index_array
            array_indices = self._parse_index_array()
        
        # Now check for assignment operators
        if self._match("ASSIGN") or self._match("OP_PLUS_ASSIGN") or \
           self._match("OP_MINUS_ASSIGN") or self._match("OP_MUL_ASSIGN") or \
           self._match("OP_DIV_ASSIGN") or self._match("OP_MOD_ASSIGN"):
            # Assignment: Rule 48 or 49
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            value = self._parse_expression()  # assign_values is just <expr>
            self._consume("SEMICOLON")
            
            return AssignmentStatement(
                identifier=identifier,
                array_indices=array_indices,
                operator=operator,
                value=value,
                line=token.line,
                column=token.column
            )
        else:
            # Unexpected token after identifier
            unexpected_token = self._current_token()
            if unexpected_token:
                # Check if it's a typo - identifier followed by something that suggests a keyword
                suggestion = self._find_similar_keyword(identifier)
                if suggestion and suggestion != identifier.lower():
                    msg = f"Unexpected identifier '{identifier}'. Did you mean '{suggestion}'? (Found '{unexpected_token.lexeme}' after identifier)"
                else:
                    msg = f"Unexpected token '{unexpected_token.lexeme}' after identifier '{identifier}'. Expected: '(', '=', '+=', '-=', '*=', '/=', '%=', '++', '--', or ';'"
            else:
                msg = f"Unexpected end of input after identifier '{identifier}'"
            raise ParseError(msg, unexpected_token or token)
    
    def _parse_index_array(self) -> List[Expression]:
        """
        Parse: [<expr_ar>] <index_array> | λ
        According to CFG Rule 138-139
        """
        indices = []
        while self._match("LBRACKET"):
            self._consume("LBRACKET")
            # CFG says <expr_ar>, not full <expr>
            indices.append(self._parse_arithmetic_expression())
            self._consume("RBRACKET")
        return indices
    
    def _parse_input_statement(self) -> InputStatement:
        """Parse: give >> id; | overshare(id);"""
        token = self._current_token()
        
        if self._match("give"):
            self._consume("give")
            self._consume("OP_RSHIFT", "Expected '>>' after 'give'. Complete structure: give >> id;")
            id_token = self._consume("id", "Expected identifier after '>>'. Complete structure: give >> id;")
            self._consume("SEMICOLON", "Expected ';' after identifier. Complete structure: give >> id;")
            
            return InputStatement(
                method="give",
                identifier=id_token.lexeme,
                line=token.line,
                column=token.column
            )
        elif self._match("overshare"):
            self._consume("overshare")
            self._consume("LPAREN", "Expected '(' after 'overshare'. Complete structure: overshare(id);")
            id_token = self._consume("id", "Expected identifier in overshare. Complete structure: overshare(id);")
            self._consume("RPAREN", "Expected ')' to close 'overshare ('. Complete structure: overshare(id);")
            self._consume("SEMICOLON", "Expected ';' after 'overshare()'. Complete structure: overshare(id);")
            
            return InputStatement(
                method="overshare",
                identifier=id_token.lexeme,
                line=token.line,
                column=token.column
            )
        else:
            raise ParseError("Expected 'give' or 'overshare'", token)
    
    def _parse_output_statement(self) -> OutputStatement:
        """
        Parse: express <more_output>;
        According to CFG:
        - Rule 68: express <more_output>;
        - Rule 69: << <output_values> <more_output>
        - Rule 70: << <output_values>
        - Rule 71: <expr>
        - Rule 72: periodt
        """
        token = self._consume("express", context="output statement")
        values = []
        
        # Check for common typo: single < instead of <<
        if self._match("LT"):
            # User wrote a single < instead of <<
            lt_token = self._current_token()
            msg = f"Unexpected token '<' after 'express'. Expected '<<' (double less-than) for output operator. Did you mean '<<'? Complete structure: express << <expr> << periodt;"
            error = ParseError(msg, lt_token)
            self.errors.append(error)
            raise error
        
        # Check if we have at least one << operator
        if not self._match("OP_LSHIFT"):
            # No output operator found - this is an error
            next_token = self._current_token()
            if next_token:
                msg = f"Unexpected token '{next_token.lexeme}' after 'express'. Expected '<<' (output operator)"
            else:
                msg = "Unexpected end of input after 'express'. Expected '<<' (output operator)"
            error = ParseError(msg, next_token or token)
            self.errors.append(error)
            raise error
        
        # Parse more_output (right-recursive in CFG, but we can use iterative approach)
        # Rule 69: << <output_values> <more_output>
        # Rule 70: << <output_values> (base case)
        while self._match("OP_LSHIFT"):
            self._consume("OP_LSHIFT", context="output statement after <<")
            # Parse output_values: <expr> | periodt (Rule 71, 72)
            if self._match("periodt"):
                self._consume("periodt")
                values.append("periodt")
            else:
                # Parse expression - if it fails, we want context-aware error
                # Check if we have a valid expression starter first
                if self._match("NEWLINE") or self._match("SEMICOLON") or self._match("RBRACE"):
                    # Missing expression after <<
                    next_token = self._current_token()
                    possible = self._get_all_possible_terminals("output statement after <<")
                    if possible:
                        terminal_names = [self._format_expected_token(t).strip("'") for t in possible]
                        terminals_str = ", ".join(terminal_names)
                        msg = f"Unexpected token '{next_token.lexeme if next_token else 'end of input'}' after '<<'. Expected one of: {terminals_str}. Complete structure: express << <expr> << periodt;"
                    else:
                        msg = f"Unexpected token '{next_token.lexeme if next_token else 'end of input'}' after '<<'. Expected an expression or 'periodt'. Complete structure: express << <expr> << periodt;"
                    error = ParseError(msg, next_token)
                    self.errors.append(error)
                    raise error
                values.append(self._parse_expression())
        
        self._consume("SEMICOLON")
        
        return OutputStatement(
            values=values,
            line=token.line,
            column=token.column
        )
    
    def _parse_return_statement(self) -> ReturnStatement:
        """Parse: comeback [expr];"""
        token = self._consume("comeback")
        value = None
        
        if not self._match("SEMICOLON"):
            value = self._parse_expression()
        
        self._consume("SEMICOLON", "Expected ';' after 'comeback'. Complete structure: comeback [<expr>];")
        
        return ReturnStatement(
            value=value,
            line=token.line,
            column=token.column
        )
    
    def _parse_if_statement(self) -> IfStatement:
        """Parse: forever (expr) { body } [forevermore ...] [more { body }]"""
        # Consume "forever" - handle typo recovery if needed
        if self._match("forever"):
            token = self._consume("forever")
        elif self._match("id"):
            # Check if this is a typo for "forever"
            current_token = self._current_token()
            suggestion = self._find_similar_keyword(current_token.lexeme)
            if suggestion == "forever":
                # Error may have already been reported in _parse_statement, check first
                error_already_reported = any(
                    e.token == current_token and "forever" in e.message.lower()
                    for e in self.errors
                )
                if not error_already_reported:
                    # Report error if not already reported
                    error = ParseError(
                        f"Unexpected identifier '{current_token.lexeme}'. Did you mean 'forever'?",
                        current_token
                    )
                    self.errors.append(error)
                # Use typo token for line/column info, then advance
                token = current_token
                self._advance()  # Skip typo
            else:
                raise ParseError(f"Expected 'forever', found '{current_token.lexeme}'", current_token)
        else:
            current_token = self._current_token()
            if not current_token:
                raise ParseError("Expected 'forever', found end of input", None)
            raise ParseError(f"Expected 'forever', found '{current_token.lexeme}'", current_token)
        self._consume("LPAREN")
        # Store position of opening parenthesis for better error messages
        opening_paren_index = self.current_index - 1
        
        # Check if expression is empty (immediately followed by RPAREN)
        if self._match("RPAREN"):
            # Empty expression - report error immediately
            rparen_token = self._current_token()
            possible = self._get_all_possible_terminals("expression")
            if possible:
                terminal_names = [self._format_expected_token(t).strip("'") for t in possible]
                terminals_str = ", ".join(terminal_names)
                msg = f"Unexpected token ')' in expression. Expected one of: {terminals_str}. Complete structure: forever (<expr>) {{ ... }}"
            else:
                msg = "Unexpected token ')' in expression. Expected an expression (identifier, literal, '(', or function call). Complete structure: forever (<expr>) { ... }"
            error = ParseError(msg, rparen_token)
            self.errors.append(error)
            condition = None
        else:
            # Try to parse expression - if it fails, still try to parse the braces and body
            condition = None
            try:
                condition = self._parse_expression()
            except ParseError as e:
                # Expression parsing failed (e.g., invalid expression)
                # Record the error so it's reported to the user
                self.errors.append(e)
                # Still try to parse the braces and body to prevent cascading errors.
                # The parser should still be at the ')' token, so we can consume it normally.
                condition = None  # Will be None, but that's okay for recovery
        
        # Consume RPAREN - check if it exists first
        if not self._match("RPAREN"):
            # Check if there's a matching closing parenthesis ahead
            if opening_paren_index is not None:
                # Look for matching RPAREN
                paren_depth = 1
                found_rparen = False
                for i in range(self.current_index, len(self.tokens)):
                    token = self.tokens[i]
                    if token.kind == "LPAREN":
                        paren_depth += 1
                    elif token.kind == "RPAREN":
                        paren_depth -= 1
                        if paren_depth == 0:
                            # Found matching RPAREN - advance to it
                            self.current_index = i
                            found_rparen = True
                            break
                    elif token.kind == "EOF":
                        break
                
                if not found_rparen:
                    # No matching RPAREN - report error
                    next_token = self._current_token()
                    error = ParseError(
                        f"Expected ')' to close 'forever (' statement. Found '{next_token.lexeme if next_token else 'end of input'}' instead. Complete structure: forever (<expr>) {{ ... }}",
                        next_token
                    )
                    self.errors.append(error)
                    raise error
            else:
                # Can't find opening paren index, use normal consume (will raise error)
                self._consume("RPAREN")
        else:
            self._consume("RPAREN")
        
        # Consume LBRACE - check if it exists first
        if not self._match("LBRACE"):
            # Check if there's a matching opening brace ahead
            next_token = self._current_token()
            if next_token and next_token.kind == "LBRACE":
                # It's there, just consume it
                self._consume("LBRACE")
            else:
                # No LBRACE found - report error
                error = ParseError(
                    f"Expected '{{' after 'forever ()'. Found '{next_token.lexeme if next_token else 'end of input'}' instead. Complete structure: forever (<expr>) {{ ... }}",
                    next_token
                )
                self.errors.append(error)
                raise error
        else:
            self._consume("LBRACE")
        self._skip_whitespace()
        # Store position of opening brace for better error detection
        opening_brace_index = None
        for i in range(self.current_index - 1, -1, -1):
            if i < len(self.tokens) and self.tokens[i].kind == "LBRACE":
                opening_brace_index = i
                break
        
        # Use recovery version for nested bodies so errors don't break the entire chain
        try:
            then_body = self._parse_function_body()
        except ParseError:
            # Error in then body - use recovery version
            then_body = self._parse_function_body_with_recovery()
        
        # Check for closing brace with better detection
        if not self._match("RBRACE"):
            # Try to find matching closing brace
            matching_brace_idx = None
            if opening_brace_index is not None:
                matching_brace_idx = self._find_matching_closing_brace(opening_brace_index)
            
            if matching_brace_idx is not None:
                # Found it - advance to it and consume
                self.current_index = matching_brace_idx
                self._advance()
            else:
                # No matching brace - check if we have structural errors
                has_structural_errors = any(
                    "expression" in e.message.lower() or 
                    "unexpected token" in e.message.lower()
                    for e in self.errors
                )
                if not has_structural_errors:
                    # Report error only if no structural errors (to avoid cascading)
                    next_token = self._current_token()
                    error = ParseError(
                        f"Expected '}}' to close 'forever () {{' block. Found '{next_token.lexeme if next_token else 'end of input'}' instead. Complete structure: forever (<expr>) {{ ... }}",
                        next_token
                    )
                    self.errors.append(error)
                    raise error
                # Otherwise, don't report (likely cascading from structural error)
        else:
            # Normal case - brace is there, consume it
            self._consume("RBRACE")
        self._skip_whitespace()  # Skip whitespace after closing brace
        
        # Parse elif clauses
        elif_clauses = []
        while True:
            # Check for "forevermore" or typo for it
            if self._match("forevermore"):
                self._consume("forevermore")
            elif self._match("id") and self._peek_token() and self._peek_token().kind == "LPAREN":
                # Check if this identifier is a typo for "forevermore"
                current_token = self._current_token()
                suggestion = self._find_similar_keyword(current_token.lexeme)
                if suggestion == "forevermore":
                    # It's a typo for "forevermore" - report error but continue parsing
                    error = ParseError(
                        f"Unexpected identifier '{current_token.lexeme}'. Did you mean 'forevermore'?",
                        current_token
                    )
                    self.errors.append(error)
                    # Advance past the typo and continue as if it were "forevermore"
                    self._advance()  # Skip the typo identifier
                else:
                    # Not a typo for forevermore, break the loop
                    break
            else:
                # Not forevermore and not a typo, break the loop
                break
            self._consume("LPAREN", "Expected '(' after 'forevermore'. Complete structure: forevermore (<expr>) { ... }")
            # Check for empty expression
            if self._match("RPAREN"):
                rparen_token = self._current_token()
                possible = self._get_all_possible_terminals("expression")
                if possible:
                    terminal_names = [self._format_expected_token(t).strip("'") for t in possible]
                    terminals_str = ", ".join(terminal_names)
                    msg = f"Unexpected token ')' in expression. Expected one of: {terminals_str}. Complete structure: forevermore (<expr>) {{ ... }}"
                else:
                    msg = "Unexpected token ')' in expression. Expected an expression (identifier, literal, '(', or function call). Complete structure: forevermore (<expr>) { ... }"
                error = ParseError(msg, rparen_token)
                self.errors.append(error)
                elif_condition = None
            else:
                elif_condition = self._parse_expression()
            self._consume("RPAREN", "Expected ')' to close 'forevermore ('. Complete structure: forevermore (<expr>) { ... }")
            self._consume("LBRACE", "Expected '{' after 'forevermore ()'. Complete structure: forevermore (<expr>) { ... }")
            self._skip_whitespace()
            # Use recovery version for nested bodies so errors don't break the entire chain
            try:
                elif_body = self._parse_function_body()
            except ParseError:
                # Error in elif body - use recovery version
                elif_body = self._parse_function_body_with_recovery()
            self._consume("RBRACE", "Expected '}' to close 'forevermore () {' block. Complete structure: forevermore (<expr>) { ... }")
            self._skip_whitespace()  # Skip whitespace after closing brace
            elif_clauses.append(ElifClause(
                condition=elif_condition,
                body=elif_body,
                line=token.line,
                column=token.column
            ))
        
        # Parse else clause
        else_body = None
        if self._match("more"):
            self._consume("more")
            self._consume("LBRACE")
            self._skip_whitespace()
            # Use recovery version for nested bodies so errors don't break the entire chain
            try:
                else_body = self._parse_function_body()
            except ParseError:
                # Error in else body - use recovery version
                else_body = self._parse_function_body_with_recovery()
            self._consume("RBRACE")
        elif self._match("id"):
            # Check if this identifier is a typo for "more"
            current_token = self._current_token()
            suggestion = self._find_similar_keyword(current_token.lexeme)
            if suggestion == "more":
                # It's a typo for "more" - report error but continue parsing
                error = ParseError(
                    f"Unexpected identifier '{current_token.lexeme}'. Did you mean 'more'?",
                    current_token
                )
                self.errors.append(error)
                # Advance past the typo and continue as if it were "more"
                self._advance()  # Skip the typo identifier
                # Check if next token is LBRACE (expected after "more")
                if self._match("LBRACE"):
                    self._consume("LBRACE")
                    self._skip_whitespace()
                    # Parse the else body with recovery
                    try:
                        else_body = self._parse_function_body()
                    except ParseError:
                        else_body = self._parse_function_body_with_recovery()
                    self._consume("RBRACE")
                else:
                    # Typo but wrong structure - report additional error
                    next_token = self._current_token()
                    if next_token:
                        error2 = ParseError(
                            f"Expected '{{' after 'more', found '{next_token.lexeme}'. Complete structure: more {{ ... }}",
                            next_token
                        )
                        self.errors.append(error2)
        
        return IfStatement(
            condition=condition,
            then_body=then_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
            line=token.line,
            column=token.column
        )
    
    def _parse_while_statement(self) -> WhileStatement:
        """Parse: while (expr) { body }"""
        token = self._consume("while")
        self._consume("LPAREN", "Expected '(' after 'while'. Complete structure: while (<expr>) { ... }")
        # Check for empty expression
        if self._match("RPAREN"):
            rparen_token = self._current_token()
            possible = self._get_all_possible_terminals("expression")
            if possible:
                terminal_names = [self._format_expected_token(t).strip("'") for t in possible]
                terminals_str = ", ".join(terminal_names)
                msg = f"Unexpected token ')' in expression. Expected one of: {terminals_str}. Complete structure: while (<expr>) {{ ... }}"
            else:
                msg = "Unexpected token ')' in expression. Expected an expression (identifier, literal, '(', or function call). Complete structure: while (<expr>) { ... }"
            error = ParseError(msg, rparen_token)
            self.errors.append(error)
            condition = None
        else:
            condition = self._parse_expression()
        self._consume("RPAREN", "Expected ')' to close 'while ('. Complete structure: while (<expr>) { ... }")
        self._consume("LBRACE", "Expected '{' after 'while ()'. Complete structure: while (<expr>) { ... }")
        self._skip_whitespace()
        body = self._parse_function_body()
        self._consume("RBRACE", "Expected '}' to close 'while () {' block. Complete structure: while (<expr>) { ... }")
        
        return WhileStatement(
            condition=condition,
            body=body,
            line=token.line,
            column=token.column
        )
    
    def _parse_do_while_statement(self) -> DoWhileStatement:
        """Parse: pursue (expr) { body }"""
        token = self._consume("pursue")
        self._consume("LPAREN", "Expected '(' after 'pursue'. Complete structure: pursue (<expr>) { ... }")
        # Check for empty expression
        if self._match("RPAREN"):
            rparen_token = self._current_token()
            possible = self._get_all_possible_terminals("expression")
            if possible:
                terminal_names = [self._format_expected_token(t).strip("'") for t in possible]
                terminals_str = ", ".join(terminal_names)
                msg = f"Unexpected token ')' in expression. Expected one of: {terminals_str}. Complete structure: pursue (<expr>) {{ ... }}"
            else:
                msg = "Unexpected token ')' in expression. Expected an expression (identifier, literal, '(', or function call). Complete structure: pursue (<expr>) { ... }"
            error = ParseError(msg, rparen_token)
            self.errors.append(error)
            condition = None
        else:
            condition = self._parse_expression()
        self._consume("RPAREN", "Expected ')' to close 'pursue ('. Complete structure: pursue (<expr>) { ... }")
        self._consume("LBRACE", "Expected '{' after 'pursue ()'. Complete structure: pursue (<expr>) { ... }")
        self._skip_whitespace()
        body = self._parse_function_body()
        self._consume("RBRACE", "Expected '}' to close 'pursue () {' block. Complete structure: pursue (<expr>) { ... }")
        
        return DoWhileStatement(
            condition=condition,
            body=body,
            line=token.line,
            column=token.column
        )
    
    def _parse_for_statement(self) -> ForStatement:
        """Parse: for (init; condition; update) { body }"""
        token = self._consume("for")
        self._consume("LPAREN", "Expected '(' after 'for'. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        
        # Parse init
        init = None
        if not self._match("SEMICOLON"):
            init = self._parse_for_init()
        self._consume("SEMICOLON", "Expected ';' after for loop init. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        
        # Parse condition
        condition = None
        if not self._match("SEMICOLON"):
            condition = self._parse_expression()
        self._consume("SEMICOLON", "Expected ';' after for loop condition. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        
        # Parse update
        update = None
        if not self._match("RPAREN"):
            update = self._parse_for_update()
        self._consume("RPAREN", "Expected ')' to close 'for ('. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        
        self._consume("LBRACE", "Expected '{' after 'for ()'. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        self._skip_whitespace()
        body = self._parse_function_body()
        self._consume("RBRACE", "Expected '}' to close 'for () {' block. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        
        return ForStatement(
            init=init,
            condition=condition,
            update=update,
            body=body,
            line=token.line,
            column=token.column
        )
    
    def _parse_for_init(self) -> ForInit:
        """Parse: [data_type] id = expr"""
        token = self._current_token()
        
        data_type = None
        if self._match("dear") or self._match("dearest") or \
           self._match("rant") or self._match("status"):
            data_type = self._parse_data_type()
        
        id_token = self._consume("id", "Expected identifier in for loop init. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        self._consume("ASSIGN", "Expected '=' in for loop init. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
        value = self._parse_expression()
        
        return ForInit(
            data_type=data_type,
            identifier=id_token.lexeme,
            value=value,
            line=token.line if token else 1,
            column=token.column if token else 1
        )
    
    def _parse_for_update(self) -> ForUpdate:
        """Parse: id assign_op expr | id unary_op | unary_op id"""
        token = self._current_token()
        
        if self._match("OP_INC") or self._match("OP_DEC"):
            # Prefix unary: ++id or --id
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            id_token = self._consume("id", "Expected identifier after unary operator")
            
            return ForUpdate(
                identifier=id_token.lexeme,
                operator=operator,
                value=None,
                is_prefix=True,
                line=token.line if token else 1,
                column=token.column if token else 1
            )
        else:
            # id assign_op expr or id unary_op
            id_token = self._consume("id", "Expected identifier in for loop update. Complete structure: for (<for_init>; <expr>; <for_ud>) { ... }")
            
            if self._match("OP_INC") or self._match("OP_DEC"):
                # Postfix unary: id++ or id--
                op_token = self._current_token()
                operator = op_token.lexeme
                self._advance()
                
                return ForUpdate(
                    identifier=id_token.lexeme,
                    operator=operator,
                    value=None,
                    is_prefix=False,
                    line=token.line if token else 1,
                    column=token.column if token else 1
                )
            else:
                # Assignment: id assign_op expr
                op_token = self._current_token()
                operator = op_token.lexeme
                self._advance()
                value = self._parse_expression()
                
                return ForUpdate(
                    identifier=id_token.lexeme,
                    operator=operator,
                    value=value,
                    is_prefix=False,
                    line=token.line if token else 1,
                    column=token.column if token else 1
                )
    
    def _parse_switch_statement(self) -> SwitchStatement:
        """Parse: choose (expr) { phase ... [bareminimum ...] }"""
        # Consume "choose" - handle typo recovery if needed
        if self._match("choose"):
            token = self._consume("choose")
        elif self._match("id"):
            # Check if this is a typo for "choose"
            current_token = self._current_token()
            suggestion = self._find_similar_keyword(current_token.lexeme)
            if suggestion == "choose":
                # Error may have already been reported in _parse_statement, check first
                error_already_reported = any(
                    e.token == current_token and "choose" in e.message.lower()
                    for e in self.errors
                )
                if not error_already_reported:
                    # Report error if not already reported
                    error = ParseError(
                        f"Unexpected identifier '{current_token.lexeme}'. Did you mean 'choose'?",
                        current_token
                    )
                    self.errors.append(error)
                # Use typo token for line/column info, then advance
                token = current_token
                self._advance()  # Skip typo
            else:
                raise ParseError(f"Expected 'choose', found '{current_token.lexeme}'. Complete structure: choose (<expr>) {{ phase <const>: ... breakup; ... }}", current_token)
        else:
            current_token = self._current_token()
            if not current_token:
                raise ParseError("Expected 'choose', found end of input. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }", None)
            raise ParseError(f"Expected 'choose', found '{current_token.lexeme}'. Complete structure: choose (<expr>) {{ phase <const>: ... breakup; ... }}", current_token)
        self._consume("LPAREN", "Expected '(' after 'choose'. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }")
        expression = self._parse_expression()
        self._consume("RPAREN", "Expected ')' to close 'choose ('. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }")
        self._consume("LBRACE", "Expected '{' after 'choose ()'. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }")
        self._skip_whitespace()
        
        # Parse cases
        cases = []
        while self._match("phase"):
            self._consume("phase")
            
            # Parse case value
            case_token = self._current_token()
            if self._match("dear_lit") or self._match("dearest_lit"):
                lit_token = self._current_token()
                if lit_token.kind == "dear_lit":
                    value = int(lit_token.literal) if lit_token.literal else 0
                    self._consume("dear_lit")
                else:
                    value = float(lit_token.literal) if lit_token.literal else 0.0
                    self._consume("dearest_lit")
            elif self._match("rant_lit"):
                lit_token = self._consume("rant_lit")
                value = lit_token.literal or ""
            else:
                raise ParseError("Expected literal value in case. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }", case_token)
            
            self._consume("COLON", "Expected ':' after phase value. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }")
            case_body = self._parse_function_body()
            self._consume("breakup", "Expected 'breakup' after phase body. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }")
            self._consume("SEMICOLON", "Expected ';' after 'breakup'. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }")
            
            cases.append(CaseClause(
                value=value,
                body=case_body,
                line=case_token.line,
                column=case_token.column
            ))
        
        # Parse default case
        default_case = None
        if self._match("bareminimum"):
            self._consume("bareminimum")
            self._consume("COLON", "Expected ':' after 'bareminimum'. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... bareminimum: ... breakup; }")
            default_case = self._parse_function_body()
            self._consume("breakup", "Expected 'breakup' after bareminimum body. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... bareminimum: ... breakup; }")
            self._consume("SEMICOLON", "Expected ';' after 'breakup'. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... bareminimum: ... breakup; }")
        
        self._consume("RBRACE", "Expected '}' to close 'choose () {' block. Complete structure: choose (<expr>) { phase <const>: ... breakup; ... }")
        
        return SwitchStatement(
            expression=expression,
            cases=cases,
            default_case=default_case,
            line=token.line,
            column=token.column
        )
    
    def _parse_unary_statement(self) -> UnaryStatement:
        """Parse: ++id; | --id;"""
        token = self._current_token()
        operator = token.lexeme
        self._advance()
        id_token = self._consume("id", "Expected identifier after unary operator")
        self._consume("SEMICOLON")
        
        return UnaryStatement(
            operator=operator,
            identifier=id_token.lexeme,
            is_prefix=True,
            line=token.line,
            column=token.column
        )
    
    def _parse_arguments(self) -> List[Expression]:
        """Parse: expr [more_arguments] | empty"""
        args = []
        
        if self._match("RPAREN"):
            return args
        
        args.append(self._parse_expression())
        
        while self._match("COMMA"):
            self._consume("COMMA")
            args.append(self._parse_expression())
        
        return args
    
    # =========================================================================
    # Expressions (Right-Recursive for LL(1))
    # =========================================================================
    
    def _parse_expression(self) -> Expression:
        """Parse: log_expr"""
        return self._parse_logical_expression()
    
    def _parse_logical_expression(self) -> Expression:
        """Parse: and_expr [|| and_expr ...]"""
        left = self._parse_and_expression()
        
        while self._match("OP_OR"):
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            right = self._parse_and_expression()
            left = BinaryExpression(
                operator=operator,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def _parse_and_expression(self) -> Expression:
        """Parse: rel_expr [&& rel_expr ...]"""
        left = self._parse_relational_expression()
        
        while self._match("OP_AND"):
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            right = self._parse_relational_expression()
            left = BinaryExpression(
                operator=operator,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def _parse_relational_expression(self) -> Expression:
        """Parse: expr_ar [rel_op expr_ar ...]"""
        left = self._parse_arithmetic_expression()
        
        while self._match("OP_EQ") or self._match("OP_NEQ") or \
              self._match("LT") or self._match("OP_LTE") or \
              self._match("GT") or self._match("OP_GTE"):
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            right = self._parse_arithmetic_expression()
            left = BinaryExpression(
                operator=operator,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def _parse_arithmetic_expression(self) -> Expression:
        """Parse: term [expr_next] where expr_next: + term expr_next | - term expr_next | empty"""
        left = self._parse_term()
        
        while self._match("PLUS") or self._match("MINUS"):
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            right = self._parse_term()
            left = BinaryExpression(
                operator=operator,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def _parse_term(self) -> Expression:
        """Parse: factor [term_next] where term_next: * factor term_next | / factor term_next | % factor term_next | empty"""
        left = self._parse_factor()
        
        while self._match("STAR") or self._match("SLASH") or self._match("PERCENT"):
            op_token = self._current_token()
            operator = op_token.lexeme
            self._advance()
            right = self._parse_factor()
            left = BinaryExpression(
                operator=operator,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def _parse_factor(self) -> Expression:
        """
        Parse: (expr) | func_call | id | literal
        According to CFG:
        - Rule 85: (<expr>)
        - Rule 86: id
        - Rule 87-90: literals
        - Rule 93: <func_call>
        - Rule 133: id <boundaries_suffix> (<arguments>)
        """
        token = self._current_token()
        
        if self._match("LPAREN"):
            self._consume("LPAREN")
            expr = self._parse_expression()
            self._consume("RPAREN")
            return ParenthesizedExpression(
                expression=expr,
                line=token.line,
                column=token.column
            )
        elif self._match("id"):
            # Could be identifier or function call
            id_token = self._consume("id")
            identifier = id_token.lexeme
            
            # Check for function call: id <boundaries_suffix> (<arguments>)
            # Rule 133: func_call → id <boundaries_suffix> (<arguments>)
            namespace = None
            if self._match("OP_SCOPE"):
                # Rule 134: boundaries_suffix → :: id
                self._consume("OP_SCOPE")
                namespace_token = self._consume("id", "Expected namespace identifier")
                namespace = namespace_token.lexeme
            
            if self._match("LPAREN"):
                # It's a function call
                self._consume("LPAREN")
                arguments = self._parse_arguments()
                self._consume("RPAREN")
                
                return FunctionCallExpression(
                    identifier=identifier,
                    namespace=namespace,
                    arguments=arguments,
                    line=id_token.line,
                    column=id_token.column
                )
            else:
                # It's just an identifier (possibly with array indexing)
                # Array indexing is handled in IdentifierExpression
                array_indices = []
                while self._match("LBRACKET"):
                    self._consume("LBRACKET")
                    array_indices.append(self._parse_arithmetic_expression())
                    self._consume("RBRACKET")
                
                return IdentifierExpression(
                    name=identifier,
                    array_indices=array_indices,
                    line=id_token.line,
                    column=id_token.column
                )
        elif self._match("dear_lit"):
            lit_token = self._consume("dear_lit")
            value = int(lit_token.literal) if lit_token.literal else 0
            return LiteralExpression(
                value=value,
                literal_type="int",
                line=lit_token.line,
                column=lit_token.column
            )
        elif self._match("dearest_lit"):
            lit_token = self._consume("dearest_lit")
            value = float(lit_token.literal) if lit_token.literal else 0.0
            return LiteralExpression(
                value=value,
                literal_type="float",
                line=lit_token.line,
                column=lit_token.column
            )
        elif self._match("rant_lit"):
            lit_token = self._consume("rant_lit")
            value = lit_token.literal or ""
            return LiteralExpression(
                value=value,
                literal_type="string",
                line=lit_token.line,
                column=lit_token.column
            )
        elif self._match("greenflag") or self._match("redflag"):
            lit_token = self._current_token()
            value = lit_token.kind == "greenflag"
            self._advance()
            return LiteralExpression(
                value=value,
                literal_type="bool",
                line=lit_token.line,
                column=lit_token.column
            )
        else:
            # Use context-aware error message with suggestions
            # Check if we're in an output statement context
            context = "expression"
            possible = self._get_all_possible_terminals(context)
            if possible:
                terminal_names = [self._format_expected_token(t).strip("'") for t in possible]
                terminals_str = ", ".join(terminal_names)
                msg = f"Unexpected token '{token.lexeme}' in expression. Expected one of: {terminals_str}"
            else:
                msg = f"Unexpected token '{token.lexeme}' in expression. Expected an identifier, literal, '(', or function call"
            raise ParseError(msg, token)


# =============================================================================
# Convenience Functions
# =============================================================================

def parse_from_source(source: str) -> Program:
    """
    Parse source code and return AST.
    
    Args:
        source: Source code string
        
    Returns:
        Program AST node
        
    Raises:
        ParseError: If parsing fails
    """
    # Import here to avoid circular dependency
    from Backend.Lexical.Lexer import Lexer
    
    lexer = Lexer(source)
    parser = RecursiveDescentParser(lexer)
    return parser.parse()


def parse_with_errors_rd(source: str) -> tuple[Optional[Program], List]:
    """
    Parse source code with error collection and recovery (compatible with existing API).
    Collects multiple errors in a single parse attempt.
    
    Args:
        source: Source code string
        
    Returns:
        Tuple of (program, errors) where program is None if parsing failed,
        and errors is a list of SyntaxError-compatible objects.
    """
    # Import here to avoid circular dependency
    from Backend.Lexical.Lexer import Lexer
    from Backend.Syntax.errors import SyntaxError
    
    lexer = Lexer(source)
    parser = RecursiveDescentParser(lexer)
    
    # Use recovery mode to collect multiple errors
    program, parse_errors = parser.parse_with_recovery()
    
    # Convert ParseError objects to SyntaxError format
    syntax_errors = []
    for parse_error in parse_errors:
        syntax_error = SyntaxError(
            message=parse_error.message,  # Use the enhanced message with suggestions
            line=parse_error.line,
            column=parse_error.column,
            expected=[],
            found=parse_error.token.lexeme if parse_error.token else "",
            raw_message=parse_error.message,
            is_end_of_input=parse_error.token is None or (parse_error.token and parse_error.token.kind == "EOF")
        )
        syntax_errors.append(syntax_error)
    
    # Debug: Print all errors to console (can be removed later)
    if len(syntax_errors) > 0:
        print(f"[DEBUG parse_with_errors_rd] Collected {len(syntax_errors)} errors:", file=sys.stderr)
        for i, err in enumerate(syntax_errors, 1):
            print(f"  Error {i}: Line {err.line}:{err.column} - {err.message[:100]}", file=sys.stderr)
    
    return program, syntax_errors
