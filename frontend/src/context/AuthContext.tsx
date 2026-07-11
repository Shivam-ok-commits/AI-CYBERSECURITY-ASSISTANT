import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { login as apiLogin, getProfile } from "../api/auth";

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  mfa_enabled?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

/**
 * Attempt to restore a saved session by validating the stored JWT.
 * If the token is missing or invalid, returns null (does NOT auto-login
 * with default credentials — that's a user action).
 */
async function tryRestoreSession(): Promise<{ user: User; token: string } | null> {
  const saved = localStorage.getItem("token");
  if (!saved) return null;
  try {
    const profile = await getProfile();
    return { user: profile, token: saved };
  } catch {
    // Token invalid or expired — silently discard
    localStorage.removeItem("token");
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Restore session on mount (backend is guaranteed healthy by StartupManager)
  useEffect(() => {
    (async () => {
      try {
        const restored = await tryRestoreSession();
        if (restored) {
          setUser(restored.user);
          setToken(restored.token);
        }
      } catch {
        // Network or server error — leave user as null
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setError(null);
    try {
      const res = await apiLogin({ username, password });
      localStorage.setItem("token", res.access_token);
      setToken(res.access_token);
      const profile = await getProfile();
      setUser(profile);
    } catch (err: any) {
      const message = err?.response?.data?.detail || err?.message || "Login failed";
      setError(message);
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    setError(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
