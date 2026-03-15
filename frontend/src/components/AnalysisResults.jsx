import { useState } from "react";
import { FileText } from "lucide-react";
import ClauseCard from "./ClauseCard";
import RiskSummary from "./RiskSummary";
import ClauseFilter from "./ClauseFilter";
import DocumentView from "./DocumentView";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "document", label: "Document View" },
];

export default function AnalysisResults({ analysis, onReset }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [riskFilter, setRiskFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  const filteredClauses = analysis.clauses.filter((c) => {
    const matchesRisk = riskFilter === "all" || c.flagged.risk_level === riskFilter;
    const matchesType = typeFilter === "all" || c.flagged.clause.clause_type === typeFilter;
    return matchesRisk && matchesType;
  });

  const clauseTypes = [...new Set(analysis.clauses.map((c) => c.flagged.clause.clause_type))];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Analysis Complete</h2>
          <p className="text-gray-500 text-sm mt-1.5 flex items-center gap-2">
            <FileText className="w-3.5 h-3.5" />
            {analysis.filename} — {analysis.total_clauses} clauses identified
          </p>
        </div>
      </div>

      {/* Risk Summary Cards */}
      <RiskSummary analysis={analysis} onFilterClick={setRiskFilter} activeFilter={riskFilter} />

      {/* Tabs - underline style */}
      <div className="flex gap-6 mt-8 mb-6 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`pb-3 text-sm font-medium transition-all duration-200 relative ${
              activeTab === tab.key
                ? "text-gray-900"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            {tab.label}
            {activeTab === tab.key && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div>
          <ClauseFilter
            riskFilter={riskFilter}
            setRiskFilter={setRiskFilter}
            typeFilter={typeFilter}
            setTypeFilter={setTypeFilter}
            clauseTypes={clauseTypes}
            totalCount={analysis.clauses.length}
            filteredCount={filteredClauses.length}
          />

          <div className="space-y-3 mt-5">
            {filteredClauses.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <p className="text-lg">No clauses match the current filters</p>
                <button onClick={() => { setRiskFilter("all"); setTypeFilter("all"); }} className="mt-2 text-sm text-blue-600 hover:text-blue-800 transition-colors">
                  Clear filters
                </button>
              </div>
            ) : (
              filteredClauses.map((clause, i) => (
                <ClauseCard key={i} clause={clause} index={i} />
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === "document" && (
        <DocumentView analysis={analysis} />
      )}
    </div>
  );
}
