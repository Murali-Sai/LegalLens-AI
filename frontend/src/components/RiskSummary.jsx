import { AlertTriangle, AlertCircle, CheckCircle } from "lucide-react";

const riskConfig = {
  high: {
    bg: "bg-gradient-to-br from-red-50 to-rose-50",
    border: "border-red-200/60",
    text: "text-red-700",
    bar: "bg-gradient-to-r from-red-500 to-rose-500",
    hoverBorder: "hover:border-red-300",
    activeBorder: "border-red-400 ring-2 ring-red-100 shadow-lg shadow-red-500/10",
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
    Icon: AlertTriangle,
  },
  medium: {
    bg: "bg-gradient-to-br from-amber-50 to-orange-50",
    border: "border-amber-200/60",
    text: "text-amber-700",
    bar: "bg-gradient-to-r from-amber-500 to-orange-500",
    hoverBorder: "hover:border-amber-300",
    activeBorder: "border-amber-400 ring-2 ring-amber-100 shadow-lg shadow-amber-500/10",
    iconBg: "bg-amber-100",
    iconColor: "text-amber-600",
    Icon: AlertCircle,
  },
  low: {
    bg: "bg-gradient-to-br from-green-50 to-emerald-50",
    border: "border-green-200/60",
    text: "text-green-700",
    bar: "bg-gradient-to-r from-green-500 to-emerald-500",
    hoverBorder: "hover:border-green-300",
    activeBorder: "border-green-400 ring-2 ring-green-100 shadow-lg shadow-green-500/10",
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
    Icon: CheckCircle,
  },
};

export default function RiskSummary({ analysis, onFilterClick, activeFilter }) {
  const items = [
    { label: "High Risk", count: analysis.high_risk_count, level: "high" },
    { label: "Medium Risk", count: analysis.medium_risk_count, level: "medium" },
    { label: "Low Risk", count: analysis.low_risk_count, level: "low" },
  ];

  const total = analysis.total_clauses || 1;

  return (
    <div className="grid grid-cols-3 gap-4">
      {items.map(({ label, count, level }) => {
        const c = riskConfig[level];
        const pct = Math.round((count / total) * 100);
        const isActive = activeFilter === level;
        const RiskIcon = c.Icon;

        return (
          <button
            key={level}
            onClick={() => onFilterClick(isActive ? "all" : level)}
            className={`rounded-xl border p-5 text-left transition-all duration-300 cursor-pointer hover:-translate-y-0.5 hover:shadow-md ${c.bg} ${
              isActive ? c.activeBorder : `${c.border} ${c.hoverBorder}`
            }`}
          >
            <div className={`w-8 h-8 ${c.iconBg} rounded-lg flex items-center justify-center mb-3`}>
              <RiskIcon className={`w-4 h-4 ${c.iconColor}`} />
            </div>
            <div className="flex items-baseline justify-between mb-2">
              <span className={`text-3xl font-bold tabular-nums ${c.text}`}>{count}</span>
              <span className={`text-sm font-medium tabular-nums ${c.text}`}>{pct}%</span>
            </div>
            <div className={`text-sm font-medium ${c.text} mb-2`}>{label}</div>
            <div className="w-full h-1.5 bg-white/80 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${c.bar}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}
