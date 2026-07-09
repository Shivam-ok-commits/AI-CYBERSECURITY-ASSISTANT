import api from "./client";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const login = (data: LoginRequest) =>
  api.post<AuthResponse>("/auth/login", data).then((r) => r.data);

export const loginMfa = (data: LoginRequest & { mfa_code: string }) =>
  api.post<AuthResponse>("/auth/login/mfa", data).then((r) => r.data);

export const register = (data: { username: string; password: string }) =>
  api.post<AuthResponse>("/auth/register", data).then((r) => r.data);

export const getProfile = () =>
  api.get<{ id: number; username: string; email: string; role: string; mfa_enabled: boolean }>("/auth/me").then((r) => r.data);

export const getOAuthUrl = (provider: string, redirectUri: string) =>
  api.get<{ authorization_url: string }>(`/auth/oauth/${provider}/url`, { params: { redirect_uri: redirectUri } }).then((r) => r.data);

export const oauthCallback = (provider: string, code: string, redirectUri: string) =>
  api.post<AuthResponse>(`/auth/oauth/${provider}/callback`, { provider, code, redirect_uri: redirectUri }).then((r) => r.data);

export const setupMfa = () =>
  api.post<{ secret: string; qr_code: string }>("/auth/mfa/setup").then((r) => r.data);

export const verifyMfa = (code: string) =>
  api.post<{ verified: boolean }>("/auth/mfa/verify", { code }).then((r) => r.data);

export const enableMfa = (code: string) =>
  api.post<{ mfa_enabled: boolean }>("/auth/mfa/enable", { code }).then((r) => r.data);

export const disableMfa = () =>
  api.post<{ mfa_enabled: boolean }>("/auth/mfa/disable").then((r) => r.data);
