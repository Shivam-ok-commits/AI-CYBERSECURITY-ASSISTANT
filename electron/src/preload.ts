import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("sentinel", {
  platform: process.platform,
  isElectron: true,

  versions: {
    electron: process.versions.electron,
    node: process.versions.node,
    chrome: process.versions.chrome,
  },

  app: {
    getPath: (name: string) => ipcRenderer.invoke("app:getPath", name),
    getVersion: () => ipcRenderer.invoke("app:getVersion"),
    quit: () => ipcRenderer.send("app:quit"),
  },

  backend: {
    status: () => ipcRenderer.invoke("backend:status"),
    restart: () => ipcRenderer.invoke("backend:restart"),
    onStatusChange: (cb: (state: unknown) => void) => {
      const handler = (_event: Electron.IpcRendererEvent, state: unknown) => cb(state);
      ipcRenderer.on("backend:status-changed", handler);
      return () => ipcRenderer.removeListener("backend:status-changed", handler);
    },
  },

  file: {
    open: (options?: { filters?: { name: string; extensions: string[] }[] }) =>
      ipcRenderer.invoke("file:open", options),
    save: (options?: { defaultPath?: string; filters?: { name: string; extensions: string[] }[] }) =>
      ipcRenderer.invoke("file:save", options),
    openFolder: () => ipcRenderer.invoke("file:openFolder"),
    openInExplorer: (itemPath: string) => ipcRenderer.invoke("file:openInExplorer", itemPath),
    read: (filePath: string) => ipcRenderer.invoke("file:read", filePath),
    readBuffer: (filePath: string) => ipcRenderer.invoke("file:readBuffer", filePath),
    write: (filePath: string, data: string) => ipcRenderer.invoke("file:write", filePath, data),
    getStats: (filePath: string) => ipcRenderer.invoke("file:getStats", filePath),
  },

  window: {
    minimize: () => ipcRenderer.send("window:minimize"),
    maximize: () => ipcRenderer.send("window:maximize"),
    close: () => ipcRenderer.send("window:close"),
    isMaximized: () => ipcRenderer.invoke("window:isMaximized"),
    onMaximize: (cb: () => void) => {
      ipcRenderer.on("window:maximized", cb);
      return () => ipcRenderer.removeListener("window:maximized", cb);
    },
    onUnmaximize: (cb: () => void) => {
      ipcRenderer.on("window:unmaximized", cb);
      return () => ipcRenderer.removeListener("window:unmaximized", cb);
    },
  },

  storage: {
    get: (key: string) => ipcRenderer.invoke("storage:get", key),
    set: (key: string, value: unknown) => ipcRenderer.invoke("storage:set", key, value),
    delete: (key: string) => ipcRenderer.invoke("storage:delete", key),
  },
});
