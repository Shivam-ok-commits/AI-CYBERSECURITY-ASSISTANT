import api from "./client";

export const uploadLog = (formData: FormData) =>
  api.post("/logs/upload", formData).then((r) => r.data);

export const getAnalyses = () =>
  api.get("/logs").then((r) => r.data);

export const getAnalysis = (id: number) =>
  api.get(`/logs/${id}`).then((r) => r.data);

export const getTimeline = (id: number) =>
  api.get(`/logs/${id}/timeline`).then((r) => r.data);

export const getGlobalStats = () =>
  api.get("/logs/stats/global").then((r) => r.data);
