import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { listSessions, createSession, chat, investigate, getRecommendations, explainLog } from "../../api/ai";
import { Bot, Send, Plus, MessageSquare, Lightbulb, Search } from "lucide-react";
import { useToast } from "../../components/Toast";

export default function AIAssistant() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
  const [evidence, setEvidence] = useState("");
  const [logLine, setLogLine] = useState("");
  const { toast } = useToast();

  const { data: sessions, refetch: refetchSessions } = useQuery({ queryKey: ["ai-sessions"], queryFn: listSessions });

  const createMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (data) => { setSessionId(data.id); refetchSessions(); toast("success", "Session created"); },
    onError: () => toast("error", "Failed to create session"),
  });

  const chatMutation = useMutation({
    mutationFn: () => chat(sessionId!, message),
    onSuccess: (data) => {
      setChatMessages((prev) => [...prev, { role: "user", content: message }, { role: "assistant", content: data.response || data.reply || data.message }]);
      setMessage("");
    },
  });

  const investigateMutation = useMutation({ mutationFn: () => investigate(evidence) });
  const explainMutation = useMutation({ mutationFn: () => explainLog(logLine) });
  const { data: recommendations } = useQuery({ queryKey: ["recommendations"], queryFn: () => getRecommendations(0), enabled: false });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">AI Investigation Assistant</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2"><MessageSquare size={18} className="text-cyan-400" /> Chat</h2>
              <button onClick={() => createMutation.mutate("New Session")} className="flex items-center gap-1 text-sm bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 rounded-lg transition-colors">
                <Plus size={16} /> New Session
              </button>
            </div>
            {sessionId ? (
              <>
                <div className="h-64 overflow-y-auto mb-4 space-y-3 bg-gray-950 rounded-lg p-4">
                  {chatMessages.length === 0 && <p className="text-gray-500 text-sm text-center">Start a conversation</p>}
                  {chatMessages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${m.role === "user" ? "bg-cyan-600/20 text-cyan-300" : "bg-gray-800 text-gray-200"}`}>{m.content}</div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input type="text" value={message} onChange={(e) => setMessage(e.target.value)}
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500"
                    placeholder="Ask about threats, logs, or IOCs..." onKeyDown={(e) => e.key === "Enter" && chatMutation.mutate()} />
                  <button onClick={() => chatMutation.mutate()} disabled={!message}
                    className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"><Send size={18} /></button>
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Bot size={48} className="mx-auto mb-3 opacity-30" />
                <p>Select a session or create a new one</p>
                <div className="mt-4 space-y-2 max-h-40 overflow-y-auto">
                  {sessions?.map((s: { id: number; title: string }) => (
                    <button key={s.id} onClick={() => setSessionId(s.id)}
                      className="block w-full text-left bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">{s.title}</button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Search size={18} className="text-purple-400" /> Investigate</h2>
            <textarea value={evidence} onChange={(e) => setEvidence(e.target.value)} rows={3}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:border-purple-500 mb-3"
              placeholder="Paste evidence, logs, or IOCs to investigate..." />
            <button onClick={() => investigateMutation.mutate()} disabled={!evidence}
              className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">Investigate</button>
            {investigateMutation.data && (
              <div className="mt-4 p-4 bg-gray-800 rounded-lg text-sm text-gray-200 whitespace-pre-wrap">{investigateMutation.data.analysis || investigateMutation.data.response || JSON.stringify(investigateMutation.data)}</div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Lightbulb size={18} className="text-yellow-400" /> Recommendations</h2>
            {recommendations?.length > 0 ? recommendations.map((r: { title: string; description: string; priority: string }, i: number) => (
              <div key={i} className="bg-gray-800 rounded-lg p-3 mb-2 text-sm">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                    r.priority === "high" ? "bg-red-600/20 text-red-400" :
                    r.priority === "medium" ? "bg-yellow-600/20 text-yellow-400" : "bg-green-600/20 text-green-400"
                  }`}>{r.priority}</span>
                  <span className="text-white font-medium">{r.title}</span>
                </div>
                <p className="text-gray-400 text-xs">{r.description}</p>
              </div>
            )) : <p className="text-gray-500 text-sm">No recommendations yet</p>}
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Bot size={18} className="text-green-400" /> Explain Log</h2>
            <textarea value={logLine} onChange={(e) => setLogLine(e.target.value)} rows={2}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:border-green-500 mb-3"
              placeholder="Paste a log line to explain..." />
            <button onClick={() => explainMutation.mutate()} disabled={!logLine}
              className="bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">Explain</button>
            {explainMutation.data && (
              <div className="mt-4 p-3 bg-gray-800 rounded-lg text-sm text-gray-200 whitespace-pre-wrap">
                {explainMutation.data.explanation || explainMutation.data.response || JSON.stringify(explainMutation.data)}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
