/**
 * API Configuration — single source of truth for the API base URL.
 *
 * Auto-detection logic:
 *   - Electron (file:// protocol): full URL to local backend
 *   - Browser (Vite dev or served): relative path (Vite proxy handles routing)
 *
 * Every API request in the app MUST use this config or the `api` client
 * that imports it.  Never hardcode `localhost:8000` in individual files.
 */

export const API_PORT = 8000;
export const API_HOST = "127.0.0.1";
export const API_PREFIX = "/api/v1";

function detectApiBaseUrl(): string {
  if (typeof window !== "undefined" && typeof (window as any).sentinel !== "undefined") {
    // Running inside Electron — window.location.protocol is "file:"
    // Backend runs on the same machine; no Vite proxy available.
    return `http://${API_HOST}:${API_PORT}${API_PREFIX}`;
  }
  // Running in a browser (dev via Vite HMR or served via nginx).
  // Vite proxies /api/* to the backend, so the relative path works.
  return API_PREFIX;
}

/** The one true API base URL.  Every request uses this. */
export const API_BASE_URL = detectApiBaseUrl();
