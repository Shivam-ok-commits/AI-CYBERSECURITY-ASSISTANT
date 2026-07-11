import { autoUpdater, UpdateInfo } from "electron-updater";
import { BrowserWindow } from "electron";
import * as path from "path";

export type UpdateStatus =
  | { type: "idle" }
  | { type: "checking" }
  | { type: "available"; info: UpdateInfo }
  | { type: "not-available"; info: UpdateInfo }
  | { type: "downloading"; percent: number; bytesPerSecond: number; total: number }
  | { type: "downloaded"; info: UpdateInfo }
  | { type: "error"; message: string };

type StatusListener = (status: UpdateStatus) => void;

const listeners: Set<StatusListener> = new Set();
let currentStatus: UpdateStatus = { type: "idle" };

autoUpdater.autoDownload = true;
autoUpdater.autoInstallOnAppQuit = true;

autoUpdater.setFeedURL({
  provider: "github",
  owner: "sentinel",
  repo: "sentinel-desktop",
});

autoUpdater.on("checking-for-update", () => {
  setStatus({ type: "checking" });
});

autoUpdater.on("update-available", (info: UpdateInfo) => {
  setStatus({ type: "available", info });
  notifyRenderer("update:status", currentStatus);
  showNativeNotification(
    "Update Available",
    `Sentinel ${info.version} is ready to download.`
  );
});

autoUpdater.on("update-not-available", (info: UpdateInfo) => {
  setStatus({ type: "not-available", info });
  notifyRenderer("update:status", currentStatus);
});

autoUpdater.on("download-progress", (progress) => {
  setStatus({
    type: "downloading",
    percent: Math.round(progress.percent),
    bytesPerSecond: progress.bytesPerSecond,
    total: progress.total,
  });
  notifyRenderer("update:status", currentStatus);
});

autoUpdater.on("update-downloaded", (info: UpdateInfo) => {
  setStatus({ type: "downloaded", info });
  notifyRenderer("update:status", currentStatus);
  showNativeNotification(
    "Update Downloaded",
    `Sentinel ${info.version} will install on quit.`
  );
});

autoUpdater.on("error", (err: Error) => {
  setStatus({ type: "error", message: err.message });
  notifyRenderer("update:status", currentStatus);
});

function setStatus(status: UpdateStatus): void {
  currentStatus = status;
  for (const listener of listeners) {
    listener(status);
  }
}

function notifyRenderer(channel: string, data: unknown): void {
  const win = BrowserWindow.getAllWindows()[0];
  if (win && !win.isDestroyed()) {
    win.webContents.send(channel, data);
  }
}

function showNativeNotification(title: string, body: string): void {
  const { Notification } = require("electron");
  if (Notification.isSupported()) {
    new Notification({ title, body });
  }
}

export function onStatusChange(listener: StatusListener): () => void {
  listeners.add(listener);
  // Immediately send current status
  listener(currentStatus);
  return () => listeners.delete(listener);
}

export function checkForUpdates(): void {
  if (currentStatus.type === "idle" || currentStatus.type === "not-available" || currentStatus.type === "error") {
    autoUpdater.checkForUpdates().catch((err: Error) => {
      setStatus({ type: "error", message: err.message });
    });
  }
}

export function downloadUpdate(): void {
  if (currentStatus.type === "available") {
    autoUpdater.downloadUpdate().catch((err: Error) => {
      setStatus({ type: "error", message: err.message });
    });
  }
}

export function installUpdate(): void {
  if (currentStatus.type === "downloaded") {
    setImmediate(() => {
      autoUpdater.quitAndInstall(false, true);
    });
  }
}

export function getStatus(): UpdateStatus {
  return currentStatus;
}
