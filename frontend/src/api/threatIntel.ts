import api from "./client";

export const extractIocs = (text: string) =>
  api.post("/threat/extract", { text }).then((r) => r.data);

export const enrichIoc = (indicator: string) =>
  api.get("/threat/lookup", { params: { indicator } }).then((r) => r.data);

export const correlateIocs = (logId: number) =>
  api.get(`/threat/correlate/${logId}`).then((r) => r.data);

export const getThreatFeed = () =>
  api.get("/threat/feed").then((r) => r.data);
