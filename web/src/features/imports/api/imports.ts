import { request } from "@/shared/api/client";
import type { ImportJob } from "../types";

// `POST /api/imports` answers once the file is imported, so there is nothing to poll.
export function uploadCsv(file: File): Promise<ImportJob> {
  const body = new FormData();
  body.append("file", file);
  return request<ImportJob>("/imports", { method: "POST", body });
}
