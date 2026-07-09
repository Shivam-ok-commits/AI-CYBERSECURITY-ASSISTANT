interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

const colors: Record<string, string> = {
  critical: "bg-red-600/20 text-red-400 border-red-600/30",
  high: "bg-orange-600/20 text-orange-400 border-orange-600/30",
  medium: "bg-yellow-600/20 text-yellow-400 border-yellow-600/30",
  low: "bg-green-600/20 text-green-400 border-green-600/30",
  info: "bg-blue-600/20 text-blue-400 border-blue-600/30",
  open: "bg-blue-600/20 text-blue-400 border-blue-600/30",
  in_progress: "bg-yellow-600/20 text-yellow-400 border-yellow-600/30",
  resolved: "bg-green-600/20 text-green-400 border-green-600/30",
  closed: "bg-gray-600/20 text-gray-400 border-gray-600/30",
  enabled: "bg-green-600/20 text-green-400 border-green-600/30",
  disabled: "bg-gray-600/20 text-gray-400 border-gray-600/30",
  true: "bg-green-600/20 text-green-400 border-green-600/30",
  false: "bg-gray-600/20 text-gray-400 border-gray-600/30",
  ok: "bg-green-600/20 text-green-400 border-green-600/30",
  error: "bg-red-600/20 text-red-400 border-red-600/30",
  active: "bg-green-600/20 text-green-400 border-green-600/30",
};

export function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const key = status?.toLowerCase().replace(/\s+/g, "_");
  const colorClass = colors[key] || "bg-gray-700 text-gray-300 border-gray-600";
  const textSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full font-medium border ${colorClass} ${textSize} capitalize`}>
      {status}
    </span>
  );
}
