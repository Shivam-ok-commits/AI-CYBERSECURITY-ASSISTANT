/**
 * Splash & Error Screen HTML Templates
 * ======================================
 * Standalone HTML builders — no Electron imports, safe for circular-dep-free
 * usage by both `startup.ts` and `window.ts`.
 */

// ─── Splash / Loading Screen ──────────────────────────────────────────────

interface SplashOptions {
  status?: string;
  error?: string;
}

export function buildSplashHtml(opts: SplashOptions = {}): string {
  const statusText = opts.status || "Initializing...";
  const isError = !!opts.error;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sentinel — Starting...</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0B1220;
    color: #E2E8F0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    overflow: hidden;
    user-select: none;
  }
  .container {
    text-align: center;
    padding: 2rem;
  }
  .logo {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    background: linear-gradient(135deg, #3B82F6, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
  }
  .subtitle {
    font-size: 0.85rem;
    color: #64748B;
    margin-bottom: 2rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
  }
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #1E293B;
    border-top-color: #3B82F6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 1.5rem;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .status {
    font-size: 0.9rem;
    color: #94A3B8;
    min-height: 1.4em;
  }
  .error {
    color: #EF4444;
    font-size: 0.8rem;
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 8px;
    max-width: 360px;
    word-break: break-word;
    display: ${isError ? "block" : "none"};
  }
  .dots::after {
    content: '';
    animation: dots 1.5s steps(4, end) infinite;
  }
  @keyframes dots {
    0%   { content: ''; }
    25%  { content: '.'; }
    50%  { content: '..'; }
    75%  { content: '...'; }
    100% { content: ''; }
  }
</style>
</head>
<body>
<div class="container">
  <div class="logo">SENTINEL</div>
  <div class="subtitle">Security Operations Center</div>
  <div class="spinner"></div>
  <div class="status">${escapeHtml(statusText)}<span class="dots"></span></div>
  <div class="error">${escapeHtml(opts.error || "")}</div>
</div>
</body>
</html>`;
}

// ─── Error Screen ─────────────────────────────────────────────────────────

export function buildErrorHtml(error: string, attempts: number): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sentinel — Startup Error</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0B1220;
    color: #E2E8F0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    padding: 2rem;
    text-align: center;
  }
  .icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  h1 {
    font-size: 1.25rem;
    margin-bottom: 0.75rem;
    color: #F8FAFC;
  }
  .detail {
    font-size: 0.85rem;
    color: #94A3B8;
    margin-bottom: 0.5rem;
    line-height: 1.5;
    max-width: 400px;
  }
  .error-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: #FCA5A5;
    font-family: 'SF Mono', 'Consolas', monospace;
    font-size: 0.8rem;
    margin: 1rem 0;
    max-width: 440px;
    word-break: break-word;
    text-align: left;
    line-height: 1.4;
  }
  .hint {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 1.5rem;
  }
</style>
</head>
<body>
  <div class="icon">&#9888;&#65039;</div>
  <h1>Startup Failed</h1>
  <div class="detail">
    The backend service was unable to start after ${attempts} attempts.
  </div>
  <div class="error-box">${escapeHtml(error)}</div>
  <div class="hint">Sentinel will close automatically.</div>
</body>
</html>`;
}

// ─── Shared helper ────────────────────────────────────────────────────────

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
