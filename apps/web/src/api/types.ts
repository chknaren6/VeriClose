export type ReadyResponse = { status: "ready"; checks: Record<string, string> };
export type MetaResponse = {
  app: string; environment: string; build_commit: string; rule_version: string;
  policy_version: string; demo_mode: boolean; model_enabled: boolean;
};
export type RuntimeStatus = { ready: ReadyResponse; meta: MetaResponse };
export type UploadDocument = {
  file_id: "gateway" | "bank" | "erp"; original_name: string;
  media_type: string; content_base64: string;
};
export type UploadPayload = {
  run_id: string; legal_entity_id: string; documents: UploadDocument[];
  confirmations: Array<{ file_id: string; adapter_id: string; profile_versioned_id: string }>;
};
export type Detection = {
  file_id: string; requires_confirmation: boolean;
  candidates: Array<{ adapter_id: string; profile_versioned_id: string;
    confidence_bps: number; reasons: string[] }>;
};
export type ValidationIssue = {
  stage: string; severity: string; code: string; message: string; file_id: string;
  row_number: number | null; field_name: string | null; suggested_fix: string; blocking: boolean;
};
export type ImportedFile = {
  file_id: string; original_name: string; source_type: string; adapter_id: string;
  profile_versioned_id: string; explicitly_confirmed: boolean; rows_seen: number; is_valid: boolean;
  mapping: Array<{ canonical_field: string; source_column: string | null;
    required: boolean; transform: string }>;
  sample_rows: Array<Record<string, unknown>>; issues: ValidationIssue[];
  control_totals: Array<{ component: string; currency: string;
    amount_minor: number; record_count: number }>;
};
export type ImportResult = {
  run_id: string; state: string; is_ready: boolean; event_count: number;
  files: ImportedFile[]; cross_source_issues: ValidationIssue[];
};
export type OperationalSummary = {
  decision_count: number; verified_count: number; review_or_exception_count: number;
  amount_at_risk_minor: number; currency: "INR";
  stage_timings: Array<{ stage: string; duration_ms: number;
    input_count: number; output_count: number }>;
};
export type RunResult = {
  run_id: string; state: string; policy_version: string; rule_version: string;
  created_at: string; files: unknown[]; validation_issues: ValidationIssue[];
  operational_summary: OperationalSummary | null; benchmark_accuracy_available: false;
};
export type Review = {
  review_id: string; state: string; reviewer_id: string; reviewed_at: string; comment: string | null;
};
export type Investigation = {
  investigation_id: string | null; status: string; message: string;
  hypothesis: string | null; explanation: string | null; evidence_ids: string[];
  confidence_bps: number; recommended_action: string | null;
  requires_human_approval: boolean; prompt_version: string | null;
  model_version: string | null; latency_ms: number; failure_code: string | null;
  created_at: string | null; reviews: Review[];
  advisory_journal: Array<{ account_code: string; direction: string;
    amount_minor: number; evidence_ids: string[] }>;
};
export type CaseItem = {
  case_id: string; decision_id: string; state: string; proof_level: string;
  reason_code: string | null; severity: string | null; amount_at_risk_minor: number;
  currency: "INR"; recommended_action: string | null; requires_company_input: boolean;
  latest_review: Review | null;
};
export type FinanceEvent = {
  event_id: string; source_type: string; source_record_id: string; event_type: string;
  amount_minor: number; currency: string; direction: string; event_at: string;
  value_date: string | null; external_reference: string | null;
  settlement_reference: string | null; bank_utr: string | null; account_code: string | null;
  narration: string | null; source_file_id: string; table_name: string; row_number: number;
  raw_fields: Record<string, unknown>;
};
export type ProofCheck = {
  check_code: string; expected: unknown; observed: unknown; tolerance_minor: number | null;
  passed: boolean; required: boolean;
};
export type CaseDetail = CaseItem & {
  uniqueness_passed: boolean; contradiction_reason: string | null;
  policy_allows_auto_clear: boolean; rules_attempted: string[]; events: FinanceEvent[];
  evidence: Array<{ event_id: string | null; source_file_id: string;
    table_name: string; row_number: number; purpose: string }>;
  proof_checks: ProofCheck[]; reviews: Review[];
  advisory: Investigation;
};
export type JournalLine = {
  account_code: string; direction: string; amount_minor: number; currency: string;
  narration: string; evidence_ids: string[];
};
export type ActionReceipt = {
  receipt_id: string; action_id: string; idempotency_key: string;
  executed_at: string; result: Record<string, string>; download_url: string | null;
};
export type ProposedAction = {
  action_id: string; action_type: string; case_id: string; state: string;
  payload: Record<string, string>; journal_lines: JournalLine[];
  evidence: CaseDetail["evidence"]; created_at: string; effect_scope: string;
  reviews: Review[]; receipts: ActionReceipt[];
};
export type CorrectionResult = {
  previous_run_id: string; new_run_id: string; previous_case_id: string;
  new_case_id: string | null; previous_proof_level: string;
  new_proof_level: string | null; resolved: boolean; receipt: ActionReceipt;
};
export type GroundedAnswer = {
  status: "ANSWERED" | "ABSTAINED"; answer: string;
  case_ids: string[]; evidence_ids: string[];
};
