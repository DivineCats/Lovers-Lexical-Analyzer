import "./Terminals.css";

export type ValidationTokenInfo = {
  lexeme?: string;
  kind?: string;
  line?: number;
  column?: number;
};

export type ValidationResult = {
  ok: boolean;
  message: string;
  code?: string;
  token?: ValidationTokenInfo;
  expected?: string[];
};

export type ErrorItem = {
  type: "lexical" | "syntax" | "semantic";
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
};

export default function Terminal({ validation = null, lexError = null, lexErrors = [] }: Props) {
  // Parse lexical errors into structured format
  const errors: ErrorItem[] = [];
  
  if (lexErrors.length > 0) {
    lexErrors.forEach((err) => {
      const lines = err.split(/\r?\n/).filter(line => line.trim().length > 0);
      const firstLine = lines[0] || "";
      
      // Extract line and column if present (format: "at line X, column Y" or "at X:Y")
      const locationMatch = firstLine.match(/at (?:line )?(\d+)[,:]\s*(?:column )?(\d+)/i);
      
      // Extract expected tokens
      let expectedTokens: string[] = [];
      const expectedLine = lines.find(line => line.toLowerCase().includes("expected one of:"));
      if (expectedLine) {
        const expectedPart = expectedLine.split(/expected one of:/i)[1];
        if (expectedPart) {
          expectedTokens = expectedPart
            .split(/[,\s]+/)
            .map(t => t.trim().replace(/^['"`-]+|['"`-]+$/g, ''))
            .filter(t => t.length > 0);
        }
      }
      
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
    
    // Extract expected tokens
    let expectedTokens: string[] = [];
    const expectedLine = lines.find(line => line.toLowerCase().includes("expected one of:"));
    if (expectedLine) {
      const expectedPart = expectedLine.split(/expected one of:/i)[1];
      if (expectedPart) {
        expectedTokens = expectedPart
          .split(/[,\s]+/)
          .map(t => t.trim().replace(/^['"`-]+|['"`-]+$/g, ''))
          .filter(t => t.length > 0);
      }
    }
    
    errors.push({
      type: "lexical",
      message: firstLine,
      line: locationMatch ? parseInt(locationMatch[1]) : undefined,
      column: locationMatch ? parseInt(locationMatch[2]) : undefined,
      expected: expectedTokens.length > 0 ? expectedTokens : undefined,
    });
  }

  const lexicalCount = errors.filter(e => e.type === "lexical").length;
  const syntaxCount = 0; // Disabled for now
  const semanticCount = 0; // Disabled for now
  const hasErrors = lexicalCount > 0 || syntaxCount > 0 || semanticCount > 0;

  return (
    <div className="terminal-panel">
      <div className="header">Terminal</div>
      <div className="term-log" aria-live="polite">
        {hasErrors && (
          <div className="error-summary">
            {lexicalCount > 0 && <span className="error-count">Lexical: {lexicalCount}</span>}
            {/* {syntaxCount > 0 && <span className="error-count">Syntax: {syntaxCount}</span>} */}
            {/* {semanticCount > 0 && <span className="error-count">Semantic: {semanticCount}</span>} */}
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
          </div>
        ))}
      </div>
    </div>
  );
}
