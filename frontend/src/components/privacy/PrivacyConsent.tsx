import React from "react";
import { ShieldCheck, EyeOff, Lock, CheckCircle2 } from "lucide-react";

interface PrivacyConsentProps {
  onAccept: () => void;
  onDecline: () => void;
}

export function PrivacyConsent({ onAccept, onDecline }: PrivacyConsentProps) {
  return (
    <div className="relative z-10 w-full animate-fade-in bg-white/70 backdrop-blur-2xl rounded-3xl p-6 sm:p-8 border border-white/50 shadow-xl mb-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2.5 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-center justify-center">
          <ShieldCheck className="w-6 h-6 text-emerald-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-800">
            Privacy-First Camera Consent
          </h3>
          <p className="text-xs text-slate-500 font-medium">
            100% Local Real-Time Emotion Assistant
          </p>
        </div>
      </div>

      <p className="text-slate-600 text-sm leading-relaxed mb-5">
        To support you with deeper empathy, NeuroNest can analyze your facial cues to understand your feelings in real-time. Your safety and privacy are our top priorities:
      </p>

      <div className="space-y-3 mb-6">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-slate-600 leading-normal">
            <strong className="text-slate-800">Local Frame Processing:</strong> Camera frames are processed strictly in your browser. Video bytes never leave your device.
          </div>
        </div>
        <div className="flex items-start gap-3">
          <EyeOff className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-slate-600 leading-normal">
            <strong className="text-slate-800">Coordinates Stripped:</strong> Raw 3D coordinates or geometry grids are completely discarded. Only high-level emotion scores are analyzed.
          </div>
        </div>
        <div className="flex items-start gap-3">
          <Lock className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-slate-600 leading-normal">
            <strong className="text-slate-800">Compliant Design:</strong> No photos, videos, or coordinate mappings are saved or stored.
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={onAccept}
          className="flex-1 py-3 px-5 text-sm font-bold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 rounded-2xl shadow-md hover:shadow-lg transition-all duration-200 active:scale-[0.98]"
        >
          Enable Camera Assistant
        </button>
        <button
          onClick={onDecline}
          className="py-3 px-5 text-sm font-bold text-slate-500 hover:text-slate-700 hover:bg-slate-50/50 rounded-2xl border border-slate-200/60 transition-all duration-200"
        >
          Voice Only
        </button>
      </div>
    </div>
  );
}
