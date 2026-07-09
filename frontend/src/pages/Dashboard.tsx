import { useQuery } from "@tanstack/react-query";
import { getFullDashboard } from "../api/dashboard";
import { getAnalytics } from "../api/detection";
import { Shield, FileText, Search, AlertTriangle, Activity, Radar } from "lucide-react";

function StatCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: string | number; color: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-3">
        <div className={`p-3 rounded-lg ${color}`}><Icon size={24} className="text-white" /></div>
        <div>
          <p className="text-sm text-gray-400">{label}</p>
          <p className="text-2xl font-bold text-white">{value ?? "—"}</p>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: dashboard } = useQuery({ queryKey: ["dashboard"], queryFn: getFullDashboard });
  const { data: analytics } = useQuery({ queryKey: ["analytics"], queryFn: getAnalytics });

  const exec = (dashboard as Record<string, unknown>)?.executive as Record<string, unknown> | undefined;
  const logStats = (dashboard as Record<string, unknown>)?.log_stats as Record<string, unknown> | undefined;

  const totalAnalyses = logStats?.total_events ?? 0;
  const totalIocs = exec?.total_iocs ?? 0;
  const alerts = exec?.critical_alerts ?? 0;
  const totalRules = (analytics as Record<string, unknown>)?.total_rules ?? 0;
  const recentActivity = logStats?.recent_activity as Array<Record<string, string>> | undefined;
  const byCategory = (analytics as Record<string, unknown>)?.by_category as Record<string, number> | undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Security Dashboard</h1>
        <span className="text-sm text-gray-500">{new Date().toLocaleString()}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard icon={FileText} label="Total Events" value={totalAnalyses as number} color="bg-blue-600" />
        <StatCard icon={Search} label="IOCs Found" value={totalIocs as number} color="bg-purple-600" />
        <StatCard icon={AlertTriangle} label="Critical Alerts" value={alerts as number} color="bg-red-600" />
        <StatCard icon={Activity} label="System Health" value={exec?.security_health as string || "OK"} color="bg-green-600" />
        <StatCard icon={Radar} label="Detection Rules" value={totalRules as number} color="bg-cyan-600" />
        <StatCard icon={Shield} label="Status" value="Online" color="bg-emerald-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Activity</h2>
          {recentActivity && recentActivity.length > 0 ? (
            <ul className="space-y-3">
              {recentActivity.slice(0, 8).map((a, i: number) => (
                <li key={i} className="flex items-center justify-between text-sm border-b border-gray-800 pb-2">
                  <span className="text-gray-300">{a.action}</span>
                  <span className="text-gray-500 text-xs">{a.timestamp ? new Date(a.timestamp).toLocaleString() : ""}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-sm">No recent activity</p>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Detection Rules by Category</h2>
          {byCategory ? (
            <div className="space-y-3">
              {Object.entries(byCategory).map(([cat, count]) => (
                <div key={cat} className="flex items-center justify-between text-sm">
                  <span className="text-gray-300 capitalize">{cat}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${Math.min(Number(count) / (Number(totalRules) || 1) * 100, 100)}%` }} />
                    </div>
                    <span className="text-gray-400 w-6 text-right">{count as number}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No rules configured</p>
          )}
        </div>
      </div>
    </div>
  );
}
