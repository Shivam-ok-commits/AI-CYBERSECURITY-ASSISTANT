import { app, ipcMain, dialog, shell, Notification, BrowserWindow } from "electron";
import * as path from "path";
import * as fs from "fs";
import { getMainWindow, createMainWindow, loadFrontend } from "./window";
import { StartupManager } from "./startup";
import { createTray, destroyTray } from "./tray";
import { checkForUpdates, downloadUpdate, installUpdate, getStatus, onStatusChange } from "./updater";
import { getSecureStore } from "./secure-store";
import { validateIPC, validateFilePath, sanitizeString, validateStorageKey } from "./ipc-validator";

// ── Single instance lock ──────────────────────────────────────────────────
// Prevent duplicate Sentinel processes (e.g., double-clicking the EXE twice).
// If another instance is detected, the existing window receives focus instead.
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
  process.exit(0);
}

const secureStore = getSecureStore();
const startup = new StartupManager();
let backupInterval: ReturnType<typeof setInterval> | null = null;

const appAny = app as unknown as { isQuitting?: boolean };

const ALLOWED_APP_PATHS = new Set([
  "userData", "home", "appData", "desktop", "documents", "downloads", "music", "pictures", "videos", "temp", "exe", "module",
]);

function ensureDirectories(): void {
  const dirs = [
    path.join(app.getPath("userData"), "storage"),
    path.join(app.getPath("userData"), "uploads"),
    path.join(app.getPath("userData"), "logs"),
    path.join(app.getPath("userData"), "reports"),
    path.join(app.getPath("userData"), "backups"),
  ];
  for (const dir of dirs) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function getRecentFiles(): string[] {
  return (secureStore.get<string[]>("recentFiles")) || [];
}

function addRecentFile(filePath: string): void {
  const validated = validateFilePath(filePath);
  if (!validated) return;
  const files = getRecentFiles().filter((f) => f !== validated);
  files.unshift(validated);
  secureStore.set("recentFiles", files.slice(0, 20));
}

function showNativeNotification(title: string, body: string): void {
  if (Notification.isSupported()) {
    new Notification({ title, body });
  }
}

function runBackup(): void {
  try {
    const userData = app.getPath("userData");
    const dbPath = path.join(userData, "sentinel.db");
    const backupsDir = path.join(userData, "backups");

    if (!fs.existsSync(dbPath)) return;

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const backupPath = path.join(backupsDir, `sentinel-${timestamp}.db`);
    fs.copyFileSync(dbPath, backupPath);

    const cutoff = Date.now() - 30 * 24 * 60 * 60 * 1000;
    for (const file of fs.readdirSync(backupsDir)) {
      if (!file.startsWith("sentinel-")) continue;
      const filePath = path.join(backupsDir, file);
      try {
        if (fs.statSync(filePath).mtimeMs < cutoff) {
          fs.unlinkSync(filePath);
        }
      } catch { /* skip */ }
    }
  } catch (err) {
    console.error("[backup] Failed:", err);
  }
}

// ── App lifecycle ─────────────────────────────────────────────────────────

app.whenReady().then(async () => {
  ensureDirectories();
  registerIpcHandlers();

  // ── Startup orchestration via StartupManager ──
  //  1. Creates window with splash screen
  //  2. Launches backend with retries
  //  3. Loads React frontend only when backend is healthy
  //  4. If backend never becomes healthy: shows error screen, exits
  await startup.start();

  // If startup failed, the manager already quit — don't continue
  if (startup.phase === "error" || startup.phase === "shutdown") {
    return;
  }

  // ── Post-startup (only reached if backend is running) ──

  const mainWindow = getMainWindow();
  if (!mainWindow || mainWindow.isDestroyed()) return;

  createTray(mainWindow);

  mainWindow.on("close", (event) => {
    if (!appAny.isQuitting) {
      if (app.isPackaged) {
        // In production, close = quit (clean shutdown)
        appAny.isQuitting = true;
        app.quit();
      } else {
        // In dev, minimize to tray
        event.preventDefault();
        mainWindow.hide();
        showNativeNotification(
          "Sentinel is still running",
          "The app has been minimized to the system tray. Use the tray icon to reopen."
        );
      }
    }
  });

  backupInterval = setInterval(runBackup, 6 * 60 * 60 * 1000);
  runBackup();

  if (app.isPackaged) {
    const autoUpdate = secureStore.get<string>("autoUpdate");
    if (autoUpdate !== "false") {
      setTimeout(() => checkForUpdates(), 5000);
    }
  }

  app.on("activate", () => {
    const existing = getMainWindow();
    if (existing && !existing.isDestroyed()) {
      existing.show();
      existing.focus();
    } else {
      // Window was destroyed — re-create it with a fresh frontend load
      const win = createMainWindow();
      loadFrontend(win);
      createTray(win);
    }
  });
});

// When a second instance is launched (e.g., user double-clicks EXE again),
// focus the existing main window instead of creating a duplicate.
app.on("second-instance", () => {
  const existing = getMainWindow();
  if (existing && !existing.isDestroyed()) {
    if (existing.isMinimized()) existing.restore();
    existing.show();
    existing.focus();
  }
});

app.on("before-quit", () => {
  startup.shutdown();
  if (backupInterval) clearInterval(backupInterval);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

// ── IPC handlers ──────────────────────────────────────────────────────────

ipcMain.on("file:open-recent", (_event, filePath: string) => {
  const validated = validateFilePath(filePath);
  if (!validated) return;
  const win = getMainWindow();
  if (win) {
    win.webContents.send("file:open-recent", validated);
  }
});

function registerIpcHandlers(): void {
  // ── Validation wrapper ──
  function validate(channel: string, args: unknown[]): boolean {
    const ok = validateIPC(channel, args);
    if (!ok) {
      console.warn(`[security] Blocked IPC call to "${channel}" with args:`, args);
    }
    return ok;
  }

  ipcMain.handle("backend:status", () => {
    if (!validate("backend:status", [])) return null;
    return startup.getBackendState();
  });

  ipcMain.handle("backend:restart", async () => {
    if (!validate("backend:restart", [])) return;
    // Kill and re-start the backend — startup.start() handles the full
    // lifecycle: splash → backend retry → frontend load
    startup.shutdown();
    await startup.start();
  });

  ipcMain.handle("app:getPath", (_event, name: string) => {
    if (!validate("app:getPath", [name])) return null;
    if (!ALLOWED_APP_PATHS.has(name)) return null;
    return app.getPath(name as Parameters<typeof app.getPath>[0]);
  });

  ipcMain.handle("app:getVersion", () => {
    return app.getVersion();
  });

  ipcMain.on("app:quit", () => {
    appAny.isQuitting = true;
    app.quit();
  });

  ipcMain.handle("file:open", async (_event, options) => {
    if (!validate("file:open", [options])) return null;
    const win = getMainWindow();
    if (!win) return null;
    const result = await dialog.showOpenDialog(win, {
      properties: ["openFile", "multiSelections"],
      filters: options?.filters,
    });
    if (result.canceled) return null;
    for (const p of result.filePaths) addRecentFile(p);
    return result.filePaths;
  });

  ipcMain.handle("file:save", async (_event, options) => {
    if (!validate("file:save", [options])) return null;
    const win = getMainWindow();
    if (!win) return null;
    const result = await dialog.showSaveDialog(win, {
      defaultPath: options?.defaultPath,
      filters: options?.filters,
    });
    if (result.canceled) return null;
    return result.filePath;
  });

  ipcMain.handle("file:read", async (_event, filePath: string) => {
    if (!validate("file:read", [filePath])) return null;
    const validated = validateFilePath(filePath);
    if (!validated) return null;
    addRecentFile(validated);
    return fs.readFileSync(validated, "utf-8");
  });

  ipcMain.handle("file:write", async (_event, filePath: string, data: string) => {
    if (!validate("file:write", [filePath, data])) return;
    const validated = validateFilePath(filePath);
    if (!validated) return;
    const userData = app.getPath("userData");
    if (!validated.startsWith(userData)) return;
    fs.writeFileSync(validated, data, "utf-8");
  });

  ipcMain.handle("file:openFolder", async (_event, options) => {
    if (!validate("file:openFolder", [options])) return null;
    const win = getMainWindow();
    if (!win) return null;
    const result = await dialog.showOpenDialog(win, {
      properties: ["openDirectory"],
    });
    if (result.canceled) return null;
    return result.filePaths[0] ?? null;
  });

  ipcMain.handle("file:openInExplorer", async (_event, itemPath: string) => {
    if (!validate("file:openInExplorer", [itemPath])) return;
    const validated = validateFilePath(itemPath);
    if (!validated) return;
    if (!fs.existsSync(validated)) {
      fs.mkdirSync(validated, { recursive: true });
    }
    await shell.openPath(validated);
  });

  ipcMain.handle("file:readBuffer", async (_event, filePath: string) => {
    if (!validate("file:readBuffer", [filePath])) return null;
    const validated = validateFilePath(filePath);
    if (!validated) return null;
    addRecentFile(validated);
    const buffer = fs.readFileSync(validated);
    return buffer.toString("base64");
  });

  ipcMain.handle("file:getStats", async (_event, filePath: string) => {
    if (!validate("file:getStats", [filePath])) return null;
    const validated = validateFilePath(filePath);
    if (!validated) return null;
    const stats = fs.statSync(validated);
    return {
      size: stats.size,
      name: path.basename(validated),
      ext: path.extname(validated),
    };
  });

  ipcMain.handle("notify:show", (_event, title: string, body: string) => {
    if (!validate("notify:show", [title, body])) return;
    showNativeNotification(sanitizeString(title), sanitizeString(body));
  });

  ipcMain.handle("recent:list", () => {
    return getRecentFiles();
  });

  ipcMain.handle("recent:add", (_event, filePath: string) => {
    if (!validate("recent:add", [filePath])) return;
    const validated = validateFilePath(filePath);
    if (validated) addRecentFile(validated);
  });

  ipcMain.handle("backup:run", () => {
    runBackup();
    return { success: true };
  });

  ipcMain.handle("backup:status", () => {
    const backupsDir = path.join(app.getPath("userData"), "backups");
    try {
      const files = fs.readdirSync(backupsDir)
        .filter((f) => f.startsWith("sentinel-"))
        .map((f) => {
          const stat = fs.statSync(path.join(backupsDir, f));
          return { name: f, size: stat.size, date: stat.mtime.toISOString() };
        })
        .sort((a, b) => b.date.localeCompare(a.date));
      return { total: files.length, latest: files[0] || null, backups: files.slice(0, 10) };
    } catch {
      return { total: 0, latest: null, backups: [] };
    }
  });

  ipcMain.on("window:minimize", () => {
    getMainWindow()?.minimize();
  });

  ipcMain.on("window:maximize", () => {
    const win = getMainWindow();
    if (win?.isMaximized()) {
      win.unmaximize();
    } else {
      win?.maximize();
    }
  });

  ipcMain.on("window:close", () => {
    getMainWindow()?.close();
  });

  ipcMain.handle("window:isMaximized", () => {
    return getMainWindow()?.isMaximized() ?? false;
  });

  // ── Secure encrypted storage (replaces electron-store) ──

  ipcMain.handle("storage:get", (_event, key: string) => {
    if (!validateStorageKey(key)) return undefined;
    return secureStore.get(key);
  });

  ipcMain.handle("storage:set", (_event, key: string, value: unknown) => {
    if (!validateStorageKey(key)) return;
    secureStore.set(key, value);
  });

  ipcMain.handle("storage:delete", (_event, key: string) => {
    if (!validateStorageKey(key)) return;
    secureStore.delete(key);
  });

  ipcMain.handle("settings:getAll", () => {
    return secureStore.getAll();
  });

  ipcMain.handle("settings:setAll", (_event, values: Record<string, unknown>) => {
    if (!validate("settings:setAll", [values])) return;
    secureStore.setAll(values);
  });

  // ── Update IPC handlers ──

  ipcMain.handle("update:check", () => {
    checkForUpdates();
  });

  ipcMain.handle("update:download", () => {
    downloadUpdate();
  });

  ipcMain.handle("update:install", () => {
    installUpdate();
  });

  ipcMain.handle("update:status", () => {
    return getStatus();
  });

  ipcMain.handle("update:onStatusChange", (_event) => {
    const unsubscribe = onStatusChange((status) => {
      const win = getMainWindow();
      if (win && !win.isDestroyed()) {
        win.webContents.send("update:status", status);
      }
    });
    _event.sender.on("destroyed", unsubscribe);
  });
}
