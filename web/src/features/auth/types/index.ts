import type { Role } from "@/shared/api/session";

export type Credentials = { username: string; password: string };

export type TokenResponse = {
  access_token: string;
  token_type: string;
  username: string;
  role: Role;
};
