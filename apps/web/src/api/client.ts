import type { MetaResponse, ReadyResponse, RuntimeStatus } from "./types";

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`${path} returned HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getRuntimeStatus(signal?: AbortSignal): Promise<RuntimeStatus> {
  const [ready, meta] = await Promise.all([
    getJson<ReadyResponse>("/health/ready", signal),
    getJson<MetaResponse>("/api/meta", signal),
  ]);

  return { ready, meta };
}
