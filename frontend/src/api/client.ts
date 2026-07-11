import axios from "axios";
import { API_BASE_URL } from "./config";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Token expired or invalid — clear it and dispatch an event so
      // any UI component (like a session timeout banner) can react.
      localStorage.removeItem("token");
      window.dispatchEvent(new CustomEvent("sentinel:session-expired"));
    }
    return Promise.reject(err);
  }
);

export default api;
