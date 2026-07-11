import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import { useToast } from "../components/Toast";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import {
  Puzzle, Play, Square, RefreshCw,
  Package, Search, FileCode, Globe, Cpu, Download,
} from "lucide-react";

interface PluginInfo {
  id: string;
  name: string;
  version: string;
  plugin_type: string;
  description: string;
  author: string;
  enabled: boolean;
  config: Record<string, string>;
  settings_schema: Record<string, unknown>;
}

const PLUGIN_ICONS: Record<string, typeof Package> = {
  parser: FileCode,
  "threat-feed": Globe,
  "ai-provider": Cpu,
  exporter: Download,
  "detection-pack": Search,
};

const PLUGIN_COLORS: Record<string, string> = {
  parser: "info",
  "threat-feed": "warning",
  "ai-provider": "success",
  exporter: "default",
  "detection-pack": "danger",
} as const;

export default function Plugins() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState("");

  const { data: plugins, isLoading } = useQuery<PluginInfo[]>({
    queryKey: ["plugins", selectedType],
    queryFn: () =>
      api.get("/plugins/", { params: selectedType ? { type: selectedType } : {} }).then((r) => r.data),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enable }: { id: string; enable: boolean }) =>
      api.post(`/plugins/${id}/${enable ? "enable" : "disable"}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
      toast("success", "Plugin status updated");
    },
    onError: () => toast("error", "Failed to update plugin"),
  });

  const reloadMutation = useMutation({
    mutationFn: () => api.post("/plugins/reload"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
      toast("success", "Plugins reloaded");
    },
    onError: () => toast("error", "Failed to reload plugins"),
  });

  const types = [
    { value: "", label: "All", icon: Package },
    { value: "parser", label: "Parsers", icon: FileCode },
    { value: "threat-feed", label: "Threat Feeds", icon: Globe },
    { value: "ai-provider", label: "AI Providers", icon: Cpu },
    { value: "exporter", label: "Exporters", icon: Download },
    { value: "detection-pack", label: "Detection Packs", icon: Search },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Puzzle size={20} className="text-primary" /> Plugins
          </h1>
          <p className="text-sm text-text-secondary mt-1">Extend Sentinel with parsers, threat feeds, AI models, exporters, and detection packs.</p>
        </div>
        <Button variant="secondary" size="sm" icon={<RefreshCw size={14} />} onClick={() => reloadMutation.mutate()} loading={reloadMutation.isPending}>
          Reload Plugins
        </Button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {types.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.value}
              onClick={() => setSelectedType(t.value)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition-colors ${
                selectedType === t.value
                  ? "bg-primary/10 border-primary text-primary"
                  : "bg-surface-secondary border-border text-text-secondary hover:border-primary/50"
              }`}
            >
              <Icon size={16} /> {t.label}
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-sm text-text-muted">Loading plugins...</div>
      ) : !plugins?.length ? (
        <div className="text-center py-12">
          <Package size={48} className="mx-auto mb-3 text-text-muted opacity-30" />
          <p className="text-text-secondary text-sm">No plugins found</p>
          <p className="text-text-muted text-xs mt-1">Install plugins in the plugins/ directory and click Reload</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {plugins.map((plugin) => {
            const Icon = PLUGIN_ICONS[plugin.plugin_type] || Package;
            const badgeVariant = (PLUGIN_COLORS[plugin.plugin_type] || "default") as "default" | "success" | "warning" | "danger" | "info";
            return (
              <Card key={plugin.id} className="flex flex-col">
                <div className="flex items-start gap-3 mb-3">
                  <div className={`p-2 rounded-lg ${plugin.enabled ? "bg-primary/10" : "bg-surface-secondary"}`}>
                    <Icon size={20} className={plugin.enabled ? "text-primary" : "text-text-muted"} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-text-primary truncate">{plugin.name}</h3>
                      <Badge variant={badgeVariant}>{plugin.plugin_type}</Badge>
                    </div>
                    <p className="text-xs text-text-secondary mt-1">{plugin.description}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-text-muted mb-3">
                  <span>v{plugin.version}</span>
                  <span>by {plugin.author}</span>
                </div>

                <div className="flex items-center gap-2 mt-auto">
                  {plugin.enabled ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Square size={14} />}
                      onClick={() => toggleMutation.mutate({ id: plugin.id, enable: false })}
                    >
                      Disable
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<Play size={14} />}
                      onClick={() => toggleMutation.mutate({ id: plugin.id, enable: true })}
                    >
                      Enable
                    </Button>
                  )}
                  <Badge variant={plugin.enabled ? "success" : "default"} dot>
                    {plugin.enabled ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
