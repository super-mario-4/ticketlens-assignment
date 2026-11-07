import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { PageHeader } from "@/shared/components/PageHeader";
import { Card, CardContent } from "@/shared/components/ui/card";
import { ImportForm } from "../components/ImportForm";
import { ImportResult } from "../components/ImportResult";
import { useCsvImport } from "../hooks/use-csv-import";

export function ImportPage() {
  const { upload, job, error, busy } = useCsvImport();

  return (
    <div className="max-w-2xl space-y-4">
      <PageHeader
        title="CSV import"
        description="Ustunlar: id, channel, created_at, text, customer_id. Fayl 10 MB gacha, UTF-8. Xom fayl saqlanmaydi: matn maskalangandan keyin yoziladi."
      />
      <Card>
        <CardContent className="pt-6">
          <ImportForm busy={busy} onUpload={(file) => void upload(file)} />
        </CardContent>
      </Card>
      {error && <ErrorAlert message={error} />}
      {job && <ImportResult job={job} />}
    </div>
  );
}
