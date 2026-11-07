import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";

export function TicketTextCard({ text }: { text: string | null }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">
          <h2>Maskalangan matn</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Shown as text, never as HTML: this is customer input. */}
        <p className="whitespace-pre-wrap break-words">{text ?? "Matn yo‘q"}</p>
      </CardContent>
    </Card>
  );
}
