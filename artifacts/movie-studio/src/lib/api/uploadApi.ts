import type { APIResponse } from "../types";

const BASE = import.meta.env.BASE_URL + "api";

export interface UploadResult {
  job_id: string;
  filename: string;
  chunk_count: number;
  status: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}

export function uploadDocumentWithProgress(
  formData: FormData,
  onProgress: (progress: UploadProgress) => void,
  signal?: AbortSignal
): Promise<APIResponse<UploadResult>> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE}/upload/document`);

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        onProgress({
          loaded: e.loaded,
          total: e.total,
          percent: Math.round((e.loaded / e.total) * 100),
        });
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Invalid response"));
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `Upload failed: ${xhr.status}`));
        } catch {
          reject(new Error(`Upload failed: ${xhr.status}`));
        }
      }
    });

    xhr.addEventListener("error", () => reject(new Error("Network error")));
    xhr.addEventListener("abort", () => reject(new Error("Upload aborted")));

    if (signal) {
      signal.addEventListener("abort", () => xhr.abort());
    }

    xhr.send(formData);
  });
}

export async function uploadDocument(formData: FormData): Promise<APIResponse<UploadResult>> {
  const res = await fetch(`${BASE}/upload/document`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function getUploadStatus(jobId: string): Promise<APIResponse<UploadResult>> {
  const res = await fetch(`${BASE}/upload/status/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch upload status");
  return res.json();
}
