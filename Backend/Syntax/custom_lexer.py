# Backend/Syntax/custom_lexer.py
"""Custom lexer adapter for Lark that uses our Lexer.py"""

from lark import Token as LarkToken
from lark.lexer import Lexer as LarkLexer


class CustomLarkLexer(LarkLexer):
    """
    Adapter that makes our custom Lexer.py compatible with Lark's parser.
    Lark will use this instead of its built-in lexer.
    """
    
    def __init__(self, lexer_conf):
        """Initialize with Lark's lexer configuration (ignored since we use our own lexer)."""
        pass
    
    def lex(self, data: str):
        """
        Tokenize the input data using our custom Lexer.py.
        Yields Lark Token objects.
        """
        # Lazy import to avoid circular dependency
        from Backend.Lexical.Lexer import Lexer, LexerError
        
        lexer = Lexer(data)
        try:
            tokens, errors = lexer.scan_tokens_collect_errors()
        except LexerError as e:
            # If lexer fails, yield what we have and let parser handle the error
            tokens = getattr(e, 'tokens', [])
            errors = [str(e)]
        
        for tok in tokens:
            if tok.kind == "EOF":
                continue
            if tok.kind == "NEWLINE":
                continue  # Skip newlines for parsing
            
            # Convert all token kinds to uppercase to match Lark's terminal naming convention
            # Lexer outputs lowercase grammar terminals (id, dear_lit, etc.) which need to be uppercased
            token_type = tok.kind.upper()
            lark_tok = LarkToken(
                type_=token_type,
                value=tok.lexeme,
            )
            lark_tok.line = tok.line
            lark_tok.column = tok.column
            yield lark_tok
