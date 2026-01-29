import "./Terminals.css";
import {
  getConstructionHint,
  getKeywordSuggestions,
  getSymbolSuggestions,
  extractExpectedTokens,
} from "./syntaxHelper";

export type ValidationTokenInfo = {
  lexeme?: string;
  kind?: string;
  line?: number;
  column?: number;
};

export type ValidationError = {
  ok: boolean;
  message: string;
  code?: string;
  token?: ValidationTokenInfo;
  expected?: string[];
  line?: number;
  column?: number;
  found?: string;
  context?: string;
};

export type ValidationResult = {
  ok: boolean;
  message: string;
  code?: string;
  token?: ValidationTokenInfo;
  expected?: string[];
  errors?: ValidationError[];
  line?: number;
  column?: number;
  found?: string;
};

export type ErrorItem = {
  type: "lexical" | "syntax" | "semantic" | "backend";
  message: string;
  line?: number;
  column?: number;
  expected?: string[];
  unexpectedToken?: string;
  context?: string;
  expectedDelimiter?: string;
  possibleReserved?: string;
};

type Props = {
  validation?: ValidationResult | null;
  lexError?: string | null;
  lexErrors?: string[];
  backendError?: string | null;
};

export default function Terminal({ validation = null, lexError = null, lexErrors = [], backendError = null }: Props) {
  // Parse all errors into structured format
  const errors: ErrorItem[] = [];

  const renderKeywordSuggestions = (message: string) => {
    // Try to extract an offending lexeme from backticks in the first line
    const m = message.match(/`([A-Za-z][A-Za-z0-9_]*)`/);
    const word = m ? m[1] : undefined;
    if (!word) return null;
    const suggestions = getKeywordSuggestions(word);
    if (suggestions.length === 0) return null;
    return (
      <div className="error-details">
        <div className="error-detail-line">Possible Reserved words: {suggestions.join(", ")}</div>
      </div>
    );
  };

  const renderSymbolSuggestions = (message: string) => {
    // Extract offending symbol inside backticks (operators often are non-letters)
    const m = message.match(/`([^`]+)`/);
    const sym = m ? m[1] : undefined;
    if (!sym) return null;
    const suggestions = getSymbolSuggestions(sym);
    if (suggestions.length === 0) return null;
    return (
      <div className="error-details">
        <div className="error-detail-line">Possible symbols: {suggestions.join(", ")}</div>
      </div>
    );
  };
  
  if (lexErrors.length > 0) {
    lexErrors.forEach((err) => {
      const lines = err.split(/\r?\n/).filter(line => line.trim().length > 0);
      const firstLine = lines[0] || "";
      
      // Extract line and column if present (format: "at line X, column Y" or "at X:Y")
      const locationMatch = firstLine.match(/at (?:line )?(\d+)[,:]\s*(?:column )?(\d+)/i);
      
      // Extract "Expected delimiter:" line for reserved words
      const expectedDelimiterLine = lines.find(line => line.toLowerCase().startsWith("expected delimiter:"));
      
      // Extract "Possible Reserved words:" line
      const possibleReservedLine = lines.find(line => line.toLowerCase().startsWith("possible reserved"));
      
      const expectedTokens = extractExpectedTokens(lines);
      
      errors.push({
        type: "lexical",
        message: firstLine,
        line: locationMatch ? parseInt(locationMatch[1]) : undefined,
        column: locationMatch ? parseInt(locationMatch[2]) : undefined,
        expected: expectedTokens.length > 0 ? expectedTokens : undefined,
        expectedDelimiter: expectedDelimiterLine,
        possibleReserved: possibleReservedLine,
      });
    });
  } else if (lexError) {
    const lines = lexError.split(/\r?\n/).filter(line => line.trim().length > 0);
    const firstLine = lines[0] || "";
    const locationMatch = firstLine.match(/at (?:line )?(\d+)[,:]\s*(?:column )?(\d+)/i);
    
    // Extract "Expected delimiter:" line for reserved words
    const expectedDelimiterLine = lines.find(line => line.toLowerCase().startsWith("expected delimiter:"));
    
    // Extract "Possible Reserved words:" line
    const possibleReservedLine = lines.find(line => line.toLowerCase().startsWith("possible reserved"));
    
    const expectedTokens = extractExpectedTokens(lines);
    
    errors.push({
      type: "lexical",
      message: firstLine,
      line: locationMatch ? parseInt(locationMatch[1]) : undefined,
      column: locationMatch ? parseInt(locationMatch[2]) : undefined,
      expected: expectedTokens.length > 0 ? expectedTokens : undefined,
      expectedDelimiter: expectedDelimiterLine,
      possibleReserved: possibleReservedLine,
    });
  }

  // Process syntax validation errors
  if (validation && !validation.ok) {
    if (validation.errors && validation.errors.length > 0) {
      validation.errors.forEach((err: any) => {
        errors.push({
          type: "syntax",
          message: err.message || "Syntax error",
          line: err.line,
          column: err.column,
          expected: err.expected,
          unexpectedToken: err.found,
          context: err.context,
        });
      });
    } else {
      errors.push({
        type: "syntax",
        message: validation.message,
        line: (validation as any).line,
        column: (validation as any).column,
        expected: validation.expected,
        unexpectedToken: (validation as any).found,
      });
    }
  }

  if (backendError) {
    errors.push({
      type: "backend",
      message: backendError,
    });
  }

  const lexicalCount = errors.filter(e => e.type === "lexical").length;
  const syntaxCount = errors.filter(e => e.type === "syntax").length;
  const semanticCount = errors.filter(e => e.type === "semantic").length;
  const backendCount = errors.filter(e => e.type === "backend").length;
  const hasErrors = lexicalCount > 0 || syntaxCount > 0 || semanticCount > 0 || backendCount > 0;

  // Check if we should show the "resolve lexical first" prompt
  const hasLexicalErrors = lexicalCount > 0;

  return (
    <div className="terminal-panel">
      <div className="header">Terminal</div>
      <div className="term-log" aria-live="polite">
        {hasErrors && (
          <div className="error-summary">
            {lexicalCount > 0 && <span className="error-count">Lexical: {lexicalCount}</span>}
            {syntaxCount > 0 && <span className="error-count">Syntax: {syntaxCount}</span>}
            {semanticCount > 0 && <span className="error-count">Semantic: {semanticCount}</span>}
            {backendCount > 0 && <span className="error-count">Backend: {backendCount}</span>}
          </div>
        )}
        {errors.length === 0 && (
          <div className="term-log__empty">No errors detected.</div>
        )}
        {errors.map((error, idx) => {
          const constructionHint = error.type === "syntax" ? getConstructionHint(error.expected, error.message, error.unexpectedToken) : null;
          // Universal syntax error format: first line = what went wrong; second line = expected token(s) from CFG (always shown in bar)
          const lines = error.message.split(/\n/).map((s) => s.trim()).filter(Boolean);
          const mainMessage = lines[0] || error.message;
          const expectedLineRaw = lines.find((l) => /^Expected Token:\s*/i.test(l) || /^Expected:\s*/i.test(l));
          const expectedTokenLine = expectedLineRaw
            ? expectedLineRaw.replace(/^Expected:\s*/i, "Expected Token: ")
            : null;
          const showInlineLocation = mainMessage.indexOf("(line ") === -1 && error.type !== "lexical" && error.line !== undefined && error.column !== undefined && error.line > 0 && error.column > 0;

          // Extract location pattern from message if it's embedded: "(line X, col Y)" or "(line X, col Y)"
          const locationMatch = mainMessage.match(/(\(line\s+\d+,\s*col\s+\d+\))/i);
          const messageWithoutLocation = locationMatch ? mainMessage.replace(locationMatch[0], "").trim() : mainMessage;
          const locationText = locationMatch ? locationMatch[1] : null;

          return (
            <div key={idx} className="error-container">
              <div className="error-item">
                <span className={`error-badge error-badge--${error.type}`}>
                  {error.type.toUpperCase()}
                </span>
                <span className="error-message">
                  {messageWithoutLocation}
                  {locationText && (
                    <span className="error-location-inline"> {locationText}</span>
                  )}
                  {showInlineLocation && (
                    <span className="error-location-inline"> (line {error.line}, col {error.column})</span>
                  )}
                </span>
              </div>

              {/* Expected Token bar (design from 2nd image: dark bar, left accent, light pink text) */}
              {expectedTokenLine && (
                <div className="error-expected-token-bar">
                  {expectedTokenLine}
                </div>
              )}
              
              {/* Show expected delimiter for lexical errors (reserved words) */}
              {error.type === "lexical" && error.expectedDelimiter && (
                <div className="error-details">
                  <div className="error-detail-line">{error.expectedDelimiter}</div>
                </div>
              )}
              
              {/* Show construction hint only when we don't already show Expected Token bar (avoid 3rd redundant line) */}
              {constructionHint && !expectedTokenLine && (
                <div className="error-hint">
                  {constructionHint}
                </div>
              )}
              
              {renderKeywordSuggestions(error.message)}
              {renderSymbolSuggestions(error.message)}
            </div>
          );
        })}
        {/* Show prompt to resolve lexical errors first before syntax analysis */}
        {hasLexicalErrors && (
          <div className="error-container">
            <div className="error-item">
              <span className="error-badge error-badge--syntax">SYNTAX</span>
              <span className="error-message">Lexical errors detected. Resolve them before syntax analysis.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
