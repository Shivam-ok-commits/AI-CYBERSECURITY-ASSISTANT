import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Shield, LayoutDashboard, FileText, Search, Bot, FolderOpen,
  Radar, LogOut, Menu, X, Settings
} from "lucide-react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/logs", label: "Log Analysis", icon: FileText },
  { to: "/threat-intel", label: "Threat Intel", icon: Search },
  { to: "/ai", label: "AI Assistant", icon: Bot },
  { to: "/cases", label: "Case Management", icon: FolderOpen },
  { to: "/detection", label: "Detection & Hunting", icon: Radar },
  { to: "/mfa", label: "Security Settings", icon: Settings },
];

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      <aside className={`${sidebarOpen ? "w-64" : "w-16"} transition-all duration-300 bg-gray-900 border-r border-gray-800 flex flex-col`}>
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-cyan-500" />
              <span className="font-bold text-sm">Cybersec AI</span>
            </div>
          )}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-gray-400 hover:text-white p-1">
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        <nav className="flex-1 py-4 space-y-1 px-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive ? "bg-cyan-600/20 text-cyan-400" : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`
              }
            >
              <item.icon size={20} />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800">
          {sidebarOpen && (
            <div className="flex items-center gap-2 mb-3">
              <div className="h-8 w-8 rounded-full bg-cyan-600 flex items-center justify-center text-xs font-bold">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <div className="text-sm">
                <div className="font-medium">{user?.username}</div>
                <div className="text-xs text-gray-500 capitalize">{user?.role}</div>
              </div>
            </div>
          )}
          <button onClick={handleLogout} className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-400 w-full px-3 py-2">
            <LogOut size={18} />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
