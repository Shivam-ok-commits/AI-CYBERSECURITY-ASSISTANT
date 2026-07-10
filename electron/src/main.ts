import { app, ipcMain, dialog, shell, Notification, BrowserWindow } from "electron";
import * as path from "path";
import * as fs from "fs";
import { createMainWindow, getMainWindow } from "./window";
import { BackendManager } from "./backend";
import { createTray, destroyTray } from "./tray";

const store: any = new (require("electron-store"))({
  name: "sentinel-settings",
  cwd: getStoragePath(),
});

const backend = new BackendManager();
let backupInterval: ReturnType<typeof setInterval> | null = null;

// Extend App type for isQuitting flag
const appAny = app as unknown as { isQuitting?: boolean };

function getStoragePath(): string {
  const base = app.getPath("userData");
  return path.join(base, "storage");
}

function ensureDirectories(): void {
  const dirs = [
    getStoragePath(),
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
  return (store.get("recentFiles") as string[]) || [];
}

function addRecentFile(filePath: string): void {
  const files = getRecentFiles().filter((f) => f !== filePath);
  files.unshift(filePath);
  store.set("recentFiles", files.slice(0, 20));
}

function showNativeNotification(title: string, body: string): void {
  if (Notification.isSupported()) {
    new Notification({ title, body, icon: undefined });
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

    // Clean up backups older than 30 days
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

app.whenReady().then(async () => {
  ensureDirectories();
  registerIpcHandlers();

  try {
    await backend.start();
  } catch (err) {
    console.error("[main] Backend failed to start:", err);
    dialog.showErrorBox(
      "Sentinel — Backend Error",
      `The backend server failed to start.\n\n${err instanceof Error ? err.message : String(err)}\n\nMake sure Python and uvicorn are installed.`
    );
    app.quit();
    return;
  }

  const mainWindow = createMainWindow();

  createTray(mainWindow);

  // Minimize to tray instead of closing
  mainWindow.on("close", (event) => {
    if (!appAny.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      showNativeNotification(
        "Sentinel is still running",
        "The app has been minimized to the system tray. Use the tray icon to reopen."
      );
    }
  });

  // Start auto-backup (every 6 hours)
  backupInterval = setInterval(runBackup, 6 * 60 * 60 * 1000);
  runBackup();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    } else {
      mainWindow.show();
    }
  });
});

app.on("before-quit", () => {
  backend.kill();
  if (backupInterval) clearInterval(backupInterval);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

// Handle renderer -> main IPC for tray menu actions
ipcMain.on("file:open-recent", (_event, filePath: string) => {
  const win = getMainWindow();
  if (win) {
    win.webContents.send("file:open-recent", filePath);
  }
});

function registerIpcHandlers(): void {
  ipcMain.handle("backend:status", () => {
    return backend.getState();
  });

  ipcMain.handle("backend:restart", async () => {
    backend.kill();
    await backend.start();
  });

  ipcMain.handle("app:getPath", (_event, name: string) => {
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
    addRecentFile(filePath);
    return fs.readFileSync(filePath, "utf-8");
  });

  ipcMain.handle("file:write", async (_event, filePath: string, data: string) => {
    fs.writeFileSync(filePath, data, "utf-8");
  });

  ipcMain.handle("file:openFolder", async (_event, options) => {
    const win = getMainWindow();
    if (!win) return null;
    const result = await dialog.showOpenDialog(win, {
      properties: ["openDirectory"],
    });
    if (result.canceled) return null;
    return result.filePaths[0] ?? null;
  });

  ipcMain.handle("file:openInExplorer", async (_event, itemPath: string) => {
    const normalized = path.normalize(itemPath);
    if (!fs.existsSync(normalized)) {
      fs.mkdirSync(normalized, { recursive: true });
    }
    await shell.openPath(normalized);
  });

  ipcMain.handle("file:readBuffer", async (_event, filePath: string) => {
    addRecentFile(filePath);
    const buffer = fs.readFileSync(filePath);
    return buffer.toString("base64");
  });

  ipcMain.handle("file:getStats", async (_event, filePath: string) => {
    const stats = fs.statSync(filePath);
    return {
      size: stats.size,
      name: path.basename(filePath),
      ext: path.extname(filePath),
    };
  });

  ipcMain.handle("notify:show", (_event, title: string, body: string) => {
    showNativeNotification(title, body);
  });

  ipcMain.handle("recent:list", () => {
    return getRecentFiles();
  });

  ipcMain.handle("recent:add", (_event, filePath: string) => {
    addRecentFile(filePath);
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

  ipcMain.handle("storage:get", (_event, key: string) => {
    return store.get(key);
  });

  ipcMain.handle("storage:set", (_event, key: string, value: unknown) => {
    store.set(key, value);
  });

  ipcMain.handle("storage:delete", (_event, key: string) => {
    store.delete(key);
  });
}
