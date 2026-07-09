import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { setupMfa, enableMfa, disableMfa } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { Smartphone, Key, CheckCircle2, XCircle } from "lucide-react";
import { useToast } from "../components/Toast";

export default function MfaSettings() {
  const { user, token } = useAuth();
  const { toast } = useToast();
  const [step, setStep] = useState<"idle" | "setup" | "verify">("idle");
  const [code, setCode] = useState("");
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");

  const setupMutation = useMutation({
    mutationFn: setupMfa,
    onSuccess: (data) => { setQrCode(data.qr_code); setSecret(data.secret); setStep("setup"); },
    onError: () => toast("error", "Failed to setup MFA"),
  });

  const enableMutation = useMutation({
    mutationFn: () => enableMfa(code),
    onSuccess: () => { setStep("idle"); setCode(""); toast("success", "MFA enabled"); window.location.reload(); },
    onError: () => toast("error", "Invalid code"),
  });

  const disableMutation = useMutation({
    mutationFn: disableMfa,
    onSuccess: () => { toast("success", "MFA disabled"); window.location.reload(); },
    onError: () => toast("error", "Failed to disable MFA"),
  });

  const isMfaEnabled = user?.mfa_enabled === true;

  if (!token) return null;

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Security Settings</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-lg ${isMfaEnabled ? "bg-green-600/20" : "bg-gray-800"}`}>
              <Smartphone size={24} className={isMfaEnabled ? "text-green-400" : "text-gray-400"} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Two-Factor Authentication</h2>
              <p className="text-sm text-gray-500">Protect your account with TOTP</p>
            </div>
          </div>
          {isMfaEnabled ? (
            <span className="flex items-center gap-1 text-green-400 text-sm"><CheckCircle2 size={16} /> Enabled</span>
          ) : (
            <span className="flex items-center gap-1 text-gray-500 text-sm"><XCircle size={16} /> Disabled</span>
          )}
        </div>

        {isMfaEnabled ? (
          <button onClick={() => disableMutation.mutate()} disabled={disableMutation.isPending}
            className="bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            {disableMutation.isPending ? "Disabling..." : "Disable MFA"}
          </button>
        ) : step === "idle" ? (
          <button onClick={() => setupMutation.mutate()} disabled={setupMutation.isPending}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            {setupMutation.isPending ? "Setting up..." : "Setup MFA"}
          </button>
        ) : (
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              {qrCode && <img src={qrCode} alt="QR Code" className="mx-auto mb-3 w-48 h-48" />}
              <p className="text-sm text-gray-400 mb-1">Scan with Google Authenticator or any TOTP app</p>
              {secret && (
                <div className="bg-gray-950 rounded p-2">
                  <p className="text-xs text-gray-500 mb-1">Or enter this key manually:</p>
                  <code className="text-cyan-400 text-sm font-mono select-all">{secret}</code>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1.5">Verify with 6-digit code</label>
              <div className="flex gap-2">
                <input type="text" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-center text-lg tracking-widest placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                  placeholder="000000" maxLength={6} />
                <button onClick={() => enableMutation.mutate()} disabled={code.length < 6}
                  className="bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                  Enable
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 rounded-lg bg-blue-600/20"><Key size={24} className="text-blue-400" /></div>
          <div>
            <h2 className="text-lg font-semibold text-white">Account</h2>
            <p className="text-sm text-gray-500">Manage your account details</p>
          </div>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-gray-400">Username</span><span className="text-white">{user?.username}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Role</span><span className="text-white capitalize">{user?.role}</span></div>
        </div>
      </div>
    </div>
  );
}
