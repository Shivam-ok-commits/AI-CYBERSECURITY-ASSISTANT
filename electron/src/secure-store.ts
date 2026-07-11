import * as crypto from "crypto";
import * as path from "path";
import * as fs from "fs";
import { app } from "electron";

const ALGORITHM = "aes-256-gcm";
const KEY_LENGTH = 32;
const IV_LENGTH = 16;
const TAG_LENGTH = 16;
const SALT_LENGTH = 32;

const SENSITIVE_KEYS = new Set([
  "openaiApiKey",
  "geminiApiKey",
  "anthropicApiKey",
  "virustotalApiKey",
  "abuseipdbApiKey",
  "otxApiKey",
  "nvdApiKey",
]);

export class SecureStore {
  private storePath: string;
  private encryptionKey: Buffer;
  private cache: Map<string, unknown> = new Map();
  private dirty: boolean = false;

  constructor() {
    const userData = app.getPath("userData");
    const storageDir = path.join(userData, "storage");
    fs.mkdirSync(storageDir, { recursive: true });
    this.storePath = path.join(storageDir, "sentinel-settings.json");

    // Derive encryption key from machine-specific data
    const machineId = this.getMachineId();
    this.encryptionKey = crypto.scryptSync(machineId, "sentinel-v2-salt", KEY_LENGTH);
  }

  get<T>(key: string): T | undefined {
    return this.cache.get(key) as T | undefined;
  }

  set(key: string, value: unknown): void {
    this.cache.set(key, value);
    this.dirty = true;
    this.flush();
  }

  delete(key: string): void {
    this.cache.delete(key);
    this.dirty = true;
    this.flush();
  }

  getAll(): Record<string, unknown> {
    const result: Record<string, unknown> = {};
    for (const [key, value] of this.cache) {
      result[key] = value;
    }
    return result;
  }

  setAll(values: Record<string, unknown>): void {
    for (const [key, value] of Object.entries(values)) {
      this.cache.set(key, value);
    }
    this.dirty = true;
    this.flush();
  }

  load(): void {
    try {
      if (!fs.existsSync(this.storePath)) return;
      const encrypted = fs.readFileSync(this.storePath);
      if (encrypted.length === 0) return;

      const salt = encrypted.subarray(0, SALT_LENGTH);
      const iv = encrypted.subarray(SALT_LENGTH, SALT_LENGTH + IV_LENGTH);
      const tag = encrypted.subarray(
        encrypted.length - TAG_LENGTH,
        encrypted.length,
      );
      const ciphertext = encrypted.subarray(
        SALT_LENGTH + IV_LENGTH,
        encrypted.length - TAG_LENGTH,
      );

      const key = crypto.scryptSync(
        this.getMachineId(),
        salt.toString("hex"),
        KEY_LENGTH,
      );

      const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
      decipher.setAuthTag(tag);
      let decrypted = decipher.update(ciphertext);
      decrypted = Buffer.concat([decrypted, decipher.final()]);

      const raw = JSON.parse(decrypted.toString("utf-8"));
      this.cache = new Map(Object.entries(raw));
      this.dirty = false;
    } catch {
      // If decryption fails, start fresh
      this.cache = new Map();
      this.dirty = false;
    }
  }

  private flush(): void {
    if (!this.dirty) return;
    try {
      const raw = JSON.stringify(Object.fromEntries(this.cache));
      const salt = crypto.randomBytes(SALT_LENGTH);
      const iv = crypto.randomBytes(IV_LENGTH);
      const key = crypto.scryptSync(this.getMachineId(), salt.toString("hex"), KEY_LENGTH);

      const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
      let encrypted = cipher.update(Buffer.from(raw, "utf-8"));
      encrypted = Buffer.concat([encrypted, cipher.final()]);

      const output = Buffer.concat([salt, iv, encrypted, cipher.getAuthTag()]);
      fs.writeFileSync(this.storePath, output, { mode: 0o600 });
      this.dirty = false;
    } catch (err) {
      console.error("[secure-store] Failed to flush:", err);
    }
  }

  private getMachineId(): string {
    try {
      const os = require("os");
      // Use machine ID + app path as entropy source
      const parts = [
        os.hostname(),
        os.platform(),
        os.arch(),
        app.getPath("userData"),
      ];
      return parts.join("::");
    } catch {
      return app.getPath("userData");
    }
  }
}

// Singleton
let _instance: SecureStore | null = null;

export function getSecureStore(): SecureStore {
  if (!_instance) {
    _instance = new SecureStore();
    _instance.load();
  }
  return _instance;
}
