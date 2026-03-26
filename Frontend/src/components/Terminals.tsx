import { useState, useEffect, useMemo } from "react";
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
  semanticErrors?: ValidationError[];
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
  source?: string | null;
  validation?: ValidationResult | null;
  lexError?: string | null;
  lexErrors?: string[];
  backendError?: string | null;
  /** Captured stdout from POST /run (interpreter). */
  programStdout?: string | null;
  programRunError?: { phase?: string; message?: string } | null;
  /** Three-address code from POST /tac after successful validate. */
  tacText?: string | null;
  tacError?: { phase?: string; message?: string } | null;
};

type TabType = "lexical" | "syntax" | "semantic" | "output" | "tac";

type TacQuadRow = {
  index: string;
  op: string;
  arg1: string;
  arg2: string;
  result: string;
};

function parseTacLineToQuad(index: string, line: string): TacQuadRow {
  const mk = (op: string, arg1 = "", arg2 = "", result = ""): TacQuadRow => ({
    index,
    op,
    arg1: arg1.trim(),
    arg2: arg2.trim(),
    result: result.trim(),
  });
  const s = line.trim();
  if (!s) return mk("");
  if (s.startsWith("//")) return mk("//", s.slice(2).trim());
  if (s.endsWith(":")) return mk("label", "", "", s.slice(0, -1).trim());

  let m = s.match(/^if(False|True)\s+(.+)\s+goto\s+(.+)$/i);
  if (m) return mk(`if ${m[1].toUpperCase()}`, m[2], "", m[3]);

  m = s.match(/^goto\s+(.+)$/i);
  if (m) return mk("goto", "", "", m[1]);

  m = s.match(/^return(?:\s+(.+))?$/i);
  if (m) return mk("return", m[1] ?? "");

  m = s.match(/^printNewline$/i);
  if (m) return mk("printNewline");

  m = s.match(/^print\s+(.+)$/i);
  if (m) return mk("print", m[1]);

  m = s.match(/^param\s+(.+)$/i);
  if (m) return mk("param", m[1]);

  m = s.match(/^(.+)\s*=\s*call\s+([^,]+),\s*(.+)$/i);
  if (m) return mk("call", m[2], m[3], m[1]);

  m = s.match(/^call\s+([^,]+),\s*(.+)$/i);
  if (m) return mk("call", m[1], m[2]);

  m = s.match(/^(.+)\s*=\s*recv_param\s+(.+)$/i);
  if (m) return mk("recv_param", m[2], "", m[1]);

  m = s.match(/^(.+)\s*=\s*strcat\((.+),\s*(.+)\)$/i);
  if (m) return mk("strcat", m[2], m[3], m[1]);

  m = s.match(/^(.+)\s*=\s*(.+)\[(.+)\]$/);
  if (m) return mk("[]", m[2], m[3], m[1]);

  m = s.match(/^(.+)\[(.+)\]\s*=\s*(.+)$/);
  if (m) return mk("[]=", m[3], m[2], m[1]);

  m = s.match(/^(.+)\s*=\s*(.+)\.(.+)$/);
  if (m) return mk(".", m[2], m[3], m[1]);

  m = s.match(/^(.+)\.(.+)\s*=\s*(.+)$/);
  if (m) return mk(".=", m[3], m[2], m[1]);

  m = s.match(/^(.+)\s*=\s*(.+)\s+(\|\||&&|==|!=|<=|>=|<|>|\+|-|\*|\/|%)\s+(.+)$/);
  if (m) return mk(m[3], m[2], m[4], m[1]);

  m = s.match(/^(.+)\s*=\s*([!~\-])\s*(.+)$/);
  if (m) return mk(m[2], m[3], "", m[1]);

  m = s.match(/^(.+)\s*=\s*(.+)$/);
  if (m) return mk("=", m[2], "", m[1]);

  return mk(s);
}

function parseTacTextToRows(tacText: string): TacQuadRow[] {
  const rows: TacQuadRow[] = [];
  for (const raw of tacText.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    const indexed = line.match(/^\((\d+)\)\s*(.*)$/);
    if (indexed) {
      rows.push(parseTacLineToQuad(indexed[1], indexed[2]));
    } else {
      rows.push(parseTacLineToQuad("", line));
    }
  }
  return rows;
}

