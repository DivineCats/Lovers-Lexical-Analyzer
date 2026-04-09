/**
 * Syntax Helper - Constants and helper functions for error display
 * Used by Terminals.tsx for formatting and displaying compiler errors
 * 
 * NOTE: Token-to-symbol translation (e.g., "LSHIFT" -> "<<") is now handled
 * by the backend (Parser.py). The frontend receives symbols directly.
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

// =============================================================================
// KEYWORD STRUCTURE GUIDE - Based on CFG grammar rules
// =============================================================================
// Maps each keyword to its expected structure for user guidance
// =============================================================================

export const KEYWORD_STRUCTURE: Record<string, string> = {
  // I/O statements
  "express": "express << value ;",
  "give": "give >> variable [ >> variable ... ] ;",
  "overshare": "overshare << value1 << value2 ... ;",
  
  // Data types (variable declaration)
  "dear": "dear variableName = value ;",
  "dearest": "dearest variableName = value ;",
  "rant": "rant variableName = \"text\" ;",
  "status": "status variableName = greenflag/redflag ;",
  "const": "const type variableName = value ;",
  
  // Conditionals
  "forever": "forever ( condition ) { ... }",
  "forevermore": "forevermore ( condition ) { ... }",
  "more": "more { ... }",
  "choose": "choose ( variable ) { phase value : ... bareminimum : ... }",
  "phase": "phase value : statement ; breakup ;",
  "bareminimum": "bareminimum : statement ;",
  
  // Loops
  "for": "for ( init ; condition ; update ) { ... }",
  "while": "while ( condition ) { ... }",
  "pursue": "pursue ( condition ) { ... }",
  
  // Control flow
  "breakup": "breakup ;",
  "moveon": "moveon ;",
  "comeback": "comeback value ;",
  
  // Functions
  "boundaries": "boundaries returnType functionName ( params ) { ... }",
  "avoidant": "avoidant functionName ( params ) { ... }",
  
  // Boolean literals
  "greenflag": "greenflag (true)",
  "redflag": "redflag (false)",
  
  // Main
  "love": "love ( ) { ... }",
  "periodt": "periodt (end of statement block)",
};

/**
 * Get structure hint for a keyword or partial keyword
 */
export const getKeywordStructure = (word: string): string | null => {
  const lower = word.toLowerCase();
  
  // Exact match
  if (KEYWORD_STRUCTURE[lower]) {
    return KEYWORD_STRUCTURE[lower];
  }
  
  // Partial match - find keyword that starts with this prefix
  for (const keyword of KEYWORDS) {
    if (keyword.startsWith(lower) && lower.length >= 2) {
      return KEYWORD_STRUCTURE[keyword] || null;
    }
  }
  
  return null;
};

/**
 * Get helpful construction hints based on expected tokens.
 * Expected tokens are already translated to symbols by the backend.
 */
export const getConstructionHint = (expected: string[] | undefined, message: string, found?: string): string | null => {
  const msgLower = message.toLowerCase();
  
  // Handle reserved word errors
  if (msgLower.includes("reserved word") && msgLower.includes("cannot be used")) {
    return "Use a different name for your variable (e.g., myVar, result, value1)";
  }
  
  // Check if the "found" token looks like an incomplete keyword
  // and show the expected structure for that keyword
  if (found) {
    const structure = getKeywordStructure(found);
    if (structure) {
      return `Expected structure: ${structure}`;
    }
  }
  
  // If expected contains a keyword, show its structure
  if (expected && expected.length === 1) {
    const single = expected[0];
    const structure = KEYWORD_STRUCTURE[single.toLowerCase()];
    if (structure) {
      return `Expected: ${structure}`;
    }
  }
  
  if (!expected || expected.length === 0) {
    // Handle generic "Unexpected input" errors
    if (msgLower.includes("unexpected input")) {
      return "Start your program with: love () { ... }";
    }
    return null;
  }
  
  // Backend already translates tokens to symbols, so use expected directly
  const expectedSymbols = expected;
  
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
    return "Expected structure: express << value ;";
  }
  if (expectedSymbols.includes(">>")) {
    return "Expected structure: give >> variable [ >> variable ... ] ;";
  }
  if (expectedSymbols.some(s => ["dear", "dearest", "rant", "status"].includes(s))) {
    return "Expected data type: dear (int), dearest (float), rant (string), status (bool)";
  }
  if (expectedSymbols.includes("identifier")) {
    return "Expected a variable or function name";
  }
  if (expectedSymbols.includes("=")) {
    return "Assignment syntax: variable = value ;";
  }
  if (expectedSymbols.some(s => ["forever", "forevermore", "more"].includes(s))) {
    return "Conditional: forever ( condition ) { ... }";
  }
  if (expectedSymbols.some(s => ["for", "while", "pursue"].includes(s))) {
    return "Loop: for ( init ; condition ; update ) { ... }";
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
