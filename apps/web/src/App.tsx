import { useEffect, useMemo, useState } from "react";

import { detectUploads, getCase, getRuntimeStatus, importUploads, listCases, recordReview, startRun } from "./api/client";
import type { CaseDetail, CaseItem, Detection, ImportResult, RunResult, RuntimeStatus, UploadDocument, UploadPayload } from "./api/types";

type Slot = "gateway" | "bank" | "erp";
type Phase = "empty" | "reading" | "detected" | "validating" | "processing" | "ready" | "error";
const slots: Array<{ id: Slot; title: string; hint: string }> = [
  { id: "gateway", title: "Gateway settlement", hint: "Razorpay-style payments and fees" },
  { id: "bank", title: "Bank statement", hint: "Credits, dates and UTR references" },
  { id: "erp", title: "ERP general ledger", hint: "Journal lines, accounts and directions" },
];
const inr = (minor: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(minor / 100);

async function encodeFile(file: File, fileId: Slot): Promise<UploadDocument> {
  const bytes = new Uint8Array(await file.arrayBuffer()); let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 8192) binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
  return { file_id: fileId, original_name: file.name, media_type: file.type || "application/octet-stream", content_base64: btoa(binary) };
}

export default function App() {
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [files, setFiles] = useState<Partial<Record<Slot, File>>>({});
  const [payload, setPayload] = useState<UploadPayload | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [selectedProfiles, setSelectedProfiles] = useState<Record<string, string>>({});
  const [phase, setPhase] = useState<Phase>("empty"); const [error, setError] = useState("");
  const [imported, setImported] = useState<ImportResult | null>(null); const [run, setRun] = useState<RunResult | null>(null);
  const [cases, setCases] = useState<CaseItem[]>([]); const [selected, setSelected] = useState<CaseDetail | null>(null);
  const [filter, setFilter] = useState("ALL"); const [reviewState, setReviewState] = useState("DEFERRED");
  const [reviewer, setReviewer] = useState("finance-reviewer"); const [comment, setComment] = useState("");

  useEffect(() => { getRuntimeStatus().then(setRuntime).catch((reason: Error) => { setError(reason.message); setPhase("error"); }); }, []);
  const inspect = async () => {
    if (!slots.every(({ id }) => files[id])) return;
    try {
      setPhase("reading"); setError("");
      const documents = await Promise.all(slots.map(({ id }) => encodeFile(files[id]!, id)));
      const prepared: UploadPayload = { run_id: `close-${new Date().toISOString().replace(/[^0-9]/g, "").slice(0, 14)}`, legal_entity_id: "demo-merchant-in", documents, confirmations: [] };
      const result = await detectUploads(prepared); setPayload(prepared); setDetections(result.files);
      setSelectedProfiles(Object.fromEntries(result.files.map((item) => [item.file_id, item.candidates[0]?.profile_versioned_id ?? ""])));
      setPhase("detected");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Detection failed"); setPhase("error"); }
  };
  const reconcile = async () => {
    if (!payload) return;
    try {
      const confirmed = { ...payload, confirmations: detections.map((item) => {
        const candidate = item.candidates.find((value) => value.profile_versioned_id === selectedProfiles[item.file_id]) ?? item.candidates[0];
        return { file_id: item.file_id, adapter_id: candidate.adapter_id, profile_versioned_id: candidate.profile_versioned_id };
      }) };
      setPhase("validating"); const importedResult = await importUploads(confirmed); setImported(importedResult);
      if (!importedResult.is_ready) { setPhase("error"); setError("Validation failed. Fix the listed source issues and start a new run."); return; }
      setPhase("processing"); const runResult = await startRun(importedResult.run_id); const caseResult = await listCases(importedResult.run_id);
      setRun(runResult); setCases(caseResult); setPhase("ready");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Reconciliation failed"); setPhase("error"); }
  };
  const openCase = async (item: CaseItem) => setSelected(await getCase(item.case_id));
  const saveReview = async () => {
    if (!selected || !run) return; await recordReview(selected.case_id, reviewState, reviewer, comment);
    setSelected(await getCase(selected.case_id)); setCases(await listCases(run.run_id)); setComment("");
  };
  const filtered = useMemo(() => cases.filter((item) => filter === "ALL" || item.proof_level === filter || item.reason_code === filter), [cases, filter]);
  const reasons = [...new Set(cases.map((item) => item.reason_code).filter(Boolean))] as string[];

  return <main className="app-shell">
    <header className="topbar"><a className="brand" href="/"><span className="brand-mark">V</span>VeriClose</a><nav><span className="synthetic-notice">Synthetic data only</span><span className="runtime-pill">{runtime ? "System ready" : "Connecting…"}</span></nav></header>
    <section className="intro"><div><p className="eyebrow">Finance close workspace</p><h1>Reconcile with proof,<br />not probability.</h1></div><p>Upload one gateway, bank and ERP export. VeriClose validates every row, proves safe matches, and routes every unresolved rupee into an inspectable exception queue.</p></section>

    {phase !== "ready" && <section className="panel import-panel">
      <div className="section-heading"><div><p className="step">01 · Import</p><h2>Bring the three ledgers together</h2></div><span className="scope">CSV or XLSX · INR · one legal entity</span></div>
      <div className="upload-grid">{slots.map((slot) => <label className={`upload-slot ${files[slot.id] ? "filled" : ""}`} key={slot.id}><input type="file" accept=".csv,.xlsx" onChange={(event) => { const file = event.target.files?.[0]; if (file) setFiles((current) => ({ ...current, [slot.id]: file })); }} /><span className="slot-index">{slot.id.slice(0, 1).toUpperCase()}</span><strong>{slot.title}</strong><small>{files[slot.id]?.name ?? slot.hint}</small><em>{files[slot.id] ? "Selected" : "Choose file"}</em></label>)}</div>
      {phase === "detected" && <div className="detection-grid">{detections.map((item) => <article key={item.file_id}><span>{item.file_id}</span><select aria-label={`${item.file_id} mapping profile`} value={selectedProfiles[item.file_id] ?? ""} onChange={(event) => setSelectedProfiles((current) => ({ ...current, [item.file_id]: event.target.value }))}>{item.candidates.map((candidate) => <option key={`${candidate.adapter_id}-${candidate.profile_versioned_id}`} value={candidate.profile_versioned_id}>{candidate.profile_versioned_id}</option>)}</select><small>{item.requires_confirmation ? "Confirmation required" : "High-confidence detection"} · {(item.candidates[0]?.confidence_bps ?? 0) / 100}%</small></article>)}</div>}
      {imported && <ValidationSummary result={imported} />}
      {phase === "error" && <div className="alert" role="alert"><strong>Could not continue</strong><p>{error}</p></div>}
      <div className="action-row">{phase !== "detected" && <button className="primary" disabled={!slots.every(({ id }) => files[id]) || ["reading", "validating", "processing"].includes(phase)} onClick={inspect}>{phase === "reading" ? "Reading source files…" : "Inspect files & mappings"}</button>}{phase === "detected" && <button className="primary" onClick={reconcile}>Confirm mappings & run reconciliation</button>}{phase === "validating" && <span className="progress-text">Validating schemas, rows and control totals…</span>}{phase === "processing" && <span className="progress-text">Applying deterministic proof rules…</span>}</div>
    </section>}

    {phase === "ready" && run?.operational_summary && <>
      <section className="cockpit"><div className="section-heading"><div><p className="step">02 · Run cockpit</p><h2>Close position</h2></div><span className="run-id">{run.run_id} · {run.state}</span></div><div className="metric-grid"><Metric label="Verified" value={`${run.operational_summary.verified_count}`} note="Policy-proved auto-clears" /><Metric label="Review / unresolved" value={`${run.operational_summary.review_or_exception_count}`} note="Human attention required" /><Metric label="Amount at risk" value={inr(run.operational_summary.amount_at_risk_minor)} note="Across non-proved cases" /><Metric label="Runtime" value={`${run.operational_summary.stage_timings.reduce((sum, item) => sum + item.duration_ms, 0)} ms`} note="Operational result—not accuracy" /></div><div className="reason-strip"><strong>Reason distribution</strong>{reasons.map((reason) => <span key={reason}>{reason} · {cases.filter((item) => item.reason_code === reason).length}</span>)}</div><p className="accuracy-note">Precision and recall are benchmark-only metrics and are intentionally absent from this operational run.</p>{imported && <SourceInspection result={imported} />}</section>
      <section className="workspace"><div className="queue panel"><div className="queue-head"><div><p className="step">03 · Exception queue</p><h2>Cases requiring judgment</h2></div><select aria-label="Filter cases" value={filter} onChange={(event) => setFilter(event.target.value)}><option value="ALL">All cases</option><option value="SUPPORTED">Supported</option><option value="AMBIGUOUS">Ambiguous</option><option value="CONTRADICTED">Contradicted</option>{reasons.map((reason) => <option value={reason} key={reason}>{reason}</option>)}</select></div><div className="case-list">{filtered.length ? filtered.map((item) => <button className={`case-row ${selected?.case_id === item.case_id ? "active" : ""}`} key={item.case_id} onClick={() => openCase(item)}><span className={`severity ${item.severity?.toLowerCase() ?? "proved"}`}>{item.severity ?? "VERIFIED"}</span><span><strong>{item.reason_code ?? "PROVED MATCH"}</strong><small>{item.case_id} · {item.proof_level}</small><small>{item.recommended_action ?? "NO_ACTION"} · {item.requires_company_input ? "Company input needed" : "Internal review"}</small></span><b>{inr(item.amount_at_risk_minor)}</b></button>) : <div className="empty-state"><strong>No cases in this view</strong><p>Adjust the filter, or celebrate a clean exception queue.</p></div>}</div></div>
        <CaseWorkbench selected={selected} reviewer={reviewer} setReviewer={setReviewer} reviewState={reviewState} setReviewState={setReviewState} comment={comment} setComment={setComment} saveReview={saveReview} /></section>
    </>}
    <footer><span>M4 review workflow</span><span>AI: {runtime?.meta.model_enabled ? "advisory available" : "deterministic fallback"}</span><a href="/docs">API docs</a></footer>
  </main>;
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) { return <article><small>{label}</small><strong>{value}</strong><span>{note}</span></article>; }
function ValidationSummary({ result }: { result: ImportResult }) {
  const issues = [...result.files.flatMap((item) => item.issues), ...result.cross_source_issues];
  return <div className="validation-summary"><strong>{result.event_count} canonical events · {result.state}</strong>{issues.length ? <ul>{issues.map((issue, index) => <li key={`${issue.code}-${index}`}><b>{issue.code}</b> {issue.message}<small>{issue.suggested_fix}</small></li>)}</ul> : <span>All source and cross-source validation checks passed.</span>}</div>;
}
function SourceInspection({ result }: { result: ImportResult }) {
  return <details className="source-inspection"><summary>Inspect source mappings, sample rows and control totals</summary><div className="source-grid">{result.files.map((file) => <article key={file.file_id}><h3>{file.source_type} · {file.profile_versioned_id}</h3><p>{file.rows_seen} rows · {file.is_valid ? "validated" : "needs correction"}</p><h4>Field mapping</h4><ul>{file.mapping.filter((field) => field.required).map((field) => <li key={field.canonical_field}><span>{field.source_column ?? "UNRESOLVED"}</span> → {field.canonical_field}</li>)}</ul><h4>Control totals</h4>{file.control_totals.map((total) => <p key={total.component}>{total.component}: <strong>{inr(total.amount_minor)}</strong> · {total.record_count} records</p>)}<h4>Sample source row</h4><pre>{JSON.stringify(file.sample_rows[0] ?? {}, null, 2)}</pre></article>)}</div></details>;
}
type WorkbenchProps = { selected: CaseDetail | null; reviewer: string; setReviewer: (value: string) => void; reviewState: string; setReviewState: (value: string) => void; comment: string; setComment: (value: string) => void; saveReview: () => Promise<void> };
function CaseWorkbench(props: WorkbenchProps) {
  const item = props.selected;
  if (!item) return <aside className="workbench panel empty-workbench"><span>04 · Evidence workbench</span><strong>Select a case</strong><p>Open any exception to inspect aligned source rows, proof checks and reviewer history.</p></aside>;
  const component = item.proof_checks.find((check) => check.check_code === "SETTLEMENT_COMPONENT_INVARIANT");
  const variance = item.proof_checks.find((check) => check.check_code === "SETTLEMENT_COMPONENT_VARIANCE");
  return <aside className="workbench panel"><div className="workbench-head"><div><p className="step">04 · Evidence workbench</p><h2>{item.reason_code ?? "Verified case"}</h2></div><span className="proof-badge">{item.proof_level}</span></div><div className="equation"><span>Settlement equation</span><strong>{inr(item.amount_at_risk_minor)} at risk</strong><small>{component ? `${inr(Number(component.observed))} observed vs ${inr(Number(component.expected))} expected` : "No settlement component equation for this orphan case"}{variance ? ` · variance ${inr(Number(variance.observed))}` : ""}</small></div>
    <h3>Aligned source evidence</h3><div className="evidence-stack">{item.events.map((event) => <details key={event.event_id}><summary><span>{event.source_type}</span><strong>{event.source_record_id}</strong><b>{event.direction} {inr(event.amount_minor)}</b></summary><dl><div><dt>Source row</dt><dd>{event.source_file_id} · row {event.row_number}</dd></div><div><dt>Reference</dt><dd>{event.bank_utr ?? event.settlement_reference ?? event.external_reference ?? "—"}</dd></div><div><dt>Canonical date</dt><dd>{event.value_date ?? event.event_at.slice(0, 10)}</dd></div></dl><pre>{JSON.stringify(event.raw_fields, null, 2)}</pre></details>)}</div>
    <h3>Deterministic proof checks</h3><p className="rules-attempted">Rules attempted: {item.rules_attempted.join(", ") || "deterministic orphan routing"}</p><div className="check-list">{item.proof_checks.map((check) => <div key={check.check_code} className={check.passed ? "passed" : "failed"}><span>{check.passed ? "PASS" : "STOP"}</span><strong>{check.check_code}</strong><small>{String(check.observed)} observed · {String(check.expected)} expected</small></div>)}</div><div className="advisory"><strong>AI advisory · {item.advisory.status}</strong><p>{item.advisory.message}</p></div>
    <h3>Preliminary review</h3><div className="review-form"><input aria-label="Reviewer ID" value={props.reviewer} onChange={(event) => props.setReviewer(event.target.value)} /><select value={props.reviewState} onChange={(event) => props.setReviewState(event.target.value)}><option value="APPROVED">Approve classification</option><option value="REJECTED">Reject classification</option><option value="EDIT_REQUESTED">Request correction</option><option value="INFORMATION_REQUESTED">Request information</option><option value="DEFERRED">Defer</option></select><textarea placeholder="Evidence-based review note" value={props.comment} onChange={(event) => props.setComment(event.target.value)} /><button className="primary" onClick={props.saveReview}>Record review</button></div>{item.reviews.length > 0 && <div className="review-history">{item.reviews.map((review) => <p key={review.review_id}><strong>{review.state}</strong> by {review.reviewer_id}<small>{review.comment ?? "No note"}</small></p>)}</div>}
  </aside>;
}
