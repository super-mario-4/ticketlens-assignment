export type ImportStatus = "processing" | "completed" | "failed";

export type ImportRowError = { row?: number; id?: string; code: string };

export type ImportJob = {
  id: string;
  filename: string;
  status: ImportStatus;
  total: number;
  inserted: number;
  skipped: number;
  errors: ImportRowError[];
  created_at: string;
  finished_at: string | null;
};
