import api from "./client";

export const listRules = (params?: Record<string, string>) =>
  api.get("/detection/rules", { params }).then((r) => r.data);

export const createRule = (data: Record<string, unknown>) =>
  api.post("/detection/rules", data).then((r) => r.data);

export const getRule = (id: number) =>
  api.get(`/detection/rules/${id}`).then((r) => r.data);

export const updateRule = (id: number, data: Record<string, unknown>) =>
  api.put(`/detection/rules/${id}`, data).then((r) => r.data);

export const deleteRule = (id: number) =>
  api.delete(`/detection/rules/${id}`);

export const testRule = (id: number, sampleData: string[]) =>
  api.post(`/detection/rules/${id}/test`, sampleData).then((r) => r.data);

export const listSigmaRules = () =>
  api.get("/detection/sigma").then((r) => r.data);

export const createSigmaRule = (data: Record<string, unknown>) =>
  api.post("/detection/sigma", data).then((r) => r.data);

export const listYaraRules = () =>
  api.get("/detection/yara").then((r) => r.data);

export const createYaraRule = (data: Record<string, unknown>) =>
  api.post("/detection/yara", data).then((r) => r.data);

export const listHunts = () =>
  api.get("/detection/hunts").then((r) => r.data);

export const createHunt = (data: Record<string, unknown>) =>
  api.post("/detection/hunts", data).then((r) => r.data);

export const executeHunt = (id: number) =>
  api.post(`/detection/hunts/${id}/execute`).then((r) => r.data);

export const getHuntResults = () =>
  api.get("/detection/hunts/results").then((r) => r.data);

export const getAnalytics = () =>
  api.get("/detection/analytics").then((r) => r.data);
