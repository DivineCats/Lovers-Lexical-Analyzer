import { useCallback, useEffect, useState } from "react";
import Header from "./components/Header";
import Editor, { type FileTab } from "./components/Editor";
import TokenTable from "./components/TokenTable";
import Terminal, { type ValidationResult } from "./components/Terminals";
import "./App.css";

type TokenRow = { lexeme: string; token: string; tokenType: string };
type TokenStatus = "idle" | "loading" | "ready" | "error";
type LexResult = { rows: TokenRow[]; hasLexError: boolean };

const TOKEN_STATUS_LABEL: Record<TokenStatus, string> = {
  idle: "Idle",
  loading: "Lexing…",
  ready: "Synced",
  error: "Error",
};

const DEFAULT_SOURCE = `love () {
  express << "hello, lover";
}
`;

const DEFAULT_FILE: FileTab = {
  id: "main-love",
  name: "main.love",
  content: DEFAULT_SOURCE,
};

const EMPTY_SOURCE_MESSAGE = "A main program is needed in order to run.";

const API_BASE =
  import.meta.env.VITE_API_BASE?.trim() ||
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  "";

const normalizeEndpoint = (
  rawValue: string | undefined,
  fallbackPath: "/lex" | "/validate"
) => {
  const value = rawValue?.trim();
  if (value) {
    const lower = value.toLowerCase();
    if (lower.endsWith("/lex") || lower.endsWith("/validate")) {
      return value;
    }
    return `${value.replace(/\/+$/, "")}${fallbackPath}`;
  }

  if (API_BASE) {
    return `${API_BASE.replace(/\/+$/, "")}${fallbackPath}`;
  }

  return fallbackPath;
};

function useDebounce<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}

const LEX_ENDPOINT = normalizeEndpoint(import.meta.env.VITE_LEX_ENDPOINT, "/lex");
const VALIDATE_ENDPOINT = normalizeEndpoint(
  import.meta.env.VITE_VALIDATE_ENDPOINT,
  "/validate"
);

const normalizeRunEndpoint = (rawValue: string | undefined) => {
  const value = rawValue?.trim();
  if (value) {
    const lower = value.toLowerCase();
    if (lower.endsWith("/run")) {
      return value;
    }
    return `${value.replace(/\/+$/, "")}/run`;
  }
  if (API_BASE) {
    return `${API_BASE.replace(/\/+$/, "")}/run`;
  }
  return "/run";
};

const RUN_ENDPOINT = normalizeRunEndpoint(import.meta.env.VITE_RUN_ENDPOINT);

const normalizeTacEndpoint = (rawValue: string | undefined) => {
  const value = rawValue?.trim();
  if (value) {
    const lower = value.toLowerCase();
    if (lower.endsWith("/tac")) {
      return value;
    }
    return `${value.replace(/\/+$/, "")}/tac`;
  }
  if (API_BASE) {
    return `${API_BASE.replace(/\/+$/, "")}/tac`;
  }
  return "/tac";
};

const TAC_ENDPOINT = normalizeTacEndpoint(import.meta.env.VITE_TAC_ENDPOINT);

async function parseResponseBody(
  resp: Response
): Promise<{ data: any; raw: string | null }> {
  const text = await resp.text();
  if (!text) {
    return { data: {}, raw: null };
  }
  try {
    return { data: JSON.parse(text), raw: null };
  } catch {
    return { data: {}, raw: text };
  }
}

