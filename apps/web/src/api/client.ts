import type {
  CaseDetail, CaseItem, CorrectionResult, Detection, GroundedAnswer, ImportResult,
  MetaResponse, ProposedAction, ReadyResponse, RunResult, RuntimeStatus, UploadPayload,
} from "./types";

type ApiError = { error?: { message?: string; suggested_fix?: string } };

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiError;
    const detail = payload.error?.suggested_fix
      ? `${payload.error.message}. ${payload.error.suggested_fix}` : payload.error?.message;
    throw new Error(detail ?? `${path} returned HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function getRuntimeStatus(signal?: AbortSignal): Promise<RuntimeStatus> {
  const [ready, meta] = await Promise.all([
    requestJson<ReadyResponse>("/health/ready", { signal }),
    requestJson<MetaResponse>("/api/meta", { signal }),
  ]);
  return { ready, meta };
}
export const detectUploads = (payload: UploadPayload) => requestJson<{ files: Detection[] }>(
  "/api/v1/uploads/detect", { method: "POST", body: JSON.stringify(payload) });
export const importUploads = (payload: UploadPayload) => requestJson<ImportResult>(
  "/api/v1/uploads", { method: "POST", body: JSON.stringify(payload) });
export const startRun = (runId: string) => requestJson<RunResult>(
  "/api/v1/runs", { method: "POST", body: JSON.stringify({ run_id: runId }) });
export const resetDemo = () => requestJson<RunResult>(
  "/api/v1/demo/reset", { method: "POST" });
export const getRun = (runId: string) => requestJson<RunResult>(
  `/api/v1/runs/${encodeURIComponent(runId)}`);
export const listCases = (runId: string) => requestJson<CaseItem[]>(
  `/api/v1/runs/${encodeURIComponent(runId)}/cases`);
export const getCase = (caseId: string) => requestJson<CaseDetail>(
  `/api/v1/cases/${encodeURIComponent(caseId)}`);
export const recordReview = (caseId: string, state: string, reviewerId: string, comment: string) =>
  requestJson(`/api/v1/cases/${encodeURIComponent(caseId)}/reviews`, {
    method: "POST",
    body: JSON.stringify({ state, reviewer_id: reviewerId, comment: comment || null }),
  });
export const investigateCase = (caseId: string) => requestJson<CaseDetail["advisory"]>(
  `/api/v1/cases/${encodeURIComponent(caseId)}/investigations`, { method: "POST" });
export const reviewInvestigation = (
  caseId: string, state: "APPROVED" | "REJECTED", reviewerId: string, comment: string,
) => requestJson(`/api/v1/cases/${encodeURIComponent(caseId)}/investigation-reviews`, {
  method: "POST", body: JSON.stringify({ state, reviewer_id: reviewerId, comment: comment || null }),
});
export const proposeAction = (caseId: string) => requestJson<ProposedAction>(
  `/api/v1/cases/${encodeURIComponent(caseId)}/actions`, { method: "POST" });
export const getAction = (actionId: string) => requestJson<ProposedAction>(
  `/api/v1/actions/${encodeURIComponent(actionId)}`);
export const reviewAction = (
  actionId: string, state: string, reviewerId: string, comment: string,
  edits: Record<string, string> = {},
) => requestJson<ProposedAction>(`/api/v1/actions/${encodeURIComponent(actionId)}/reviews`, {
  method: "POST",
  body: JSON.stringify({ state, reviewer_id: reviewerId, comment: comment || null, edits }),
});
export const exportAction = (actionId: string) => requestJson(
  `/api/v1/actions/${encodeURIComponent(actionId)}/export`, { method: "POST" });
export const applyCorrection = (actionId: string, newRunId: string) =>
  requestJson<CorrectionResult>(
    `/api/v1/actions/${encodeURIComponent(actionId)}/apply-correction`,
    { method: "POST", body: JSON.stringify({ new_run_id: newRunId }) },
  );
export const askRunQuestion = (runId: string, question: string) => requestJson<GroundedAnswer>(
  `/api/v1/runs/${encodeURIComponent(runId)}/questions`,
  { method: "POST", body: JSON.stringify({ question }) },
);
