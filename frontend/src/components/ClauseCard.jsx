import { useState } from "react";
import { ChevronDown } from "lucide-react";

const CLAUSE_TYPE_LABELS = {
  liability: "Liability",
  termination: "Termination",
  ip_ownership: "IP Ownership",
  payment: "Payment",
  confidentiality: "Confidentiality",
  non_compete: "Non-Compete",
  indemnification: "Indemnification",
  auto_renewal: "Auto-Renewal",
  other: "Other",
};

const riskConfig = {
  high: { badge: "bg-red-100 text-red-700", border: "border-l-red-500" },
  medium: { badge: "bg-amber-100 text-amber-700", border: "border-l-amber-500" },
  low: { badge: "bg-green-100 text-green-700", border: "border-l-green-500" },
};

export default function ClauseCard({ clause, index }) {
  const [expanded, setExpanded] = useState(false);
  const { flagged, plain_english_summary, recommended_action } = clause;
  const { clause: classified, risk_level, risk_reasoning, benchmark } = flagged;
  const rc = riskConfig[risk_level];

  return (
    <div className={`border border-l-4 ${rc.border} rounded-xl bg-white/90 backdrop-blur-sm shadow-sm transition-all duration-300 hover:shadow-lg hover:shadow-gray-200/50 hover:-translate-y-0.5`}>
      <div
        className="p-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-xs font-mono text-gray-400">#{index + 1}</span>
              <span className="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full transition-colors duration-200">
                {CLAUSE_TYPE_LABELS[classified.clause_type] || classified.clause_type}
              </span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full transition-colors duration-200 ${rc.badge}`}>
                {risk_level} risk
              </span>
              {classified.confidence && (
                <span className="text-xs text-gray-400 tabular-nums">
                  {Math.round(classified.confidence * 100)}% confidence
                </span>
              )}
            </div>
            <p className="text-sm text-gray-800 leading-relaxed">{plain_english_summary}</p>
            <div className="mt-2 flex items-start gap-2">
              <span className="text-xs font-medium text-gray-500 shrink-0 mt-0.5">Action:</span>
              <p className="text-sm font-medium text-gray-900">{recommended_action}</p>
            </div>
          </div>
          <div className="flex-shrink-0 mt-1">
            <ChevronDown
              className={`w-5 h-5 text-gray-400 transition-transform duration-300 ${expanded ? "rotate-180" : ""}`}
            />
          </div>
        </div>
      </div>

      {expanded && (
        <div className="px-5 pb-5 pt-0 border-t border-gray-100 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            {/* Original Text */}
            <div>
              <h4 className="font-medium text-gray-500 text-xs mb-2 uppercase tracking-wider">Original Clause Text</h4>
              <div className="bg-gray-50/80 p-4 rounded-lg text-xs font-mono leading-relaxed text-gray-700 max-h-48 overflow-y-auto border border-gray-100">
                {classified.chunk.text}
              </div>
              {classified.chunk.page_number && (
                <p className="text-xs text-gray-400 mt-1">Page {classified.chunk.page_number}</p>
              )}
            </div>

            {/* Risk Analysis */}
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-500 text-xs mb-2 uppercase tracking-wider">Risk Analysis</h4>
                <p className="text-sm text-gray-700 leading-relaxed">{risk_reasoning}</p>
              </div>

              {benchmark && benchmark.deviation_summary && (
                <div>
                  <h4 className="font-medium text-gray-500 text-xs mb-2 uppercase tracking-wider">Benchmark Comparison</h4>
                  <p className="text-sm text-gray-600">
                    {benchmark.is_standard ? (
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-2 h-2 bg-green-500 rounded-full" />
                        <span className="text-green-600 font-medium">Standard language — </span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-2 h-2 bg-amber-500 rounded-full" />
                        <span className="text-amber-600 font-medium">Non-standard — </span>
                      </span>
                    )}
                    {benchmark.deviation_summary || "Matches standard legal clause patterns."}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
