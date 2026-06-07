import { useState } from "react";
import DocumentUpload from "./components/DocumentUpload";
import AnalysisResults from "./components/AnalysisResults";
import AnalysisHistory from "./components/AnalysisHistory";
import PipelineProgress from "./components/PipelineProgress";

export const PIPELINE_STEPS = [
  { key: "extract", label: "Extracting text",        desc: "Parsing document structure..." },
  { key: "analyze", label: "Analyzing clauses",       desc: "Classifying clause types with AI..." },
  { key: "compare", label: "Benchmarking",            desc: "Comparing against legal clause database..." },
  { key: "flag",    label: "Scoring risk",            desc: "Evaluating risk levels..." },
  { key: "explain", label: "Generating explanations", desc: "Writing plain-English summaries..." },
];

export default function App() {
  const [analysis, setAnalysis]       = useState(null);
  const [loading, setLoading]         = useState(false);
  const [pipelineStep, setPipelineStep] = useState(-1);
  const [error, setError]             = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  const handleUploadStart = () => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    setPipelineStep(0);
  };

  // Called by SSE progress events — step_index is 0-based
  const handleStep = (stepIndex) => {
    setPipelineStep(stepIndex);
  };

  const handleAnalysisComplete = (result) => {
    setPipelineStep(PIPELINE_STEPS.length - 1);
    setTimeout(() => {
      setAnalysis(result);
      setLoading(false);
      setPipelineStep(-1);
    }, 600);
  };

  const handleError = (message) => {
    setLoading(false);
    setPipelineStep(-1);
    setError(message);
  };

  const reset = () => {
    setAnalysis(null);
    setError(null);
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 px-6 py-3.5 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-indigo-600 via-blue-600 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/25 ring-1 ring-black/5">
              <span className="text-white font-bold text-sm tracking-tight">LL</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold leading-tight tracking-tight">LegalLens</h1>
              <span className="text-xs text-gray-400">AI Contract Analyst</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {(analysis || error) && (
              <button
                onClick={reset}
                className="px-4 py-2 text-sm font-medium bg-gray-900 text-white hover:bg-gray-800 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
              >
                New Analysis
              </button>
            )}
            <button
              onClick={() => setShowHistory((v) => !v)}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200"
            >
              History
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        {loading ? (
          <PipelineProgress steps={PIPELINE_STEPS} currentStep={pipelineStep} />
        ) : error ? (
          <ErrorView message={error} onReset={reset} />
        ) : analysis ? (
          <AnalysisResults analysis={analysis} onReset={reset} />
        ) : showHistory ? (
          <AnalysisHistory onSelect={setAnalysis} onClose={() => setShowHistory(false)} />
        ) : (
          <DocumentUpload
            onUploadStart={handleUploadStart}
            onStep={handleStep}
            onAnalysisComplete={handleAnalysisComplete}
            onError={handleError}
          />
        )}
      </main>

      <footer className="text-center text-xs text-gray-400 py-6 border-t border-gray-100/60">
        This tool provides informational analysis only — not legal advice. Always consult a qualified attorney.
      </footer>
    </div>
  );
}

function ErrorView({ message, onReset }) {
  return (
    <div className="flex flex-col items-center justify-center pt-24 animate-fade-in">
      <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mb-5 ring-1 ring-red-100">
        <span className="text-2xl">⚠</span>
      </div>
      <h2 className="text-xl font-semibold mb-2 text-gray-900">Analysis Failed</h2>
      <p className="text-gray-500 text-sm mb-6 max-w-md text-center">{message}</p>
      <button
        onClick={onReset}
        className="px-6 py-2.5 text-sm font-medium bg-gray-900 text-white hover:bg-gray-800 rounded-lg transition-all duration-200 shadow-sm"
      >
        Try Again
      </button>
    </div>
  );
}
