import { app, BrowserWindow, screen } from "electron";
import * as path from "path";

const isDev = !app.isPackaged;

const WINDOW_DEFAULTS = {
  width: 1440,
  height: 900,
  minWidth: 1024,
  minHeight: 700,
};

let mainWindow: BrowserWindow | null = null;

export function createMainWindow(): BrowserWindow {
  const { width, height } = getCenteredSize();

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
      sandbox: false,
    },
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow?.show();
    if (isDev) {
      mainWindow?.webContents.openDevTools({ mode: "detach" });
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "../../frontend/dist/index.html"));
  }

  return mainWindow;
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
