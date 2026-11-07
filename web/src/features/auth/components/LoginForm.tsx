import { type FormEvent, useState } from "react";
import { ErrorAlert } from "@/shared/components/ErrorAlert";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { useLogin } from "../hooks/use-login";

export function LoginForm() {
  const { signIn, error, busy } = useLogin();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();
    void signIn({ username, password });
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="username">Login</Label>
        <Input
          id="username"
          value={username}
          autoComplete="username"
          maxLength={64}
          onChange={(event) => setUsername(event.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">Parol</Label>
        <Input
          id="password"
          type="password"
          value={password}
          autoComplete="current-password"
          maxLength={256}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </div>
      {error && <ErrorAlert message={error} />}
      <Button type="submit" className="w-full" disabled={busy}>
        Kirish
      </Button>
    </form>
  );
}
