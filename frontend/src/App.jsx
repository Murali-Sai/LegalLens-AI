import { useState, useRef } from "react";
import DocumentUpload from "./components/DocumentUpload";
import AnalysisResults from "./components/AnalysisResults";
import PipelineProgress from "./components/PipelineProgress";

const PIPELINE_STEPS = [
  { key: "extract", label: "Extracting text", desc: "Parsing document structure..." },
  { key: "analyze", label: "Analyzing clauses", desc: "Classifying clause types with AI..." },
  { key: "compare", label: "Benchmarking", desc: "Comparing against legal clause database..." },
  { key: "flag", label: "Scoring risk", desc: "Evaluating risk levels..." },
  { key: "explain", label: "Generating explanations", desc: "Writing plain-English summaries..." },
];

export default function App() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(-1);
  const intervalRef = useRef(null);
  const pendingResultRef = useRef(null);

  const handleUploadStart = () => {
    setLoading(true);
    setPipelineStep(0);
    pendingResultRef.current = null;
    // Simulate pipeline progress (actual backend processes all at once)
    intervalRef.current = setInterval(() => {
      setPipelineStep((prev) => {
        if (prev >= PIPELINE_STEPS.length - 1) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
          // If result already arrived, show it now
          if (pendingResultRef.current) {
            const result = pendingResultRef.current;
            pendingResultRef.current = null;
            setTimeout(() => {
              setAnalysis(result);
              setLoading(false);
              setPipelineStep(-1);
            }, 800);
          }
          return prev;
        }
        return prev + 1;
      });
    }, 2000);
  };

  const handleAnalysisComplete = (result) => {
    // If timer is still running, store result and let timer finish naturally
    if (intervalRef.current) {
      pendingResultRef.current = result;
      // Speed up remaining steps
      clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        setPipelineStep((prev) => {
          if (prev >= PIPELINE_STEPS.length - 1) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
            setTimeout(() => {
              setAnalysis(result);
              setLoading(false);
              setPipelineStep(-1);
            }, 800);
            return prev;
          }
          return prev + 1;
        });
      }, 600);
    } else {
      // Timer already done, show result immediately
      setPipelineStep(PIPELINE_STEPS.length - 1);
      setTimeout(() => {
        setAnalysis(result);
        setLoading(false);
        setPipelineStep(-1);
      }, 800);
    }
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
          {analysis && (
            <button
              onClick={() => setAnalysis(null)}
              className="px-4 py-2 text-sm font-medium bg-gray-900 text-white hover:bg-gray-800 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
            >
              New Analysis
            </button>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        {loading ? (
          <PipelineProgress steps={PIPELINE_STEPS} currentStep={pipelineStep} />
        ) : analysis ? (
          <AnalysisResults analysis={analysis} onReset={() => setAnalysis(null)} />
        ) : (
          <DocumentUpload
            onAnalysisComplete={handleAnalysisComplete}
            onUploadStart={handleUploadStart}
          />
        )}
      </main>

      <footer className="text-center text-xs text-gray-400 py-6 border-t border-gray-100/60">
        This tool provides informational analysis only — not legal advice. Always consult a qualified attorney.
      </footer>
    </div>
  );
}
