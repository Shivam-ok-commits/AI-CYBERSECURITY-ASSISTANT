import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from "../context/AuthContext";
import { setupMfa, enableMfa, disableMfa } from "../api/auth";
import { useToast } from "../components/Toast";
import { useElectron, type UpdateStatus } from "../hooks/useElectron";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Tabs } from "../components/ui/Tabs";
import { listProviders, type AIProviderInfo } from "../api/ai";
import {
  Sun, Moon, Cpu, Database, HardDrive, RefreshCw, Shield,
  Globe, Network, Key, Smartphone, CheckCircle, XCircle,
  Save, FolderOpen, Server,
} from "lucide-react";

type SettingsData = Record<string, string>;

const SETTINGS_KEYS = [
  "theme",
  "aiProvider",
  "openaiApiKey",
  "geminiApiKey",
  "anthropicApiKey",
  "ollamaBaseUrl",
  "ollamaModel",
  "lmstudioBaseUrl",
  "lmstudioModel",
  "backendPort",
  "logLevel",
  "autoUpdate",
  "virustotalApiKey",
  "abuseipdbApiKey",
  "otxApiKey",
  "nvdApiKey",
];

export default function Settings() {
  const { user, token } = useAuth();
  const { toast } = useToast();
  const { isElectron, api, runBackup, getBackupStatus } = useElectron();
  const [activeTab, setActiveTab] = useState("general");
  const [settings, setSettings] = useState<SettingsData>({});
  const [loading, setLoading] = useState(true);
  const [backupInfo, setBackupInfo] = useState<{ total: number; latest: { name: string; size: number; date: string } | null } | null>(null);

  // MFA state
  const [mfaStep, setMfaStep] = useState<"idle" | "setup" | "verify">("idle");
  const [mfaCode, setMfaCode] = useState("");
  const [qrCode, setQrCode] = useState("");
  const [mfaSecret, setMfaSecret] = useState("");

  useEffect(() => {
    loadSettings();
    loadBackupStatus();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    const loaded: SettingsData = {};
    if (isElectron && api) {
      for (const key of SETTINGS_KEYS) {
        const val = await api.storage.get(key) as string | undefined;
        if (val !== undefined) loaded[key] = val;
      }
    }
    // Defaults
    if (!loaded.theme) loaded.theme = "dark";
    if (!loaded.aiProvider) loaded.aiProvider = "openai";
    if (!loaded.ollamaBaseUrl) loaded.ollamaBaseUrl = "http://localhost:11434";
    if (!loaded.ollamaModel) loaded.ollamaModel = "llama3.2";
    if (!loaded.lmstudioBaseUrl) loaded.lmstudioBaseUrl = "http://localhost:1234";
    if (!loaded.lmstudioModel) loaded.lmstudioModel = "local-model";
    if (!loaded.backendPort) loaded.backendPort = "8000";
    if (!loaded.logLevel) loaded.logLevel = "info";
    if (!loaded.autoUpdate) loaded.autoUpdate = "true";
    setSettings(loaded);
    setLoading(false);
  };

  const loadBackupStatus = async () => {
    if (!isElectron) return;
    const status = await getBackupStatus();
    if (status) setBackupInfo(status);
  };

  const updateSetting = (key: string, value: string) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    if (isElectron && api) {
      api.storage.set(key, value);
    }
  };

  // MFA handlers
  const setupMfaMutation = useMutation({
    mutationFn: setupMfa,
    onSuccess: (data) => { setQrCode(data.qr_code); setMfaSecret(data.secret); setMfaStep("setup"); },
    onError: () => toast("error", "Failed to setup MFA"),
  });

  const enableMfaMutation = useMutation({
    mutationFn: () => enableMfa(mfaCode),
    onSuccess: () => { setMfaStep("idle"); setMfaCode(""); toast("success", "MFA enabled"); },
    onError: () => toast("error", "Invalid code"),
  });

  const disableMfaMutation = useMutation({
    mutationFn: disableMfa,
    onSuccess: () => { toast("success", "MFA disabled"); },
    onError: () => toast("error", "Failed to disable MFA"),
  });

  const isMfaEnabled = user?.mfa_enabled === true;

  if (!token) return null;

  const tabs = [
    { id: "general", label: "General", icon: <Cpu size={14} /> },
    { id: "storage", label: "Storage", icon: <HardDrive size={14} /> },
    { id: "integrations", label: "Integrations", icon: <Globe size={14} /> },
    { id: "network", label: "Network", icon: <Network size={14} /> },
    { id: "security", label: "Security", icon: <Shield size={14} /> },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">Settings</h1>
        <p className="text-sm text-text-secondary mt-1">Configure Sentinel desktop and integrations</p>
      </div>

      <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

      {loading ? (
        <div className="text-center py-12 text-sm text-text-muted">Loading settings...</div>
      ) : (
        <div className="space-y-6">
          {activeTab === "general" && <GeneralSection settings={settings} onUpdate={updateSetting} isElectron={isElectron} />}
          {activeTab === "storage" && (
            <StorageSection
              isElectron={isElectron}
              api={api}
              backupInfo={backupInfo}
              onBackup={async () => { await runBackup(); toast("success", "Backup created"); loadBackupStatus(); }}
              onRefresh={loadBackupStatus}
            />
          )}
          {activeTab === "integrations" && <IntegrationsSection settings={settings} onUpdate={updateSetting} />}
          {activeTab === "network" && <NetworkSection settings={settings} onUpdate={updateSetting} />}
          {activeTab === "security" && (
            <SecuritySection
              isMfaEnabled={isMfaEnabled}
              mfaStep={mfaStep}
              mfaCode={mfaCode}
              qrCode={qrCode}
              mfaSecret={mfaSecret}
              onMfaCodeChange={setMfaCode}
              onSetupMfa={() => setupMfaMutation.mutate()}
              onEnableMfa={() => enableMfaMutation.mutate()}
              onDisableMfa={() => disableMfaMutation.mutate()}
              setupPending={setupMfaMutation.isPending}
              enablePending={enableMfaMutation.isPending}
              disablePending={disableMfaMutation.isPending}
              user={user}
            />
          )}
        </div>
      )}
    </div>
  );
}

