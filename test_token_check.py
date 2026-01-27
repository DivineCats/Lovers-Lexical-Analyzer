from Backend.Lexical.Lexer import Lexer

source = """love () {
    forever (x) { }
    forevermore (x) { }
}"""

lexer = Lexer(source)
tokens = lexer.scan_tokens()

print('All tokens:')
for i, t in enumerate(tokens):
    print(f'  {i}: {t.kind} = "{t.lexeme}" (line {t.line}, col {t.column})')

print('\nTokens after forever block closes (after RBRACE):')
# Find the RBRACE that closes the forever block
for i, t in enumerate(tokens):
    if t.kind == "RBRACE" and i > 5:  # After the forever block
        print(f'After token {i} ({t.kind}):')
        for j in range(i+1, min(i+6, len(tokens))):
            print(f'  {j}: {tokens[j].kind} = "{tokens[j].lexeme}"')
        break
