/**
 * Syntax Helper - Constants and helper functions for error display
 * Used by Terminals.tsx for formatting and displaying compiler errors
 */

// Reserved keywords (mirror of backend set) for suggestions
export const KEYWORDS = [
  "give", "express", "overshare", "dear", "dearest", "rant", "status",
  "forever", "more", "forevermore", "choose", "phase", "bareminimum",
  "for", "while", "pursue", "breakup", "moveon", "love", "periodt",
  "const", "redflag", "greenflag", "boundaries", "comeback", "avoidant"
];

// Operator/symbol suggestions based on prefix
export const SYMBOLS = [
  "+", "++", "+=", "-", "--", "-=", "*", "*=", "/", "/=", "%", "%=",
  "==", "!=", ">", ">=", "<", "<=", "&&", "||", "::", "<<", ">>"
];

// Map internal token names to human-readable symbols
export const TOKEN_TO_SYMBOL: Record<string, string> = {
  // Keywords
  LOVE: "love", BOUNDARIES: "boundaries", CONST: "const", AVOIDANT: "avoidant",
  COMEBACK: "comeback", DEAR: "dear", DEAREST: "dearest", RANT: "rant",
  STATUS: "status", FOREVER: "forever", FOREVERMORE: "forevermore", MORE: "more",
  CHOOSE: "choose", PHASE: "phase", BAREMINIMUM: "bareminimum", FOR: "for",
  WHILE: "while", PURSUE: "pursue", BREAKUP: "breakup", GIVE: "give",
  EXPRESS: "express", OVERSHARE: "overshare", PERIODT: "periodt",
  GREENFLAG: "greenflag", REDFLAG: "redflag", MOVEON: "moveon",
  // Operators
  ASSIGN: "=", PLUS_ASSIGN: "+=", MINUS_ASSIGN: "-=", MUL_ASSIGN: "*=",
  DIV_ASSIGN: "/=", MOD_ASSIGN: "%=", INC: "++", DEC: "--",
  EQ: "==", NEQ: "!=", LT: "<", LTE: "<=", GT: ">", GTE: ">=",
  AND: "&&", OR: "||", PLUS: "+", MINUS: "-", STAR: "*", SLASH: "/", PERCENT: "%",
  // Symbols
  SEMICOLON: ";", COMMA: ",", LPAREN: "(", RPAREN: ")", LBRACE: "{", RBRACE: "}",
  LBRACKET: "[", RBRACKET: "]", COLON: ":", SCOPE: "::", LSHIFT: "<<", RSHIFT: ">>",
  // Literals
  IDENTIFIER: "identifier", INT_LITERAL: "number", FLOAT_LITERAL: "decimal",
  STRING_LITERAL: "string",
};

/**
 * Convert internal token name to readable symbol
 */
export const formatToken = (token: string): string => {
  return TOKEN_TO_SYMBOL[token] || token;
};

/**
 * Get helpful construction hints based on expected tokens
 */
export const getConstructionHint = (expected: string[] | undefined, message: string): string | null => {
  const msgLower = message.toLowerCase();
  
  // Handle reserved word errors
  if (msgLower.includes("reserved word") && msgLower.includes("cannot be used")) {
    return "Use a different name for your variable (e.g., myVar, result, value1)";
  }
  
  if (!expected || expected.length === 0) {
    // Handle generic "Unexpected input" errors
    if (msgLower.includes("unexpected input")) {
      return "Start your program with: love () { ... }";
    }
    return null;
  }
  
  const expectedSymbols = expected.map(formatToken);
  
  // Detect missing brackets/parentheses (single expected token)
  if (expectedSymbols.length === 1) {
    const single = expectedSymbols[0];
    if (single === ")") return "Missing ')'";
    if (single === "(") return "Missing '('";
    if (single === "}") return "Missing '}'";
    if (single === "{") return "Missing '{'";
    if (single === "]") return "Missing ']'";
    if (single === "[") return "Missing '['";
    if (single === ";") return "Missing ';'";
  }
  
  // Check for specific patterns and provide helpful hints
  if (expectedSymbols.includes("love")) {
    return "Start your program with: love () { ... }";
  }
  if (expectedSymbols.includes("(") && expectedSymbols.includes(")")) {
    return "Expected parentheses for function call or condition";
  }
  if (expectedSymbols.includes("{") && !expectedSymbols.includes("}")) {
    return "Missing '{'";
  }
  if (expectedSymbols.includes("}") && !expectedSymbols.includes("{")) {
    return "Missing '}'";
  }
  if (expectedSymbols.includes(";")) {
    return "Missing ';'";
  }
  if (expectedSymbols.includes("<<")) {
    return "Output syntax: express << value;";
  }
  if (expectedSymbols.includes(">>")) {
    return "Input syntax: give >> variable;";
  }
  if (expectedSymbols.some(s => ["dear", "dearest", "rant", "status"].includes(s))) {
    return "Expected data type: dear (int), dearest (float), rant (string), status (bool)";
  }
  if (expectedSymbols.includes("identifier")) {
    return "Expected a variable or function name";
  }
  if (expectedSymbols.includes("=")) {
    return "Assignment syntax: variable = value;";
  }
  if (expectedSymbols.some(s => ["forever", "forevermore", "more"].includes(s))) {
    return "Conditional syntax: forever (condition) { ... } forevermore (condition) { ... } more { ... }";
  }
  if (expectedSymbols.some(s => ["for", "while", "pursue"].includes(s))) {
    return "Loop syntax: for (init; cond; update) { ... } or while (cond) { ... } or pursue (cond) { ... }";
  }
  
  return null;
};

/**
 * Get keyword suggestions based on partial input
 */
export const getKeywordSuggestions = (word: string): string[] => {
  const lower = word.toLowerCase();
  return KEYWORDS.filter(k => k !== lower && k.startsWith(lower)).slice(0, 6);
};

/**
 * Get symbol suggestions based on partial input
 */
export const getSymbolSuggestions = (sym: string): string[] => {
  return SYMBOLS.filter(s => s !== sym && s.startsWith(sym)).slice(0, 6);
};

/**
 * Extract expected tokens from error message lines
 */
export const extractExpectedTokens = (lines: string[]): string[] => {
  for (const line of lines) {
    const match = line.match(/expected(?: one of)?\s*[:\-]\s*(.*)/i);
    if (match && match[1]) {
      const payload = match[1].trim();
      const clean = (t: string) => t.trim().replace(/^[`]+|[`]+$/g, "");
      const keep = (t: string) => t.length > 0 && t !== "-";

      // Prefer backend dash-separated format: "- token - token - , - :"
      const dashSplit = payload
        .split(/\s*-\s+/)
        .map(clean)
        .filter(keep);
      if (dashSplit.length > 0) {
        return dashSplit;
      }
      // Fallback: split on whitespace only (preserve literal comma tokens)
      return payload
        .split(/\s+/)
        .map(clean)
        .filter(keep);
    }
  }
  return [];
};
