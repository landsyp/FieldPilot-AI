import type { Job, TreatmentSession, TreatmentSessionPayload } from "@/lib/types";

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const tenantSlug = process.env.NEXT_PUBLIC_TENANT_SLUG ?? "vision-gazon";

async function apiFetch<T>(path: string, options: { method?: string; body?: unknown } = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: options.method ?? "GET",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-Slug": tenantSlug,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getTodayJobs(): Promise<Job[]> {
  return apiFetch<Job[]>("/api/jobs/today");
}

export function getJob(jobId: number): Promise<Job> {
  return apiFetch<Job>(`/api/jobs/${jobId}`);
}

export function saveTreatmentSession(jobId: number, payload: TreatmentSessionPayload): Promise<TreatmentSession> {
  return apiFetch<TreatmentSession>(`/api/jobs/${jobId}/treatment-sessions`, {
    method: "POST",
    body: payload,
  });
}
