import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { extractIocs, enrichIoc, correlateIocs, getThreatFeed } from "../../api/threatIntel";
import { Search, Globe, Link, RefreshCw } from "lucide-react";

export default function ThreatIntel() {
  const [text, setText] = useState("");
  const [indicator, setIndicator] = useState("");
  const [correlationIocs, setCorrelationIocs] = useState("");

  const extractMutation = useMutation({ mutationFn: extractIocs });
  const enrichMutation = useMutation({ mutationFn: enrichIoc });
  const correlateMutation = useMutation({
    mutationFn: (iocs: string[]) => correlateIocs(iocs),
  });
  const { data: feed } = useQuery({ queryKey: ["threat-feed"], queryFn: getThreatFeed });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Threat Intelligence</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Search size={18} className="text-purple-400" /> IOC Extraction</h2>
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:border-purple-500 mb-3"
            placeholder="Paste text to extract IPs, domains, hashes, URLs..." />
          <button onClick={() => extractMutation.mutate(text)} disabled={!text}
            className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            Extract IOCs
          </button>
          {extractMutation.data && (
            <div className="mt-4 space-y-2 text-sm">
              {["ips", "domains", "urls", "hashes", "emails"].map((type) => {
                const items = extractMutation.data[type] || extractMutation.data[`${type}_detected`] || [];
                if (!items?.length) return null;
                return (
                  <div key={type}>
                    <p className="text-gray-400 capitalize mb-1">{type} ({items.length})</p>
                    <div className="flex flex-wrap gap-1">
                      {items.map((item: string, i: number) => (
                        <span key={i} className="bg-gray-800 text-gray-300 px-2 py-0.5 rounded text-xs">{item}</span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Globe size={18} className="text-cyan-400" /> IOC Enrichment</h2>
          <div className="flex gap-2 mb-3">
            <input type="text" value={indicator} onChange={(e) => setIndicator(e.target.value)}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500"
              placeholder="IP, domain, hash, or URL" />
            <button onClick={() => enrichMutation.mutate(indicator)} disabled={!indicator}
              className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">
              Enrich
            </button>
          </div>
          {enrichMutation.data && (
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2"><span className="text-gray-400">Source:</span><span className="text-white">{enrichMutation.data.source || "N/A"}</span></div>
              <div className="flex items-center gap-2"><span className="text-gray-400">Reputation:</span>
                <span className={`${(enrichMutation.data.malicious || enrichMutation.data.risk === "malicious") ? "text-red-400" : "text-green-400"}`}>
                  {(enrichMutation.data.malicious || enrichMutation.data.risk || "unknown")}
                </span>
              </div>
              {enrichMutation.data.country && <div className="flex items-center gap-2"><span className="text-gray-400">Country:</span><span className="text-white">{enrichMutation.data.country}</span></div>}
              {enrichMutation.data.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {enrichMutation.data.tags.map((t: string, i: number) => (
                    <span key={i} className="bg-cyan-600/20 text-cyan-400 px-2 py-0.5 rounded text-xs">{t}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><Link size={18} className="text-orange-400" /> IOC Correlation</h2>
          <textarea value={correlationIocs} onChange={(e) => setCorrelationIocs(e.target.value)} rows={3}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:border-orange-500 mb-3"
            placeholder="Enter IOCs (one per line)" />
          <button onClick={() => correlateMutation.mutate(correlationIocs.split("\n").filter(Boolean))} disabled={!correlationIocs}
            className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            Correlate
          </button>
          {correlateMutation.data?.groups?.length > 0 && (
            <div className="mt-4 space-y-3">
              {correlateMutation.data.groups.map((g: { name: string; type: string; iocs: string[] }, i: number) => (
                <div key={i} className="bg-gray-800 rounded-lg p-3">
                  <p className="text-white font-medium text-sm mb-1">{g.name}</p>
                  <p className="text-xs text-gray-500 mb-2">{g.type}</p>
                  <div className="flex flex-wrap gap-1">{g.iocs.map((ioc, j) => <span key={j} className="bg-gray-700 text-gray-300 px-2 py-0.5 rounded text-xs">{ioc}</span>)}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2"><RefreshCw size={18} className="text-green-400" /> Threat Feed</h2>
          <p className="text-gray-500 text-sm mb-3">Curated threat intelligence from multiple sources.</p>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {feed?.map((f: { indicator: string; type: string; risk: string; source: string; updated: string }, i: number) => (
              <div key={i} className="flex items-center justify-between bg-gray-800 rounded-lg p-2 text-sm">
                <span className="text-white">{f.indicator}</span>
                <span className="text-xs text-gray-500">{f.type} · {f.source}</span>
              </div>
            )) ?? <p className="text-gray-500 text-sm">No feed data yet</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