const PROVIDER_OPTIONS: { value: string; label: string; description: string }[] = [
  { value: "openai", label: "OpenAI", description: "GPT-4o-mini (requires API key)" },
  { value: "gemini", label: "Gemini", description: "Gemini 2.0 Flash (requires API key)" },
  { value: "anthropic", label: "Anthropic", description: "Claude Sonnet 4 (requires API key)" },
  { value: "ollama", label: "Ollama", description: "Local LLM (no API key needed)" },
  { value: "lmstudio", label: "LM Studio", description: "Local LLM (no API key needed)" },
];

const PROVIDER_API_KEYS: Record<string, { key: string; label: string; type: string; placeholder: string }[]> = {
  openai: [{ key: "openaiApiKey", label: "API Key", type: "password", placeholder: "sk-..." }],
  gemini: [{ key: "geminiApiKey", label: "API Key", type: "password", placeholder: "AIza..." }],
  anthropic: [{ key: "anthropicApiKey", label: "API Key", type: "password", placeholder: "sk-ant-..." }],
  ollama: [
    { key: "ollamaBaseUrl", label: "Base URL", type: "text", placeholder: "http://localhost:11434" },
    { key: "ollamaModel", label: "Model", type: "text", placeholder: "llama3.2" },
  ],
  lmstudio: [
    { key: "lmstudioBaseUrl", label: "Base URL", type: "text", placeholder: "http://localhost:1234" },
    { key: "lmstudioModel", label: "Model", type: "text", placeholder: "local-model" },
  ],
};

