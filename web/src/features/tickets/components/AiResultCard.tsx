import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { CATEGORY } from "@/shared/lib/labels";
import type { Classification } from "../types";
import { PriorityBadge } from "./PriorityBadge";

export function AiResultCard({ result }: { result: Classification | undefined }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">
          <h2>AI natijasi</h2>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {result ? (
          <>
            <p>{result.summary}</p>
            <div className="flex flex-wrap items-center gap-2">
              <PriorityBadge priority={result.priority} />
              {CATEGORY[result.category] ?? result.category} · {result.team ?? "Jamoasiz"} · ishonch{" "}
              {Math.round(result.confidence * 100)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {result.model}, prompt {result.prompt_version},{" "}
              {(result.latency_ms / 1000).toFixed(1)} s
            </p>
          </>
        ) : (
          <p className="text-muted-foreground">Bu ticket AI’ga yuborilmagan.</p>
        )}
      </CardContent>
    </Card>
  );
}
