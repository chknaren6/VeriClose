import { useCallback, useEffect, useState } from "react";

import { getRuntimeStatus } from "./api/client";
import type { RuntimeStatus } from "./api/types";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; runtime: RuntimeStatus }
  | { kind: "error"; message: string };

const pipeline = ["Gateway", "Bank", "ERP", "Verify", "Review"];

export default function App() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  const loadRuntime = useCallback((signal?: AbortSignal) => {
    setState({ kind: "loading" });
    getRuntimeStatus(signal)
      .then((runtime) => setState({ kind: "ready", runtime }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({
          kind: "error",
          message: error instanceof Error ? error.message : "Unknown connectivity failure",
        });
      });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadRuntime(controller.signal);
    return () => controller.abort();
  }, [loadRuntime]);

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="VeriClose home">
          <span className="brand-mark" aria-hidden="true">V</span>
          <span>VeriClose</span>
        </a>
        <span className="synthetic-notice">Synthetic data only</span>
      </header>

      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">Evidence-first finance operations</p>
        <h1 id="hero-title">Prove where the money went.</h1>
        <p className="hero-copy">
          Settlement-to-bank-to-ERP reconciliation that clears only provable cases and
          exposes every unresolved exception.
        </p>

        <ol className="pipeline" aria-label="Planned reconciliation pipeline">
          {pipeline.map((item, index) => (
            <li key={item}>
              <span>{index + 1}</span>
              {item}
            </li>
          ))}
        </ol>
      </section>

      <section className="status-card" aria-live="polite">
        <div>
          <p className="status-label">Walking skeleton</p>
          <h2>Runtime connection</h2>
        </div>

        {state.kind === "loading" && <p className="status-message">Checking API readiness…</p>}

        {state.kind === "error" && (
          <div className="error-state" role="alert">
            <p>The web shell cannot reach the VeriClose API.</p>
            <code>{state.message}</code>
            <button type="button" onClick={() => loadRuntime()}>
              Retry connection
            </button>
          </div>
        )}

        {state.kind === "ready" && (
          <div className="ready-state">
            <p className="ready-line">
              <span className="ready-dot" aria-hidden="true" />
              VeriClose is ready
            </p>
            <dl className="runtime-grid">
              <div>
                <dt>Environment</dt>
                <dd>{state.runtime.meta.environment}</dd>
              </div>
              <div>
                <dt>Build</dt>
                <dd>{state.runtime.meta.build_commit}</dd>
              </div>
              <div>
                <dt>AI mode</dt>
                <dd>{state.runtime.meta.model_enabled ? "Model enabled" : "Deterministic fallback"}</dd>
              </div>
              <div>
                <dt>Storage</dt>
                <dd>{state.runtime.ready.checks.data_directory}</dd>
              </div>
            </dl>
          </div>
        )}
      </section>

      <footer>
        <span>Foundation milestone M0</span>
        <a href="/docs">API documentation</a>
      </footer>
    </main>
  );
}
