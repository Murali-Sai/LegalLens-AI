import { useState } from "react";
import { MousePointerClick } from "lucide-react";

const riskHighlight = {
  high: "bg-red-50/80 border-red-200/60 hover:bg-red-100/80 hover:border-red-300",
  medium: "bg-amber-50/80 border-amber-200/60 hover:bg-amber-100/80 hover:border-amber-300",
  low: "bg-green-50/80 border-green-200/60 hover:bg-green-100/80 hover:border-green-300",
};

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

export default function DocumentView({ analysis }) {
  const [selectedClause, setSelectedClause] = useState(null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in">
      {/* Document with highlights */}
      <div className="lg:col-span-2 bg-white/90 backdrop-blur-sm rounded-xl border border-gray-200/60 p-6 max-h-[70vh] overflow-y-auto shadow-sm">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Document Clauses
        </h3>
        <div className="space-y-3">
          {analysis.clauses.map((clause, i) => {
            const risk = clause.flagged.risk_level;
            const isSelected = selectedClause === i;

            return (
              <div
                key={i}
                onClick={() => setSelectedClause(isSelected ? null : i)}
                className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 text-sm leading-relaxed ${
                  riskHighlight[risk]
                } ${isSelected ? "ring-2 ring-blue-400/50 shadow-lg shadow-blue-500/5" : ""}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-mono text-gray-500">#{i + 1}</span>
                  <span className="text-xs font-medium px-2 py-0.5 bg-white/70 rounded-full">
                    {CLAUSE_TYPE_LABELS[clause.flagged.clause.clause_type] || clause.flagged.clause.clause_type}
                  </span>
                  <span className={`text-xs font-semibold ${
                    risk === "high" ? "text-red-700" : risk === "medium" ? "text-amber-700" : "text-green-700"
                  }`}>
                    {risk} risk
                  </span>
                </div>
                <p className="font-mono text-xs text-gray-700">
                  {clause.flagged.clause.chunk.text}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detail sidebar */}
      <div className="bg-white/90 backdrop-blur-sm rounded-xl border border-gray-200/60 p-6 max-h-[70vh] overflow-y-auto shadow-sm">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Clause Details
        </h3>
        {selectedClause !== null ? (
          <ClauseDetail clause={analysis.clauses[selectedClause]} index={selectedClause} />
        ) : (
          <div className="text-center py-12 text-gray-400 animate-fade-in">
            <MousePointerClick className="w-10 h-10 mx-auto mb-3 text-gray-300" />
            <p className="text-sm">Click a clause to see details</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ClauseDetail({ clause, index }) {
  const { flagged, plain_english_summary, recommended_action } = clause;
  const { risk_level, risk_reasoning, benchmark } = flagged;

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Summary</h4>
        <p className="text-sm text-gray-800 leading-relaxed">{plain_english_summary}</p>
      </div>

      <div>
        <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Risk Level</h4>
        <span className={`inline-block text-sm font-semibold px-3 py-1 rounded-full ${
          risk_level === "high"
            ? "bg-red-100 text-red-700"
            : risk_level === "medium"
            ? "bg-amber-100 text-amber-700"
            : "bg-green-100 text-green-700"
        }`}>
          {risk_level.charAt(0).toUpperCase() + risk_level.slice(1)} Risk
        </span>
      </div>

      <div>
        <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Why This Rating</h4>
        <p className="text-sm text-gray-700 leading-relaxed">{risk_reasoning}</p>
      </div>

      {benchmark && benchmark.deviation_summary && (
        <div>
          <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Benchmark</h4>
          <p className="text-sm text-gray-600 leading-relaxed">
            {benchmark.is_standard ? (
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 bg-green-500 rounded-full" />
                <span className="font-medium">Matches standard language. </span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 bg-amber-500 rounded-full" />
                <span className="font-medium">Deviates from standard. </span>
              </span>
            )}
            {benchmark.deviation_summary}
          </p>
        </div>
      )}

      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100/50">
        <h4 className="text-xs font-medium text-blue-600 uppercase tracking-wider mb-1">Recommended Action</h4>
        <p className="text-sm font-medium text-blue-900">{recommended_action}</p>
      </div>
    </div>
  );
}