export default function Terminal({
  source = null,
  validation = null,
  lexError = null,
  lexErrors = [],
  backendError = null,
  programStdout = null,
  programRunError = null,
  tacText = null,
  tacError = null,
}: Props) {
  const [activeTab, setActiveTab] = useState<TabType>("lexical");

  const isErrorTab =
    activeTab === "lexical" ||
    activeTab === "syntax" ||
    activeTab === "semantic";

  // Auto-switch to first tab that has errors: lexical first, then syntax, then semantic.
  // If no analyzer errors remain, jump to Output by default.
  useEffect(() => {
    const hasLexical = lexErrors.length > 0 || (lexError != null && lexError.trim() !== "");
    const hasSyntax = validation != null && !validation.ok && validation.code !== "ERR_SEMANTIC";
    const hasSemantic = validation != null && !validation.ok && validation.code === "ERR_SEMANTIC";
    if (hasLexical) setActiveTab("lexical");
    else if (hasSyntax) setActiveTab("syntax");
    else if (hasSemantic) setActiveTab("semantic");
    else setActiveTab("output");
  }, [lexErrors.length, lexError, validation]);

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
  if (validation && !validation.ok && validation.code !== "ERR_SEMANTIC") {
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

  if (validation?.semanticErrors && validation.semanticErrors.length > 0) {
    validation.semanticErrors.forEach((err: any) => {
      errors.push({
        type: "semantic",
        message: err.message || "Semantic error",
        line: err.line,
        column: err.column,
        context: err.context,
      });
    });
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

  // Gated analyzer counters (pipeline-style):
  // - lexical errors also block syntax + semantic
  // - syntax errors block semantic
  const hasLexicalErrors = lexicalCount > 0;
  const hasSyntaxErrors = syntaxCount > 0;
  const syntaxDisplayCount = hasLexicalErrors ? lexicalCount : syntaxCount;
  const semanticDisplayCount = hasLexicalErrors
    ? lexicalCount
    : hasSyntaxErrors
      ? syntaxCount
      : semanticCount;
  const isSyntaxBlocked = hasLexicalErrors;
  const isSemanticBlocked = hasLexicalErrors || hasSyntaxErrors;
  const hasAnalyzerErrors = lexicalCount > 0 || syntaxCount > 0 || semanticCount > 0;
  const hasOutputContent = programStdout != null || Boolean(programRunError?.message);
  const hasTacContent = (tacText != null && tacText.length > 0) || Boolean(tacError?.message);
  const tacRows = useMemo(
    () => (tacText && tacText.length > 0 ? parseTacTextToRows(tacText) : []),
    [tacText]
  );

  const filteredErrors = errors.filter(error => error.type === activeTab);

  return (
    <div className="terminal-panel">
      <div className="terminal-header">
        <div className="header">Terminal</div>
        <div className="tab-navigation">
          <button
            className={`tab-button ${activeTab === "lexical" ? "active" : ""}`}
            onClick={() => setActiveTab("lexical")}
          >
            Lexical ({lexicalCount})
          </button>
          <button
            className={`tab-button ${activeTab === "syntax" ? "active" : ""}`}
            onClick={() => setActiveTab("syntax")}
          >
            Syntax ({syntaxDisplayCount})
          </button>
          <button
            className={`tab-button ${activeTab === "semantic" ? "active" : ""}`}
            onClick={() => setActiveTab("semantic")}
          >
            Semantic ({semanticDisplayCount})
          </button>
          <button
            className={`tab-button ${activeTab === "output" ? "active" : ""}`}
            onClick={() => setActiveTab("output")}
            disabled={!hasOutputContent && hasAnalyzerErrors}
          >
            Output
          </button>
          <button
            className={`tab-button ${activeTab === "tac" ? "active" : ""}`}
            onClick={() => setActiveTab("tac")}
            disabled={!hasTacContent}
          >
            TAC
          </button>
        </div>
      </div>
      <div className="term-log" aria-live="polite">
        {activeTab === "output" && (
          <div className="c-gen-panel">
            {programRunError?.message ? (
              <div className="error-container">
                <div className="error-item">
                  <span className="error-badge error-badge--backend">RUN</span>
                  <span className="error-message">
                    {programRunError.message}
                    {programRunError.phase ? (
                      <span className="error-location-inline"> ({programRunError.phase})</span>
                    ) : null}
                  </span>
                </div>
              </div>
            ) : programStdout != null ? (
              <>
                <div className="c-gen-hint">== LOVE OF MY LIFE EXECUTED SUCCESFULLY &lt;3 ==</div>
                {programStdout.length > 0 ? (
                  <pre className="c-source-pre" tabIndex={0}>{programStdout}</pre>
                ) : (
                  <div className="term-log__empty">(no output)</div>
                )}
              </> 
            ) : null}
          </div>
        )}
        {activeTab === "tac" && (
          <div className="c-gen-panel">
            {tacError?.message ? (
              <div className="error-container">
                <div className="error-item">
                  <span className="error-badge error-badge--backend">TAC</span>
                  <span className="error-message">
                    {tacError.message}
                    {tacError.phase ? (
                      <span className="error-location-inline"> ({tacError.phase})</span>
                    ) : null}
                  </span>
                </div>
              </div>
            ) : tacText != null && tacText.length > 0 ? (
              <>
                <div className="c-gen-hint">== TAC ==</div>
                {tacRows.length > 0 ? (
                  <div className="tac-split">
                    <pre className="tac-list-pre" tabIndex={0}>{tacText}</pre>
                    <div className="tac-table-wrap" tabIndex={0}>
                      <table className="tac-table">
                        <thead>
                          <tr>
                            <th>Index</th>
                            <th>op</th>
                            <th>arg1</th>
                            <th>arg2</th>
                            <th>result</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tacRows.map((row, i) => (
                            <tr key={`${row.index}-${i}`}>
                              <td>{row.index ? `(${row.index})` : ""}</td>
                              <td>{row.op}</td>
                              <td>{row.arg1}</td>
                              <td>{row.arg2}</td>
                              <td>{row.result}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <pre className="c-source-pre" tabIndex={0}>{tacText}</pre>
                )}
              </>
            ) : null}
          </div>
        )}
        {isErrorTab &&
          filteredErrors.length === 0 &&
          !(activeTab === "syntax" && isSyntaxBlocked) &&
          !(activeTab === "semantic" && isSemanticBlocked) && (
          <div className="term-log__empty">
            {hasErrors ? `No ${activeTab} errors detected.` : "No errors detected."}
          </div>
        )}
        {isErrorTab && filteredErrors.map((error, idx) => {
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

          // Code snippet: show offending line with caret when we have source + line/column
          const sourceLines = source ? source.split(/\r?\n/) : [];
          const errorLineContent = error.line != null && error.line >= 1 && error.line <= sourceLines.length
            ? sourceLines[error.line - 1]
            : null;
          const caretColumn = (error.column != null && error.column >= 1 && errorLineContent != null)
            ? Math.min(error.column - 1, errorLineContent.length)
            : null;
          const showCodeSnippet = errorLineContent != null && caretColumn != null;

          return (
            <div key={idx} className={`error-container${error.type === "lexical" ? " error-container--lexical" : ""}`}>
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

              {/* Middle: code snippet with line number and caret pointing to error */}
              {showCodeSnippet && (
                <div className="error-code-snippet">
                  <div className="error-code-snippet-line">
                    <span className="error-code-line-num">{error.line}</span>
                    <span className="error-code-line">{errorLineContent}</span>
                  </div>
                  <div className="error-code-snippet-caret">
                    <span className="error-code-line-num" aria-hidden></span>
                    <span className="error-code-caret-line">
                      {" ".repeat(caretColumn)}^
                    </span>
                  </div>
                </div>
              )}

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
        {isErrorTab && isSyntaxBlocked && activeTab === "syntax" && (
          <div className="error-container">
            <div className="error-item">
              <span className="error-badge error-badge--syntax">SYNTAX</span>
              <span className="error-message">Lexical errors detected. Resolve them before syntax analysis.</span>
            </div>
          </div>
        )}
        {/* Show prompt for semantic gating by earlier phases */}
        {isErrorTab && activeTab === "semantic" && isSemanticBlocked && (
          <div className="error-container">
            <div className="error-item">
              <span className="error-badge error-badge--semantic">SEMANTIC</span>
              <span className="error-message">
                {hasLexicalErrors
                  ? "Lexical errors detected. Resolve them before semantic analysis."
                  : "Syntax errors detected. Resolve them before semantic analysis."}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
