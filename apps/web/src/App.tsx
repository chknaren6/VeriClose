import { useEffect, useMemo, useState } from "react";

import {
  applyCorrection, askRunQuestion, detectUploads, exportAction, getAction, getCase, getRun,
  getRuntimeStatus, importUploads, investigateCase, listCases, proposeAction, recordReview,
  resetDemo, reviewAction, reviewInvestigation, startRun,
} from "./api/client";
import type {
  CaseDetail, CaseItem, CorrectionResult, Detection, FinanceEvent, GroundedAnswer, ImportResult,
  ProofCheck, ProposedAction, RunResult, RuntimeStatus, UploadDocument, UploadPayload,
} from "./api/types";

type Slot = "gateway" | "bank" | "erp";
type Phase = "empty" | "reading" | "detected" | "validating" | "processing" | "ready" | "error";
type Page = "overview" | "cases" | "control-flow";

const pathForPage: Record<Page, string> = { overview: "/", cases: "/cases", "control-flow": "/control-flow" };
const pageFromPath = (): Page => window.location.pathname.startsWith("/cases")
  ? "cases"
  : window.location.pathname.startsWith("/control-flow") ? "control-flow" : "overview";

const slots: Array<{ id: Slot; title: string; hint: string }> = [
  { id: "gateway", title: "Gateway file", hint: "Payments, refunds, fees and tax per settlement" },
  { id: "bank", title: "Bank statement", hint: "Credits, value dates and UTRs" },
  { id: "erp", title: "Ledger export", hint: "Journal lines with accounts" },
];
const proofLevels = ["PROVED", "SUPPORTED", "AMBIGUOUS", "CONTRADICTED", "INVALID_INPUT"] as const;
// Plain-language maps so the demo reads like a finance tool, not a model dump.
const proofInfo: Record<string, { short: string; what: string }> = {
  PROVED: { short: "Cleared", what: "Every check passed. Safe to close." },
  SUPPORTED: { short: "Looks OK", what: "Evidence mostly lines up. A person should still confirm." },
  AMBIGUOUS: { short: "Needs a call", what: "More than one explanation fits. You need to choose." },
  CONTRADICTED: { short: "Blocked", what: "Evidence disagrees. Fix it before this can clear." },
  INVALID_INPUT: { short: "Bad data", what: "A source row is unusable. Fix the file and re-run." },
};
const reasonInfo: Record<string, { title: string; todo: string }> = {
  SETTLEMENT_COMPONENT_MISMATCH: { title: "Gateway totals don't add up", todo: "Payments minus fees and tax differ from the reported net. Open the gateway rows." },
  BANK_AMOUNT_MISMATCH: { title: "Bank paid a different amount", todo: "The reference matches but the paise don't. Compare gateway vs bank rows." },
  ERP_POSTING_MISMATCH: { title: "Ledger doesn't match the bank", todo: "The journal differs from money actually received. Correct the ERP lines." },
  REFERENCE_MISMATCH: { title: "Reference doesn't prove the link", todo: "Amount and date fit, but the UTR or reference is off. Confirm it." },
  MISSING_BANK_RECEIPT: { title: "No bank receipt found", todo: "Gateway expects money in, but no bank row proves it. Check UTR and value date." },
  MISSING_ERP_POSTING: { title: "Missing from the ledger", todo: "Money arrived, but no balanced journal records it. Post or fix the entry." },
  BANK_RECEIPT_AMBIGUOUS: { title: "Two bank rows could fit", todo: "VeriClose stopped instead of guessing. Pick the one correct UTR." },
  ERP_JOURNAL_UNBALANCED: { title: "Journal doesn't balance", todo: "Debits and credits differ. Fix the unbalanced side." },
  BANK_DATE_OUT_OF_RANGE: { title: "Paid outside the window", todo: "Value date is outside the allowed range. Check if it belongs to another cycle." },
  ORPHAN_BANK_CREDIT: { title: "Bank money with no settlement", todo: "A credit arrived with no gateway expectation. Trace it back." },
  ORPHAN_ERP_POSTING: { title: "Ledger entry with no proof", todo: "The ledger records money neither source proves. Trace it back." },
  DUPLICATE_ERP_POSTING: { title: "Same ledger entry twice", todo: "Only one entry can count. Keep the right one." },
  DUPLICATE_IDENTIFIER: { title: "Same reference twice", todo: "A repeated UTR blocks a unique match. Confirm the right record." },
  UNKNOWN_UNRESOLVED: { title: "Needs a look", todo: "Checks blocked this case. Work through the cited rows." },
};
const actionInfo: Record<string, string> = {
  CLARIFICATION_REQUEST: "Ask for missing proof",
  JOURNAL_EXPORT: "Prepare a balanced journal",
  MAPPING_CORRECTION: "Fix the file mapping",
  CORRECTED_DATA_IMPORT: "Import a corrected file",
  WAIT: "Wait and re-check",
  ACCEPT_DIFFERENCE: "Accept the difference",
  MANUAL_REVIEW: "Review manually",
  NO_ACTION: "No action needed",
};
const plainProof = (level: string) => proofInfo[level]?.short ?? labelize(level);
const plainReason = (code: string | null | undefined) =>
  (code && reasonInfo[code]?.title) || (code ? labelize(code) : "All checks passed");
const plainAction = (code: string | null | undefined) =>
  (code && actionInfo[code]) || (code ? labelize(code) : "A person reviews");
const integer = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const inr = (value: number) => {
  const amount = Math.abs(value);
  return `${value < 0 ? "−" : ""}₹${integer.format(Math.floor(amount / 100))}.${String(amount % 100).padStart(2, "0")}`;
};
const labelize = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const asMinor = (value: unknown) => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) return Number(value);
  return null;
};

async function encodeFile(file: File, fileId: Slot): Promise<UploadDocument> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 8192) binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
  return { file_id: fileId, original_name: file.name, media_type: file.type || "application/octet-stream", content_base64: btoa(binary) };
}

