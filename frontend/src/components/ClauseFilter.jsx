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

export default function ClauseFilter({
  riskFilter,
  setRiskFilter,
  typeFilter,
  setTypeFilter,
  clauseTypes,
  totalCount,
  filteredCount,
}) {
  return (
    <div className="flex items-center justify-between flex-wrap gap-3 bg-white rounded-xl border border-gray-100 px-4 py-3 shadow-sm">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-gray-500 mr-1">Filter:</span>

        {/* Risk filter pills */}
        {["all", "high", "medium", "low"].map((level) => (
          <button
            key={level}
            onClick={() => setRiskFilter(level)}
            className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all duration-200 hover:scale-105 ${
              riskFilter === level
                ? level === "high"
                  ? "bg-red-100 text-red-700"
                  : level === "medium"
                  ? "bg-amber-100 text-amber-700"
                  : level === "low"
                  ? "bg-green-100 text-green-700"
                  : "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {level === "all" ? "All Risks" : `${level.charAt(0).toUpperCase() + level.slice(1)} Risk`}
          </button>
        ))}

        <span className="w-px h-5 bg-gray-200 mx-1" />

        {/* Type filter dropdown */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 bg-gray-50 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 transition-all duration-200 cursor-pointer"
        >
          <option value="all">All Types</option>
          {clauseTypes.map((type) => (
            <option key={type} value={type}>
              {CLAUSE_TYPE_LABELS[type] || type}
            </option>
          ))}
        </select>
      </div>

      <span className="text-xs text-gray-400 font-medium tabular-nums">
        Showing {filteredCount} of {totalCount} clauses
      </span>
    </div>
  );
}
