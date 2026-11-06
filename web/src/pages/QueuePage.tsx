import { type FormEvent, useEffect, useState } from "react";
import { ApiError, type Meta, request, type Session, type TicketPage } from "../api";
import { PriorityBadge } from "../components";
import { CATEGORY, dateText, errorText, REASON, STATUS } from "../labels";

const PAGE_SIZE = 50;
const EMPTY = { category: "", priority: "", team: "", channel: "", status: "" };

type Props = { session: Session; review?: boolean; onError: (error: unknown) => void };

export function QueuePage({ session, review = false, onError }: Props) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [filters, setFilters] = useState(EMPTY);
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<TicketPage | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    request<Meta>("/meta", session.token).then(setMeta).catch(onError);
  }, [session.token, onError]);

  useEffect(() => {
    let current = true;
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
    for (const [name, value] of Object.entries(filters)) {
      if (value) params.set(name, value);
    }
    if (review) params.set("status", "needs_review");
    if (query) params.set("q", query);

    request<TicketPage>(`/tickets?${params}`, session.token)
      .then((next) => {
        if (!current) return;
        setPage(next);
        setError("");
      })
      .catch((caught) => {
        if (!current) return;
        onError(caught);
        setError(errorText(caught instanceof ApiError ? caught.code : "error"));
      });
    return () => {
      current = false;
    };
  }, [session.token, filters, query, offset, review, onError]);

  function setFilter(name: keyof typeof EMPTY, value: string) {
    setFilters({ ...filters, [name]: value });
    setOffset(0);
  }

  function search(event: FormEvent) {
    event.preventDefault();
    setQuery(text.trim());
    setOffset(0);
  }

  const select = (name: keyof typeof EMPTY, label: string, values: string[], names = {}) => (
    <select
      aria-label={label}
      className="field"
      value={filters[name]}
      onChange={(event) => setFilter(name, event.target.value)}
    >
      <option value="">{label}</option>
      {values.map((value) => (
        <option key={value} value={value}>
          {(names as Record<string, string>)[value] ?? value}
        </option>
      ))}
    </select>
  );

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{review ? "Qo‘lda tekshirish navbati" : "Navbat"}</h1>
      <div className="flex flex-wrap items-center gap-2">
        <form onSubmit={search} className="flex gap-2">
          <input
            className="field w-56"
            placeholder="Matn bo‘yicha qidirish"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          <button className="button-quiet">Qidirish</button>
        </form>
        {meta && (
          <>
            {select("category", "Kategoriya", meta.categories, CATEGORY)}
            {select("priority", "Ustuvorlik", meta.priorities)}
            {select("team", "Jamoa", meta.teams)}
            {select("channel", "Kanal", meta.channels)}
            {!review && select("status", "Holat", meta.statuses, STATUS)}
          </>
        )}
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Ustuvorlik</th>
              <th className="px-3 py-2">Murojaat</th>
              <th className="px-3 py-2">{review ? "Sabab" : "Kategoriya"}</th>
              <th className="px-3 py-2">Jamoa</th>
              <th className="px-3 py-2">Kelgan vaqti</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {page?.items.map((ticket) => (
              <tr key={ticket.id} className="align-top hover:bg-slate-50">
                <td className="px-3 py-2">
                  <PriorityBadge priority={ticket.priority} />
                </td>
                <td className="max-w-md px-3 py-2">
                  <a href={`#/tickets/${ticket.id}`} className="hover:underline">
                    {ticket.summary ?? ticket.preview ?? "Matn yo‘q"}
                  </a>
                  <div className="text-xs text-slate-500">
                    {ticket.source_ticket_id} · {ticket.channel}
                  </div>
                </td>
                <td className="px-3 py-2">
                  {review
                    ? (REASON[ticket.review_reason ?? ""] ?? "—")
                    : ticket.category
                      ? (CATEGORY[ticket.category] ?? ticket.category)
                      : (STATUS[ticket.status] ?? ticket.status)}
                </td>
                <td className="px-3 py-2">{ticket.team ?? "—"}</td>
                <td className="whitespace-nowrap px-3 py-2 text-slate-600">
                  {dateText(ticket.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {page?.items.length === 0 && (
          <p className="p-6 text-center text-sm text-slate-500">Ticket topilmadi.</p>
        )}
      </div>

      {page && page.total > 0 && (
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <span>
            {page.offset + 1}–{page.offset + page.items.length} / {page.total}
          </span>
          <button
            className="button-quiet"
            disabled={offset === 0}
            onClick={() => setOffset(offset - PAGE_SIZE)}
          >
            Oldingi
          </button>
          <button
            className="button-quiet"
            disabled={offset + PAGE_SIZE >= page.total}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            Keyingi
          </button>
        </div>
      )}
    </div>
  );
}
