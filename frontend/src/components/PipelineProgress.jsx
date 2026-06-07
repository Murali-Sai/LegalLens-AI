import { FileSearch, Brain, GitCompare, AlertTriangle, MessageCircle, CheckCircle2, Loader2 } from "lucide-react";

const stepIcons = {
  extract: FileSearch,
  analyze: Brain,
  compare: GitCompare,
  flag: AlertTriangle,
  explain: MessageCircle,
};

// currentStep is the 0-based index of the step CURRENTLY running (from SSE progress events)
export default function PipelineProgress({ steps, currentStep }) {
  const progress = Math.min(((currentStep + 1) / steps.length) * 100, 100);

  return (
    <div className="flex flex-col items-center pt-20 animate-fade-in">
      <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-500/25">
        <Loader2 className="w-8 h-8 text-white animate-spin" />
      </div>
      <h2 className="text-2xl font-bold mb-2 tracking-tight">Analyzing Your Document</h2>
      <p className="text-gray-500 mb-10">Running 5-step AI reasoning pipeline</p>

      {/* Overall progress bar */}
      <div className="w-full max-w-md h-1.5 bg-gray-100 rounded-full mb-14 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Horizontal step indicators */}
      <div className="flex items-start w-full max-w-2xl">
        {steps.map((step, i) => {
          const isActive = i === currentStep;
          const isDone = i < currentStep;
          const StepIcon = stepIcons[step.key] || FileSearch;

          return (
            <div key={step.key} className="flex-1 flex flex-col items-center relative">
              {/* Connecting line */}
              {i < steps.length - 1 && (
                <div
                  className={`absolute top-5 left-1/2 w-full h-0.5 transition-colors duration-500 ${
                    isDone ? "bg-green-400" : "bg-gray-200"
                  }`}
                />
              )}
              {/* Circle */}
              <div
                className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500 ${
                  isDone
                    ? "bg-green-500 shadow-md shadow-green-500/25"
                    : isActive
                    ? "bg-blue-600 shadow-lg shadow-blue-500/30 animate-pulse-soft"
                    : "bg-gray-200"
                }`}
              >
                {isDone ? (
                  <CheckCircle2 className="w-5 h-5 text-white" />
                ) : isActive ? (
                  <StepIcon className="w-4 h-4 text-white" />
                ) : (
                  <span className="text-xs font-bold text-gray-400">{i + 1}</span>
                )}
              </div>
              {/* Label */}
              <p
                className={`text-xs font-medium mt-3 text-center transition-colors duration-300 px-1 ${
                  isActive ? "text-blue-700" : isDone ? "text-green-700" : "text-gray-400"
                }`}
              >
                {step.label}
              </p>
              {isActive && (
                <p className="text-[11px] text-blue-500 mt-1 text-center animate-fade-in">
                  {step.desc}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
