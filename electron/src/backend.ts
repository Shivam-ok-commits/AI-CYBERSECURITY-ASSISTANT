import { ChildProcess, spawn } from "child_process";
import * as path from "path";
import * as http from "http";
import { app } from "electron";

export type BackendStatus = "starting" | "running" | "stopped" | "error";

export interface BackendState {
  status: BackendStatus;
  port: number;
  pid?: number;
  error?: string;
}

type StatusListener = (state: BackendState) => void;

const HEALTH_ENDPOINT = "/api/v1/health";
const DEFAULT_PORT = 8000;
const MAX_STARTUP_WAIT_MS = 30_000;
const HEALTH_CHECK_INTERVAL_MS = 500;

function getProjectRoot(): string {
  return path.resolve(__dirname, "../..");
}

function getPythonPath(): string {
  if (app.isPackaged) {
    return "python";
  }
  const venvPath = path.join(getProjectRoot(), ".venv", "Scripts", "python.exe");
  return venvPath;
}

export class BackendManager {
  private process: ChildProcess | null = null;
  private port: number;
  private status: BackendStatus = "stopped";
  private listeners: Set<StatusListener> = new Set();
  private shutdownTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(port: number = DEFAULT_PORT) {
    this.port = port;
  }

  onStatusChange(listener: StatusListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private emit(state: BackendState): void {
    for (const listener of this.listeners) {
      listener(state);
    }
  }

  private setStatus(status: BackendStatus, error?: string): void {
    this.status = status;
    this.emit({
      status,
      port: this.port,
      pid: this.process?.pid,
      error,
    });
  }

  async start(): Promise<void> {
    if (this.process) {
      return;
    }

    this.setStatus("starting");

    const projectRoot = getProjectRoot();
    const python = getPythonPath();
    const apiModule = "src.api";
    const args = [
      "-m", "uvicorn", apiModule,
      "--host", "127.0.0.1",
      "--port", String(this.port),
      "--workers", "2",
      "--log-level", "info",
    ];

    const userData = app.getPath("userData");
    const databasePath = path.join(userData, "sentinel.db");
    const uploadsDir = path.join(userData, "uploads");

    this.process = spawn(python, args, {
      cwd: projectRoot,
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        DATABASE_PATH: databasePath,
        UPLOADS_DIR: uploadsDir,
      },
    });

    const proc = this.process;
    this.setStatus("starting");

    proc.stdout?.on("data", (data: Buffer) => {
      const text = data.toString();
      process.stdout.write(`[backend] ${text}`);
    });

    proc.stderr?.on("data", (data: Buffer) => {
      const text = data.toString();
      process.stderr.write(`[backend:err] ${text}`);
    });

    proc.on("error", (err: Error) => {
      this.setStatus("error", err.message);
      this.process = null;
    });

    proc.on("exit", (code: number | null, signal: string | null) => {
      if (this.process === proc) {
        if (code !== 0 && this.status !== "stopped") {
          this.setStatus("error", `Process exited with code ${code ?? signal}`);
        } else {
          this.setStatus("stopped");
        }
        this.process = null;
      }
    });

    const ok = await this.waitForHealth();
    if (!ok) {
      this.kill();
      throw new Error(
        `Backend failed to start within ${MAX_STARTUP_WAIT_MS / 1000}s. ` +
        `Check that uvicorn is installed and the port ${this.port} is available.`
      );
    }

    this.setStatus("running");
  }

  private waitForHealth(): Promise<boolean> {
    return new Promise((resolve) => {
      const startTime = Date.now();

      const check = () => {
        if (this.status === "stopped") {
          resolve(false);
          return;
        }

        if (Date.now() - startTime > MAX_STARTUP_WAIT_MS) {
          resolve(false);
          return;
        }

        const req = http.get(
          `http://127.0.0.1:${this.port}${HEALTH_ENDPOINT}`,
          { timeout: 2000 },
          (res) => {
            if (res.statusCode === 200) {
              resolve(true);
            } else {
              setTimeout(check, HEALTH_CHECK_INTERVAL_MS);
            }
          }
        );

        req.on("error", () => {
          setTimeout(check, HEALTH_CHECK_INTERVAL_MS);
        });

        req.on("timeout", () => {
          req.destroy();
          setTimeout(check, HEALTH_CHECK_INTERVAL_MS);
        });
      };

      check();
    });
  }

  kill(): void {
    if (this.shutdownTimer) {
      clearTimeout(this.shutdownTimer);
      this.shutdownTimer = null;
    }

    if (this.process) {
      const proc = this.process;
      this.setStatus("stopped");

      if (process.platform === "win32") {
        spawn("taskkill", ["/pid", String(proc.pid), "/f", "/t"]);
      } else {
        proc.kill("SIGTERM");
        this.shutdownTimer = setTimeout(() => {
          try { proc.kill("SIGKILL"); } catch { /* already dead */ }
        }, 5000);
      }

      this.process = null;
    }
  }

  getState(): BackendState {
    return {
      status: this.status,
      port: this.port,
      pid: this.process?.pid,
    };
  }
}
