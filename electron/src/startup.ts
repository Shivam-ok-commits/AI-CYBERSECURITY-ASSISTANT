/**
 * StartupManager — Sentinel Application Startup Orchestration
 * ============================================================
 *
 * Responsibilities:
 *   - Create the main window with a loading splash screen
 *   - Launch the backend (FastAPI) with configurable retries
 *   - Wait for the /health endpoint before proceeding
 *   - Load the React frontend only when the backend is ready
 *   - Display meaningful error screens instead of blank windows
 *   - Never create the app window if the backend failed
 *   - Gracefully shut down all services on failure or quit
 */

import { app, dialog } from "electron";
import { BackendManager, BackendState } from "./backend";
import {
  createMainWindow,
  getMainWindow,
  loadSplash,
  loadFrontend,
  showErrorScreen,
  updateSplashStatus,
} from "./window";
import { destroyTray } from "./tray";

export type StartupPhase =
  | "initializing"
  | "starting-backend"
  | "starting-backend-retry"
  | "backend-ready"
  | "loading-frontend"
  | "ready"
  | "error"
  | "shutdown";

export interface StartupEvent {
  phase: StartupPhase;
  message: string;
  error?: string;
  attempt?: number;
  maxAttempts?: number;
}

type StartupListener = (event: StartupEvent) => void;

const MAX_STARTUP_ATTEMPTS = 3;
const RETRY_DELAY_MS = 3000;

export class StartupManager {
  private _backend: BackendManager;
  private listeners: Set<StartupListener> = new Set();
  private _phase: StartupPhase = "initializing";
  private _isShuttingDown = false;

  constructor() {
    this._backend = new BackendManager();
  }

  get phase(): StartupPhase {
    return this._phase;
  }

  /** Expose backend state for IPC handlers without breaking encapsulation. */
  getBackendState(): BackendState {
    return this._backend.getState();
  }

  onStatusChange(listener: StartupListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private emit(event: StartupEvent): void {
    this._phase = event.phase;
    for (const listener of this.listeners) {
      listener(event);
    }
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /**
   * Run the full startup sequence:
   *   1. Create window with splash/loading screen
   *   2. Start backend with automatic retries
   *   3. Load the React frontend
   *   4. Show the final window
   *
   * If the backend cannot start after MAX_STARTUP_ATTEMPTS, an error screen
   * is displayed and the app exits.  The React frontend is NEVER loaded if
   * the backend is not healthy.
   */
  async start(): Promise<void> {
    this._isShuttingDown = false;

    // ── Step 1: Create window with splash ──
    this.emit({ phase: "initializing", message: "Initializing..." });

    const mainWindow = createMainWindow();
    if (!mainWindow || mainWindow.isDestroyed()) {
      this.showFatalError("Failed to create application window.");
      return;
    }

    loadSplash(mainWindow);

    // ── Step 2: Start backend with retries ──

    let lastError: string | null = null;

    for (let attempt = 1; attempt <= MAX_STARTUP_ATTEMPTS; attempt++) {
      if (this._isShuttingDown) return;

      const isRetry = attempt > 1;
      const phase: StartupPhase = isRetry
        ? "starting-backend-retry"
        : "starting-backend";

      this.emit({
        phase,
        message: isRetry
          ? `Retrying backend (attempt ${attempt}/${MAX_STARTUP_ATTEMPTS})...`
          : `Starting backend (attempt ${attempt}/${MAX_STARTUP_ATTEMPTS})...`,
        attempt,
        maxAttempts: MAX_STARTUP_ATTEMPTS,
      });

      try {
        // Update splash with current status
        updateSplashStatus(
          mainWindow,
          isRetry
            ? `Retrying backend connection (${attempt}/${MAX_STARTUP_ATTEMPTS})...`
            : `Starting backend services...`
        );

        await this._backend.start();

        // Check actual status — in dev mode, start() can return without
        // throwing even if health check failed.
        const state = this._backend.getState();
        if (state.status !== "running") {
          throw new Error(state.error || "Backend failed to become healthy");
        }

        // Backend is running!
        lastError = null;
        break;

      } catch (err) {
        lastError = err instanceof Error ? err.message : String(err);

        this.emit({
          phase: "error",
          message: `Backend failed to start`,
          error: lastError,
          attempt,
          maxAttempts: MAX_STARTUP_ATTEMPTS,
        });

        if (attempt < MAX_STARTUP_ATTEMPTS && !this._isShuttingDown) {
          // Show retry message on splash screen
          updateSplashStatus(
            mainWindow,
            `Connection failed. Retrying in ${RETRY_DELAY_MS / 1000}s...`,
            lastError
          );

          await this.sleep(RETRY_DELAY_MS);
        }
      }
    }

    // ── Step 3: Handle failure ──
    if (lastError !== null) {
      this.emit({
        phase: "error",
        message: `Backend failed after ${MAX_STARTUP_ATTEMPTS} attempts`,
        error: lastError,
        attempt: MAX_STARTUP_ATTEMPTS,
        maxAttempts: MAX_STARTUP_ATTEMPTS,
      });

      showErrorScreen(mainWindow, lastError, MAX_STARTUP_ATTEMPTS);

      // Give the user a moment to read the error, then exit
      await this.sleep(5000);
      if (!this._isShuttingDown) {
        this.shutdown();
        app.quit();
      }
      return;
    }

    // ── Step 4: Load React frontend ──
    this.emit({
      phase: "loading-frontend",
      message: "Loading application...",
    });

    loadFrontend(mainWindow);

    this.emit({ phase: "ready", message: "Sentinel is ready" });
  }

  /**
   * Gracefully shut down the backend and prepare for app exit.
   */
  shutdown(): void {
    if (this._isShuttingDown) return;
    this._isShuttingDown = true;

    this.emit({ phase: "shutdown", message: "Shutting down..." });

    this._backend.kill();
    destroyTray();
  }

  // ── Private helpers ─────────────────────────────────────────────────────

  private showFatalError(message: string): void {
    this.emit({ phase: "error", message, error: message });
    dialog.showErrorBox("Sentinel — Startup Error", message);
    this.shutdown();
    app.quit();
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
  }
}
