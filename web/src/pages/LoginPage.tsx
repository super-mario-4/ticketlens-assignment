import { type FormEvent, useState } from "react";
import { ApiError, request, type Session } from "../api";
import { errorText } from "../labels";

type Token = { access_token: string; username: string; role: Session["role"] };

export function LoginPage({ onLogin }: { onLogin: (session: Session) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const token = await request<Token>("/auth/login", null, {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      onLogin({ token: token.access_token, username: token.username, role: token.role });
    } catch (caught) {
      setError(errorText(caught instanceof ApiError ? caught.code : "error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-3">
        <h1 className="text-lg font-semibold">TicketLens</h1>
        <label className="block text-sm">
          Login
          <input
            className="field mt-1 w-full"
            value={username}
            autoComplete="username"
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Parol
          <input
            className="field mt-1 w-full"
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button className="button w-full" disabled={busy}>
          Kirish
        </button>
      </form>
    </div>
  );
}
