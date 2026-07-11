import * as path from "path";
import * as fs from "fs";

/**
 * Allowed IPC channels and their parameter schemas.
 */
const IPC_SCHEMAS: Record<string, { params: string[]; returnType?: string }> = {
  "app:getPath": { params: ["string"] },
  "app:getVersion": { params: [] },
  "app:quit": { params: [] },
  "backend:status": { params: [] },
  "backend:restart": { params: [] },
  "file:open": { params: ["object|undefined"] },
  "file:save": { params: ["object|undefined"] },
  "file:openFolder": { params: [] },
  "file:openInExplorer": { params: ["string"] },
  "file:read": { params: ["string"] },
  "file:write": { params: ["string", "string"] },
  "file:readBuffer": { params: ["string"] },
  "file:getStats": { params: ["string"] },
  "file:open-recent": { params: ["string"] },
  "window:minimize": { params: [] },
  "window:maximize": { params: [] },
  "window:close": { params: [] },
  "window:isMaximized": { params: [] },
  "storage:get": { params: ["string"] },
  "storage:set": { params: ["string", "any"] },
  "storage:delete": { params: ["string"] },
  "settings:getAll": { params: [] },
  "settings:setAll": { params: ["object"] },
  "notify:show": { params: ["string", "string"] },
  "recent:list": { params: [] },
  "recent:add": { params: ["string"] },
  "backup:run": { params: [] },
  "backup:status": { params: [] },
  "update:check": { params: [] },
  "update:download": { params: [] },
  "update:install": { params: [] },
  "update:status": { params: [] },
  "update:onStatusChange": { params: [] },
};

/**
 * Validate an IPC channel exists and params match expected types.
 */
export function validateIPC(channel: string, args: unknown[]): boolean {
  const schema = IPC_SCHEMAS[channel];
  if (!schema) {
    console.warn(`[ipc-validator] Unknown channel: ${channel}`);
    return false;
  }

  if (args.length < schema.params.length) {
    console.warn(`[ipc-validator] Channel "${channel}": expected ${schema.params.length} args, got ${args.length}`);
    return false;
  }

  for (let i = 0; i < schema.params.length; i++) {
    const expected = schema.params[i];
    const actual = args[i];

    if (!typeMatches(expected, actual)) {
      console.warn(`[ipc-validator] Channel "${channel}" arg[${i}]: expected ${expected}, got ${typeof actual}`);
      return false;
    }
  }

  return true;
}

function typeMatches(expected: string, actual: unknown): boolean {
  if (expected === "any") return true;
  if (expected === "object|undefined") return actual === undefined || typeof actual === "object";
  if (expected === "object") return typeof actual === "object" && actual !== null && !Array.isArray(actual);
  if (expected === "string") return typeof actual === "string";
  if (expected === "number") return typeof actual === "number";
  if (expected === "boolean") return typeof actual === "boolean";
  if (expected === "array") return Array.isArray(actual);
  return false;
}

/**
 * Validate a file path to prevent path traversal outside userData.
 */
export function validateFilePath(filePath: string): string | null {
  if (typeof filePath !== "string" || !filePath) {
    return null;
  }

  // Normalize and resolve to absolute
  const normalized = path.normalize(filePath);
  const resolved = path.resolve(normalized);

  // Reject null bytes
  if (resolved.includes("\0")) return null;

  // Check for path traversal patterns
  if (resolved.includes("..")) {
    const { app } = require("electron");
    const userData = app.getPath("userData");
    if (!resolved.startsWith(userData)) {
      return null;
    }
  }

  // Only allow alphanumeric, dots, dashes, underscores, slashes, colons
  if (!/^[a-zA-Z0-9_\-./:\\@() ]+$/.test(resolved)) {
    return null;
  }

  return resolved;
}

/**
 * Sanitize a string to prevent injection attacks.
 */
export function sanitizeString(input: string): string {
  if (typeof input !== "string") return "";
  // Strip control characters and null bytes
  return input.replace(/[\x00-\x1f\x7f-\x9f]/g, "").trim();
}

/**
 * Validate storage key (only allow alphanumeric + underscore).
 */
export function validateStorageKey(key: string): boolean {
  return typeof key === "string" && /^[a-zA-Z0-9_]+$/.test(key);
}
