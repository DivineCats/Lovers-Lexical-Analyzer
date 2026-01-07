import "./Terminals.css";

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
};

export type ValidationResult = {
  ok: boolean;
  message: string;
  code?: string;
  token?: ValidationTokenInfo;
  expected?: string[];
  errors?: ValidationError[];
};

export type ErrorItem = {
  type: "lexical" | "semantic" | "backend";
  message: string;
  line?: number;
  column?: number;
  expected?: string[];
  unexpectedToken?: string;
};

type Props = {
  validation?: ValidationResult | null;
  lexError?: string | null;
  lexErrors?: string[];
  backendError?: string | null;
};

export default function Terminal({ lexError = null, lexErrors = [], backendError = null }: Props) {
  // Parse lexical errors into structured format
  const errors: ErrorItem[] = [];

  // Reserved keywords (mirror of backend set) for suggestions
  const KEYWORDS = [
    "give","express","overshare","dear","dearest","rant","status",
    "forever","more","forevermore","choose","phase","bareminimum",
    "for","while","pursue","breakup","moveon","love","periodt",
    "const","redflag","greenflag","boundaries","comeback","avoidant"
  ];

  const renderKeywordSuggestions = (message: string) => {
    // Try to extract an offending lexeme from backticks in the first line
    const m = message.match(/`([A-Za-z][A-Za-z0-9_]*)`/);
    const word = m ? m[1] : undefined;
    if (!word) return null;
    const lower = word.toLowerCase();
    const suggestions = KEYWORDS.filter(k => k !== lower && k.startsWith(lower)).slice(0, 6);
    if (suggestions.length === 0) return null;
    return (
      <div className="error-details">
        <div className="error-detail-line">Possible keywords: {suggestions.join(", ")}</div>
      </div>
    );
  };

  const extractExpectedTokens = (lines: string[]): string[] => {
    for (const line of lines) {
      const match = line.match(/expected(?: one of)?\s*[:\-]\s*(.*)/i);
      if (match && match[1]) {
        return match[1]
          .split(/[-,\s]+/)
          .map(t => t.trim().replace(/^['`]+|['`]+$/g, ""))
          .filter(t => t.length > 0);
      }
    }
    return [];
  };
  
  if (lexErrors.length > 0) {
    lexErrors.forEach((err) => {
      const lines = err.split(/\r?\n/).filter(line => line.trim().length > 0);
      const firstLine = lines[0] || "";
      
      // Extract line and column if present (format: "at line X, column Y" or "at X:Y")
      const locationMatch = firstLine.match(/at (?:line )?(\d+)[,:]\s*(?:column )?(\d+)/i);
      
      const expectedTokens = extractExpectedTokens(lines);
      
      errors.push({
        type: "lexical",
        message: firstLine,
        line: locationMatch ? parseInt(locationMatch[1]) : undefined,
        column: locationMatch ? parseInt(locationMatch[2]) : undefined,
        expected: expectedTokens.length > 0 ? expectedTokens : undefined,
      });
    });
  } else if (lexError) {
    const lines = lexError.split(/\r?\n/).filter(line => line.trim().length > 0);
    const firstLine = lines[0] || "";
    const locationMatch = firstLine.match(/at (?:line )?(\d+)[,:]\s*(?:column )?(\d+)/i);
    
    const expectedTokens = extractExpectedTokens(lines);
    
    errors.push({
      type: "lexical",
      message: firstLine,
      line: locationMatch ? parseInt(locationMatch[1]) : undefined,
      column: locationMatch ? parseInt(locationMatch[2]) : undefined,
      expected: expectedTokens.length > 0 ? expectedTokens : undefined,
    });
  }

  if (backendError) {
    errors.push({
      type: "backend",
      message: backendError,
    });
  }

  const lexicalCount = errors.filter(e => e.type === "lexical").length;
  const semanticCount = errors.filter(e => e.type === "semantic").length;
  const backendCount = errors.filter(e => e.type === "backend").length;
  const hasErrors = lexicalCount > 0 || semanticCount > 0 || backendCount > 0;

  return (
    <div className="terminal-panel">
      <div className="header">Terminal</div>
      <div className="term-log" aria-live="polite">
        {hasErrors && (
          <div className="error-summary">
            {lexicalCount > 0 && <span className="error-count">Lexical: {lexicalCount}</span>}
            {semanticCount > 0 && <span className="error-count">Semantic: {semanticCount}</span>}
            {backendCount > 0 && <span className="error-count">Backend: {backendCount}</span>}
          </div>
        )}
        {errors.length === 0 && (
          <div className="term-log__empty">No errors detected.</div>
        )}
        {errors.map((error, idx) => (
          <div key={idx} className="error-container">
            <div className="error-item">
              <span className={`error-badge error-badge--${error.type}`}>
                {error.type.toUpperCase()}
              </span>
              <span className="error-message">{error.message}</span>
            </div>
            {error.unexpectedToken && (
              <div className="error-details">
                <div className="error-detail-line">
                  Unexpected token: <span className="token-value">{error.unexpectedToken}</span>
                </div>
              </div>
            )}
            {error.expected && error.expected.length > 0 && (
              <div className="error-details">
                <div className="error-detail-line">
                  Expected tokens: {error.expected.join(", ")}
                </div>
              </div>
            )}
            {renderKeywordSuggestions(error.message)}
          </div>
        ))}
      </div>
    </div>
  );
}
