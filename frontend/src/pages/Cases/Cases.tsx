import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listCases, getCase, createCase, addEvidence, addComment } from "../../api/cases";
import { FolderOpen, Plus, MessageSquare, Paperclip } from "lucide-react";
import { useToast } from "../../components/Toast";

export default function Cases() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newCase, setNewCase] = useState({ title: "", description: "", severity: "medium" });
  const [newEvidence, setNewEvidence] = useState({ description: "", source: "", content: "" });
  const [newComment, setNewComment] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: cases } = useQuery({ queryKey: ["cases"], queryFn: () => listCases() });
  const { data: detail } = useQuery({ queryKey: ["case", selectedId], queryFn: () => getCase(selectedId!), enabled: !!selectedId });

  const createMutation = useMutation({
    mutationFn: () => createCase(newCase),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["cases"] }); setShowCreate(false); setNewCase({ title: "", description: "", severity: "medium" }); toast("success", "Case created"); },
    onError: () => toast("error", "Failed to create case"),
  });

  const evidenceMutation = useMutation({
    mutationFn: () => addEvidence(selectedId!, newEvidence),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["case", selectedId] }); setNewEvidence({ description: "", source: "", content: "" }); toast("success", "Evidence added"); },
    onError: () => toast("error", "Failed to add evidence"),
  });

  const commentMutation = useMutation({
    mutationFn: () => addComment(selectedId!, { content: newComment }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["case", selectedId] }); setNewComment(""); toast("success", "Comment added"); },
    onError: () => toast("error", "Failed to add comment"),
  });

  const severityColor = (s: string) => s === "critical" || s === "high" ? "text-red-400" : s === "medium" ? "text-yellow-400" : "text-green-400";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Case Management</h1>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg text-sm transition-colors">
          <Plus size={18} /> New Case
        </button>
      </div>

      {showCreate && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Create Case</h2>
          <div className="space-y-3">
            <input type="text" value={newCase.title} onChange={(e) => setNewCase({ ...newCase, title: e.target.value })} placeholder="Title"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500" />
            <textarea value={newCase.description} onChange={(e) => setNewCase({ ...newCase, description: e.target.value })} rows={2} placeholder="Description"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:border-cyan-500" />
            <select value={newCase.severity} onChange={(e) => setNewCase({ ...newCase, severity: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500">
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
            <button onClick={() => createMutation.mutate()} disabled={!newCase.title}
              className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">Create</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">Cases</h2>
          <div className="space-y-2 max-h-[70vh] overflow-y-auto">
            {cases?.map((c: { id: number; title: string; severity: string; status: string; created_at: string }) => (
              <button key={c.id} onClick={() => setSelectedId(c.id)}
                className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${selectedId === c.id ? "bg-cyan-600/20 border border-cyan-600/30" : "bg-gray-800/50 border border-gray-800 hover:bg-gray-800"}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white font-medium truncate">{c.title}</span>
                  <span className={`text-xs font-medium capitalize ${severityColor(c.severity)}`}>{c.severity}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="capitalize">{c.status}</span>
                  <span>·</span>
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {detail ? (
            <>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white">{detail.title}</h2>
                  <span className={`text-sm font-medium capitalize ${severityColor(detail.severity)}`}>{detail.severity}</span>
                </div>
                <p className="text-gray-400 text-sm mb-4">{detail.description || "No description"}</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-gray-800 rounded-lg p-3"><p className="text-xs text-gray-500">Status</p><p className="text-white capitalize text-sm">{detail.status}</p></div>
                  <div className="bg-gray-800 rounded-lg p-3"><p className="text-xs text-gray-500">Stage</p><p className="text-white text-sm">{detail.attack_stage || "—"}</p></div>
                  <div className="bg-gray-800 rounded-lg p-3"><p className="text-xs text-gray-500">Assignee</p><p className="text-white text-sm">{detail.assignee || "—"}</p></div>
                  <div className="bg-gray-800 rounded-lg p-3"><p className="text-xs text-gray-500">Evidence</p><p className="text-white text-sm">{detail.evidence?.length ?? 0} items</p></div>
                </div>
              </div>

              {detail.evidence?.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Paperclip size={18} className="text-cyan-400" /> Evidence</h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {detail.evidence.map((e: { id: number; description: string; type: string; source: string; created_at: string }) => (
                      <div key={e.id} className="bg-gray-800 rounded-lg p-3 text-sm">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-white">{e.description}</span>
                          <span className="text-xs text-gray-500 capitalize">{e.type}</span>
                        </div>
                        <span className="text-xs text-gray-500">{e.source} · {new Date(e.created_at).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Paperclip size={18} className="text-purple-400" /> Add Evidence</h3>
                <div className="space-y-2">
                  <input type="text" value={newEvidence.description} onChange={(e) => setNewEvidence({ ...newEvidence, description: e.target.value })} placeholder="Description"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-purple-500" />
                  <input type="text" value={newEvidence.source} onChange={(e) => setNewEvidence({ ...newEvidence, source: e.target.value })} placeholder="Source"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-purple-500" />
                  <textarea value={newEvidence.content} onChange={(e) => setNewEvidence({ ...newEvidence, content: e.target.value })} rows={2} placeholder="Content"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:border-purple-500" />
                  <button onClick={() => evidenceMutation.mutate()} disabled={!newEvidence.description || !newEvidence.content}
                    className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">Add Evidence</button>
                </div>
              </div>

              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><MessageSquare size={18} className="text-green-400" /> Comments</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto mb-3">
                  {detail.comments?.length > 0 ? detail.comments.map((c: { id: number; content: string; user: string; created_at: string; internal?: boolean }) => (
                    <div key={c.id} className="bg-gray-800 rounded-lg p-3 text-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-white font-medium">{c.user || "Unknown"}</span>
                        <div className="flex items-center gap-2">
                          {c.internal && <span className="text-xs text-yellow-400">Internal</span>}
                          <span className="text-xs text-gray-500">{new Date(c.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <p className="text-gray-400">{c.content}</p>
                    </div>
                  )) : <p className="text-gray-500 text-sm">No comments</p>}
                </div>
                <div className="flex gap-2">
                  <input type="text" value={newComment} onChange={(e) => setNewComment(e.target.value)} placeholder="Add a comment..."
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-green-500"
                    onKeyDown={(e) => e.key === "Enter" && commentMutation.mutate()} />
                  <button onClick={() => commentMutation.mutate()} disabled={!newComment}
                    className="bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">Send</button>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 flex items-center justify-center h-64">
              <div className="text-center text-gray-500">
                <FolderOpen size={40} className="mx-auto mb-3 opacity-30" />
                <p>Select a case to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
