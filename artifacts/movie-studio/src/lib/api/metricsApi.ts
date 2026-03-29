import type { APIResponse, AdminMetrics } from "../types";

const BASE = import.meta.env.BASE_URL + "api";

export async function getMetrics(): Promise<AdminMetrics> {
  const res = await fetch(`${BASE}/eval/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  const json: APIResponse<AdminMetrics> = await res.json();
  return json.data;
}

export async function runEvaluation(
  dataset: string,
  maxQueries = 5
): Promise<unknown> {
  const res = await fetch(`${BASE}/eval/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset, max_queries: maxQueries }),
  });
  if (!res.ok) throw new Error("Evaluation run failed");
  return res.json();
}
