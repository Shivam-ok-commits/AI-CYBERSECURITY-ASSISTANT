import { useState } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Shield,
  LayoutDashboard,
  FileText,
  Search,
  Bot,
  FolderOpen,
  Radar,
  FileBarChart,
  Settings,
  Bell,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Menu,
} from "lucide-react";

interface NavGroup {
  label: string;
  items: { to: string; label: string; icon: React.ElementType }[];
}

const navGroups: NavGroup[] = [
  {
    label: "Core",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/logs", label: "Log Analysis", icon: FileText },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { to: "/threat-intel", label: "Threat Intelligence", icon: Search },
      { to: "/ai", label: "AI Copilot", icon: Bot },
    ],
  },
  {
    label: "Operations",
    items: [
      { to: "/cases", label: "Case Management", icon: FolderOpen },
      { to: "/detection", label: "Detection Rules", icon: Radar },
    ],
  },
  {
    label: "Settings",
    items: [
      { to: "/reports", label: "Reports", icon: FileBarChart },
      { to: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

const routeLabels: Record<string, string> = {
  dashboard: "Dashboard",
  logs: "Log Analysis",
  "threat-intel": "Threat Intelligence",
  ai: "AI Copilot",
  cases: "Case Management",
  detection: "Detection Rules",
  reports: "Reports",
  settings: "Settings",
  mfa: "Settings",
};

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();

  const segments = location.pathname.split("/").filter(Boolean);
  const currentLabel = routeLabels[segments[0]] || segments[0];

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {mobileOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}

      <aside
        className={`${
          sidebarOpen ? "w-60" : "w-16"
        } hidden lg:flex flex-col bg-surface border-r border-border transition-all duration-200 z-30`}
      >
        <div className="h-14 flex items-center gap-3 px-4 border-b border-border">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <Shield size={16} className="text-white" />
          </div>
          {sidebarOpen && (
            <div className="flex items-center justify-between flex-1 min-w-0">
              <span className="text-sm font-bold text-text-primary tracking-wide">Sentinel</span>
            </div>
          )}
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
          {navGroups.map((group) => (
            <div key={group.label}>
              {sidebarOpen && (
                <p className="px-3 mb-2 text-[10px] font-semibold text-text-muted uppercase tracking-widest">
                  {group.label}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150 ${
                        isActive
                          ? "bg-primary/10 text-primary"
                          : "text-text-secondary hover:text-text-primary hover:bg-surface-secondary"
                      } ${!sidebarOpen ? "justify-center px-0" : ""}`
                    }
                  >
                    <item.icon size={18} className="shrink-0" />
                    {sidebarOpen && <span>{item.label}</span>}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="p-3 border-t border-border">
          <div className="flex items-center gap-3 px-1 mb-2">
            {sidebarOpen && user && (
              <>
                <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-xs font-bold text-primary shrink-0">
                  {user.username?.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary truncate">{user.username}</p>
                  <p className="text-[11px] text-text-muted capitalize">{user.role}</p>
                </div>
              </>
            )}
          </div>
          <button
            onClick={handleLogout}
            className={`flex items-center gap-3 w-full text-sm text-text-secondary hover:text-danger transition-colors px-3 py-2 rounded-lg hover:bg-surface-secondary ${
              !sidebarOpen ? "justify-center px-0" : ""
            }`}
          >
            <LogOut size={16} />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>

        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="hidden lg:flex items-center justify-center h-8 border-t border-border text-text-muted hover:text-text-primary transition-colors"
        >
          {sidebarOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
        </button>
      </aside>

      <aside
        className={`${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } lg:hidden fixed inset-y-0 left-0 z-50 w-60 bg-surface border-r border-border transition-transform duration-200`}
      >
        <div className="h-14 flex items-center gap-3 px-4 border-b border-border">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <Shield size={16} className="text-white" />
          </div>
          <span className="text-sm font-bold text-text-primary tracking-wide">Sentinel</span>
        </div>
        <nav className="overflow-y-auto py-4 px-2 space-y-6">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="px-3 mb-2 text-[10px] font-semibold text-text-muted uppercase tracking-widest">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150 ${
                        isActive
                          ? "bg-primary/10 text-primary"
                          : "text-text-secondary hover:text-text-primary hover:bg-surface-secondary"
                      }`
                    }
                  >
                    <item.icon size={18} />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
        <div className="p-3 border-t border-border">
          <button onClick={handleLogout} className="flex items-center gap-3 text-sm text-text-secondary hover:text-danger px-3 py-2 rounded-lg hover:bg-surface-secondary w-full transition-colors">
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 flex items-center gap-4 px-4 border-b border-border bg-surface">
          <button
            onClick={() => setMobileOpen(true)}
            className="lg:hidden text-text-secondary hover:text-text-primary"
          >
            <Menu size={20} />
          </button>

          <nav className="flex items-center gap-1.5 text-xs">
            <span className="text-text-muted">Sentinel</span>
            {segments.length > 0 && (
              <>
                <span className="text-text-muted">/</span>
                <span className="text-text-primary font-medium">{currentLabel}</span>
              </>
            )}
          </nav>

          <div className="flex-1" />

          <div className="hidden sm:flex items-center">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                type="text"
                placeholder="Search... (Ctrl+K)"
                className="w-56 bg-surface-secondary border border-border rounded-lg pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-primary transition-colors"
                readOnly
              />
            </div>
          </div>

          <button className="relative text-text-secondary hover:text-text-primary transition-colors">
            <Bell size={18} />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-danger" />
          </button>

          {user && (
            <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
              {user.username?.charAt(0).toUpperCase()}
            </div>
          )}
        </header>

        <main className="flex-1 overflow-auto">
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
