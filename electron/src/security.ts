import { session as electronSession } from "electron";

const CSP_SOURCE = {
  SELF: "'self'",
  NONE: "'none'",
  LOCALHOST_DEV: "http://localhost:5173",
  DATA: "data:",
  BLOB: "blob:",
};

export function applySecurityHeaders(isDev: boolean): void {
  electronSession.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const csp = buildCSP(isDev);
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [csp],
        "X-Content-Type-Options": ["nosniff"],
        "X-Frame-Options": ["DENY"],
        "X-XSS-Protection": ["1; mode=block"],
        "Referrer-Policy": ["strict-origin-when-cross-origin"],
        "Cross-Origin-Opener-Policy": ["same-origin"],
        "Cross-Origin-Embedder-Policy": ["require-corp"],
        "Cross-Origin-Resource-Policy": ["same-origin"],
        "Permissions-Policy": [
          "camera=(), microphone=(), geolocation=(), midi=(), sync-xhr=()",
        ],
      },
    });
  });
}

function buildCSP(isDev: boolean): string {
  const connectSrc = [CSP_SOURCE.SELF, CSP_SOURCE.LOCALHOST_DEV, "http://127.0.0.1:8000"].join(" ");
  const imgSrc = [CSP_SOURCE.SELF, CSP_SOURCE.DATA, CSP_SOURCE.BLOB].join(" ");
  const scriptSrc = isDev
    ? [CSP_SOURCE.SELF, CSP_SOURCE.LOCALHOST_DEV, "'unsafe-inline'", "'unsafe-eval'"].join(" ")
    : CSP_SOURCE.SELF;
  const styleSrc = isDev
    ? [CSP_SOURCE.SELF, CSP_SOURCE.LOCALHOST_DEV, "'unsafe-inline'"].join(" ")
    : [CSP_SOURCE.SELF, "'unsafe-inline'"].join(" ");
  const fontSrc = [CSP_SOURCE.SELF, CSP_SOURCE.DATA].join(" ");

  const directives = [
    `default-src ${CSP_SOURCE.NONE}`,
    `script-src ${scriptSrc}`,
    `style-src ${styleSrc}`,
    `connect-src ${connectSrc}`,
    `img-src ${imgSrc}`,
    `font-src ${fontSrc}`,
    `frame-src ${CSP_SOURCE.NONE}`,
    `object-src ${CSP_SOURCE.NONE}`,
    `base-uri ${CSP_SOURCE.SELF}`,
    `form-action ${CSP_SOURCE.SELF}`,
  ];

  return directives.join("; ");
}
