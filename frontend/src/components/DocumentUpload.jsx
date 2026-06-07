import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Shield, MessageSquare, Brain, Play } from "lucide-react";
import { uploadAndStream, streamDemo } from "../utils/api";

const FEATURES = [
  { title: "Clause Detection",          desc: "Identifies liability, termination, IP, payment, and confidentiality clauses", icon: FileText },
  { title: "Risk Scoring",              desc: "Rates each clause as low, medium, or high risk with reasoning",               icon: Shield },
  { title: "Plain-English Explanations",desc: "Translates legal jargon into simple language anyone can understand",          icon: MessageSquare },
  { title: "Actionable Recommendations",desc: "Specific advice on what to negotiate, accept, or flag for a lawyer",          icon: Brain },
];

const DOC_TYPES = ["Leases", "NDAs", "Employment Agreements", "Service Contracts"];

export default function DocumentUpload({ onUploadStart, onStep, onAnalysisComplete, onError }) {
  const callbacks = { onStep, onComplete: onAnalysisComplete, onError };

  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;
      onUploadStart();
      await uploadAndStream(acceptedFiles[0], callbacks);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [onUploadStart, onStep, onAnalysisComplete, onError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
  });

  const handleDemo = async () => {
    onUploadStart();
    await streamDemo(callbacks);
  };

  return (
    <div className="flex flex-col items-center gap-12 pt-16 animate-fade-in">
      <div className="text-center max-w-xl">
        <h2 className="text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-600 bg-clip-text text-transparent tracking-tight leading-tight">
          Understand Your Contract
        </h2>
        <p className="text-gray-500 text-lg leading-relaxed max-w-md mx-auto">
          Upload a legal document and get AI-powered analysis with plain-English explanations,
          risk scoring, and recommended actions for every clause.
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`group w-full max-w-lg rounded-2xl p-14 text-center cursor-pointer transition-all duration-300 relative overflow-hidden ${
          isDragActive
            ? "border-blue-400 bg-blue-50/50 shadow-xl shadow-blue-500/10 scale-[1.02]"
            : "border border-gray-200/80 bg-white shadow-sm hover:shadow-xl hover:shadow-blue-500/5 hover:border-blue-300"
        }`}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/0 via-transparent to-indigo-50/0 group-hover:from-blue-50/50 group-hover:to-indigo-50/30 transition-all duration-500 pointer-events-none" />
        <input {...getInputProps()} />
        <div className="relative z-10">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-5 group-hover:scale-110 transition-transform duration-300 ring-1 ring-blue-100">
            <Upload className="w-6 h-6 text-blue-600" />
          </div>
          <p className="text-lg font-semibold mb-1">
            {isDragActive ? "Drop your document here" : "Drag & drop a contract"}
          </p>
          <p className="text-sm text-gray-500 mb-3">or click to browse files</p>
          <p className="text-xs text-gray-400">Supports PDF and DOCX up to 20MB</p>
        </div>
      </div>

      {/* Demo button */}
      <div className="flex flex-col items-center gap-2">
        <p className="text-xs text-gray-400">No contract handy?</p>
        <button
          onClick={handleDemo}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 hover:border-blue-300 rounded-xl transition-all duration-200 hover:shadow-md hover:shadow-blue-500/10 active:scale-[0.98]"
        >
          <Play className="w-4 h-4" />
          Try with a sample contract
        </button>
      </div>

      <div className="w-full max-w-2xl">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-5 text-center">
          What you&apos;ll get
        </h3>
        <div className="grid grid-cols-2 gap-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="group/card bg-white border border-gray-100 rounded-xl p-5 shadow-sm hover:shadow-md hover:border-gray-200 transition-all duration-300 hover:-translate-y-0.5"
            >
              <div className="w-9 h-9 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg flex items-center justify-center mb-3 ring-1 ring-blue-100/50 group-hover/card:ring-blue-200/80 transition-all duration-300">
                <f.icon className="w-4 h-4 text-blue-600" />
              </div>
              <h4 className="font-semibold text-sm mb-1 text-gray-900">{f.title}</h4>
              <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap justify-center">
        {DOC_TYPES.map((tag) => (
          <span key={tag} className="text-xs text-gray-400 bg-gray-100/80 px-3 py-1 rounded-full">
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
