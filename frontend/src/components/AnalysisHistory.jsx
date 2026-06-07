import { useEffect, useState } from "react";
import { FileText, AlertTriangle, Clock, X } from "lucide-react";
import { listAnalyses, getAnalysis } from "../utils/api";

export default function AnalysisHistory({ onSelect, onClose }) {
  const [items, setItems]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    listAnalyses()
      .then(setItems)
      .catch(() => setError("Could not load history"))
      .finally(() => setLoading(false));
  }, []);

  const handleOpen = async (documentId) => {
    try {
      const result = await getAnalysis(documentId);
      onSelect(result);
    } catch {
      setError("Could not load that analysis");
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold tracking-tight">Analysis History</h2>
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {loading && (
        <div className="text-center py-16 text-gray-400">Loading history…</div>
      )}

      {error && (
        <div className="text-center py-16 text-red-500">{error}</div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <FileText className="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p>No analyses yet. Upload a contract to get started.</p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => (
            <button
              key={item.document_id}
              onClick={() => handleOpen(item.document_id)}
              className="w-full text-left bg-white border border-gray-100 rounded-xl p-5 shadow-sm hover:shadow-md hover:border-gray-200 transition-all duration-200 hover:-translate-y-0.5 group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4 text-gray-400 shrink-0" />
                    <span className="font-medium text-gray-900 truncate">{item.filename}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(item.created_at)}
                    </span>
                    <span>{item.total_clauses} clauses</span>
                  </div>
                </div>
                <RiskBadges item={item} />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function RiskBadges({ item }) {
  return (
    <div className="flex items-center gap-1.5 shrink-0">
      {item.high_risk_count > 0 && (
        <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 bg-red-100 text-red-700 rounded-full">
          <AlertTriangle className="w-3 h-3" />
          {item.high_risk_count}
        </span>
      )}
      {item.medium_risk_count > 0 && (
        <span className="text-xs font-medium px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
          {item.medium_risk_count}
        </span>
      )}
      {item.low_risk_count > 0 && (
        <span className="text-xs font-medium px-2 py-0.5 bg-green-100 text-green-700 rounded-full">
          {item.low_risk_count}
        </span>
      )}
    </div>
  );
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
