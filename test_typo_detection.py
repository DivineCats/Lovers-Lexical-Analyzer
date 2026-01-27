from Backend.Syntax.SimpleRecursiveDescentParser import SimpleRecursiveDescentParser
from Backend.Lexical.Lexer import Lexer

# Test typo detection
parser = SimpleRecursiveDescentParser(None)
test_words = ["exprss", "foreerore", "express", "forevermore"]
for word in test_words:
    suggestion = parser._find_similar_keyword(word)
    print(f"'{word}' -> '{suggestion}'")
