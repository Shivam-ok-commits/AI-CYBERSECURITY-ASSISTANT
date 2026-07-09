import api from "./client";

export interface CaseData {
  title: string;
  description?: string;
  severity?: string;
  status?: string;
  attack_stage?: string;
  assignee?: string;
  tags?: string[];
}

export const listCases = (params?: Record<string, string>) =>
  api.get("/cases", { params }).then((r) => r.data);

export const getCase = (id: number) =>
  api.get(`/cases/${id}`).then((r) => r.data);

export const createCase = (data: CaseData) =>
  api.post("/cases", data).then((r) => r.data);

export const updateCase = (id: number, data: Partial<CaseData>) =>
  api.put(`/cases/${id}`, data).then((r) => r.data);

export const archiveCase = (id: number) =>
  api.post(`/cases/${id}/archive`).then((r) => r.data);

export const addEvidence = (caseId: number, data: { description: string; source: string; content: string; evidence_type?: string }) =>
  api.post(`/cases/${caseId}/evidence`, data).then((r) => r.data);

export const addComment = (caseId: number, data: { content: string; internal?: boolean }) =>
  api.post(`/cases/${caseId}/comments`, data).then((r) => r.data);

export const generateReport = (caseId: number, format?: string) =>
  api.post(`/cases/${caseId}/reports`, { format }).then((r) => r.data);
