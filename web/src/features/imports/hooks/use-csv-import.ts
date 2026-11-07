import { useState } from "react";
import { ApiError } from "@/shared/api/client";
import { errorMessage, errorText } from "@/shared/api/errors";
import { uploadCsv } from "../api/imports";
import type { ImportJob } from "../types";

// nginx rejects anything larger with a page the API error handling cannot read.
const MAX_BYTES = 10 * 1024 * 1024;

function uploadError(caught: unknown): string {
  const columns = caught instanceof ApiError ? caught.detail?.columns : null;
  const message = errorMessage(caught);
  return Array.isArray(columns) ? `${message} ${columns.join(", ")}` : message;
}

export function useCsvImport() {
  const [job, setJob] = useState<ImportJob | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function upload(file: File): Promise<void> {
    setError("");
    setJob(null);
    if (file.size > MAX_BYTES) {
      setError(errorText("file_too_large"));
      return;
    }
    setBusy(true);
    try {
      setJob(await uploadCsv(file));
    } catch (caught) {
      setError(uploadError(caught));
    } finally {
      setBusy(false);
    }
  }

  return { upload, job, error, busy };
}
