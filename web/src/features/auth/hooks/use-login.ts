import { useState } from "react";
import { errorMessage } from "@/shared/api/errors";
import { setSession } from "@/shared/api/session";
import { login } from "../api/login";
import type { Credentials } from "../types";

export function useLogin() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function signIn(credentials: Credentials): Promise<void> {
    setBusy(true);
    setError("");
    try {
      const token = await login(credentials);
      setSession({ token: token.access_token, username: token.username, role: token.role });
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(false);
    }
  }

  return { signIn, error, busy };
}
