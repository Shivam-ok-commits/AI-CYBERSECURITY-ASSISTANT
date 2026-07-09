import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadLog, getAnalyses, getAnalysis, getTimeline } from "../../api/logs";
import { Upload, FileText, Clock, AlertTriangle, Search } from "lucide-react";
import { useToast } from "../../components/Toast";

export default function LogAnalysis() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: analyses } = useQuery({ queryKey: ["analyses"], queryFn: getAnalyses });
  const { data: detail } = useQuery({
    queryKey: ["analysis", selectedId],
    queryFn: () => getAnalysis(selectedId!),
    enabled: !!selectedId,
  });
  const { data: timeline } = useQuery({
    queryKey: ["timeline", selectedId],
    queryFn: () => getTimeline(selectedId!),
    enabled: !!selectedId,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadLog,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["analyses"] }); toast("success", "Log uploaded and analyzed"); },
    onError: () => toast("error", "Upload failed"),
  });

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    uploadMutation.mutate(fd);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Log Analysis</h1>
        <label className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg cursor-pointer text-sm transition-colors">
          <Upload size={18} />
          Upload Log
          <input type="file" onChange={handleUpload} className="hidden" accept=".log,.txt,.csv,.json,.evtx" />
        </label>
      </div>

      {uploadMutation.isPending && <div className="bg-blue-600/10 border border-blue-600/30 text-blue-400 px-4 py-2 rounded-lg text-sm">Uploading and analyzing...</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-sm font-semibold text-gray-400 uppercase mb-3">Analyses</h2>
          {analyses?.length === 0 && <p className="text-gray-500 text-sm">No analyses yet. Upload a log file to begin.</p>}
          <div className="space-y-2 max-h-[70vh] overflow-y-auto">
            {analyses?.map((a: { id: number; filename: string; created_at: string; total_events?: number; suspicious_count?: number }) => (
              <button
                key={a.id}
                onClick={() => setSelectedId(a.id)}
                className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${
                  selectedId === a.id ? "bg-cyan-600/20 border border-cyan-600/30" : "bg-gray-800/50 border border-gray-800 hover:bg-gray-800"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <FileText size={14} className="text-cyan-400" />
                  <span className="text-white font-medium truncate">{a.filename}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span className="flex items-center gap-1"><Clock size={12} />{new Date(a.created_at).toLocaleDateString()}</span>
                  <span>{a.total_events ?? 0} events</span>
                  {(a.suspicious_count ?? 0) > 0 && <span className="text-red-400 flex items-center gap-1"><AlertTriangle size={12} />{a.suspicious_count}</span>}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {detail && (
            <>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4">{detail.filename}</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-gray-800 rounded-lg p-3 text-center"><p className="text-xs text-gray-400">Format</p><p className="text-white font-medium">{detail.format}</p></div>
                  <div className="bg-gray-800 rounded-lg p-3 text-center"><p className="text-xs text-gray-400">Events</p><p className="text-white font-medium">{detail.total_events}</p></div>
                  <div className="bg-gray-800 rounded-lg p-3 text-center"><p className="text-xs text-gray-400">Suspicious</p><p className="text-red-400 font-medium">{detail.suspicious_count}</p></div>
                  <div className="bg-gray-800 rounded-lg p-3 text-center"><p className="text-xs text-gray-400">Event Types</p><p className="text-white font-medium">{detail.event_types?.length ?? 0}</p></div>
                </div>
              </div>

              {timeline && timeline.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                  <h2 className="text-lg font-semibold text-white mb-4">Timeline</h2>
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {timeline.map((t: { timestamp: string; event_type: string; source_ip?: string; severity?: string; details?: string }, i: number) => (
                      <div key={i} className="flex items-start gap-3 text-sm border-b border-gray-800 pb-2">
                        <span className="text-xs text-gray-500 whitespace-nowrap w-32">{t.timestamp}</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          t.severity === "high" || t.severity === "critical" ? "bg-red-600/20 text-red-400" :
                          t.severity === "medium" ? "bg-yellow-600/20 text-yellow-400" : "bg-gray-700 text-gray-300"
                        }`}>{t.event_type}</span>
                        <span className="text-gray-400">{t.source_ip || t.details || ""}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {!detail && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 flex items-center justify-center h-64">
              <div className="text-center text-gray-500">
                <Search size={40} className="mx-auto mb-3 opacity-30" />
                <p>Select an analysis to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
