'use client';

import React, { useEffect, useState } from 'react';
import {
  Sliders,
  CheckCircle2,
  Database,
  Save,
  RefreshCw,
  AlertCircle,
  HelpCircle
} from 'lucide-react';
import { api } from '@/services/api';

export default function SettingsPage() {
  const [weights, setWeights] = useState({
    weight_identity_mismatch: 0.25,
    weight_document_issues: 0.20,
    weight_registration_issues: 0.20,
    weight_address_mismatch: 0.15,
    weight_ml_anomaly: 0.10,
    weight_missing_info: 0.10,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    const loadWeights = async () => {
      try {
        const data = await api.getWeights();
        setWeights(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadWeights();
  }, []);

  const handleWeightChange = (key: string, val: number) => {
    setWeights((prev) => ({ ...prev, [key]: val }));
    setSavedSuccess(false);
  };

  const totalPercent = Math.round(
    Object.values(weights).reduce((acc, v) => acc + v, 0) * 100
  );

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);
    try {
      await api.updateWeights(weights);
      setSavedSuccess(true);
    } catch (err: any) {
      alert(err.message || 'Failed to update weights');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-slate-900">System Configuration & Scoring Weights</h2>
        <p className="text-xs text-slate-500 mt-1">
          Adjust the relative mathematical weights assigned by the Risk Engine during vendor evaluation.
        </p>
      </div>

      <form onSubmit={handleSave} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Multi-Factor Risk Weights</h3>
            <p className="text-xs text-slate-500">Total must ideally equal 100%</p>
          </div>
          <span
            className={`text-xs font-bold px-3 py-1 rounded-full border ${
              totalPercent === 100
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
          >
            Total Allocation: {totalPercent}%
          </span>
        </div>

        {savedSuccess && (
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" /> Scoring weights successfully updated in the engine.
          </div>
        )}

        <div className="space-y-4">
          {/* Identity Mismatch */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-800">1. Identity Mismatch (Legal Name, PAN, GSTIN)</span>
              <span className="text-slate-900 font-bold">{Math.round(weights.weight_identity_mismatch * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="1"
              value={Math.round(weights.weight_identity_mismatch * 100)}
              onChange={(e) => handleWeightChange('weight_identity_mismatch', Number(e.target.value) / 100)}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>

          {/* Document Issues */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-800">2. Document Completeness & Mandatory Docs</span>
              <span className="text-slate-900 font-bold">{Math.round(weights.weight_document_issues * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="1"
              value={Math.round(weights.weight_document_issues * 100)}
              onChange={(e) => handleWeightChange('weight_document_issues', Number(e.target.value) / 100)}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>

          {/* Registration Issues */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-800">3. Official Registration Status (Active vs Suspended)</span>
              <span className="text-slate-900 font-bold">{Math.round(weights.weight_registration_issues * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="1"
              value={Math.round(weights.weight_registration_issues * 100)}
              onChange={(e) => handleWeightChange('weight_registration_issues', Number(e.target.value) / 100)}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>

          {/* Address Mismatch */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-800">4. Physical Address Alignment & Discrepancies</span>
              <span className="text-slate-900 font-bold">{Math.round(weights.weight_address_mismatch * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="1"
              value={Math.round(weights.weight_address_mismatch * 100)}
              onChange={(e) => handleWeightChange('weight_address_mismatch', Number(e.target.value) / 100)}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>

          {/* ML Anomaly */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-800">5. Machine Learning Anomaly Score (Isolation Forest)</span>
              <span className="text-slate-900 font-bold">{Math.round(weights.weight_ml_anomaly * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="30"
              step="1"
              value={Math.round(weights.weight_ml_anomaly * 100)}
              onChange={(e) => handleWeightChange('weight_ml_anomaly', Number(e.target.value) / 100)}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>

          {/* Missing Info */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-800">6. Missing Secondary Information (CIN, Udyam, Phone)</span>
              <span className="text-slate-900 font-bold">{Math.round(weights.weight_missing_info * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="30"
              step="1"
              value={Math.round(weights.weight_missing_info * 100)}
              onChange={(e) => handleWeightChange('weight_missing_info', Number(e.target.value) / 100)}
              className="w-full accent-indigo-600 cursor-pointer"
            />
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t border-slate-100">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            {saving ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" /> Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" /> Save Weights Configuration
              </>
            )}
          </button>
        </div>
      </form>

      {/* Mock Government Verification Notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-xs text-amber-900 space-y-2">
        <div className="flex items-center gap-2 font-bold text-sm text-amber-950">
          <Database className="h-4 w-4 text-amber-700" />
          MOCK GOVERNMENT VERIFICATION REGISTRY STATUS
        </div>
        <p>
          The platform currently connects to a simulated high-fidelity mock environment replicating Indian Government verification portals: <b>GSTN</b>, <b>Udyam MSME Registry</b>, and <b>MCA21 (Ministry of Corporate Affairs)</b>.
        </p>
        <p className="text-amber-800 text-[11px]">
          Architecture notice: All mock endpoints strictly adhere to standard government API schemas so production credentials and authorized GSP/ASP gateways can be substituted via environment variables without modifying core logic.
        </p>
      </div>
    </div>
  );
}
