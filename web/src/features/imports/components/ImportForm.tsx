import { Loader2, Upload } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";

type Props = { busy: boolean; onUpload: (file: File) => void };

export function ImportForm({ busy, onUpload }: Props) {
  const [file, setFile] = useState<File | null>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (file) onUpload(file);
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="csv-file">CSV fayl</Label>
        <Input
          id="csv-file"
          type="file"
          accept=".csv,text/csv"
          className="bg-card"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </div>
      <Button type="submit" disabled={!file || busy}>
        {busy ? <Loader2 className="animate-spin" aria-hidden /> : <Upload aria-hidden />}
        {busy ? "Yuklanmoqda..." : "Yuklash"}
      </Button>
    </form>
  );
}
