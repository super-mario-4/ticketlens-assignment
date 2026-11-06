import { type FormEvent, useState } from "react";
import { ApiError, type ImportJob, request, type Session } from "../api";
import { errorText } from "../labels";

type Props = { session: Session; onError: (error: unknown) => void };

export function ImportPage({ session, onError }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<ImportJob | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    setJob(null);
    const body = new FormData();
    body.append("file", file);
    try {
      setJob(await request<ImportJob>("/imports", session.token, { method: "POST", body }));
    } catch (caught) {
      onError(caught);
      setError(errorText(caught instanceof ApiError ? caught.code : "error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl space-y-4">
      <h1 className="text-xl font-semibold">CSV import</h1>
      <form onSubmit={submit} className="card space-y-3">
        <p className="text-sm text-slate-600">
          Ustunlar: id, channel, created_at, text, customer_id. Fayl 10 MB gacha, UTF-8. Xom fayl
          saqlanmaydi: matn maskalangandan keyin yoziladi.
        </p>
        <input
          type="file"
          accept=".csv,text/csv"
          className="block text-sm"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <button className="button" disabled={!file || busy}>
          {busy ? "Yuklanmoqda..." : "Yuklash"}
        </button>
      </form>

      {error && <p className="text-sm text-red-700">{error}</p>}

      {job && (
        <section className="card space-y-1 text-sm">
          <h2 className="font-medium">{job.filename}</h2>
          <p>Holat: {job.status}</p>
          <p>
            Jami {job.total}, qo‘shildi {job.inserted}, o‘tkazib yuborildi {job.skipped}
          </p>
          {job.errors.length > 0 && <p>Xato qatorlar: {job.errors.length}</p>}
          <p className="text-slate-600">AI tasnifi fonda ishlaydi, natija navbatda ko‘rinadi.</p>
        </section>
      )}
    </div>
  );
}
