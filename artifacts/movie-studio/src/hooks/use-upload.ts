import { useState, useCallback, useRef } from "react";
import { uploadDocumentWithProgress, type UploadProgress, type UploadResult } from "../lib/api/uploadApi";
import type { APIResponse } from "../lib/types";

interface UseUploadReturn {
  upload: (formData: FormData) => Promise<APIResponse<UploadResult>>;
  progress: UploadProgress;
  isUploading: boolean;
  error: string | null;
  reset: () => void;
}

export function useUpload(): UseUploadReturn {
  const [progress, setProgress] = useState<UploadProgress>({ loaded: 0, total: 0, percent: 0 });
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const upload = useCallback(async (formData: FormData) => {
    setIsUploading(true);
    setError(null);
    setProgress({ loaded: 0, total: 0, percent: 0 });
    abortRef.current = new AbortController();

    try {
      const result = await uploadDocumentWithProgress(
        formData,
        (p) => setProgress(p),
        abortRef.current.signal
      );
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setError(message);
      throw err;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setProgress({ loaded: 0, total: 0, percent: 0 });
    setIsUploading(false);
    setError(null);
  }, []);

  return { upload, progress, isUploading, error, reset };
}