export default function App() {
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [files, setFiles] = useState<Partial<Record<Slot, File>>>({});
  const [payload, setPayload] = useState<UploadPayload | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [selectedProfiles, setSelectedProfiles] = useState<Record<string, string>>({});
  const [phase, setPhase] = useState<Phase>("empty");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [imported, setImported] = useState<ImportResult | null>(null);
  const [run, setRun] = useState<RunResult | null>(null);
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [selected, setSelected] = useState<CaseDetail | null>(null);
  const [action, setAction] = useState<ProposedAction | null>(null);
  const [correction, setCorrection] = useState<CorrectionResult | null>(null);
  const [actionRationale, setActionRationale] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [reviewState, setReviewState] = useState("DEFERRED");
  const [reviewer, setReviewer] = useState("finance-reviewer");
  const [comment, setComment] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<GroundedAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState("");
  const [caseLoading, setCaseLoading] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [page, setPage] = useState<Page>(pageFromPath);

  const navigate = (next: Page) => {
    const nextPath = pathForPage[next];
    if (window.location.pathname !== nextPath) window.history.pushState({}, "", nextPath);
    setPage(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const controller = new AbortController();
    getRuntimeStatus(controller.signal).then(setRuntime).catch((reason: Error) => {
      if (reason.name !== "AbortError") { setError(reason.message); setPhase("error"); }
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const handleNavigation = () => setPage(pageFromPath());
    window.addEventListener("popstate", handleNavigation);
    return () => window.removeEventListener("popstate", handleNavigation);
  }, []);

  const loadCompletedRun = async (completed: RunResult) => {
    const runCases = await listCases(completed.run_id);
    setRun(completed);
    setCases(runCases);
    const hero = runCases.find((item) => item.proof_level === "PROVED") ?? runCases[0];
    setSelected(hero ? await getCase(hero.case_id) : null);
    setPhase("ready");
  };

  const inspect = async () => {
    if (!slots.every(({ id }) => files[id])) return;
    try {
      setPhase("reading"); setError(""); setNotice("");
      const documents = await Promise.all(slots.map(({ id }) => encodeFile(files[id] as File, id)));
      const prepared: UploadPayload = {
        run_id: `close-${new Date().toISOString().replace(/[^0-9]/g, "").slice(0, 14)}`,
        legal_entity_id: "demo-merchant-in", documents, confirmations: [],
      };
      const result = await detectUploads(prepared);
      setPayload(prepared); setDetections(result.files);
      setSelectedProfiles(Object.fromEntries(result.files.map((item) => [item.file_id, item.candidates[0]?.profile_versioned_id ?? ""])));
      setPhase("detected");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Detection failed"); setPhase("error"); }
  };

  const reconcile = async () => {
    if (!payload) return;
    try {
      setError(""); setNotice("");
      const confirmed = { ...payload, confirmations: detections.map((item) => {
        const candidate = item.candidates.find((value) => value.profile_versioned_id === selectedProfiles[item.file_id]) ?? item.candidates[0];
        return { file_id: item.file_id, adapter_id: candidate.adapter_id, profile_versioned_id: candidate.profile_versioned_id };
      }) };
      setPhase("validating");
      const result = await importUploads(confirmed); setImported(result);
      if (!result.is_ready) {
        setError("Validation stopped this run. Review the row-level issues, correct the source file, and try again."); setPhase("error"); return;
      }
      setPhase("processing");
      await loadCompletedRun(await startRun(result.run_id));
      setNotice("Close complete. A cleared case is open so you can see what good looks like.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Reconciliation failed"); setPhase("error"); }
  };

  const refreshCase = async (caseId: string) => {
    setSelected(await getCase(caseId));
    if (run) setCases(await listCases(run.run_id));
  };
  const openCase = async (item: CaseItem) => {
    setCaseLoading(true); setError(""); setAction(null); setCorrection(null); setActionRationale(""); setNotice("");
    setQuestion(""); setAnswer(null); navigate("cases");
    try { await refreshCase(item.case_id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not open this case"); }
    finally { setCaseLoading(false); }
  };
  const runCaseAction = async (label: string, operation: () => Promise<void>) => {
    setBusy(true); setBusyLabel(label); setError("");
    try { await operation(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "The requested operation failed"); }
    finally { setBusy(false); setBusyLabel(""); }
  };
  const saveReview = () => runCaseAction("Saving…", async () => {
    if (!selected) return; await recordReview(selected.case_id, reviewState, reviewer, comment); await refreshCase(selected.case_id);
    setComment(""); setNotice("Decision saved. Past decisions stay on record.");
  });
  const investigate = () => runCaseAction("Getting suggestion…", async () => {
    if (!selected) return; await investigateCase(selected.case_id); await refreshCase(selected.case_id);
    setNotice("Suggestion ready. The result didn't change — only the note is new.");
  });
  const judgeInvestigation = (state: "APPROVED" | "REJECTED") => runCaseAction("Saving…", async () => {
    if (!selected) return; await reviewInvestigation(selected.case_id, state, reviewer, comment); await refreshCase(selected.case_id);
    setComment(""); setNotice(`Suggestion ${state === "APPROVED" ? "accepted" : "rejected"}. Kept on record.`);
  });
  const prepareAction = () => runCaseAction("Drafting fix…", async () => {
    if (!selected) return; const proposed = await proposeAction(selected.case_id); setAction(proposed);
    setActionRationale(proposed.payload.rationale ?? ""); setNotice("Fix drafted from the checked rows. You still need to approve it.");
  });
  const judgeAction = (state: "APPROVED" | "REJECTED") => runCaseAction("Saving…", async () => {
    if (!action) return;
    const current = action.payload.rationale ?? "";
    const edits: Record<string, string> = actionRationale.trim() && actionRationale.trim() !== current
      ? { rationale: actionRationale.trim() } : {};
    const reviewed = await reviewAction(action.action_id, state, reviewer, comment, edits);
    setAction(reviewed); setActionRationale(reviewed.payload.rationale ?? ""); setComment("");
    setNotice(`Fix ${state === "APPROVED" ? "approved" : "rejected"}. The original draft stays on record.`);
  });
  const exportApprovedAction = () => runCaseAction("Exporting…", async () => {
    if (!action) return; await exportAction(action.action_id); setAction(await getAction(action.action_id));
    setNotice("Fix exported with receipt. Download it and re-run after correcting the source.");
  });
  const correctAndRerun = () => runCaseAction("Re-running with fix…", async () => {
    if (!action) return;
    const result = await applyCorrection(action.action_id, `corrected-${new Date().toISOString().replace(/[^0-9]/g, "").slice(0, 14)}`);
    setRun(await getRun(result.new_run_id)); setCases(await listCases(result.new_run_id));
    setSelected(result.new_case_id ? await getCase(result.new_case_id) : null); setCorrection(result); setAction(null);
    setActionRationale(""); setQuestion(""); setAnswer(null); setFilter("ALL");
    setNotice(result.resolved
      ? `Fixed: ${plainProof(result.previous_proof_level)} → ${result.new_proof_level ? plainProof(result.new_proof_level) : "open"}. Old result kept.`
      : "Re-ran with the fix, but it still doesn't clear. The rows show why.");
  });
  const askQuestion = () => runCaseAction("Reading saved rows…", async () => {
    if (!run || !question.trim()) return;
    const groundedQuestion = selected && !question.includes(selected.case_id) ? `${question} Case ${selected.case_id}` : question;
    setAnswer(await askRunQuestion(run.run_id, groundedQuestion));
  });
  const restoreDemo = async () => {
    setBusy(true); setBusyLabel("Loading demo close…"); setPhase("processing"); setError(""); setNotice("");
    setImported(null); setSelected(null); setAction(null); setCorrection(null); setActionRationale(""); setQuestion(""); setAnswer(null); setFilter("ALL");
    try { await loadCompletedRun(await resetDemo()); navigate("overview"); setNotice("Demo close loaded fresh. Start with a cleared case, then open a blocked one."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not restore the demo"); setPhase("error"); }
    finally { setBusy(false); setBusyLabel(""); }
  };

  const filtered = useMemo(() => cases.filter((item) => filter === "ALL" || item.proof_level === filter || item.reason_code === filter), [cases, filter]);
  const reasons = [...new Set(cases.map((item) => item.reason_code).filter(Boolean))] as string[];
  const distribution = Object.fromEntries(proofLevels.map((level) => [level, cases.filter((item) => item.proof_level === level).length]));
  const totalRecords = run?.operational_summary ? Math.max(0, ...run.operational_summary.stage_timings.map((timing) => timing.input_count)) : imported?.event_count ?? 0;
  const integrityCases = cases.filter((item) => item.requires_company_input).length;

  return <main className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" onClick={(event) => { event.preventDefault(); navigate("overview"); }}><span className="brand-mark">V</span><span>VeriClose<small>Month-end control</small></span></a>
      <nav className="page-nav" aria-label="Primary navigation"><a className={page === "overview" ? "active" : ""} href="/" onClick={(event) => { event.preventDefault(); navigate("overview"); }}>Summary</a><a className={page === "cases" ? "active" : ""} href="/cases" onClick={(event) => { event.preventDefault(); navigate("cases"); }}>Cases{cases.length > 0 && <small>{cases.length}</small>}</a><a className={page === "control-flow" ? "active" : ""} href="/control-flow" onClick={(event) => { event.preventDefault(); navigate("control-flow"); }}>How it works</a></nav>
      <div className="topbar-actions"><span className="synthetic-notice">Synthetic data only</span>{runtime?.meta.demo_mode && <button className="demo-reset" onClick={restoreDemo} disabled={busy}>Restore demo</button>}<span className={`runtime-pill ${runtime ? "ready" : ""}`}><i />{runtime ? "Ready" : "Connecting…"}</span></div>
    </header>
    {page === "overview" && <section className={`intro ${phase === "ready" ? "compact" : ""}`}>
      <div><p className="eyebrow">Gateway → Bank → Ledger · INR · One business</p><h1>{phase === "ready" ? <>Know where every<br />rupee went.</> : <>Know where every<br />rupee went.</>}</h1></div>
      <div className="product-story" aria-label="Product flow"><div><b>Gateway</b><small>What should have arrived</small></div><span>→</span><div><b>Bank</b><small>What actually arrived</small></div><span>→</span><div><b>Ledger</b><small>What got recorded</small></div><strong>Cleared, or flagged with a reason · every decision cites its rows</strong></div>
    </section>}

    {page === "overview" && phase !== "ready" && <section className="panel import-panel">
      <Heading step="Step 1 · Bring the books together" title="Drop in the three files" copy="We check every row, keep the original values, and remember exactly which file and line each number came from." aside="CSV / XLSX · INR · one business" />
      <div className="upload-grid">{slots.map((slot, index) => <label className={`upload-slot ${files[slot.id] ? "filled" : ""}`} key={slot.id}><input type="file" accept=".csv,.xlsx" onChange={(event) => { const file = event.target.files?.[0]; if (file) setFiles((current) => ({ ...current, [slot.id]: file })); }} /><span className="slot-index">0{index + 1}</span><strong>{slot.title}</strong><small>{files[slot.id]?.name ?? slot.hint}</small><em>{files[slot.id] ? "✓ Ready" : "Choose source file"}</em></label>)}</div>
      {phase === "detected" && <div className="detection-grid">{detections.map((item) => <article key={item.file_id}><span>{item.file_id}</span><select aria-label={`${item.file_id} mapping profile`} value={selectedProfiles[item.file_id] ?? ""} onChange={(event) => setSelectedProfiles((current) => ({ ...current, [item.file_id]: event.target.value }))}>{item.candidates.map((candidate) => <option key={`${candidate.adapter_id}-${candidate.profile_versioned_id}`} value={candidate.profile_versioned_id}>{candidate.profile_versioned_id}</option>)}</select><small>{item.requires_confirmation ? "Confirmation required" : "High-confidence detection"} · {(item.candidates[0]?.confidence_bps ?? 0) / 100}%</small></article>)}</div>}
      {imported && <ValidationSummary result={imported} />}
      {phase === "error" && <div className="alert" role="alert"><strong>Run stopped safely</strong><p>{error}</p><small>No source evidence or prior decision was overwritten.</small></div>}
      {(["reading", "validating", "processing"] as Phase[]).includes(phase) && <ProcessingState phase={phase} label={busyLabel} />}
      <div className="action-row">{!["detected", "reading", "validating", "processing"].includes(phase) && <button className="primary" disabled={!slots.every(({ id }) => files[id])} onClick={inspect}>Inspect files & mappings <span>→</span></button>}{phase === "detected" && <button className="primary" onClick={reconcile}>Confirm mappings & run proof <span>→</span></button>}{phase === "error" && runtime?.meta.demo_mode && <button className="secondary" onClick={restoreDemo} disabled={busy}>Restore known demo instead</button>}</div>
    </section>}

    {page === "overview" && phase === "ready" && run?.operational_summary && <>
      <section className="cockpit panel">
        <div className="section-heading"><div><p className="step">Step 2 · Close summary</p><h2>{integer.format(totalRecords)} rows checked. {integer.format(run.operational_summary.decision_count)} cases decided.</h2><p className="section-copy">Cleared, waiting on you, or blocked with a reason. Select any row below to see its cases.</p></div><div className="run-stamp"><span>CLOSE COMPLETE</span><code>{run.run_id}</code><small>{run.rule_version} · {run.policy_version}</small></div></div>
        <div className="metric-grid"><Metric label="Rows checked" value={integer.format(totalRecords)} note="Gateway · Bank · Ledger" /><Metric label="Cases" value={integer.format(run.operational_summary.decision_count)} note="Nothing left uncounted" /><Metric label="Cleared" value={integer.format(run.operational_summary.verified_count)} note="No action needed" tone="good" /><Metric label="Needs you" value={integer.format(run.operational_summary.review_or_exception_count)} note="Review or fix" tone="warn" /><Metric label="At stake" value={inr(run.operational_summary.amount_at_risk_minor)} note="Uncleared only" tone="risk" /></div>
        <div className="cockpit-detail-grid">
          <section className="proof-distribution"><Subhead eyebrow="Results" title="What happened to the money" aside="Select a row to see cases" /><div className="distribution-list">{proofLevels.map((level) => { const count = distribution[level] ?? 0; const share = count / Math.max(run.operational_summary!.decision_count, 1) * 100; const info = proofInfo[level]; return <button key={level} className={`distribution-row tone-${level.toLowerCase()} has-cases`} disabled={count === 0} onClick={() => { setFilter(level); navigate("cases"); }} title={count === 0 ? "No cases here" : `Open ${count} ${info.short.toLowerCase()} cases`} aria-label={count === 0 ? `${info.short}: none` : `Open ${count} ${info.short} cases`}><span className="status-dot" /><b>{info.short}</b><div><i style={{ width: `${share}%` }} /></div><strong>{count}</strong><small>{Math.round(share)}% · Open →</small></button>; })}</div><p className="distribution-hint">Tip: “Blocked” usually means the bank and gateway disagree on amount or reference. “Looks OK” still wants a quick human confirm.</p></section>
          <aside className="controls-summary"><span>Why you can trust it</span><h3>Checks before suggestions</h3><div><b>Cleared</b><small>means every required check passed</small></div><div><b>{integrityCases}</b><small>wait on proof from outside this file set</small></div><p>An AI score can explain a case. It can never clear one.</p><div className="benchmark-boundary"><strong>This is the live close</strong><span>Test scores are kept separate</span></div></aside>
        </div>
        <div className="run-tools"><div className="artifact-row"><strong>Close pack</strong><a href={`/api/v1/runs/${encodeURIComponent(run.run_id)}/artifacts/close-report`}>Close report ↗</a><a href={`/api/v1/runs/${encodeURIComponent(run.run_id)}/artifacts/exception-pack`}>Exceptions ↗</a><a href={`/api/v1/runs/${encodeURIComponent(run.run_id)}/artifacts/audit-log`}>Audit trail ↗</a></div><div className="overview-next"><span><strong>Cases are ready to review</strong><small>Each one shows its rows, checks, and next step.</small></span><button className="primary" onClick={() => { setFilter("ALL"); navigate("cases"); }}>Review cases <span>→</span></button></div></div>
        {imported && <SourceInspection result={imported} />}
      </section>
    </>}
    {page === "cases" && phase === "ready" && run && <CasesPageHeader run={run} filter={filter} count={filtered.length} navigate={navigate} />}
    {page === "cases" && phase === "ready" && run && <>
      {(notice || error) && <div className={error ? "alert global-message" : "notice global-message"} role={error ? "alert" : "status"}><strong>{error ? "Kept safe — nothing was overwritten" : "Updated"}</strong><span>{error || notice}</span></div>}
      <section className="workspace cases-layout"><div className="queue panel"><div className="queue-head"><div><p className="step">Cases</p><h2>{filter === "ALL" ? "All cases" : plainProof(filter)}</h2></div><select aria-label="Filter cases" value={filter} onChange={(event) => setFilter(event.target.value)}><option value="ALL">All {cases.length} cases</option>{proofLevels.map((level) => <option value={level} key={level}>{proofInfo[level].short} · {distribution[level]}</option>)}{reasons.map((reason) => <option value={reason} key={reason}>{plainReason(reason)}</option>)}</select></div><div className="queue-summary"><span><i className="good" />{distribution.PROVED} cleared</span><span><i className="warn" />{cases.length - distribution.PROVED} need you</span>{filter !== "ALL" && <button className="link-button" onClick={() => setFilter("ALL")}>Clear filter ×</button>}</div><div className="case-list" aria-busy={caseLoading}>{filtered.length ? filtered.map((item) => <button className={`case-row proof-${item.proof_level.toLowerCase()} ${selected?.case_id === item.case_id ? "active" : ""}`} key={item.case_id} onClick={() => openCase(item)}><span className="case-proof"><i />{plainProof(item.proof_level)}</span><span className="case-main"><strong>{item.reason_code ? plainReason(item.reason_code) : "Everything matches"}</strong><small>{item.case_id}</small><em>{caseStatus(item)}</em></span><b>{item.amount_at_risk_minor ? inr(item.amount_at_risk_minor) : "Cleared"}</b>{item.requires_company_input && <small className="integrity-tag">Needs proof from outside these files</small>}</button>) : <div className="empty-state"><strong>No cases here</strong><p>The close itself is fine. Try another result.</p><button onClick={() => setFilter("ALL")}>Show all cases</button></div>}</div></div>
        {caseLoading ? <div className="workbench panel loading-workbench"><span className="loading-mark" /><strong>Loading immutable evidence…</strong><p>The selected case will appear here without changing its state.</p></div> : <CaseWorkbench selected={selected} run={run} action={action} correction={correction} actionRationale={actionRationale} setActionRationale={setActionRationale} reviewer={reviewer} setReviewer={setReviewer} reviewState={reviewState} setReviewState={setReviewState} comment={comment} setComment={setComment} saveReview={saveReview} investigate={investigate} judgeInvestigation={judgeInvestigation} prepareAction={prepareAction} judgeAction={judgeAction} exportApprovedAction={exportApprovedAction} correctAndRerun={correctAndRerun} busy={busy} busyLabel={busyLabel} />}
        <EvidenceAssistant selected={selected} runtime={runtime} question={question} setQuestion={setQuestion} answer={answer} askQuestion={askQuestion} investigate={investigate} busy={busy} busyLabel={busyLabel} />
      </section>
    </>}
    {page === "cases" && phase !== "ready" && <NoRunPage navigate={navigate} restoreDemo={restoreDemo} busy={busy} />}
    {page === "control-flow" && <ControlFlowPage navigate={navigate} hasRun={phase === "ready"} />}
    <FloatingAssistant hasRun={phase === "ready" && Boolean(run)} open={assistantOpen} setOpen={setAssistantOpen} question={question} setQuestion={setQuestion} answer={answer} askQuestion={askQuestion} busy={busy} selected={selected} navigate={navigate} />
    <footer className="site-footer"><span><b>VeriClose</b> · Gateway → Bank → Ledger close</span><span>AI helper: {runtime?.meta.model_enabled ? "on (explains only)" : "off (checks still run)"}</span>{runtime?.meta.environment !== "hosted-demo" && <a href="/docs">API docs ↗</a>}</footer>
  </main>;
}

function caseStatus(item: CaseItem | CaseDetail) {
  if (item.proof_level === "PROVED") return "Cleared";
  if (["SUPPORTED", "AMBIGUOUS"].includes(item.proof_level)) return "Needs review";
  return "Blocked";
}
function Heading({ step, title, copy, aside }: { step: string; title: string; copy: string; aside: string }) { return <div className="section-heading"><div><p className="step">{step}</p><h2>{title}</h2><p className="section-copy">{copy}</p></div><span className="scope">{aside}</span></div>; }
function Subhead({ eyebrow, title, aside }: { eyebrow: string; title: string; aside: string }) { return <div className="subhead"><div><span>{eyebrow}</span><h3>{title}</h3></div><strong>{aside}</strong></div>; }
function Metric({ label, value, note, tone = "neutral" }: { label: string; value: string; note: string; tone?: string }) { return <article className={`metric metric-${tone}`}><small>{label}</small><strong>{value}</strong><span>{note}</span></article>; }
function ProcessingState({ phase, label }: { phase: Phase; label: string }) {
  const stages = [{ id: "reading", label: "Read files" }, { id: "validating", label: "Check rows" }, { id: "processing", label: "Run checks" }];
  const current = stages.findIndex((stage) => stage.id === phase);
  return <div className="processing-state" role="status"><span className="loading-mark" /><div><strong>{label || (phase === "processing" ? "Running the checks…" : "Reading your files…")}</strong><div>{stages.map((stage, index) => <span className={index < current ? "done" : index === current ? "current" : ""} key={stage.id}>{index < current ? "✓" : index + 1} {stage.label}</span>)}</div></div></div>;
}
function ValidationSummary({ result }: { result: ImportResult }) {
  const issues = [...result.files.flatMap((item) => item.issues), ...result.cross_source_issues];
  return <div className="validation-summary"><strong>{result.event_count} rows ready · {result.state}</strong>{issues.length ? <ul>{issues.map((issue, index) => <li key={`${issue.code}-${index}`}><b>{issue.code}</b> {issue.message}<small>{issue.file_id}{issue.row_number ? ` · line ${issue.row_number}` : ""}{issue.field_name ? ` · ${issue.field_name}` : ""} — {issue.suggested_fix}</small></li>)}</ul> : <span>All rows look good. Nothing to fix.</span>}</div>;
}
function SourceInspection({ result }: { result: ImportResult }) { return <details className="source-inspection"><summary>See file mappings, sample rows and totals</summary><div className="source-grid">{result.files.map((file) => <article key={file.file_id}><h3>{file.source_type} · {file.profile_versioned_id}</h3><p>{file.rows_seen} rows · {file.is_valid ? "looks good" : "needs a fix"}</p><h4>How columns map</h4><ul>{file.mapping.filter((field) => field.required).map((field) => <li key={field.canonical_field}><span>{field.source_column ?? "MISSING"}</span> → {field.canonical_field}</li>)}</ul><h4>Totals</h4>{file.control_totals.map((total) => <p key={total.component}>{labelize(total.component)}: <strong>{inr(total.amount_minor)}</strong> · {total.record_count} rows</p>)}<h4>One sample row</h4><pre>{JSON.stringify(file.sample_rows[0] ?? {}, null, 2)}</pre></article>)}</div></details>; }

function CasesPageHeader({ run, filter, count, navigate }: { run: RunResult; filter: string; count: number; navigate: (page: Page) => void }) {
  return <section className="page-header"><div><p className="eyebrow">Cases · {run.run_id.slice(0, 24)}…</p><h1>{filter === "ALL" ? "Work through the exceptions." : `${plainProof(filter)} cases.`}</h1><p>{filter === "ALL" ? "Pick a case on the left. You'll see the gateway, bank and ledger rows side by side, what failed, and what to do next." : `${count} case${count === 1 ? "" : "s"} with “${filter === "ALL" ? "all" : plainProof(filter)}”. Pick one to see its rows and next step.`}</p></div><div className="page-context"><span>CLOSE IN PROGRESS</span><code>{run.run_id}</code><strong>{count} shown</strong><button onClick={() => navigate("overview")}>← Back to summary</button></div></section>;
}

function advisoryView(advisory: CaseDetail["advisory"]) {
  const isFallback = advisory.status === "DETERMINISTIC_FALLBACK";
  const notRequested = !advisory.investigation_id;
  return { isFallback, notRequested, validated: !isFallback && !notRequested };
}

function EvidenceAssistant({ selected, runtime, question, setQuestion, answer, askQuestion, investigate, busy, busyLabel }: {
  selected: CaseDetail | null; runtime: RuntimeStatus | null; question: string; setQuestion: (value: string) => void;
  answer: GroundedAnswer | null; askQuestion: () => Promise<void>; investigate: () => Promise<void>; busy: boolean; busyLabel: string;
}) {
  const failed = selected?.proof_checks.filter((check) => !check.passed) ?? [];
  const advisory = selected?.advisory;
  const view = advisory ? advisoryView(advisory) : null;
  const prompts = selected ? [
    `Why is this case ${plainProof(selected.proof_level).toLowerCase()}?`,
    "Which rows prove it?",
    "What should I do next?",
  ] : [];
  return <aside className="assistant-panel panel" aria-label="Close assistant">
    <header><div><span className="assistant-mark">?</span><div><strong>Close assistant</strong><small>{runtime?.meta.model_enabled ? "AI helper on · checks still decide" : "AI helper off · checks still run"}</small></div></div><i className={runtime ? "online" : ""} /></header>
    <div className="assistant-guard"><b>HELPER ONLY</b><span>It explains. It can't clear a case.</span></div>
    {!selected ? <div className="assistant-empty"><strong>Pick a case</strong><p>I'll explain in plain words why it cleared or got stuck.</p></div> : <>
      <section className="assistant-case"><span>CURRENT CASE</span><code>{selected.case_id}</code><div><strong className={`tone-${selected.proof_level.toLowerCase()}`}>{plainProof(selected.proof_level)}</strong><small>{selected.reason_code ? plainReason(selected.reason_code) : "Everything matches"}</small></div></section>
      <div className="assistant-thread" aria-live="polite">
        <article className="assistant-message system"><span>What the checks found</span><p>{selected.proof_level === "PROVED" ? "Gateway, bank and ledger all agree. Nothing for you to do." : `${failed.length || 1} check${failed.length === 1 ? "" : "s"} stopped this case from clearing. The most useful row links are in the case view.`}</p>{failed.slice(0, 3).map((check) => <small key={check.check_code}>· {labelize(check.check_code)} — saw {displayCheckValue(check, check.observed)}, needed {displayCheckValue(check, check.expected)}</small>)}</article>
        {question && <article className="assistant-message user"><span>You asked</span><p>{question}</p></article>}
        {answer && <article className={`assistant-message response ${answer.status === "ABSTAINED" ? "abstained" : ""}`}><span>{answer.status === "ANSWERED" ? "Answer from the saved rows" : "I need a case reference"}</span><p>{answer.answer}</p></article>}
        {advisory?.investigation_id && view && (view.validated ? <article className="assistant-message advisory"><span>AI suggestion · {advisory.confidence_bps / 100}% sure · advisory</span><p><strong>{advisory.hypothesis ?? "No suggestion returned"}</strong></p><p>{advisory.explanation ?? advisory.message}</p>{advisory.recommended_action && <small> Suggested next step: {plainAction(advisory.recommended_action)}</small>}</article> : <article className="assistant-message advisory fallback"><span>Reviewer note · from the checks</span><p><strong>{advisory.hypothesis ?? "Needs a human look"}</strong></p><p>{advisory.explanation ?? "Work through the cited rows below."}</p>{advisory.recommended_action && <small>Suggested next step: {plainAction(advisory.recommended_action)}</small>}<details><summary>Why no AI suggestion?</summary><small>{advisory.failure_code === "MODEL_UNAVAILABLE" ? "The AI helper didn't return in time, so this note comes from the checks. The result is unchanged." : "The AI answer didn't pass evidence checks, so it was dropped and this checks-based note was kept."}</small></details></article>)}
      </div>
      <div className="assistant-prompts">{prompts.map((prompt) => <button key={prompt} onClick={() => { setQuestion(selected ? `${prompt} (Case ${selected.case_id})` : prompt); }}>{prompt}</button>)}</div>
      <form className="assistant-composer" onSubmit={(event) => { event.preventDefault(); void askQuestion(); }}><label htmlFor="case-question">Ask about this case</label><textarea id="case-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="e.g. Why is this blocked?" rows={3} /><button className="primary" type="submit" disabled={busy || !question.trim()}>{busyLabel === "Reading saved rows…" ? "Checking the saved rows…" : "Ask"}</button></form>
      {selected.proof_level !== "PROVED" && !advisory?.investigation_id && <button className="assistant-investigate" onClick={investigate} disabled={busy}>{busyLabel === "Getting suggestion…" ? "Getting a suggestion…" : "Get an AI suggestion"}<span>{runtime?.meta.model_enabled ? "Plain words, cites rows" : "Will use checks note"}</span></button>}
    </>}
  </aside>;
}

function NoRunPage({ navigate, restoreDemo, busy }: { navigate: (page: Page) => void; restoreDemo: () => Promise<void>; busy: boolean }) {
  return <section className="panel no-run-page"><span className="empty-icon">→</span><p className="eyebrow">No close loaded</p><h1>Cases show up after a close.</h1><p>Load the demo close (25 cases, already worked) or drop in your own three files.</p><div><button className="primary" onClick={restoreDemo} disabled={busy}>Load demo close</button><button className="secondary" onClick={() => navigate("overview")}>Add files</button></div></section>;
}

function ControlFlowPage({ navigate, hasRun }: { navigate: (page: Page) => void; hasRun: boolean }) {
  const stages = [
    ["01", "Bring files in", "Gateway, bank and ledger"], ["02", "Line them up", "One timeline per case"],
    ["03", "Run the checks", "Amounts, references, dates"], ["04", "Hold the risky ones", "No guessing on duplicates"],
    ["05", "You review", "Rows, reason, next step"], ["06", "Fix and re-run", "Old result stays on record"],
  ];
  return <section className="control-page">
    <header className="control-hero"><div><p className="eyebrow">How VeriClose works</p><h1>Checks decide.<br />People confirm.</h1><p>VeriClose lines up three messy files into cases you can actually review. Cleared means every check passed. Anything else tells you which rows disagree and what to do — and keeps the history when you fix it.</p></div><button className="primary" onClick={() => navigate(hasRun ? "cases" : "overview")}>{hasRun ? "Review cases" : "Start a close"} <span>→</span></button></header>
    <div className="architecture-flow">{stages.map(([step, title, copy], index) => <article key={step}><span>{step}</span><strong>{title}</strong><small>{copy}</small>{index < stages.length - 1 && <i>→</i>}</article>)}</div>
    <div className="architecture-grid"><article><span>IN</span><h3>Reads your files</h3><p>Keeps every original row, flags bad lines with the exact fix.</p><b>CSV / XLSX</b></article><article><span>CHECKS</span><h3>Runs the maths</h3><p>Amounts in paise, references, dates, balanced journals.</p><b>No rounding tricks</b></article><article><span>YOU</span><h3>You sign off</h3><p>Blocked cases wait for a person. Approvals are saved, never overwritten.</p><b>Full history</b></article><article className="advisory-architecture"><span>HELPER</span><h3>AI explains</h3><p>Plain-word suggestions that cite rows. Can never clear money.</p><b>Helper only</b></article></div>
    <div className="integrity-strip"><div><strong>Cleared means cleared</strong><span>Every required check passed.</span></div><div><strong>Blocked stays blocked</strong><span>No silent force-match.</span></div><div><strong>Fixes keep history</strong><span>Before and after both stay visible.</span></div></div>
  </section>;
}

function FloatingAssistant({ hasRun, open, setOpen, question, setQuestion, answer, askQuestion, busy, selected, navigate }: {
  hasRun: boolean; open: boolean; setOpen: (open: boolean) => void;
  question: string; setQuestion: (value: string) => void; answer: GroundedAnswer | null;
  askQuestion: () => Promise<void>; busy: boolean; selected: CaseDetail | null;
  navigate: (page: Page) => void;
}) {
  if (!hasRun) return null;
  return <div className={`floating-assistant ${open ? "open" : ""}`}>
    {!open ? <button className="floating-launcher" onClick={() => setOpen(true)} aria-label="Open close assistant"><span>?</span>Ask about this close</button> : <section className="floating-card panel" aria-label="Close assistant chat">
      <header><div><strong>Close assistant</strong><small>{selected ? plainReason(selected.reason_code) : "Ask about any case"}</small></div><button onClick={() => setOpen(false)} aria-label="Close assistant">×</button></header>
      <div className="floating-thread">
        {!question && !answer ? <p className="floating-hint">Ask with a case ID or UTR, e.g. “Why is case {selected?.case_id.slice(0, 14)}… blocked?” I answer only from the saved rows.</p> : <>
          {question && <p className="bubble user">{question}</p>}
          {answer && <p className={`bubble ${answer.status === "ABSTAINED" ? "abstained" : "bot"}`}>{answer.answer}</p>}
        </>}
      </div>
      <form onSubmit={(event) => { event.preventDefault(); void askQuestion(); }}>
        <input aria-label="Ask about the close" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Case ID or UTR…" />
        <button className="primary" type="submit" disabled={busy || !question.trim()}>Ask</button>
      </form>
      <button className="floating-link" onClick={() => { setOpen(false); navigate("cases"); }}>Open the case view →</button>
    </section>}
  </div>;
}

type WorkbenchProps = {
  selected: CaseDetail | null; run: RunResult; action: ProposedAction | null; correction: CorrectionResult | null;
  actionRationale: string; setActionRationale: (value: string) => void; reviewer: string; setReviewer: (value: string) => void;
  reviewState: string; setReviewState: (value: string) => void; comment: string; setComment: (value: string) => void;
  saveReview: () => Promise<void>; investigate: () => Promise<void>; judgeInvestigation: (state: "APPROVED" | "REJECTED") => Promise<void>;
  prepareAction: () => Promise<void>; judgeAction: (state: "APPROVED" | "REJECTED") => Promise<void>;
  exportApprovedAction: () => Promise<void>; correctAndRerun: () => Promise<void>; busy: boolean; busyLabel: string;
};

function CaseWorkbench(props: WorkbenchProps) {
  const item = props.selected;
  if (!item) return <div className="workbench panel empty-workbench"><span>Case view</span><strong>No case picked yet</strong><p>Pick any case on the left. You'll see its three rows, what failed, and what to do next.</p></div>;
  const component = item.proof_checks.find((check) => check.check_code === "SETTLEMENT_COMPONENT_INVARIANT");
  const varianceCheck = item.proof_checks.find((check) => check.check_code.includes("VARIANCE"));
  const gateway = item.events.filter((event) => event.source_type === "GATEWAY");
  const bank = item.events.filter((event) => event.source_type === "BANK");
  const erp = item.events.filter((event) => event.source_type === "ERP");
  const expected = asMinor(component?.expected) ?? sumByDirection(gateway);
  const observed = asMinor(component?.observed) ?? sumByDirection(bank);
  const variance = asMinor(varianceCheck?.observed) ?? expected - observed;
  const amount = Math.max(Math.abs(expected), Math.abs(observed), item.amount_at_risk_minor);
  const failed = item.proof_checks.filter((check) => !check.passed);
  const status = caseStatus(item);
  const reason = item.reason_code ? reasonInfo[item.reason_code] : null;
  return <article className="workbench panel">
    <header className="case-hero"><div className="case-id-line"><span>CASE</span><code>{item.case_id}</code><small>Decision {item.decision_id}</small></div><div className="case-verdict"><div><p>Result</p><strong className={`hero-proof tone-${item.proof_level.toLowerCase()}`}><i />{plainProof(item.proof_level)}</strong></div><div><p>Amount</p><strong>{inr(amount)}</strong></div><div><p>Status</p><strong className={`case-status status-${status.toLowerCase().replace(" ", "-")}`}>{status}</strong></div></div><div className="case-title"><div><p className="step">Case detail</p><h2>{item.reason_code ? plainReason(item.reason_code) : "Everything matches"}</h2><p>{reason?.todo ?? (item.proof_level === "PROVED" ? "Gateway, bank and ledger agree. Nothing for you to do." : "Clearing stopped on a check. The rows below show why.")}</p></div><div className="hero-actions">{item.reason_code && !item.advisory.investigation_id && <button className="primary" onClick={props.investigate} disabled={props.busy}>Get AI suggestion</button>}<a className="secondary-link" href="#proof-checks">See checks</a></div></div></header>
    {props.correction && <CorrectionOutcome result={props.correction} />}
    <section className="money-proof"><Subhead eyebrow="The money trail" title="Gateway → Bank → Ledger" aside={item.proof_level === "PROVED" ? "COMPLETE" : `${failed.length} CHECK${failed.length === 1 ? "" : "S"} BLOCKED THIS`} /><div className="money-chain"><MoneyNode source="1 · GATEWAY" title="Should have arrived" amount={expected} events={gateway} reference={gateway[0]?.settlement_reference ?? gateway[0]?.external_reference} detail={`${gateway.length} gateway row${gateway.length === 1 ? "" : "s"}`} /><Chain linked={Boolean(bank.length)} label={bank.length ? "matched by reference / UTR" : "no bank proof"} /><MoneyNode source="2 · BANK" title="Actually arrived" amount={observed} events={bank} reference={bank[0]?.bank_utr ?? bank[0]?.external_reference} detail={bank.length ? `${bank.length} bank row${bank.length === 1 ? "" : "s"}` : "No matching bank row"} /><Chain linked={Boolean(erp.length)} label={erp.length ? "matched by reference" : "no ledger proof"} /><MoneyNode source="3 · LEDGER" title="Recorded" amount={Math.max(sumDirection(erp, "DEBIT"), sumDirection(erp, "CREDIT"))} events={erp} reference={erp[0]?.external_reference ?? erp[0]?.settlement_reference} detail={erp.length ? `${erp.length} lines · ${sumDirection(erp, "DEBIT") === sumDirection(erp, "CREDIT") ? "balanced" : "doesn't balance"}` : "No matching ledger entry"} warning={Boolean(erp.length && sumDirection(erp, "DEBIT") !== sumDirection(erp, "CREDIT"))} /></div></section>
    <section className={`reconciliation-equation ${variance === 0 ? "balanced" : "variance"}`}><div><span>Gateway expected</span><strong>{inr(expected)}</strong></div><b>−</b><div><span>Bank received</span><strong>{inr(observed)}</strong></div><b>=</b><div><span>Difference</span><strong>{inr(variance)}</strong></div><p><i />{variance === 0 ? "Amounts match to the paise" : "This gap must be explained before it can clear"}<small>Allowed gap {inr(component?.tolerance_minor ?? 0)}</small></p></section>
    <section id="proof-checks" className="proof-section"><Subhead eyebrow="Why this decision" title="Checks that decided it" aside={`${item.proof_checks.filter((check) => check.passed).length}/${item.proof_checks.length} passed`} /><p className="rules-attempted">Checks run: {item.rules_attempted.map(labelize).join(" · ") || "all required checks"}</p><div className="check-list">{item.proof_checks.map((check) => <ProofCheckRow check={check} key={check.check_code} />)}<ControlCheck passed={item.uniqueness_passed} title="One clear match" good="Only one set of rows explains this money." bad="More than one match fits, so we stopped instead of guessing." /><ControlCheck passed={item.policy_allows_auto_clear} title="Allowed to auto-clear" good="Every required check passed." bad="Blocked from auto-clear, whatever any AI score says." /></div></section>
    <EvidenceLedger events={item.events} />
    {item.reason_code && <InvestigationPanel item={item} {...props} />}
    {item.reason_code && <ActionPanel {...props} />}
    <ReviewPanel item={item} {...props} />
  </article>;
}

function sumDirection(events: FinanceEvent[], direction: string) { return events.filter((event) => event.direction === direction).reduce((sum, event) => sum + event.amount_minor, 0); }
function sumByDirection(events: FinanceEvent[]) { return sumDirection(events, "CREDIT") || sumDirection(events, "DEBIT") || events.reduce((sum, event) => sum + event.amount_minor, 0); }
function Chain({ linked, label }: { linked: boolean; label: string }) { return <div className={`chain-link ${linked ? "linked" : "broken"}`}><span>→</span><small>{label}</small></div>; }
function MoneyNode({ source, title, amount, events, reference, detail, warning = false }: { source: string; title: string; amount: number; events: FinanceEvent[]; reference: string | null | undefined; detail: string; warning?: boolean }) { const state = !events.length ? "missing" : warning ? "warning" : "found"; return <article className={`money-node node-${state}`}><div className="node-head"><span>{source}</span><i>{state === "found" ? "✓" : state === "warning" ? "!" : "×"}</i></div><h4>{title}</h4><strong>{events.length ? inr(amount) : "Missing"}</strong><dl><div><dt>Reference</dt><dd>{reference ?? "—"}</dd></div><div><dt>Rows</dt><dd>{detail}</dd></div></dl>{events[0] && <a href={`#evidence-${events[0].event_id}`}>See row ↓</a>}</article>; }

function displayCheckValue(check: ProofCheck, value: unknown) {
  const numeric = asMinor(value);
  if (/AMOUNT|COMPONENT|VARIANCE|BALANCE|TOTAL|NET/.test(check.check_code) && numeric !== null) return inr(numeric);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (value === null || value === undefined || value === "") return "Not present";
  return String(value);
}
function ProofCheckRow({ check }: { check: ProofCheck }) { return <details className={check.passed ? "passed" : "failed"}><summary><span className="check-icon">{check.passed ? "✓" : "×"}</span><span className="check-result">{check.passed ? "PASS" : "STOP"}</span><strong>{labelize(check.check_code)}</strong><i>⌄</i></summary><div className="check-detail"><b>Needed</b><span>{displayCheckValue(check, check.expected)}</span><b>Found</b><span>{displayCheckValue(check, check.observed)}</span>{check.tolerance_minor !== null && <><b>Allowed gap</b><span>{inr(check.tolerance_minor)}</span></>}</div></details>; }
function ControlCheck({ passed, title, good, bad }: { passed: boolean; title: string; good: string; bad: string }) { return <details className={passed ? "passed" : "failed"}><summary><span className="check-icon">{passed ? "✓" : "×"}</span><span className="check-result">{passed ? "PASS" : "STOP"}</span><strong>{title}</strong><i>⌄</i></summary><div className="check-detail"><span>{passed ? good : bad}</span></div></details>; }
function EvidenceLedger({ events }: { events: FinanceEvent[] }) { return <section className="evidence-ledger"><Subhead eyebrow="Saved rows" title="Every row that decided this" aside={`${events.length} rows`} /><div className="evidence-stack">{events.map((event) => <details id={`evidence-${event.event_id}`} key={event.event_id}><summary><span className={`source-chip source-${event.source_type.toLowerCase()}`}>{event.source_type === "ERP" ? "LEDGER" : event.source_type}</span><span><strong>{event.source_record_id}</strong><small>{event.source_file_id} · line {event.row_number}</small></span><b>{event.direction} {inr(event.amount_minor)}</b><i>⌄</i></summary><div className="evidence-detail"><dl><div><dt>File line</dt><dd>{event.table_name} · {event.row_number}</dd></div><div><dt>Reference</dt><dd>{event.bank_utr ?? event.settlement_reference ?? event.external_reference ?? "—"}</dd></div><div><dt>Date</dt><dd>{event.value_date ?? event.event_at.slice(0, 10)}</dd></div><div><dt>Type</dt><dd>{labelize(event.event_type)}</dd></div><div><dt>Account</dt><dd>{event.account_code ?? "—"}</dd></div><div><dt>Row ID</dt><dd>{event.event_id}</dd></div></dl><details className="raw-row"><summary>See original file values</summary><pre>{JSON.stringify(event.raw_fields, null, 2)}</pre></details></div></details>)}</div></section>; }

function InvestigationPanel(props: WorkbenchProps & { item: CaseDetail }) {
  const { item } = props; const advisory = item.advisory; const available = Boolean(advisory.investigation_id); const failed = item.proof_checks.filter((check) => !check.passed);
  const isFallback = advisory.status === "DETERMINISTIC_FALLBACK";
  return <section className="investigation-panel"><div className="advisory-banner"><span>HELPER</span><strong>Suggestions can't clear a case</strong><small>You approve everything</small></div><Subhead eyebrow="What to do" title="Reviewer note" aside={available ? (isFallback ? "FROM THE CHECKS" : "AI SUGGESTION") : "NOT YET ASKED"} /><div className="facts-hypothesis-grid"><article className="deterministic-facts"><span>1 · Why it stopped</span><h4>{item.reason_code ? plainReason(item.reason_code) : "Blocked"}</h4><ul>{failed.length ? failed.map((check) => <li key={check.check_code}><i>×</i><span><strong>{labelize(check.check_code)}</strong><small>Saw {displayCheckValue(check, check.observed)} · needed {displayCheckValue(check, check.expected)}</small></span></li>) : <li><i>!</i><span><strong>{item.reason_code ? plainReason(item.reason_code) : "Needs review"}</strong><small>{item.contradiction_reason ?? "A person needs to look."}</small></span></li>}{!item.uniqueness_passed && <li><i>×</i><span><strong>Not a unique match</strong><small>More than one set of rows fits.</small></span></li>}</ul><p><b>Result stays:</b> {plainProof(item.proof_level)}</p></article><article className="ai-hypothesis"><span>2 · {available ? (isFallback ? "Reviewer note" : "AI suggestion") : "Suggestion"}</span>{available ? <><h4>{advisory.hypothesis ?? "Needs a human look"}</h4><p>{advisory.explanation ?? advisory.message}</p><dl><div><dt>Suggested next step</dt><dd>{plainAction(advisory.recommended_action)}</dd></div>{!isFallback && <div><dt>How sure</dt><dd><strong>{advisory.confidence_bps / 100}%</strong><small> · advisory only</small></dd></div>}<div><dt>Sign-off</dt><dd>{advisory.requires_human_approval ? "You approve" : "Not requested"}</dd></div><div><dt>Source</dt><dd>{isFallback ? "From the checks (AI didn't add one)" : advisory.model_version ?? "Checked against rows"}</dd></div></dl><div className="evidence-links"><strong>Rows cited</strong>{advisory.evidence_ids.length ? advisory.evidence_ids.map((id) => <a href={`#evidence-${id}`} key={id}>{id.slice(-18)} ↗</a>) : <small>No rows cited.</small>}</div></> : <div className="investigation-empty"><b>?</b><h4>Want a plain-word suggestion?</h4><p>It will cite the exact rows and suggest one next step. It can't change the result.</p></div>}</article></div><div className="investigation-actions">{!available ? <button className="primary" onClick={props.investigate} disabled={props.busy}>{props.busyLabel === "Getting suggestion…" ? "Getting suggestion…" : "Get AI suggestion"}</button> : <><span>Do you agree with this note?</span><button className="primary" onClick={() => props.judgeInvestigation("APPROVED")} disabled={props.busy || !props.reviewer.trim()}>Accept</button><button className="danger" onClick={() => props.judgeInvestigation("REJECTED")} disabled={props.busy || !props.reviewer.trim()}>Reject</button></>}</div></section>;
}

function ActionPanel(props: WorkbenchProps) {
  const action = props.action; const investigated = Boolean(props.selected?.advisory.investigation_id);
  const approved = action?.state === "APPROVED" || action?.state === "EXPORTED"; const exported = action?.state === "EXPORTED";
  const steps = [{ label: "Flagged", complete: true }, { label: "Suggestion", complete: investigated }, { label: "Proposal", complete: Boolean(action) }, { label: "Your approval", complete: approved }, { label: "Export", complete: exported }, { label: "Re-run", complete: Boolean(props.correction) }, { label: props.correction?.resolved ? "Cleared" : "Check again", complete: Boolean(props.correction) }];
  return <section className="action-panel"><Subhead eyebrow="Fix it properly" title="Fix without rewriting history" aside="YOU APPROVE" /><div className="correction-timeline">{steps.map((step, index) => <div className={step.complete ? "complete" : ""} key={step.label}><i>{step.complete ? "✓" : index + 1}</i><span>{step.label}</span></div>)}</div>{!action && !props.correction && <div className="action-empty"><div><strong>What happens next</strong><p>{props.selected?.requires_company_input ? "This one needs proof from outside these files (bank or business). It stays open until that arrives." : "Draft the allowed fix from the checked rows. Nothing posts to your ledger by itself."}</p></div><button className="primary" onClick={props.prepareAction} disabled={props.busy}>{props.busyLabel === "Drafting fix…" ? props.busyLabel : "Draft the fix"}</button></div>}{action && <div className="action-card"><div className="action-summary"><div><span>Suggested fix</span><strong>{plainAction(action.action_type)}</strong></div><b className={`action-state state-${action.state.toLowerCase()}`}>{labelize(action.state)}</b><p>Export only. No direct posting to your ledger. A fix creates a new close, old one stays.</p><code>{action.payload.idempotency_key}</code></div>{action.state === "PROPOSED" && <label className="action-edit">Your note (editable)<textarea value={props.actionRationale} onChange={(event) => props.setActionRationale(event.target.value)} /></label>}{action.journal_lines.length > 0 && <JournalPreview action={action} />}{action.state === "PROPOSED" && <div className="inline-actions action-approval"><span>Approving saves your decision</span><button className="primary" onClick={() => props.judgeAction("APPROVED")} disabled={props.busy || !props.reviewer.trim() || !props.actionRationale.trim()}>{props.busyLabel === "Saving…" ? props.busyLabel : "Approve fix"}</button><button className="danger" onClick={() => props.judgeAction("REJECTED")} disabled={props.busy || !props.reviewer.trim()}>Reject</button></div>}{action.state === "APPROVED" && <div className="next-action"><div><strong>You approved it</strong><p>Ready to export. Still hasn't touched your ledger.</p></div><button className="primary" onClick={props.exportApprovedAction} disabled={props.busy}>{props.busyLabel === "Exporting…" ? props.busyLabel : "Export the fix"}</button></div>}{action.state === "EXPORTED" && <div className="export-success"><div><b>✓</b><p><strong>Fix exported with receipt</strong><small>Download it, fix the source, then re-run this case.</small></p></div><div className="inline-actions"><a className="button-link" href={`/api/v1/actions/${encodeURIComponent(action.action_id)}/artifact`}>Download fix ↗</a>{action.action_type === "JOURNAL_EXPORT" && <button className="primary" onClick={props.correctAndRerun} disabled={props.busy}>{props.busyLabel === "Re-running with fix…" ? props.busyLabel : "Re-run with fix"}</button>}</div></div>}</div>}</section>;
}
function JournalPreview({ action }: { action: ProposedAction }) { const debit = action.journal_lines.filter((line) => line.direction === "DEBIT").reduce((sum, line) => sum + line.amount_minor, 0); const credit = action.journal_lines.filter((line) => line.direction === "CREDIT").reduce((sum, line) => sum + line.amount_minor, 0); return <div className="journal-preview"><header><strong>Journal preview</strong><span>{action.journal_lines.length} lines · INR</span></header>{action.journal_lines.map((line, index) => <p key={`${line.account_code}-${index}`}><span><b>{line.direction}</b> {line.account_code}</span><strong>{inr(line.amount_minor)}</strong><small>{line.narration}</small></p>)}<footer><span>Debits <b>{inr(debit)}</b></span><span>Credits <b>{inr(credit)}</b></span><strong>{debit === credit ? "✓ BALANCED" : "× OFF BALANCE"}</strong></footer></div>; }

function ReviewPanel(props: WorkbenchProps & { item: CaseDetail }) { const { item } = props; return <section className="review-section"><Subhead eyebrow="Your sign-off" title="Record your decision" aside="SAVED, NEVER OVERWRITTEN" /><div className="review-form"><label>Your name<input aria-label="Reviewer ID" value={props.reviewer} onChange={(event) => props.setReviewer(event.target.value)} /></label><label>Decision<select aria-label="Review outcome" value={props.reviewState} onChange={(event) => props.setReviewState(event.target.value)}><option value="APPROVED">Agree with the result</option><option value="REJECTED">Disagree</option><option value="EDIT_REQUESTED">Needs a fix</option><option value="INFORMATION_REQUESTED">Need more info</option><option value="DEFERRED">Decide later</option></select></label><label className="review-note">What did you check?<textarea aria-label="Review note" placeholder="e.g. Checked UTR against bank statement. Asking business for fee breakup." value={props.comment} onChange={(event) => props.setComment(event.target.value)} /></label><button className="primary" onClick={props.saveReview} disabled={props.busy || !props.reviewer.trim()}>{props.busyLabel === "Saving…" ? props.busyLabel : "Save decision"}</button></div>{item.reviews.length > 0 && <div className="review-history"><h4>Past decisions</h4>{item.reviews.map((review) => <p key={review.review_id}><i /><span><strong>{labelize(review.state)}</strong> by {review.reviewer_id}<small>{review.comment ?? "No note"} · {new Date(review.reviewed_at).toLocaleString("en-IN")}</small></span></p>)}</div>}</section>; }
function CorrectionOutcome({ result }: { result: CorrectionResult }) { return <section className={`correction-outcome ${result.resolved ? "resolved" : "open"}`}><div className="outcome-title"><span>{result.resolved ? "✓" : "!"}</span><div><small>Re-run done</small><h3>{result.resolved ? "Now it clears" : "Still needs work"}</h3><p>Old result kept in {result.previous_run_id}. New check ran in {result.new_run_id}.</p></div></div><div className="before-after"><div><span>BEFORE</span><strong className={`tone-${result.previous_proof_level.toLowerCase()}`}>{plainProof(result.previous_proof_level)}</strong><code>{result.previous_case_id}</code></div><b>→</b><div><span>AFTER</span><strong className={`tone-${(result.new_proof_level ?? "invalid_input").toLowerCase()}`}>{result.new_proof_level ? plainProof(result.new_proof_level) : "Still open"}</strong><code>{result.new_case_id ?? "No new case"}</code></div></div><footer><span>History kept</span><span>Receipt {result.receipt.receipt_id}</span><span>{result.resolved ? "Cleared by checks" : "Not forced"}</span></footer></section>; }
