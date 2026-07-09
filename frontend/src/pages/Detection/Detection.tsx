import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listRules, createRule, deleteRule, testRule,
  listSigmaRules, createSigmaRule,
  listYaraRules, createYaraRule,
  listHunts, createHunt, executeHunt, getHuntResults, getAnalytics,
} from "../../api/detection";
import { Radar, Plus, Trash2, Play, TestTube, BarChart3, Shield, Search, AlertTriangle } from "lucide-react";
import { useToast } from "../../components/Toast";
import { ConfirmDialog } from "../../components/ConfirmDialog";

export default function Detection() {
  const [tab, setTab] = useState<"rules" | "sigma" | "yara" | "hunting" | "analytics">("rules");
  const [showCreateRule, setShowCreateRule] = useState(false);
  const [newRule, setNewRule] = useState({ name: "", category: "general", rule_type: "custom", content: "", severity: "medium" });
  const [testData, setTestData] = useState("");
  const [testRuleId, setTestRuleId] = useState<number | null>(null);
  const [newHunt, setNewHunt] = useState({ name: "", hunt_type: "log", query: "" });
  const [newSigma, setNewSigma] = useState({ title: "", description: "", log_source: "", detection: "{}" });
  const [newYara, setNewYara] = useState({ name: "", description: "", rule_text: "" });
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: rules } = useQuery({ queryKey: ["rules", { limit: 100 }], queryFn: () => listRules({ limit: "100" }) });
  const { data: sigmaRules } = useQuery({ queryKey: ["sigma-rules"], queryFn: listSigmaRules });
  const { data: yaraRules } = useQuery({ queryKey: ["yara-rules"], queryFn: listYaraRules });
  const { data: hunts } = useQuery({ queryKey: ["hunts"], queryFn: listHunts });
  const { data: huntResults } = useQuery({ queryKey: ["hunt-results"], queryFn: getHuntResults });
  const { data: analytics } = useQuery({ queryKey: ["detection-analytics"], queryFn: getAnalytics });

  const createRuleMutation = useMutation({
    mutationFn: () => createRule(newRule as unknown as Record<string, unknown>),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["rules"] }); setShowCreateRule(false); },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (id: number) => deleteRule(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["rules"] }); toast("success", "Rule deleted"); setDeleteTarget(null); },
    onError: () => toast("error", "Failed to delete rule"),
  });

  const testRuleMutation = useMutation({
    mutationFn: () => testRule(testRuleId!, testData.split("\n").filter(Boolean)),
    onSuccess: (data) => toast(data.matched ? "success" : "info", data.matched ? "Rule matched!" : "No match found"),
    onError: () => toast("error", "Test failed"),
  });

  const createHuntMutation = useMutation({
    mutationFn: () => createHunt(newHunt as unknown as Record<string, unknown>),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["hunts"] }); setNewHunt({ name: "", hunt_type: "log", query: "" }); toast("success", "Hunt created"); },
    onError: () => toast("error", "Failed to create hunt"),
  });

  const executeHuntMutation = useMutation({
    mutationFn: (id: number) => executeHunt(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["hunt-results"] }); toast("success", "Hunt executed"); },
    onError: () => toast("error", "Hunt execution failed"),
  });

  const createSigmaMutation = useMutation({
    mutationFn: () => createSigmaRule(newSigma as unknown as Record<string, unknown>),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["sigma-rules"] }); setNewSigma({ title: "", description: "", log_source: "", detection: "{}" }); toast("success", "Sigma rule created"); },
    onError: () => toast("error", "Failed to create Sigma rule"),
  });

  const createYaraMutation = useMutation({
    mutationFn: () => createYaraRule(newYara as unknown as Record<string, unknown>),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["yara-rules"] }); setNewYara({ name: "", description: "", rule_text: "" }); toast("success", "YARA rule created"); },
    onError: () => toast("error", "Failed to create YARA rule"),
  });

  const tabs = [
    { key: "rules", label: "Rules", icon: Shield },
    { key: "sigma", label: "Sigma", icon: Search },
    { key: "yara", label: "YARA", icon: AlertTriangle },
    { key: "hunting", label: "Hunting", icon: Radar },
    { key: "analytics", label: "Analytics", icon: BarChart3 },
  ] as const;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Detection & Threat Hunting</h1>

      <div className="flex gap-2 border-b border-gray-800 pb-2">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
              tab === t.key ? "bg-cyan-600/20 text-cyan-400 border border-cyan-600/30" : "text-gray-400 hover:text-white hover:bg-gray-800"
            }`}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {tab === "rules" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={() => setShowCreateRule(!showCreateRule)}
              className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg text-sm transition-colors">
              <Plus size={18} /> New Rule
            </button>
          </div>

          {showCreateRule && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-3">Create Rule</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <input type="text" value={newRule.name} onChange={(e) => setNewRule({ ...newRule, name: e.target.value })} placeholder="Name"
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500" />
                <select value={newRule.category} onChange={(e) => setNewRule({ ...newRule, category: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500">
                  <option value="general">General</option>
                  <option value="malware">Malware</option>
                  <option value="phishing">Phishing</option>
                  <option value="brute_force">Brute Force</option>
                  <option value="web_attack">Web Attack</option>
                  <option value="lateral_movement">Lateral Movement</option>
                  <option value="persistence">Persistence</option>
                  <option value="execution">Execution</option>
                  <option value="credential_access">Credential Access</option>
                  <option value="exfiltration">Exfiltration</option>
                  <option value="insider_threat">Insider Threat</option>
                  <option value="custom">Custom</option>
                </select>
                <select value={newRule.rule_type} onChange={(e) => setNewRule({ ...newRule, rule_type: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500">
                  <option value="custom">Custom</option>
                  <option value="sigma">Sigma</option>
                  <option value="yara">YARA</option>
                </select>
                <select value={newRule.severity} onChange={(e) => setNewRule({ ...newRule, severity: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <textarea value={newRule.content} onChange={(e) => setNewRule({ ...newRule, content: e.target.value })} rows={2} placeholder="Rule content (regex, YARA, or Sigma)"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:border-cyan-500 mb-3" />
              <button onClick={() => createRuleMutation.mutate()} disabled={!newRule.name || !newRule.content}
                className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">Create</button>
            </div>
          )}

          <ConfirmDialog
            open={deleteTarget !== null}
            title="Delete Rule"
            message="Are you sure you want to delete this detection rule? This action cannot be undone."
            onConfirm={() => deleteRuleMutation.mutate(deleteTarget!)}
            onCancel={() => setDeleteTarget(null)}
          />
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500 text-left">
                  <th className="p-3">Name</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Severity</th>
                  <th className="p-3">Hits</th>
                  <th className="p-3">Test</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {rules?.map((r: { id: number; name: string; rule_type: string; category: string; severity: string; hit_count?: number }) => (
                  <tr key={r.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                    <td className="p-3 text-white">{r.name}</td>
                    <td className="p-3 text-gray-400 capitalize">{r.rule_type}</td>
                    <td className="p-3 text-gray-400 capitalize">{r.category}</td>
                    <td className="p-3 capitalize">{r.severity}</td>
                    <td className="p-3 text-gray-400">{r.hit_count ?? 0}</td>
                    <td className="p-3">
                      <button onClick={() => { setTestRuleId(r.id); setTestData(""); }}
                        className="text-cyan-400 hover:text-cyan-300"><TestTube size={16} /></button>
                      {testRuleId === r.id && (
                        <div className="flex gap-1 mt-1">
                          <input type="text" value={testData} onChange={(e) => setTestData(e.target.value)} placeholder="Sample data"
                            className="w-24 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white" />
                          <button onClick={() => testRuleMutation.mutate()}
                            className="bg-cyan-600 text-white px-2 py-1 rounded text-xs">Go</button>
                        </div>
                      )}
                      {testRuleMutation.data && testRuleId === r.id && (
                        <span className="text-xs ml-1">{testRuleMutation.data.matched ? "✅" : "❌"}</span>
                      )}
                    </td>
                    <td className="p-3">
                      <button onClick={() => setDeleteTarget(r.id)}
                        className="text-red-400 hover:text-red-300"><Trash2 size={16} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "sigma" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">Create Sigma Rule</h2>
            <div className="space-y-2">
              <input type="text" value={newSigma.title} onChange={(e) => setNewSigma({ ...newSigma, title: e.target.value })} placeholder="Title"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm" />
              <input type="text" value={newSigma.description} onChange={(e) => setNewSigma({ ...newSigma, description: e.target.value })} placeholder="Description"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm" />
              <input type="text" value={newSigma.log_source} onChange={(e) => setNewSigma({ ...newSigma, log_source: e.target.value })} placeholder="Log Source"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm" />
              <textarea value={newSigma.detection} onChange={(e) => setNewSigma({ ...newSigma, detection: e.target.value })} rows={4} placeholder="Detection (JSON)"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm" />
              <button onClick={() => createSigmaMutation.mutate()} disabled={!newSigma.title}
                className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm">Create</button>
            </div>
          </div>
          <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">Sigma Rules</h2>
            {sigmaRules?.map((r: { id: number; title: string; log_source: string; level: string }) => (
              <div key={r.id} className="bg-gray-800 rounded-lg p-3 mb-2 text-sm flex items-center justify-between">
                <div><span className="text-white">{r.title}</span><span className="text-gray-500 ml-2">{r.log_source}</span></div>
                <span className="text-xs capitalize">{r.level}</span>
              </div>
            )) ?? <p className="text-gray-500 text-sm">No Sigma rules</p>}
          </div>
        </div>
      )}

      {tab === "yara" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">Create YARA Rule</h2>
            <div className="space-y-2">
              <input type="text" value={newYara.name} onChange={(e) => setNewYara({ ...newYara, name: e.target.value })} placeholder="Name"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm" />
              <input type="text" value={newYara.description} onChange={(e) => setNewYara({ ...newYara, description: e.target.value })} placeholder="Description"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm" />
              <textarea value={newYara.rule_text} onChange={(e) => setNewYara({ ...newYara, rule_text: e.target.value })} rows={6} placeholder="rule malicious { strings: $a = \/evil\/ condition: $a }"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm font-mono" />
              <button onClick={() => createYaraMutation.mutate()} disabled={!newYara.name}
                className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm">Create</button>
            </div>
          </div>
          <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">YARA Rules</h2>
            {yaraRules?.map((r: { id: number; name: string; description: string }) => (
              <div key={r.id} className="bg-gray-800 rounded-lg p-3 mb-2 text-sm">
                <span className="text-white font-medium">{r.name}</span>
                <p className="text-gray-500 text-xs mt-1">{r.description}</p>
              </div>
            )) ?? <p className="text-gray-500 text-sm">No YARA rules</p>}
          </div>
        </div>
      )}

      {tab === "hunting" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">New Hunt</h2>
            <div className="space-y-2">
              <input type="text" value={newHunt.name} onChange={(e) => setNewHunt({ ...newHunt, name: e.target.value })} placeholder="Hunt name"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm" />
              <select value={newHunt.hunt_type} onChange={(e) => setNewHunt({ ...newHunt, hunt_type: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm">
                <option value="log">Log</option>
                <option value="ioc">IOC</option>
                <option value="process">Process</option>
                <option value="network">Network</option>
                <option value="user">User</option>
                <option value="custom">Custom</option>
              </select>
              <textarea value={newHunt.query} onChange={(e) => setNewHunt({ ...newHunt, query: e.target.value })} rows={3} placeholder="Query / filters"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm" />
              <button onClick={() => createHuntMutation.mutate()} disabled={!newHunt.name}
                className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm">Create Hunt</button>
            </div>
          </div>
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">Saved Hunts</h2>
              {hunts?.map((h: { id: number; name: string; hunt_type: string; created_at: string }) => (
                <div key={h.id} className="bg-gray-800 rounded-lg p-3 mb-2 text-sm flex items-center justify-between">
                  <div>
                    <span className="text-white font-medium">{h.name}</span>
                    <span className="text-gray-500 ml-2 capitalize">{h.hunt_type}</span>
                    <span className="text-gray-600 ml-2 text-xs">{new Date(h.created_at).toLocaleString()}</span>
                  </div>
                  <button onClick={() => executeHuntMutation.mutate(h.id)}
                    className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300">
                    <Play size={14} /> Run
                  </button>
                </div>
              )) ?? <p className="text-gray-500 text-sm">No saved hunts</p>}
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">Hunt Results</h2>
              {huntResults?.map((r: { id: number; hunt_type: string; match_type: string; match_value: string; severity: string; created_at: string }) => (
                <div key={r.id} className="bg-gray-800 rounded-lg p-3 mb-2 text-sm flex items-center justify-between">
                  <div>
                    <span className="text-white">{r.match_value}</span>
                    <span className="text-gray-500 ml-2 capitalize">{r.match_type} · {r.hunt_type}</span>
                  </div>
                  <span className={`text-xs capitalize ${r.severity === "critical" || r.severity === "high" ? "text-red-400" : r.severity === "medium" ? "text-yellow-400" : "text-green-400"}`}>{r.severity}</span>
                </div>
              )) ?? <p className="text-gray-500 text-sm">No results yet</p>}
            </div>
          </div>
        </div>
      )}

      {tab === "analytics" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-center">
            <p className="text-sm text-gray-400">Total Rules</p>
            <p className="text-3xl font-bold text-white">{analytics?.total_rules ?? 0}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-center">
            <p className="text-sm text-gray-400">Enabled</p>
            <p className="text-3xl font-bold text-green-400">{analytics?.enabled_rules ?? 0}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-center">
            <p className="text-sm text-gray-400">Total Hits</p>
            <p className="text-3xl font-bold text-white">{analytics?.total_hits ?? 0}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-center">
            <p className="text-sm text-gray-400">FP Rate</p>
            <p className="text-3xl font-bold text-yellow-400">{analytics?.false_positive_rate ?? "0%"} </p>
          </div>
        </div>
      )}
    </div>
  );
}