function GeneralSection({ settings, onUpdate, isElectron }: { settings: SettingsData; onUpdate: (k: string, v: string) => void; isElectron: boolean }) {
  const { data: providers } = useQuery({ queryKey: ["ai-providers"], queryFn: listProviders, retry: false, enabled: isElectron });
  const { checkForUpdates, downloadUpdate, installUpdate, getUpdateStatus, onUpdateStatusChange } = useElectron();
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null);
  const [updateChecking, setUpdateChecking] = useState(false);
  const activeProvider = settings.aiProvider || "openai";

  useEffect(() => {
    if (!isElectron) return;
    getUpdateStatus().then(setUpdateStatus);
    const unsub = onUpdateStatusChange(setUpdateStatus);
    return unsub;
  }, [isElectron]);

  const getProviderStatus = (name: string): "available" | "unavailable" | "unknown" => {
    if (!providers) return "unknown";
    const p = providers.find((p: AIProviderInfo) => p.name === name);
    if (!p) return "unknown";
    return p.available ? "available" : "unavailable";
  };

  const handleCheckForUpdates = async () => {
    setUpdateChecking(true);
    await checkForUpdates();
    setUpdateChecking(false);
  };

  const renderUpdateStatus = () => {
    if (!updateStatus || updateStatus.type === "idle") return null;
    switch (updateStatus.type) {
      case "checking":
        return <p className="text-xs text-text-muted">Checking for updates...</p>;
      case "available":
        return (
          <div className="flex items-center gap-3">
            <p className="text-xs text-text-primary">Version {updateStatus.info.version} available</p>
            <Button variant="primary" size="sm" onClick={downloadUpdate}>Download</Button>
          </div>
        );
      case "downloading":
        return (
          <div className="space-y-1">
            <p className="text-xs text-text-muted">Downloading... {updateStatus.percent}%</p>
            <div className="w-full bg-surface-secondary rounded-full h-1.5">
              <div className="bg-primary h-1.5 rounded-full transition-all" style={{ width: `${updateStatus.percent}%` }} />
            </div>
          </div>
        );
      case "downloaded":
        return (
          <div className="flex items-center gap-3">
            <p className="text-xs text-text-primary">Update ready (v{updateStatus.info.version})</p>
            <Button variant="primary" size="sm" onClick={installUpdate}>Restart & Install</Button>
          </div>
        );
      case "not-available":
        return <p className="text-xs text-text-muted">You're on the latest version</p>;
      case "error":
        return <p className="text-xs text-danger">Update check failed: {updateStatus.message}</p>;
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Sun size={16} className="text-primary" /> Appearance</h2>
        <div className="flex gap-3">
          {[
            { value: "dark", label: "Dark", icon: <Moon size={16} /> },
            { value: "light", label: "Light", icon: <Sun size={16} /> },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => onUpdate("theme", opt.value)}
              className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm border transition-colors ${
                settings.theme === opt.value
                  ? "bg-primary/10 border-primary text-primary"
                  : "bg-surface-secondary border-border text-text-secondary hover:border-primary/50"
              }`}
            >
              {opt.icon} {opt.label}
            </button>
          ))}
        </div>
      </Card>

      {isElectron && (
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Cpu size={16} className="text-primary" /> AI Provider</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-2">
              {PROVIDER_OPTIONS.map((opt) => {
                const status = getProviderStatus(opt.value);
                const isActive = activeProvider === opt.value;
                return (
                  <button
                    key={opt.value}
                    onClick={() => onUpdate("aiProvider", opt.value)}
                    className={`flex items-start gap-3 p-3 rounded-lg text-sm border transition-colors text-left ${
                      isActive
                        ? "bg-primary/10 border-primary"
                        : "bg-surface-secondary border-border hover:border-primary/50"
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-text-primary">{opt.label}</span>
                        {status === "available" && <CheckCircle size={14} className="text-success shrink-0" />}
                        {status === "unavailable" && <XCircle size={14} className="text-danger shrink-0" />}
                      </div>
                      <p className="text-xs text-text-muted mt-0.5">{opt.description}</p>
                    </div>
                    {isActive && (
                      <Badge variant="info">Active</Badge>
                    )}
                  </button>
                );
              })}
            </div>

            {PROVIDER_API_KEYS[activeProvider]?.map((field) => (
              <Input
                key={field.key}
                label={field.label}
                type={field.type as "text" | "password"}
                placeholder={field.placeholder}
                value={settings[field.key] || ""}
                onChange={(e) => onUpdate(field.key, e.target.value)}
              />
            ))}
            <p className="text-xs text-text-muted">Requires backend restart to take effect.</p>
          </div>
        </Card>
      )}

      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><RefreshCw size={16} className="text-primary" /> Updates</h2>
        <div className="space-y-3">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.autoUpdate === "true"}
              onChange={(e) => onUpdate("autoUpdate", e.target.checked ? "true" : "false")}
              className="rounded border-border bg-surface-secondary text-primary focus:ring-primary"
            />
            <span className="text-sm text-text-primary">Check for updates automatically</span>
          </label>
          {isElectron && (
            <div className="space-y-2">
              <Button
                variant="secondary"
                size="sm"
                icon={<RefreshCw size={14} />}
                onClick={handleCheckForUpdates}
                loading={updateChecking}
              >
                Check for Updates
              </Button>
              {renderUpdateStatus()}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function StorageSection({
  isElectron, api, backupInfo, onBackup, onRefresh,
}: {
  isElectron: boolean; api: ReturnType<typeof useElectron>["api"] | undefined;
  backupInfo: { total: number; latest: { name: string; size: number; date: string } | null } | null;
  onBackup: () => void; onRefresh: () => void;
}) {
  const [userDataPath, setUserDataPath] = useState("");

  useEffect(() => {
    if (isElectron && api) {
      api.app.getPath("userData").then(setUserDataPath);
    }
  }, [isElectron, api]);

  return (
    <div className="space-y-4">
      {isElectron && (
        <Card>
          <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><FolderOpen size={16} className="text-primary" /> Storage Location</h2>
          <p className="text-xs text-text-muted mb-2">All Sentinel data is stored at:</p>
          <code className="block bg-surface-secondary rounded-lg px-3 py-2 text-xs text-text-primary font-mono break-all">
            {userDataPath || "Loading..."}
          </code>
          {userDataPath && (
            <Button variant="secondary" size="sm" icon={<FolderOpen size={14} />} className="mt-3" onClick={() => api?.file.openInExplorer(userDataPath)}>
              Open Data Folder
            </Button>
          )}
        </Card>
      )}

      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Database size={16} className="text-primary" /> Database Backups</h2>
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm text-text-primary">Total backups: {backupInfo?.total ?? 0}</p>
            {backupInfo?.latest && (
              <p className="text-xs text-text-muted mt-1">
                Latest: {new Date(backupInfo.latest.date).toLocaleString()} ({(backupInfo.latest.size / 1024).toFixed(0)} KB)
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" icon={<RefreshCw size={14} />} onClick={onRefresh} />
            <Button variant="primary" size="sm" icon={<Save size={14} />} onClick={onBackup}>
              Backup Now
            </Button>
          </div>
        </div>
        <p className="text-xs text-text-muted">Automatic backups run every 6 hours. Backups older than 30 days are cleaned up.</p>
      </Card>
    </div>
  );
}

function IntegrationsSection({ settings, onUpdate }: { settings: SettingsData; onUpdate: (k: string, v: string) => void }) {
  const apiKeys = [
    { key: "virustotalApiKey", label: "VirusTotal API Key", placeholder: "Enter your API key" },
    { key: "abuseipdbApiKey", label: "AbuseIPDB API Key", placeholder: "Enter your API key" },
    { key: "otxApiKey", label: "OTX (AlienVault) API Key", placeholder: "Enter your API key" },
    { key: "nvdApiKey", label: "NVD API Key", placeholder: "Enter your API key" },
  ];

  return (
    <Card>
      <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Key size={16} className="text-primary" /> API Keys</h2>
      <div className="space-y-4">
        {apiKeys.map(({ key, label, placeholder }) => (
          <Input
            key={key}
            label={label}
            type="password"
            placeholder={placeholder}
            value={settings[key] || ""}
            onChange={(e) => onUpdate(key, e.target.value)}
          />
        ))}
        <p className="text-xs text-text-muted">API keys are stored locally and passed to the backend on startup. Requires restart to apply.</p>
      </div>
    </Card>
  );
}

function NetworkSection({ settings, onUpdate }: { settings: SettingsData; onUpdate: (k: string, v: string) => void }) {
  const { isElectron } = useElectron();

  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Server size={16} className="text-primary" /> Backend Server</h2>
        <div className="space-y-3">
          <Input
            label="Port"
            type="number"
            placeholder="8000"
            value={settings.backendPort || "8000"}
            onChange={(e) => onUpdate("backendPort", e.target.value)}
            disabled={!isElectron}
            helperText={isElectron ? "Change requires restart" : "Only configurable in desktop mode"}
          />
        </div>
      </Card>

      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Network size={16} className="text-primary" /> Proxy</h2>
        <div className="space-y-3">
          <Input label="HTTP Proxy" placeholder="http://proxy:8080" value="" onChange={() => {}} helperText="Coming soon" />
          <Input label="HTTPS Proxy" placeholder="https://proxy:8080" value="" onChange={() => {}} helperText="Coming soon" />
        </div>
      </Card>
    </div>
  );
}

function SecuritySection({
  isMfaEnabled, mfaStep, mfaCode, qrCode, mfaSecret,
  onMfaCodeChange, onSetupMfa, onEnableMfa, onDisableMfa,
  setupPending, enablePending, disablePending, user,
}: {
  isMfaEnabled: boolean; mfaStep: string; mfaCode: string; qrCode: string; mfaSecret: string;
  onMfaCodeChange: (v: string) => void; onSetupMfa: () => void; onEnableMfa: () => void; onDisableMfa: () => void;
  setupPending: boolean; enablePending: boolean; disablePending: boolean;
  user: { username?: string; role?: string; email?: string } | null;
}) {
  return (
    <div className="space-y-4">
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isMfaEnabled ? "bg-success/10" : "bg-surface-secondary"}`}>
              <Smartphone size={20} className={isMfaEnabled ? "text-success" : "text-text-muted"} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">Two-Factor Authentication</h2>
              <p className="text-xs text-text-muted">Protect your account with TOTP</p>
            </div>
          </div>
          <Badge variant={isMfaEnabled ? "success" : "default"} dot>
            {isMfaEnabled ? "Enabled" : "Disabled"}
          </Badge>
        </div>

        {isMfaEnabled ? (
          <Button variant="danger" size="sm" onClick={onDisableMfa} loading={disablePending}>
            Disable MFA
          </Button>
        ) : mfaStep === "idle" ? (
          <Button variant="primary" size="sm" onClick={onSetupMfa} loading={setupPending}>
            Setup MFA
          </Button>
        ) : (
          <div className="space-y-4">
            <div className="bg-surface-secondary rounded-lg p-4 text-center">
              {qrCode && <img src={qrCode} alt="QR Code" className="mx-auto mb-3 w-40 h-40" />}
              <p className="text-xs text-text-muted mb-1">Scan with Google Authenticator or any TOTP app</p>
              {mfaSecret && (
                <div className="bg-background rounded p-2">
                  <p className="text-xs text-text-muted mb-1">Or enter this key manually:</p>
                  <code className="text-primary text-sm font-mono select-all">{mfaSecret}</code>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="text" value={mfaCode} onChange={(e) => onMfaCodeChange(e.target.value.replace(/\D/g, "").slice(0, 6))}
                className="flex-1 bg-surface-secondary border border-border rounded-lg px-4 py-2 text-center text-lg tracking-widest text-text-primary placeholder-text-muted focus:outline-none focus:border-primary"
                placeholder="000000" maxLength={6}
              />
              <Button variant="primary" size="md" onClick={onEnableMfa} disabled={mfaCode.length < 6} loading={enablePending}>
                Enable
              </Button>
            </div>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="text-sm font-semibold text-text-primary mb-4">Account</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-muted">Username</span>
            <span className="text-text-primary">{user?.username}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Email</span>
            <span className="text-text-primary">{user?.email || "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Role</span>
            <span className="text-text-primary capitalize">{user?.role}</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
