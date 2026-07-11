import { API_BASE_URL } from "../api/config";

export type UpdateStatus =
  | { type: "idle" }
  | { type: "checking" }
  | { type: "available"; info: { version: string; releaseDate?: string; releaseNotes?: string } }
  | { type: "not-available"; info: { version: string } }
  | { type: "downloading"; percent: number; bytesPerSecond: number; total: number }
  | { type: "downloaded"; info: { version: string } }
  | { type: "error"; message: string };

interface ElectronAPI {
  platform: string;
  isElectron: boolean;
  versions: { electron: string; node: string; chrome: string };
  app: {
    getPath: (name: string) => Promise<string>;
    getVersion: () => Promise<string>;
    quit: () => void;
  };
  backend: {
    status: () => Promise<{ status: string; port: number; pid?: number; error?: string }>;
    restart: () => Promise<void>;
    onStatusChange: (cb: (state: unknown) => void) => () => void;
  };
  file: {
    open: (options?: { filters?: { name: string; extensions: string[] }[] }) => Promise<string[] | null>;
    save: (options?: { defaultPath?: string; filters?: { name: string; extensions: string[] }[] }) => Promise<string | null>;
    openFolder: () => Promise<string | null>;
    openInExplorer: (itemPath: string) => Promise<void>;
    read: (filePath: string) => Promise<string>;
    readBuffer: (filePath: string) => Promise<string>;
    write: (filePath: string, data: string) => Promise<void>;
    getStats: (filePath: string) => Promise<{ size: number; name: string; ext: string }>;
  };
  window: {
    minimize: () => void;
    maximize: () => void;
    close: () => void;
    isMaximized: () => Promise<boolean>;
    onMaximize: (cb: () => void) => () => void;
    onUnmaximize: (cb: () => void) => () => void;
  };
  storage: {
    get: (key: string) => Promise<unknown>;
    set: (key: string, value: unknown) => Promise<void>;
    delete: (key: string) => Promise<void>;
  };
  notifications: {
    show: (title: string, body: string) => Promise<void>;
  };
  recent: {
    list: () => Promise<string[]>;
    add: (filePath: string) => Promise<void>;
  };
  backup: {
    run: () => Promise<{ success: boolean }>;
    status: () => Promise<{ total: number; latest: { name: string; size: number; date: string } | null; backups: unknown[] }>;
  };
  update: {
    check: () => Promise<void>;
    download: () => Promise<void>;
    install: () => Promise<void>;
    getStatus: () => Promise<UpdateStatus>;
    onStatusChange: (cb: (status: UpdateStatus) => void) => () => void;
  };
}

declare global {
  interface Window {
    sentinel?: ElectronAPI;
  }
}

export function useElectron() {
  const api = typeof window !== "undefined" ? window.sentinel : undefined;
  const isElectron = !!api;

  async function uploadFileViaBackend(filePath: string): Promise<void> {
    if (!api) throw new Error("Not in Electron");

    const stats = await api.file.getStats(filePath);
    const base64 = await api.file.readBuffer(filePath);

    const response = await fetch(`${API_BASE_URL}/logs/upload`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${localStorage.getItem("token") || ""}` },
      body: (() => {
        const fd = new FormData();
        const byteChars = atob(base64);
        const bytes = new Uint8Array(byteChars.length);
        for (let i = 0; i < byteChars.length; i++) bytes[i] = byteChars.charCodeAt(i);
        const blob = new Blob([bytes], { type: "application/octet-stream" });
        fd.append("file", blob, stats.name);
        return fd;
      })(),
    });

    if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`);
  }

  async function openFileDialog(filters?: { name: string; extensions: string[] }[]) {
    if (!api) return null;
    return api.file.open({ filters });
  }

  async function openFolderDialog() {
    if (!api) return null;
    return api.file.openFolder();
  }

  function openInExplorer(itemPath: string) {
    if (!api) return;
    api.file.openInExplorer(itemPath);
  }

  function showNativeNotification(title: string, body: string) {
    if (!api) return;
    api.notifications.show(title, body);
  }

  async function getRecentFiles() {
    if (!api) return [];
    return api.recent.list();
  }

  async function runBackup() {
    if (!api) return;
    return api.backup.run();
  }

  async function getBackupStatus() {
    if (!api) return null;
    return api.backup.status();
  }

  async function checkForUpdates() {
    if (!api) return;
    return api.update.check();
  }

  async function downloadUpdate() {
    if (!api) return;
    return api.update.download();
  }

  async function installUpdate() {
    if (!api) return;
    return api.update.install();
  }

  async function getUpdateStatus(): Promise<UpdateStatus | null> {
    if (!api) return null;
    return api.update.getStatus();
  }

  function onUpdateStatusChange(cb: (status: UpdateStatus) => void): () => void {
    if (!api) return () => {};
    return api.update.onStatusChange(cb);
  }

  return {
    isElectron,
    api,
    uploadFileViaBackend,
    openFileDialog,
    openFolderDialog,
    openInExplorer,
    showNativeNotification,
    getRecentFiles,
    runBackup,
    getBackupStatus,
    checkForUpdates,
    downloadUpdate,
    installUpdate,
    getUpdateStatus,
    onUpdateStatusChange,
  };
}
