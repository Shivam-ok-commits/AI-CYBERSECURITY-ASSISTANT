import { useState, useEffect } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { loginMfa, oauthCallback, getOAuthUrl } from "../api/auth";
import { Shield, Eye, EyeOff, Globe } from "lucide-react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [needsMfa, setNeedsMfa] = useState(false);
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const code = searchParams.get("code");
    const provider = searchParams.get("provider") || localStorage.getItem("oauth_provider");
    if (code && provider) {
      setLoading(true);
      oauthCallback(provider, code, `${window.location.origin}/login`)
        .then((res) => {
          localStorage.removeItem("oauth_provider");
          loginWithToken(res.access_token);
        })
        .catch(() => setError("OAuth login failed"))
        .finally(() => setLoading(false));
    }
  }, [searchParams]);

  const loginWithToken = async (token: string) => {
    localStorage.setItem("token", token);
    window.location.href = "/dashboard";
  };

  const handleOAuth = async (provider: string) => {
    try {
      localStorage.setItem("oauth_provider", provider);
      const data = await getOAuthUrl(provider, `${window.location.origin}/login`);
      window.location.href = data.authorization_url;
    } catch {
      setError(`${provider} OAuth is not configured`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (needsMfa) {
        await loginMfa({ username, password, mfa_code: mfaCode });
      } else {
        await login(username, password);
      }
      navigate("/dashboard");
    } catch (err: unknown) {
      const resp = (err as { response?: { status?: number } })?.response;
      if (resp?.status === 403) {
        setNeedsMfa(true);
        setError("Enter your MFA code");
      } else {
        setError("Invalid username or password");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(6,182,212,0.08),transparent_50%),radial-gradient(ellipse_at_bottom_left,_rgba(168,85,247,0.08),transparent_50%)]" />

      <div className="w-full max-w-md relative">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/25">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Cybersecurity</h1>
            <p className="text-sm text-gray-500">Assistant Platform</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-gray-900/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-800 shadow-2xl space-y-5">
          <div>
            <h2 className="text-xl font-semibold text-white">Welcome back</h2>
            <p className="text-sm text-gray-500 mt-1">{needsMfa ? "Enter your MFA code" : "Sign in to your account"}</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Username</label>
            <input
              type="text" value={username} onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
              placeholder="Enter your username" required autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Password</label>
            <div className="relative">
              <input
                type={showPwd ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-3 pr-10 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
                placeholder="Enter your password" required
              />
              <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {needsMfa && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1.5">MFA Code</label>
              <input type="text" value={mfaCode} onChange={(e) => setMfaCode(e.target.value)}
                className="w-full bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-3 text-white text-center text-lg tracking-widest placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
                placeholder="000000" maxLength={6} required autoFocus />
            </div>
          )}

          <button type="submit" disabled={loading || !username || !password || (needsMfa && mfaCode.length < 6)}
            className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-medium py-3 rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
          >
            {loading && <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
            {loading ? "Signing in..." : needsMfa ? "Verify" : "Sign In"}
          </button>

          {!needsMfa && (
            <>
              <div className="relative">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-800" /></div>
                <div className="relative flex justify-center text-xs"><span className="bg-gray-900 px-2 text-gray-500">or continue with</span></div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {[
                  { provider: "google", label: "Google" },
                  { provider: "github", label: "GitHub" },
                  { provider: "microsoft", label: "Microsoft" },
                ].map(({ provider, label }) => (
                  <button key={provider} type="button" onClick={() => handleOAuth(provider)}
                    className="flex items-center justify-center gap-2 bg-gray-800/80 border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white px-4 py-2.5 rounded-xl text-sm transition-colors">
                    <Globe size={18} /> {label}
                  </button>
                ))}
              </div>
            </>
          )}

          <p className="text-center text-sm text-gray-500">
            Don't have an account?{" "}
            <Link to="/register" className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors">Create one</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
