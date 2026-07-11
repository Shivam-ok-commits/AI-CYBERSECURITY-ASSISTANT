import { ChildProcess, spawn } from "child_process";
import * as path from "path";
import * as fs from "fs";
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

function getBackendCommand(): { command: string; args: string[]; cwd: string } {
  const ext = process.platform === "win32" ? ".exe" : "";

  // In packaged mode, look for the bundled backend executable
  if (app.isPackaged) {
    const packagedExe = path.join(process.resourcesPath!, "backend", `sentinel-backend${ext}`);
    if (fs.existsSync(packagedExe)) {
      return { command: packagedExe, args: [], cwd: app.getPath("userData") };
    }
  }

  // Development or fallback: use Python directly
  const projectRoot = getProjectRoot();
  const venvPath = path.join(projectRoot, ".venv", "Scripts", `python${ext}`);
  const python = fs.existsSync(venvPath) ? venvPath : "python";

  return {
    command: python,
    args: ["-m", "uvicorn", "src.api:app", "--host", "127.0.0.1", "--port", String(DEFAULT_PORT), "--workers", "1", "--log-level", "info"],
    cwd: projectRoot,
  };
}

export class BackendManager {
  private process: ChildProcess | null = null;
  private port: number;
  private status: BackendStatus = "stopped";
  private listeners: Set<StatusListener> = new Set();
  private shutdownTimer: ReturnType<typeof setTimeout> | null = null;
  private logStream: fs.WriteStream | null = null;

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

    // In dev mode, backend is started externally by the dev script
    if (!app.isPackaged) {
      const ok = await this.waitForHealth();
      if (ok) {
        this.setStatus("running");
        return;
      }
      this.setStatus("error", "Backend not running. Start it with: uvicorn src.api:app --reload --port 8000");
      return;
    }

    this.setStatus("starting");

    const userData = app.getPath("userData");
    const databasePath = path.join(userData, "sentinel.db");
    const uploadsDir = path.join(userData, "uploads");

    const { command, args, cwd } = getBackendCommand();

    // Read user settings from secure store
    const { getSecureStore } = require("./secure-store");
    const settings = getSecureStore().getAll();

    // In packaged mode, hide the backend console window and log to file.
    // The backend EXE is built with --noconsole (Windows GUI subsystem), but
    // `windowsHide: true` adds extra protection against flash console windows.
    // Only pass known env vars to the backend — never leak process.env
    const spawnOptions: any = {
      cwd,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
      env: {
        // Runtime essentials
        PATH: process.env.PATH || "",
        SYSTEMROOT: process.env.SYSTEMROOT || "",
        // Backend configuration
        PYTHONUNBUFFERED: "1",
        DATABASE_PATH: databasePath,
        UPLOADS_DIR: uploadsDir,
        AI_PROVIDER: (settings.aiProvider as string) || "openai",
        OPENAI_API_KEY: (settings.openaiApiKey as string) || "",
        GEMINI_API_KEY: (settings.geminiApiKey as string) || "",
        ANTHROPIC_API_KEY: (settings.anthropicApiKey as string) || "",
        OLLAMA_BASE_URL: (settings.ollamaBaseUrl as string) || "",
        OLLAMA_MODEL: (settings.ollamaModel as string) || "llama3.2",
        LMSTUDIO_BASE_URL: (settings.lmstudioBaseUrl as string) || "",
        LMSTUDIO_MODEL: (settings.lmstudioModel as string) || "local-model",
        VIRUSTOTAL_API_KEY: (settings.virustotalApiKey as string) || "",
        ABUSEIPDB_API_KEY: (settings.abuseipdbApiKey as string) || "",
        OTX_API_KEY: (settings.otxApiKey as string) || "",
        NVD_API_KEY: (settings.nvdApiKey as string) || "",
      },
    };

    this.process = spawn(command, args, spawnOptions);

    const proc = this.process;
    this.setStatus("starting");

    // Pipe backend logs to a file instead of stdout in production
    const logsDir = path.join(app.getPath("userData"), "logs");
    fs.mkdirSync(logsDir, { recursive: true });
    const logPath = path.join(logsDir, "sentinel-backend.log");
    this.logStream = fs.createWriteStream(logPath, { flags: "a" });

    this.logStream.write(`\n--- Backend started at ${new Date().toISOString()} ---\n`);

    proc.stdout?.on("data", (data: Buffer) => {
      this.logStream?.write(`[stdout] ${data}`);
    });

    proc.stderr?.on("data", (data: Buffer) => {
      this.logStream?.write(`[stderr] ${data}`);
    });

    proc.on("error", (err: Error) => {
      this.setStatus("error", err.message);
      this.process = null;
    });

    proc.on("exit", (code: number | null, signal: string | null) => {
      if (this.process === proc) {
        // Close the log stream so we don't orphan file handles on crash
        if (this.logStream) {
          this.logStream.end(`\n--- Backend exited (code=${code}, signal=${signal}) at ${new Date().toISOString()} ---\n`);
          this.logStream = null;
        }

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

    if (this.logStream) {
      this.logStream.end(`\n--- Backend stopped at ${new Date().toISOString()} ---\n`);
      this.logStream = null;
    }

    if (this.process) {
      const proc = this.process;
      this.setStatus("stopped");

      if (process.platform === "win32") {
        spawn("taskkill", ["/pid", String(proc.pid), "/f", "/t"], { windowsHide: true });
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
