import type {
  CaseDetail, CaseItem, Detection, ImportResult, MetaResponse, ReadyResponse,
  RunResult, RuntimeStatus, UploadPayload,
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
export const listCases = (runId: string) => requestJson<CaseItem[]>(
  `/api/v1/runs/${encodeURIComponent(runId)}/cases`);
export const getCase = (caseId: string) => requestJson<CaseDetail>(
  `/api/v1/cases/${encodeURIComponent(caseId)}`);
export const recordReview = (caseId: string, state: string, reviewerId: string, comment: string) =>
  requestJson(`/api/v1/cases/${encodeURIComponent(caseId)}/reviews`, {
    method: "POST",
    body: JSON.stringify({ state, reviewer_id: reviewerId, comment: comment || null }),
  });
