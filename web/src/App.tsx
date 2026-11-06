import { useCallback, useEffect, useState } from "react";
import { ApiError, loadSession, saveSession, type Session } from "./api";
import { ImportPage } from "./pages/ImportPage";
import { LoginPage } from "./pages/LoginPage";
import { QueuePage } from "./pages/QueuePage";
import { StatsPage } from "./pages/StatsPage";
import { TicketPage } from "./pages/TicketPage";

function useRoute(): string {
  const [route, setRoute] = useState(window.location.hash.slice(1) || "/");
  useEffect(() => {
    const onChange = () => setRoute(window.location.hash.slice(1) || "/");
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

export function App() {
  const [session, setSession] = useState<Session | null>(loadSession);
  const route = useRoute();

  const logout = useCallback(() => {
    saveSession(null);
    setSession(null);
  }, []);

  // An expired token ends the session instead of showing errors on every page.
  const onError = useCallback(
    (error: unknown) => {
      if (error instanceof ApiError && error.status === 401) logout();
    },
    [logout],
  );

  if (!session) {
    return (
      <LoginPage
        onLogin={(next) => {
          saveSession(next);
          setSession(next);
        }}
      />
    );
  }

  const links = [
    { href: "#/", label: "Navbat" },
    { href: "#/review", label: "Qo‘lda tekshirish" },
    ...(session.role === "operator" ? [{ href: "#/import", label: "Import" }] : []),
    ...(session.role === "lead" ? [{ href: "#/stats", label: "Statistika" }] : []),
  ];
  const ticketId = route.startsWith("/tickets/") ? route.slice("/tickets/".length) : null;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <span className="font-semibold">TicketLens</span>
          <nav className="flex flex-wrap gap-4 text-sm">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className={
                  `#${route}` === link.href
                    ? "font-medium text-indigo-700"
                    : "text-slate-600 hover:text-slate-900"
                }
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm text-slate-600">
            <span>
              {session.username} ({session.role === "lead" ? "rahbar" : "operator"})
            </span>
            <button className="button-quiet" onClick={logout}>
              Chiqish
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        {ticketId ? (
          <TicketPage key={ticketId} id={ticketId} session={session} onError={onError} />
        ) : route === "/review" ? (
          <QueuePage key="review" session={session} review onError={onError} />
        ) : route === "/import" && session.role === "operator" ? (
          <ImportPage session={session} onError={onError} />
        ) : route === "/stats" && session.role === "lead" ? (
          <StatsPage session={session} onError={onError} />
        ) : (
          <QueuePage key="queue" session={session} onError={onError} />
        )}
      </main>
    </div>
  );
}
