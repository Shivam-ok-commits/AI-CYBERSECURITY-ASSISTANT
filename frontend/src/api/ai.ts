import api from "./client";

export const createSession = (title?: string) =>
  api.post("/ai/sessions", { title }).then((r) => r.data);

export const listSessions = () =>
  api.get("/ai/sessions").then((r) => r.data);

export const chat = (sessionId: number, message: string) =>
  api.post("/ai/chat", { session_id: sessionId, message }).then((r) => r.data);

export const investigate = (evidence: string) =>
  api.post("/ai/investigate", { evidence }).then((r) => r.data);

export const getRecommendations = (logId: number) =>
  api.post("/ai/recommendations", { log_id: logId }).then((r) => r.data);

export const explainLog = (text: string) =>
  api.post("/ai/explain", { text }).then((r) => r.data);

// ── AI Providers ──

export interface AIProviderInfo {
  name: string;
  available: boolean;
  requires_api_key: boolean;
}

export const listProviders = () =>
  api.get<AIProviderInfo[]>("/ai/providers").then((r) => r.data);

export const getActiveProvider = () =>
  api.get<AIProviderInfo>("/ai/providers/active").then((r) => r.data);

export const switchProvider = (provider: string) =>
  api.post<AIProviderInfo>("/ai/providers/switch", { provider }).then((r) => r.data);
