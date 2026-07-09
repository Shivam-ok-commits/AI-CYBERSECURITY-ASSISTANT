import api from "./client";

export const getFullDashboard = () =>
  api.get("/dashboard/summary").then((r) => r.data);

export const getAlerts = (params?: Record<string, string>) =>
  api.get("/dashboard/alerts", { params }).then((r) => r.data);

export const getLogStats = () =>
  api.get("/dashboard/logs/stats").then((r) => r.data);

export const getThreatStats = () =>
  api.get("/dashboard/threat/stats").then((r) => r.data);

export const getInvestigationStats = () =>
  api.get("/dashboard/investigations/stats").then((r) => r.data);
