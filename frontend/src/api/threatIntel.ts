import api from "./client";

export const extractIocs = (text: string) =>
  api.post("/threat/extract", { text }).then((r) => r.data);

export const enrichIoc = (indicator: string) =>
  api.get("/threat/lookup", { params: { indicator } }).then((r) => r.data);

export const correlateIocs = (iocs: string[]) =>
  api.post("/threat/correlate", { iocs }).then((r) => r.data);

export const getThreatFeed = () =>
  api.get("/threat/feed").then((r) => r.data);
