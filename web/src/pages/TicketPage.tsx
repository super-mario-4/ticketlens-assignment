import { type FormEvent, useCallback, useEffect, useState } from "react";
import { ApiError, type Meta, request, type Session, type TicketDetail } from "../api";
import { PriorityBadge } from "../components";
import { CATEGORY, dateText, errorText, REASON, STATUS } from "../labels";

const REQUEUE_REASONS = ["llm_unavailable", "schema_error"];

type Props = { id: string; session: Session; onError: (error: unknown) => void };

export function TicketPage({ id, session, onError }: Props) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [team, setTeam] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  const show = useCallback((next: TicketDetail) => {
    setTicket(next);
    setCategory(next.category ?? "");
    setPriority(next.priority ?? "");
    setTeam(next.team ?? "");
  }, []);

  const fail = useCallback(
    (caught: unknown) => {
      onError(caught);
      setError(errorText(caught instanceof ApiError ? caught.code : "error"));
    },
    [onError],
  );

  useEffect(() => {
    request<TicketDetail>(`/tickets/${id}`, session.token).then(show).catch(fail);
    request<Meta>("/meta", session.token).then(setMeta).catch(fail);
  }, [id, session.token, show, fail]);

  async function correct(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setSaved(false);
    try {
      const next = await request<TicketDetail>(`/tickets/${id}/classification`, session.token, {
        method: "PATCH",
        body: JSON.stringify({
          category,
          priority,
          team: team || null,
          reason: reason.trim() || null,
        }),
      });
      show(next);
      setReason("");
      setSaved(true);
    } catch (caught) {
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  async function reclassify() {
    setBusy(true);
    setError("");
    try {
      await request(`/tickets/${id}/reclassify`, session.token, { method: "POST" });
      show(await request<TicketDetail>(`/tickets/${id}`, session.token));
    } catch (caught) {
      fail(caught);
    } finally {
      setBusy(false);
    }
  }

  if (!ticket) {
    return <p className="text-sm text-slate-500">{error || "Yuklanmoqda..."}</p>;
  }

  const ai = ticket.classifications.at(-1);
  const canCorrect = session.role === "operator" && !["pending", "processing"].includes(ticket.status);

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <div>
          <a href="#/" className="text-sm text-indigo-700 hover:underline">
            ← Navbat
          </a>
          <h1 className="mt-1 text-xl font-semibold">{ticket.source_ticket_id}</h1>
          <p className="text-sm text-slate-600">
            {ticket.channel} · {dateText(ticket.created_at)} ·{" "}
            {STATUS[ticket.status] ?? ticket.status}
          </p>
        </div>

        {ticket.review_reason && (
          <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">
            Qo‘lda tekshirish sababi: {REASON[ticket.review_reason] ?? ticket.review_reason}
          </p>
        )}

        <section className="card">
          <h2 className="mb-2 text-sm font-medium text-slate-500">Maskalangan matn</h2>
          {/* Shown as text, never as HTML: this is customer input. */}
          <p className="whitespace-pre-wrap break-words">{ticket.text_masked ?? "Matn yo‘q"}</p>
        </section>

        <section className="card">
          <h2 className="mb-2 text-sm font-medium text-slate-500">AI natijasi</h2>
          {ai ? (
            <div className="space-y-2 text-sm">
              <p>{ai.summary}</p>
              <p className="flex flex-wrap items-center gap-2">
                <PriorityBadge priority={ai.priority} />
                {CATEGORY[ai.category] ?? ai.category} · {ai.team ?? "Jamoasiz"} · ishonch{" "}
                {Math.round(ai.confidence * 100)}%
              </p>
              <p className="text-xs text-slate-500">
                {ai.model}, prompt {ai.prompt_version}, {(ai.latency_ms / 1000).toFixed(1)} s
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Bu ticket AI’ga yuborilmagan.</p>
          )}
        </section>

        {ticket.corrections.length > 0 && (
          <section className="card">
            <h2 className="mb-2 text-sm font-medium text-slate-500">Tuzatishlar tarixi</h2>
            <ul className="space-y-2 text-sm">
              {ticket.corrections.map((item) => (
                <li key={item.corrected_at}>
                  {dateText(item.corrected_at)}, {item.corrected_by}:{" "}
                  {CATEGORY[item.old_category ?? ""] ?? "—"} →{" "}
                  {CATEGORY[item.new_category] ?? item.new_category}, {item.old_priority ?? "—"} →{" "}
                  {item.new_priority}, {item.old_team ?? "—"} → {item.new_team ?? "—"}
                  {item.reason && <span className="text-slate-600"> ({item.reason})</span>}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <aside className="space-y-4">
        <section className="card space-y-1 text-sm">
          <h2 className="text-sm font-medium text-slate-500">Amaldagi qiymat</h2>
          <p>
            <PriorityBadge priority={ticket.priority} />
          </p>
          <p>{ticket.category ? (CATEGORY[ticket.category] ?? ticket.category) : "—"}</p>
          <p>{ticket.team ?? "Jamoasiz"}</p>
        </section>

        {canCorrect && meta && (
          <form onSubmit={correct} className="card space-y-3 text-sm">
            <h2 className="font-medium">Tuzatish</h2>
            <label className="block">
              Kategoriya
              <select
                className="field mt-1 w-full"
                value={category}
                onChange={(event) => {
                  setCategory(event.target.value);
                  setTeam(meta.routing[event.target.value] ?? "");
                }}
                required
              >
                <option value="" disabled>
                  Tanlang
                </option>
                {meta.categories.map((value) => (
                  <option key={value} value={value}>
                    {CATEGORY[value] ?? value}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              Ustuvorlik
              <select
                className="field mt-1 w-full"
                value={priority}
                onChange={(event) => setPriority(event.target.value)}
                required
              >
                <option value="" disabled>
                  Tanlang
                </option>
                {meta.priorities.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <label className="block">
              Jamoa
              <select
                className="field mt-1 w-full"
                value={team}
                onChange={(event) => setTeam(event.target.value)}
              >
                <option value="">Kategoriya bo‘yicha</option>
                {meta.teams.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <label className="block">
              Izoh (ixtiyoriy)
              <textarea
                className="field mt-1 w-full"
                rows={2}
                maxLength={1000}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              />
            </label>
            <button className="button w-full" disabled={busy}>
              Saqlash
            </button>
            {saved && <p className="text-green-700">Saqlandi.</p>}
          </form>
        )}

        {session.role === "operator" &&
          ticket.status === "needs_review" &&
          REQUEUE_REASONS.includes(ticket.review_reason ?? "") && (
            <button className="button-quiet w-full" disabled={busy} onClick={reclassify}>
              Qayta tasniflash
            </button>
          )}

        {error && <p className="text-sm text-red-700">{error}</p>}
      </aside>
    </div>
  );
}
