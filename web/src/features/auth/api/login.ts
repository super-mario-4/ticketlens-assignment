import { request } from "@/shared/api/client";
import type { Credentials, TokenResponse } from "../types";

export function login(credentials: Credentials): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}
