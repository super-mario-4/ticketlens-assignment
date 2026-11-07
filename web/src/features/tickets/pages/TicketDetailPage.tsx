import { ArrowLeft, CheckCircle2, RotateCcw, TriangleAlert } from "lucide-react";
import { Link, useLocation, useParams } from "react-router";
import { useSession } from "@/shared/api/session";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { PageHeader } from "@/shared/components/PageHeader";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { dateText } from "@/shared/lib/format";
import { STATUS } from "@/shared/lib/labels";
import { AiResultCard } from "../components/AiResultCard";
import { CorrectionForm } from "../components/CorrectionForm";
import { CorrectionHistory } from "../components/CorrectionHistory";
import { CurrentValuesCard } from "../components/CurrentValuesCard";
import { TicketTextCard } from "../components/TicketTextCard";
import { useMeta } from "../hooks/use-meta";
import { useTicket } from "../hooks/use-ticket";
import { REVIEW_REASON } from "../labels";
import type { ReviewReason, TicketStatus } from "../types";

const REQUEUE_REASONS: ReviewReason[] = ["llm_unavailable", "schema_error"];
const UNFINISHED: TicketStatus[] = ["pending", "processing"];

function BackLink() {
  const from = (useLocation().state as { from?: string } | null)?.from;
  const review = from === "/review";
  return (
    <Link
      to={review ? "/review" : "/"}
      className="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
    >
      <ArrowLeft className="size-4" aria-hidden />
      {review ? "Qo‘lda tekshirish" : "Navbat"}
    </Link>
  );
}

function TicketDetailView({ id }: { id: string }) {
  const isOperator = useSession()?.role === "operator";
  const { meta, error: metaError } = useMeta();
  const { ticket, loadError, actionError, saved, busy, correct, reclassify } = useTicket(id);

  if (!ticket) {
    return (
      <div className="space-y-4">
        <BackLink />
        {loadError ? <ErrorAlert message={loadError} /> : <Skeleton className="h-64 w-full" />}
      </div>
    );
  }

  const canCorrect = isOperator && !UNFINISHED.includes(ticket.status);
  const canReclassify =
    isOperator &&
    ticket.status === "needs_review" &&
    ticket.review_reason !== null &&
    REQUEUE_REASONS.includes(ticket.review_reason);
  const error = actionError || metaError;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="min-w-0 space-y-4 lg:col-span-2">
        <div className="space-y-2">
          <BackLink />
          <PageHeader
            title={ticket.source_ticket_id}
            description={`${ticket.channel} · ${dateText(ticket.created_at)} · ${STATUS[ticket.status] ?? ticket.status}`}
          />
        </div>

        {ticket.review_reason && (
          <Alert className="border-amber-200 bg-amber-50 text-amber-900">
            <TriangleAlert className="size-4" aria-hidden />
            <AlertDescription>
              Qo‘lda tekshirish sababi: {REVIEW_REASON[ticket.review_reason]}
            </AlertDescription>
          </Alert>
        )}

        <TicketTextCard text={ticket.text_masked} />
        <AiResultCard result={ticket.classifications.at(-1)} />
        {ticket.corrections.length > 0 && <CorrectionHistory corrections={ticket.corrections} />}
      </div>

      <aside className="min-w-0 space-y-4">
        <CurrentValuesCard ticket={ticket} />

        {canCorrect && meta && (
          // A new key starts the form from the values just saved.
          <CorrectionForm
            key={`${ticket.status}-${ticket.corrections.length}`}
            ticket={ticket}
            meta={meta}
            busy={busy}
            onSubmit={(correction) => void correct(correction)}
          />
        )}

        {saved && (
          <Alert className="border-green-200 bg-green-50 text-green-900">
            <CheckCircle2 className="size-4" aria-hidden />
            <AlertDescription>Saqlandi.</AlertDescription>
          </Alert>
        )}

        {canReclassify && (
          <Button
            variant="outline"
            className="w-full bg-card"
            disabled={busy}
            onClick={() => void reclassify()}
          >
            <RotateCcw aria-hidden />
            Qayta tasniflash
          </Button>
        )}

        {error && <ErrorAlert message={error} />}
      </aside>
    </div>
  );
}

export function TicketDetailPage() {
  const { id = "" } = useParams();
  return <TicketDetailView key={id} id={id} />;
}
