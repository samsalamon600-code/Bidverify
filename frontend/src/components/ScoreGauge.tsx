'use client';

import React from 'react';
import { ShieldCheck, AlertTriangle, CheckCheck, FileSearch, Sparkles } from 'lucide-react';

interface ScoreGaugeGroupProps {
  complianceScore: number;
  riskScore: number;
  matchScore: number;
  ocrConfidence: number;
  anomalyScore: number;
  anomalyStatus?: string;
  riskLevel?: string;
}

export default function ScoreGaugeGroup({
  complianceScore = 0,
  riskScore = 0,
  matchScore = 0,
  ocrConfidence = 0,
  anomalyScore = 0,
  anomalyStatus = 'LOW ANOMALY',
  riskLevel = 'LOW',
}: ScoreGaugeGroupProps) {
  // Color decisions based on enterprise thresholds
  const getComplianceColor = (val: number) => {
    if (val >= 85) return { bg: 'bg-emerald-500', text: 'text-emerald-700', badge: 'bg-emerald-100 border-emerald-200' };
    if (val >= 60) return { bg: 'bg-amber-500', text: 'text-amber-700', badge: 'bg-amber-100 border-amber-200' };
    return { bg: 'bg-rose-500', text: 'text-rose-700', badge: 'bg-rose-100 border-rose-200' };
  };

  const getRiskColor = (val: number) => {
    if (val <= 30) return { bg: 'bg-emerald-500', text: 'text-emerald-700', badge: 'bg-emerald-100 border-emerald-200' };
    if (val <= 60) return { bg: 'bg-amber-500', text: 'text-amber-700', badge: 'bg-amber-100 border-amber-200' };
    return { bg: 'bg-rose-500', text: 'text-rose-700', badge: 'bg-rose-100 border-rose-200' };
  };

  const getAnomalyColor = (val: number) => {
    if (val < 0.35) return { bg: 'bg-emerald-500', text: 'text-emerald-700', badge: 'bg-emerald-100 border-emerald-200' };
    if (val < 0.65) return { bg: 'bg-amber-500', text: 'text-amber-700', badge: 'bg-amber-100 border-amber-200' };
    return { bg: 'bg-rose-500', text: 'text-rose-700', badge: 'bg-rose-100 border-rose-200' };
  };

  const compStyles = getComplianceColor(complianceScore);
  const riskStyles = getRiskColor(riskScore);
  const anomalyStyles = getAnomalyColor(anomalyScore);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* 1. Compliance Score */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Compliance</span>
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
        </div>
        <div className="flex items-baseline gap-1 mb-2">
          <span className="text-2xl font-bold text-slate-900">{complianceScore.toFixed(1)}</span>
          <span className="text-xs text-slate-400 font-medium">/ 100</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
          <div
            className={`h-full rounded-full transition-all duration-700 ${compStyles.bg}`}
            style={{ width: `${Math.min(100, Math.max(0, complianceScore))}%` }}
          />
        </div>
        <span className={`inline-block text-[11px] font-semibold px-2 py-0.5 rounded border ${compStyles.badge} ${compStyles.text}`}>
          {complianceScore >= 85 ? 'Fully Compliant' : complianceScore >= 60 ? 'Requires Review' : 'Non-Compliant'}
        </span>
      </div>

      {/* 2. Risk Score */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Risk Score</span>
          <AlertTriangle className="h-4 w-4 text-amber-500" />
        </div>
        <div className="flex items-baseline gap-1 mb-2">
          <span className="text-2xl font-bold text-slate-900">{riskScore.toFixed(1)}</span>
          <span className="text-xs text-slate-400 font-medium">/ 100</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
          <div
            className={`h-full rounded-full transition-all duration-700 ${riskStyles.bg}`}
            style={{ width: `${Math.min(100, Math.max(0, riskScore))}%` }}
          />
        </div>
        <span className={`inline-block text-[11px] font-semibold px-2 py-0.5 rounded border ${riskStyles.badge} ${riskStyles.text}`}>
          {riskLevel || (riskScore <= 30 ? 'LOW RISK' : riskScore <= 60 ? 'MEDIUM RISK' : 'HIGH RISK')}
        </span>
      </div>

      {/* 3. Data Match Score */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Data Match</span>
          <CheckCheck className="h-4 w-4 text-blue-600" />
        </div>
        <div className="flex items-baseline gap-1 mb-2">
          <span className="text-2xl font-bold text-slate-900">{matchScore.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
          <div
            className="h-full rounded-full bg-blue-600 transition-all duration-700"
            style={{ width: `${Math.min(100, Math.max(0, matchScore))}%` }}
          />
        </div>
        <span className="inline-block text-[11px] font-semibold px-2 py-0.5 rounded border bg-blue-50 border-blue-200 text-blue-700">
          Cross-Registry Match
        </span>
      </div>

      {/* 4. OCR Confidence */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">OCR Confidence</span>
          <FileSearch className="h-4 w-4 text-indigo-600" />
        </div>
        <div className="flex items-baseline gap-1 mb-2">
          <span className="text-2xl font-bold text-slate-900">{ocrConfidence.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
          <div
            className="h-full rounded-full bg-indigo-600 transition-all duration-700"
            style={{ width: `${Math.min(100, Math.max(0, ocrConfidence))}%` }}
          />
        </div>
        <span className="inline-block text-[11px] font-semibold px-2 py-0.5 rounded border bg-indigo-50 border-indigo-200 text-indigo-700">
          Scan Clarity Score
        </span>
      </div>

      {/* 5. ML Anomaly Score */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">ML Anomaly</span>
          <Sparkles className="h-4 w-4 text-violet-600" />
        </div>
        <div className="flex items-baseline gap-1 mb-2">
          <span className="text-2xl font-bold text-slate-900">{anomalyScore.toFixed(2)}</span>
          <span className="text-xs text-slate-400 font-medium">[0.0–1.0]</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
          <div
            className={`h-full rounded-full transition-all duration-700 ${anomalyStyles.bg}`}
            style={{ width: `${Math.min(100, Math.max(0, anomalyScore * 100))}%` }}
          />
        </div>
        <span className={`inline-block text-[11px] font-semibold px-2 py-0.5 rounded border ${anomalyStyles.badge} ${anomalyStyles.text}`}>
          {anomalyStatus}
        </span>
      </div>
    </div>
  );
}
