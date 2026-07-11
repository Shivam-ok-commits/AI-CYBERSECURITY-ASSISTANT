import { app, Tray, Menu, nativeImage, BrowserWindow } from "electron";
import * as path from "path";

let tray: Tray | null = null;

function createTrayIcon(): Electron.NativeImage {
  const size = 32;
  const canvas = Buffer.alloc(size * size * 4, 0);

  // Simple shield shape: blue square with lighter border
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (y * size + x) * 4;
      const center = Math.abs(x - size / 2) < 8 && Math.abs(y - size / 2) < 10;
      if (center) {
        canvas[idx] = 37;     // R
        canvas[idx + 1] = 99; // G
        canvas[idx + 2] = 235;// B
        canvas[idx + 3] = 255;// A
      } else if (Math.abs(x - size / 2) < 12 && Math.abs(y - size / 2) < 14) {
        canvas[idx] = 30;
        canvas[idx + 1] = 64;
        canvas[idx + 2] = 128;
        canvas[idx + 3] = 40;
      }
    }
  }

  const img = nativeImage.createFromBuffer(canvas, { width: size, height: size } as Electron.CreateFromBufferOptions);
  return img.resize({ width: 16, height: 16 });
}

function getRecentFiles(): string[] {
  try {
    const { getSecureStore } = require("./secure-store");
    return (getSecureStore().get("recentFiles") as string[]) || [];
  } catch {
    return [];
  }
}

export function createTray(mainWindow: BrowserWindow): Tray {
  const icon = createTrayIcon();
  tray = new Tray(icon);

  tray.setToolTip("Sentinel — Security Operations Center");

  const updateMenu = () => {
    const recentFiles = getRecentFiles();
    const recentMenu = recentFiles.slice(0, 10).map((f: string) => ({
      label: path.basename(f),
      click: () => {
        mainWindow.show();
        mainWindow.webContents.send("file:open-recent", f);
      },
    }));

    const contextMenu = Menu.buildFromTemplate([
      {
        label: "Show Sentinel",
        click: () => {
          mainWindow.show();
          mainWindow.focus();
        },
      },
      {
        label: "Hide",
        click: () => mainWindow.hide(),
      },
      { type: "separator" },
      {
        label: "Recent Files",
        submenu: recentFiles.length > 0 ? recentMenu : [{ label: "No recent files", enabled: false }],
      },
      { type: "separator" },
      {
        label: "Quit",
        click: () => {
          (app as unknown as { isQuitting?: boolean }).isQuitting = true;
          app.quit();
        },
      },
    ]);

    tray?.setContextMenu(contextMenu);
  };

  tray.on("click", () => {
    if (mainWindow.isVisible()) {
      mainWindow.focus();
    } else {
      mainWindow.show();
    }
  });

  updateMenu();

  // Rebuild menu when recent files change
  const origOn = mainWindow.webContents.on.bind(mainWindow.webContents);
  mainWindow.webContents.on("ipc-message-sync", () => { });

  return tray;
}

export function destroyTray(): void {
  if (tray) {
    tray.destroy();
    tray = null;
  }
}

export function refreshTrayMenu(mainWindow: BrowserWindow): void {
  if (tray) {
    tray.destroy();
  }
  createTray(mainWindow);
}