export default function App() {
  const [source, setSource] = useState(DEFAULT_SOURCE);
  const [rows, setRows] = useState<TokenRow[]>([]);
  const [status, setStatus] = useState<TokenStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [lexError, setLexError] = useState<string | null>(null);
  const [lexErrors, setLexErrors] = useState<string[]>([]);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [parserType] = useState<"rd" | "parserv2">("parserv2");
  const [isRunning, setIsRunning] = useState(false);
  const [programStdout, setProgramStdout] = useState<string | null>(null);
  const [programRunError, setProgramRunError] = useState<{
    phase?: string;
    message?: string;
  } | null>(null);
  const [tacText, setTacText] = useState<string | null>(null);
  const [tacError, setTacError] = useState<{
    phase?: string;
    message?: string;
  } | null>(null);

  const debouncedSource = useDebounce(source, 450);

  const lexSource = useCallback(async (text: string): Promise<LexResult> => {
    const body = text ?? "";
    if (!body.trim()) {
      // Empty or whitespace-only source: no lexical error, clear tokens and status.
      // The syntax stage will report a structured ERR_EMPTY instead.
      setRows([]);
      setStatus("idle");
      setError(null);
      setLexError(null);
      setLexErrors([]);
      setBackendError(null);
      setLastRunAt(null);
      return { rows: [], hasLexError: false };
    }

    setStatus("loading");
    setError(null);
    setLexError(null);
    setLexErrors([]);
    setBackendError(null);

    try {
      const resp = await fetch(LEX_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: body }),
      });

      const { data: payload, raw } = await parseResponseBody(resp);
      if (!resp.ok) {
        const detail =
          (payload?.error as string | undefined) ??
          (payload?.message as string | undefined) ??
          raw?.trim();
        const backendMsg = detail || `Request failed (${resp.status})`;
        setBackendError(backendMsg);
        setError(backendMsg);
        setStatus("error");
        setRows([]);
        return { rows: [], hasLexError: false };
      }

      const nextRows = Array.isArray(payload?.rows)
        ? (payload.rows as TokenRow[])
        : [];

      setRows(nextRows);
      setStatus("ready");
      
      // Check for multiple errors
      const hasMultipleErrors = Array.isArray(payload?.errors) && payload.errors.length > 0;
      const hasSingleError = typeof payload?.error === "string" && payload.error.trim().length > 0;
      
      if (hasMultipleErrors) {
        setLexErrors(payload.errors as string[]);
        setLexError(payload.errors.join("\n\n"));
      } else if (hasSingleError) {
        setLexError(payload.error as string);
        setLexErrors([payload.error as string]);
      }
      
      setLastRunAt(new Date());
      return { rows: nextRows, hasLexError: hasMultipleErrors || hasSingleError };
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to lex source.";
      setBackendError(message);
      setError(message);
      setLexError(null);
      setLexErrors([]);
      setStatus("error");
      return { rows: [], hasLexError: false };
    }
  }, []);

  const syntaxSource = useCallback(async (contentOverride?: string): Promise<ValidationResult> => {
    const body = (contentOverride ?? source ?? "").trim();
    if (!body) {
      const res: ValidationResult = {
        ok: false,
        message: EMPTY_SOURCE_MESSAGE,
        code: "ERR_EMPTY",
        expected: ["love"],
      };
      setValidation(res);
      return res;
    }

    try {
      const resp = await fetch(VALIDATE_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: contentOverride ?? source, parser: parserType }),
      });
      const { data: payload, raw } = await parseResponseBody(resp);

      if (resp.ok && payload?.ok) {
        const success: ValidationResult = {
          ok: true,
          message: (payload?.message as string) ?? "Structure looks valid.",
          code: payload?.code as string | undefined,
        };
        setValidation(success);
        return success;
      }

      const failureMessage =
        (payload?.message as string | undefined) ??
        (payload?.error as string | undefined) ??
        raw?.trim() ??
        `Validation failed (HTTP ${resp.status})`;

      const syntaxErrors = Array.isArray(payload?.errors)
        ? (payload.errors as any[]).map(err => ({
            ok: Boolean(err?.ok ?? false),
            message: (err?.message as string) ?? "Syntax error",
            code: err?.code as string | undefined,
            token: err?.token as ValidationResult["token"],
            expected: Array.isArray(err?.expected)
              ? (err.expected as string[])
              : undefined,
            line: err?.line as number | undefined,
            column: err?.column as number | undefined,
            found: err?.found as string | undefined,
            context: err?.context as string | undefined,
          }))
        : undefined;

      const semanticErrors = Array.isArray(payload?.semantic_errors)
        ? (payload.semantic_errors as any[]).map(err => ({
            ok: false,
            message: (err?.message as string) ?? "Semantic error",
            code: err?.code as string | undefined,
            line: err?.line as number | undefined,
            column: err?.column as number | undefined,
          }))
        : undefined;

      const failure: ValidationResult = {
        ok: false,
        message: failureMessage,
        code: payload?.code as string | undefined,
        token: payload?.token as ValidationResult["token"],
        expected: Array.isArray(payload?.expected)
          ? (payload.expected as string[])
          : undefined,
        errors: payload?.code === "ERR_SEMANTIC" ? undefined : syntaxErrors,
        semanticErrors,
        line: payload?.line as number | undefined,
        column: payload?.column as number | undefined,
        found: payload?.found as string | undefined,
      };
      setValidation(failure);
      return failure;
    } catch (err) {
      const failure: ValidationResult = {
        ok: false,
        message:
          err instanceof Error ? err.message : "Failed to reach validator.",
      };
      setValidation(failure);
      return failure;
    }
  }, [source, parserType]);

  useEffect(() => {
    setProgramStdout(null);
    setProgramRunError(null);
    setTacText(null);
    setTacError(null);
  }, [debouncedSource]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const { hasLexError } = await lexSource(debouncedSource);
      if (cancelled) return;
      // If lexing succeeds (or source is empty), always run syntax;
      // only skip syntax when there are real lexical errors.
      if (!hasLexError) {
        const v = await syntaxSource(debouncedSource);
        if (cancelled) return;
        if (v.ok) {
          try {
            const resp = await fetch(TAC_ENDPOINT, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ source: debouncedSource }),
            });
            const { data: payload } = await parseResponseBody(resp);
            if (cancelled) return;
            if (resp.ok && payload?.ok && typeof payload?.tac === "string") {
              setTacText(payload.tac as string);
              setTacError(null);
            } else {
              setTacText(null);
              setTacError({
                phase: payload?.phase as string | undefined,
                message:
                  (payload?.message as string | undefined) ??
                  `TAC failed (HTTP ${resp.status})`,
              });
            }
          } catch {
            if (!cancelled) {
              setTacText(null);
              setTacError({ message: "Failed to fetch TAC." });
            }
          }
        } else {
          setTacText(null);
          setTacError(null);
        }
      } else {
        setValidation(null);
        setTacText(null);
        setTacError(null);
      }
    })();
    return () => { cancelled = true; };
  }, [debouncedSource, lexSource, syntaxSource]);

  const hasLexOrSyntaxError =
    lexErrors.length > 0 || (validation != null && !validation.ok);

  const handleRunCode = useCallback(async () => {
    setIsRunning(true);
    setProgramStdout(null);
    setProgramRunError(null);
    try {
      const { hasLexError } = await lexSource(source);
      // Run syntax whenever lexing succeeds (or source is empty),
      // and only clear syntax state on true lexical errors.
      if (!hasLexError) {
        const v = await syntaxSource(source);
        if (!v.ok) {
          return;
        }
      } else {
        setValidation(null);
        return;
      }

      const resp = await fetch(RUN_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, stdin: "" }),
      });
      const { data: payload } = await parseResponseBody(resp);
      if (resp.ok && payload?.ok) {
        setProgramStdout((payload.stdout as string) ?? "");
        return;
      }
      const msg =
        (payload?.message as string | undefined) ??
        (payload?.error as string | undefined) ??
        `Run failed (HTTP ${resp.status})`;
      setProgramRunError({
        phase: payload?.phase as string | undefined,
        message: msg,
      });
    } finally {
      setIsRunning(false);
    }
  }, [lexSource, syntaxSource, source]);

  const handleEditorChange = useCallback(
    (files: FileTab[], activeId: string) => {
      const active = files.find(f => f.id === activeId);
      if (active) setSource(active.content);
    },
    []
  );

  return (
    <div className="app-shell">
      <Header
        label="main.love"
        right={
          <div className="header-actions">
            <button
              onClick={handleRunCode}
              disabled={isRunning || hasLexOrSyntaxError}
              className={[
                "run-button",
                (isRunning || hasLexOrSyntaxError) ? "run-button--disabled" : "",
                hasLexOrSyntaxError ? "run-button--error" : "",
              ].filter(Boolean).join(" ")}
            >
              {isRunning ? "Running..." : "▶ Run"}
            </button>

            <span className={`status status--${status}`} title={TOKEN_STATUS_LABEL[status]} aria-label={TOKEN_STATUS_LABEL[status]} />
          </div>
        }
      />
      <main className="app">
        <section className="panel panel--editor">
          <Editor initialFiles={[DEFAULT_FILE]} onChangeFiles={handleEditorChange} />
        </section>
        <section className="panel panel--tokens">
          <TokenTable rows={rows} status={status} error={error} lastRunAt={lastRunAt} />
        </section>
        <section className="panel panel--terminal">
          <Terminal
            source={source}
            validation={validation}
            lexError={lexError}
            lexErrors={lexErrors}
            backendError={backendError}
            programStdout={programStdout}
            programRunError={programRunError}
            tacText={tacText}
            tacError={tacError}
          />
        </section>
      </main>
    </div>
  );
}
