import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadLog, getAnalyses, getAnalysis, getTimeline } from "../../api/logs";
import { Upload, FileText, Clock, AlertTriangle, Search, FolderOpen } from "lucide-react";
import { useToast } from "../../components/Toast";
import { useElectron } from "../../hooks/useElectron";
import { FileDropZone } from "../../components/FileDropZone";
import { Card } from "../../components/ui/Card";

export default function LogAnalysis() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { isElectron, uploadFileViaBackend, openFileDialog, openInExplorer } = useElectron();

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

  const handleNativeUpload = async () => {
    if (!isElectron) return;
    const paths = await openFileDialog([{ name: "Log Files", extensions: ["log", "txt", "csv", "json", "evtx", "syslog", "xml"] }]);
    if (!paths) return;
    for (const p of paths) {
      try {
        await uploadFileViaBackend(p);
        queryClient.invalidateQueries({ queryKey: ["analyses"] });
        toast("success", "Log uploaded and analyzed");
      } catch {
        toast("error", `Failed to upload ${p}`);
      }
    }
  };

  const handleBrowserUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    uploadMutation.mutate(fd);
  };

  const handleDropFiles = (files: FileList) => {
    for (const file of Array.from(files)) {
      const fd = new FormData();
      fd.append("file", file);
      uploadMutation.mutate(fd);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-text-primary">Log Analysis</h1>
          <p className="text-sm text-text-secondary mt-1">Upload and analyze security logs</p>
        </div>
        <div className="flex items-center gap-2">
          {isElectron && (
            <button onClick={handleNativeUpload} className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-hover transition-colors">
              <FolderOpen size={16} />
              Open Files
            </button>
          )}
          {!isElectron && (
            <label className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-hover transition-colors cursor-pointer">
              <Upload size={16} />
              Upload Log
              <input type="file" onChange={handleBrowserUpload} className="hidden" accept=".log,.txt,.csv,.json,.evtx,.syslog,.xml" />
            </label>
          )}
        </div>
      </div>

      {uploadMutation.isPending && (
        <div className="bg-info/10 border border-info/30 text-info px-4 py-2 rounded-lg text-sm">Uploading and analyzing...</div>
      )}

      <FileDropZone
        onFiles={handleDropFiles}
        accept=".log,.txt,.csv,.json,.evtx,.syslog,.xml"
        label="Drop log files to upload and analyze"
        loading={uploadMutation.isPending}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-3">
          <h2 className="text-xs font-semibold text-text-muted uppercase tracking-wider">Analyses</h2>
          {(!analyses || analyses.length === 0) && (
            <Card><p className="text-sm text-text-muted py-4 text-center">No analyses yet. Upload a log file to begin.</p></Card>
          )}
          <div className="space-y-1 max-h-[65vh] overflow-y-auto">
            {analyses?.map((a: { id: number; filename: string; created_at: string; total_events?: number; suspicious_count?: number }) => (
              <button
                key={a.id}
                onClick={() => setSelectedId(a.id)}
                className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${
                  selectedId === a.id ? "bg-primary/10 border border-primary/30" : "bg-surface border border-border hover:bg-surface-secondary"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <FileText size={14} className="text-primary" />
                  <span className="text-text-primary font-medium truncate">{a.filename}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-text-muted">
                  <span className="flex items-center gap-1"><Clock size={12} />{new Date(a.created_at).toLocaleDateString()}</span>
                  <span>{a.total_events ?? 0} events</span>
                  {(a.suspicious_count ?? 0) > 0 && <span className="text-danger flex items-center gap-1"><AlertTriangle size={12} />{a.suspicious_count}</span>}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {detail && (
            <>
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold text-text-primary">{detail.filename}</h2>
                  {isElectron && detail.filepath && (
                    <button onClick={() => openInExplorer(detail.filepath)} className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors">
                      <FolderOpen size={14} />
                      Show in folder
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-surface-secondary rounded-lg p-3 text-center">
                    <p className="text-xs text-text-muted">Format</p>
                    <p className="text-text-primary font-medium">{detail.format}</p>
                  </div>
                  <div className="bg-surface-secondary rounded-lg p-3 text-center">
                    <p className="text-xs text-text-muted">Events</p>
                    <p className="text-text-primary font-medium">{detail.total_events}</p>
                  </div>
                  <div className="bg-surface-secondary rounded-lg p-3 text-center">
                    <p className="text-xs text-text-muted">Suspicious</p>
                    <p className="text-danger font-medium">{detail.suspicious_count}</p>
                  </div>
                  <div className="bg-surface-secondary rounded-lg p-3 text-center">
                    <p className="text-xs text-text-muted">Event Types</p>
                    <p className="text-text-primary font-medium">{detail.event_types?.length ?? 0}</p>
                  </div>
                </div>
              </Card>

              {timeline && timeline.length > 0 && (
                <Card>
                  <h2 className="text-sm font-semibold text-text-primary mb-4">Timeline</h2>
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {timeline.map((t: { timestamp: string; event_type: string; source_ip?: string; severity?: string; details?: string }, i: number) => (
                      <div key={i} className="flex items-start gap-3 text-sm border-b border-border pb-2">
                        <span className="text-xs text-text-muted whitespace-nowrap w-32">{t.timestamp}</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          t.severity === "high" || t.severity === "critical" ? "bg-danger/10 text-danger" :
                          t.severity === "medium" ? "bg-warning/10 text-warning" : "bg-surface-secondary text-text-secondary"
                        }`}>{t.event_type}</span>
                        <span className="text-text-muted">{t.source_ip || t.details || ""}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}

          {!detail && (
            <Card className="flex items-center justify-center h-64">
              <div className="text-center text-text-muted">
                <Search size={40} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Select an analysis to view details</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
