import { app, ipcMain, dialog, shell, BrowserWindow } from "electron";
import * as path from "path";
import * as fs from "fs";
import { createMainWindow, getMainWindow } from "./window";
import { BackendManager } from "./backend";

const store: any = new (require("electron-store"))({
  name: "sentinel-settings",
  cwd: getStoragePath(),
});

const backend = new BackendManager();

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

  createMainWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on("before-quit", () => {
  backend.kill();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
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

export { getStoragePath };
