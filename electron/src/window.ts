import { app, BrowserWindow, screen } from "electron";
import * as path from "path";
import { applySecurityHeaders } from "./security";
import { buildSplashHtml, buildErrorHtml } from "./splash-templates";

const isDev = !app.isPackaged;

const WINDOW_DEFAULTS = {
  width: 1440,
  height: 900,
  minWidth: 1024,
  minHeight: 700,
};

let mainWindow: BrowserWindow | null = null;

/**
 * Create (or return) the single main application window.
 * The window is created with `show: false` so the caller can first
 * display a splash screen via `loadSplash()` before revealing it.
 */
export function createMainWindow(): BrowserWindow {
  // Guard: if the window already exists, focus and return it.
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show();
    mainWindow.focus();
    return mainWindow;
  }

  const { width, height } = getCenteredSize();

  // Apply CSP and security headers (only once)
  applySecurityHeaders(isDev);

  mainWindow = new BrowserWindow({
    width,
    height,
    minWidth: WINDOW_DEFAULTS.minWidth,
    minHeight: WINDOW_DEFAULTS.minHeight,
    backgroundColor: "#0B1220",
    show: false,
    title: "Sentinel — Security Operations Center",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: !isDev,
      webSecurity: true,
      allowRunningInsecureContent: false,
      experimentalFeatures: false,
    },
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  return mainWindow;
}

/**
 * Load the splash/loading screen into the window.
 * Call this before `show()` so the user sees a branded loading state
 * instead of a blank white window.
 */
export function loadSplash(win: BrowserWindow, status?: string): void {
  const html = buildSplashHtml({ status });
  win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  win.once("ready-to-show", () => {
    if (!win.isDestroyed()) win.show();
  });
}

/**
 * Update the splash screen with a new status message.
 * Useful for showing retry progress during backend startup.
 */
export function updateSplashStatus(win: BrowserWindow, status: string, error?: string): void {
  if (win.isDestroyed()) return;
  const html = buildSplashHtml({ status, error });
  win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
}

/**
 * Load the React frontend into the window.
 * Call this ONLY after the backend is confirmed healthy.
 */
export function loadFrontend(win: BrowserWindow): void {
  if (win.isDestroyed()) return;

  if (isDev) {
    win.loadURL("http://localhost:5173");
  } else {
    win.loadFile(path.join(process.resourcesPath, "frontend", "index.html"));
  }

  if (isDev) {
    win.once("ready-to-show", () => {
      win?.webContents.openDevTools({ mode: "bottom" });
    });
  }
}

/**
 * Display a fatal error screen in the window.
 * Called when the backend cannot start after all retries.
 */
export function showErrorScreen(
  win: BrowserWindow,
  error: string,
  attempts: number
): void {
  if (win.isDestroyed()) return;
  const html = buildErrorHtml(error, attempts);
  win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  win.once("ready-to-show", () => {
    if (!win.isDestroyed()) win.show();
  });
}

function getCenteredSize(): { width: number; height: number } {
  const displays = screen.getAllDisplays();
  if (displays.length === 0) return { width: WINDOW_DEFAULTS.width, height: WINDOW_DEFAULTS.height };

  const primary = displays[0].workArea;
  const width = Math.min(WINDOW_DEFAULTS.width, primary.width);
  const height = Math.min(WINDOW_DEFAULTS.height, primary.height);

  return { width, height };
}

export function getMainWindow(): BrowserWindow | null {
  return mainWindow;
}
