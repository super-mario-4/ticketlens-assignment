import { Link } from "react-router";
import { Badge } from "@/shared/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import type { ImportJob, ImportStatus } from "../types";

// A long report stays readable; the rest of it is only counted.
const SHOWN_ERRORS = 20;

const JOB_STATUS: Record<ImportStatus, string> = {
  processing: "Jarayonda",
  completed: "Yakunlandi",
  failed: "Xato bilan to‘xtadi",
};

const ROW_ERROR: Record<string, string> = {
  wrong_column_count: "Ustunlar soni noto‘g‘ri",
  invalid_id: "ID noto‘g‘ri",
  invalid_channel: "Kanal noto‘g‘ri",
  invalid_created_at: "Sana noto‘g‘ri",
  invalid_customer_id: "Mijoz ID noto‘g‘ri",
  masking_error: "Maskalash xatosi",
  malformed_csv: "CSV fayl buzilgan",
  import_failed: "Import to‘xtadi",
};

function Figure({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-xl font-semibold tabular-nums">{value}</dd>
    </div>
  );
}

export function ImportResult({ job }: { job: ImportJob }) {
  const hidden = job.errors.length - SHOWN_ERRORS;

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0">
        <CardTitle className="break-all text-base">
          <h2>{job.filename}</h2>
        </CardTitle>
        <Badge variant={job.status === "failed" ? "destructive" : "secondary"}>
          {JOB_STATUS[job.status]}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid grid-cols-3 gap-4">
          <Figure label="Jami" value={job.total} />
          <Figure label="Qo‘shildi" value={job.inserted} />
          <Figure label="O‘tkazib yuborildi" value={job.skipped} />
        </dl>

        {job.errors.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">Xato qatorlar: {job.errors.length}</h3>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Qator</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>Xato</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {job.errors.slice(0, SHOWN_ERRORS).map((error, index) => (
                    <TableRow key={index}>
                      <TableCell className="tabular-nums">{error.row ?? "—"}</TableCell>
                      <TableCell>{error.id ?? "—"}</TableCell>
                      <TableCell>{ROW_ERROR[error.code] ?? error.code}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {hidden > 0 && <p className="text-sm text-muted-foreground">Yana {hidden} ta xato.</p>}
          </div>
        )}

        {job.status === "completed" && (
          <p className="text-sm text-muted-foreground">
            AI tasnifi fonda ishlaydi, natija{" "}
            <Link to="/" className="font-medium text-primary underline-offset-4 hover:underline">
              navbatda
            </Link>{" "}
            ko‘rinadi.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
