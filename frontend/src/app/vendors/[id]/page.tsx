'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ShieldCheck,
  AlertTriangle,
  Play,
  FileDown,
  History,
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  Sparkles,
  Building2,
  MapPin,
  Mail,
  Phone,
  ArrowLeft,
  RefreshCw,
  Info,
  FileText,
  UploadCloud,
  Clock,
  Layers,
  CheckSquare,
  Cpu,
  Trash2
} from 'lucide-react';
import { api } from '@/services/api';
import { Vendor, DocumentItem, AuditLogItem } from '@/types';
import ScoreGaugeGroup from '@/components/ScoreGauge';
import DocumentUploader from '@/components/DocumentUploader';

type TabType = 'overview' | 'documents' | 'matrix' | 'anomaly' | 'audit';

export default function VendorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vendorId = params?.id as string;

  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [inspectDocJson, setInspectDocJson] = useState<any | null>(null);
  const [needsReverification, setNeedsReverification] = useState(false);

  const fetchVendorDetails = async () => {
    setLoading(true);
    try {
      const [vData, docs, logs] = await Promise.all([
        api.getVendor(vendorId),
        api.getVendorDocuments(vendorId).catch(() => []),
        api.getAuditTrail(vendorId).catch(() => []),
      ]);
      setVendor(vData);
      setDocuments(docs);
      setAuditLogs(logs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (vendorId) {
      fetchVendorDetails();
    }
  }, [vendorId]);

  const handleRunVerification = async () => {
    setIsVerifying(true);
    try {
      await api.verifyVendor(vendorId);
      await fetchVendorDetails();
      setNeedsReverification(false);
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDownloadPdf = async () => {
    setIsGeneratingReport(true);
    try {
      await api.generateReport(vendorId);
      window.open(api.getReportDownloadUrl(vendorId), '_blank');
    } catch (err: any) {
      alert(err.message || 'Report generation failed');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const handleDeleteDocument = async (docId: number) => {
    if (!confirm('Are you sure you want to remove this document?')) return;
    try {
      await api.deleteDocument(docId);
      await fetchVendorDetails();
      setNeedsReverification(true);
    } catch (err: any) {
      alert(err.message || 'Failed to delete document');
    }
  };

  if (loading || !vendor) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-2 text-xs font-semibold text-slate-500">
          <RefreshCw className="h-6 w-6 animate-spin text-emerald-600" />
          Loading Verification Dossier...
        </div>
      </div>
    );
  }

  const verifStatus = vendor.verification_status;
  const statusColor =
    verifStatus === 'Verified'
      ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
      : verifStatus === 'Partially Verified'
      ? 'bg-blue-50 text-blue-700 border-blue-300'
      : verifStatus === 'Requires Review'
      ? 'bg-amber-50 text-amber-700 border-amber-300'
      : 'bg-rose-50 text-rose-700 border-rose-300';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Back Nav & Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          href="/vendors"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Vendors Directory
        </Link>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleRunVerification}
            disabled={isVerifying}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            {isVerifying ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Executing Verification...
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5" />
                Re-Run Verification
              </>
            )}
          </button>

          <button
            onClick={handleDownloadPdf}
            disabled={isGeneratingReport}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            {isGeneratingReport ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Generating PDF...
              </>
            ) : (
              <>
                <FileDown className="h-3.5 w-3.5" />
                Download Official PDF Report
              </>
            )}
          </button>
        </div>
      </div>

      {/* Reverification Notification Banner */}
      {needsReverification && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
            <span>Document changes detected. Re-run verification to update compliance & risk scores.</span>
          </div>
          <button
            onClick={handleRunVerification}
            disabled={isVerifying}
            className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition-colors"
          >
            Run Now
          </button>
        </div>
      )}

      {/* 1. Vendor Identity & Status Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-slate-900">{vendor.name}</h2>
              <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${statusColor}`}>
                {verifStatus}
              </span>
            </div>
            {vendor.legal_name && vendor.legal_name !== vendor.name && (
              <p className="text-xs text-slate-500 mt-0.5">
                Legal Entity: <span className="font-semibold text-slate-700">{vendor.legal_name}</span>
              </p>
            )}
            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              {vendor.address || 'Address Not Recorded'}
            </p>
          </div>

          <div className="text-right">
            <span className="text-[11px] font-semibold text-slate-400 block uppercase">Vendor ID</span>
            <span className="text-sm font-mono font-bold text-slate-900">BID-VN-{vendor.id.toString().padStart(4, '0')}</span>
            <p className="text-[11px] text-slate-400 mt-1">
              Last Verified: {vendor.last_verified ? new Date(vendor.last_verified).toLocaleString() : 'Pending'}
            </p>
          </div>
        </div>

        {/* Corporate Metadata Pills */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-100 text-xs">
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <span className="text-slate-400 font-semibold block mb-0.5 text-[10px] uppercase">GSTIN (Registry)</span>
            <span className="font-mono font-bold text-slate-800">{vendor.gstin || 'Not Provided'}</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <span className="text-slate-400 font-semibold block mb-0.5 text-[10px] uppercase">PAN</span>
            <span className="font-mono font-bold text-slate-800">{vendor.pan || 'Not Provided'}</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <span className="text-slate-400 font-semibold block mb-0.5 text-[10px] uppercase">CIN</span>
            <span className="font-mono font-bold text-slate-800">{vendor.cin || 'N/A'}</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <span className="text-slate-400 font-semibold block mb-0.5 text-[10px] uppercase">Udyam Registration</span>
            <span className="font-mono font-bold text-slate-800">{vendor.udyam_number || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Navigation Tab Switcher */}
      <div className="flex border-b border-slate-200 bg-white rounded-xl p-1 shadow-2xs gap-1">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'overview'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          Executive Overview & Scores
        </button>

        <button
          onClick={() => setActiveTab('documents')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'documents'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <FileText className="h-3.5 w-3.5" />
          Documents & Evidence OCR ({documents.length})
        </button>

        <button
          onClick={() => setActiveTab('matrix')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'matrix'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <CheckSquare className="h-3.5 w-3.5" />
          Registry Match & Rules Matrix
        </button>

        <button
          onClick={() => setActiveTab('anomaly')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'anomaly'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Cpu className="h-3.5 w-3.5" />
          AI Anomaly Engine
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'audit'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <History className="h-3.5 w-3.5" />
          Audit Trail ({auditLogs.length})
        </button>
      </div>

      {/* TAB 1: OVERVIEW & 5 SCORES */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 5 Distinct Scores */}
          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              Independent Scoring Dimensions
            </h3>
            <ScoreGaugeGroup
              complianceScore={vendor.compliance_score}
              riskScore={vendor.risk_score}
              matchScore={vendor.match_score}
              ocrConfidence={vendor.ocr_confidence}
              anomalyScore={vendor.anomaly_score}
              anomalyStatus={vendor.anomaly_status}
              riskLevel={vendor.risk_level}
            />
          </div>

          {/* Recommended Action & Explainability */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-blue-900 font-bold text-sm">
              <ShieldCheck className="h-5 w-5 text-blue-600" />
              Recommended Procurement Action
            </div>

            <p className="text-sm font-semibold text-slate-800">
              {vendor.recommended_action || 'Proceed to standard procurement review.'}
            </p>

            <div className="pt-4 border-t border-blue-200/60">
              <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <HelpCircle className="h-3.5 w-3.5" /> Why This Result?
              </h4>
              <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                {vendor.risk_assessment?.explanations?.map((exp, idx) => (
                  <li key={idx}>{exp}</li>
                )) || <li>All required identity documents and portal cross-checks validated cleanly.</li>}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DOCUMENTS & EVIDENCE OCR */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          {/* Embedded Document Uploader */}
          <DocumentUploader
            vendorId={vendor.id}
            onUploadSuccess={() => {
              fetchVendorDetails();
              setNeedsReverification(true);
            }}
            onExtractSuccess={() => {
              fetchVendorDetails();
              setNeedsReverification(true);
            }}
          />

          {/* Uploaded Documents List */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Uploaded Compliance Documents ({documents.length})
                </h3>
                <p className="text-xs text-slate-500">Verified evidence attached to this vendor record</p>
              </div>
              <button
                onClick={fetchVendorDetails}
                className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1"
              >
                <RefreshCw className="h-3 w-3" /> Refresh
              </button>
            </div>

            {documents.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-xs">
                <FileText className="h-8 w-8 mx-auto text-slate-300 mb-2" />
                No documents uploaded for this vendor yet. Use the uploader or sample buttons above.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider border-b border-slate-200 font-semibold">
                    <tr>
                      <th className="py-3 px-4">Document Name</th>
                      <th className="py-3 px-4">Category</th>
                      <th className="py-3 px-4">Size</th>
                      <th className="py-3 px-4">OCR Confidence</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {documents.map((doc) => (
                      <tr key={doc.id} className="hover:bg-slate-50/80">
                        <td className="py-3 px-4 font-semibold text-slate-900 flex items-center gap-2">
                          <FileText className="h-4 w-4 text-emerald-600 shrink-0" />
                          <span className="truncate max-w-xs">{doc.file_name}</span>
                        </td>
                        <td className="py-3 px-4 text-slate-700">{doc.doc_type}</td>
                        <td className="py-3 px-4 text-slate-500">{(doc.file_size / 1024).toFixed(1)} KB</td>
                        <td className="py-3 px-4">
                          <span className="font-bold text-emerald-700">{doc.ocr_confidence.toFixed(1)}%</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            {doc.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => setInspectDocJson(doc.extracted_data || { message: 'No structured data available' })}
                              className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px]"
                            >
                              View JSON
                            </button>
                            <button
                              onClick={() => handleDeleteDocument(doc.id)}
                              className="p-1 text-slate-400 hover:text-rose-600 rounded"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* JSON Inspection Modal/Drawer */}
          {inspectDocJson && (
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 text-xs text-white space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-emerald-400 uppercase tracking-wider">
                  Extracted JSON Evidence
                </span>
                <button
                  onClick={() => setInspectDocJson(null)}
                  className="text-slate-400 hover:text-white font-bold"
                >
                  Close ✕
                </button>
              </div>
              <pre className="p-4 rounded-xl bg-slate-900 text-emerald-300 font-mono text-[11px] overflow-x-auto max-h-80">
                {JSON.stringify(inspectDocJson, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: REGISTRY MATCH & RULES MATRIX */}
      {activeTab === 'matrix' && (
        <div className="space-y-6">
          {/* Cross-Verification Matrix */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Cross-Verification & Registry Match Matrix</h3>
                <p className="text-xs text-slate-500">
                  Extracted document data vs Mock Government Registry (GSTN / Udyam / MCA21)
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-600 border border-slate-200">
                RapidFuzz Matching
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider border-y border-slate-200 font-semibold">
                  <tr>
                    <th className="py-3 px-4">Verification Field</th>
                    <th className="py-3 px-4">Document Value (OCR)</th>
                    <th className="py-3 px-4">Government Source Record</th>
                    <th className="py-3 px-4">Match Status</th>
                    <th className="py-3 px-4">Similarity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {vendor.verification_results && vendor.verification_results.length > 0 ? (
                    vendor.verification_results.map((res, i) => (
                      <tr key={i} className="hover:bg-slate-50/60">
                        <td className="py-3 px-4 font-bold text-slate-800">{res.field_name}</td>
                        <td className="py-3 px-4 font-mono text-slate-600 max-w-xs truncate">{res.doc_value || '—'}</td>
                        <td className="py-3 px-4 font-mono text-slate-600 max-w-xs truncate">{res.portal_value || '—'}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold ${
                              res.match_type === 'EXACT'
                                ? 'bg-emerald-50 text-emerald-700'
                                : res.match_type === 'PARTIAL'
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-rose-50 text-rose-700'
                            }`}
                          >
                            {res.match_type === 'EXACT' ? <CheckCircle2 className="h-3 w-3" /> : res.match_type === 'PARTIAL' ? <AlertCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                            {res.match_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-bold text-slate-900">{res.similarity_score}%</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-slate-400">
                        No verification records logged. Click "Re-Run Verification" above to execute.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Compliance Rules and Risk Factors Side-by-Side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Deterministic Compliance Checklist */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Deterministic Compliance Rules</h3>
                <p className="text-xs text-slate-500">Evaluation against official procurement criteria</p>
              </div>

              <div className="space-y-2.5">
                {vendor.compliance_checks && vendor.compliance_checks.length > 0 ? (
                  vendor.compliance_checks.map((chk, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                      {chk.status === 'PASS' ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      ) : chk.status === 'REVIEW' ? (
                        <AlertCircle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <span className="font-bold text-slate-900 block">{chk.check_name}</span>
                        <span className="text-slate-500 text-[11px] block mt-0.5">{chk.rule_description}</span>
                        {chk.failure_reason && (
                          <span className="text-rose-600 text-[11px] font-semibold block mt-1">
                            Notice: {chk.failure_reason}
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400">Compliance checklist not evaluated.</p>
                )}
              </div>
            </div>

            {/* Risk Factor Breakdown */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Multi-Factor Risk Breakdown</h3>
                <p className="text-xs text-slate-500">Configurable weighted risk components (0–100%)</p>
              </div>

              {vendor.risk_assessment?.factors && (
                <div className="space-y-3">
                  {vendor.risk_assessment.factors.map((f, i) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-slate-800">{f.factor_name}</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            f.status === 'PASS'
                              ? 'bg-emerald-100 text-emerald-700'
                              : f.status === 'ELEVATED'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-rose-100 text-rose-700'
                          }`}
                        >
                          {f.status}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-slate-500 text-[11px]">
                        <span>Weight: {f.weight_percent}% • Raw Risk: {f.raw_risk}%</span>
                        <span className="font-bold text-slate-800">Impact: +{f.weighted_impact}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: AI ANOMALY ENGINE */}
      {activeTab === 'anomaly' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-violet-600" />
            <div>
              <h3 className="text-base font-bold text-slate-900">AI / Machine Learning Findings (Isolation Forest)</h3>
              <p className="text-xs text-slate-500">
                Multivariate statistical anomaly detection benchmarked against peer procurement profiles
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700">Model Output Status:</span>
              <span
                className={`font-bold px-2.5 py-0.5 rounded text-xs ${
                  vendor.anomaly_status === 'LOW ANOMALY'
                    ? 'bg-emerald-100 text-emerald-800'
                    : vendor.anomaly_status === 'MEDIUM ANOMALY'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-rose-100 text-rose-800'
                }`}
              >
                {vendor.anomaly_status} (Score: {vendor.anomaly_score.toFixed(2)})
              </span>
            </div>

            <p className="text-slate-600 leading-relaxed">
              {vendor.risk_assessment?.explanations?.find((e) => e.includes('deviation') || e.includes('conformance') || e.includes('anomaly')) ||
                'Operational indicators and verification metrics closely conform to standard enterprise distributions.'}
            </p>

            <div className="pt-3 text-[11px] text-slate-500 border-t border-slate-200/80 space-y-1">
              <p className="font-semibold text-slate-700">Enterprise AI Ethics Assurance:</p>
              <p className="italic">
                The ML system identifies statistical variance relative to peer distributions to guide procurement officers in prioritizing verification, and never outputs accusations or claims of fraud.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Vendor Audit Trail History ({auditLogs.length})</h3>
              <p className="text-xs text-slate-500">All registered actions and state transitions for this vendor</p>
            </div>
            <Link
              href={`/audit?vendorId=${vendor.id}`}
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
            >
              Open Full Audit Screen →
            </Link>
          </div>

          {auditLogs.length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center">No audit logs recorded for this vendor yet.</p>
          ) : (
            <div className="space-y-3">
              {auditLogs.map((log) => (
                <div key={log.id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-slate-900">{log.action}</span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-600">
                    Actor: <b>{log.user_email || 'officer@bidverify.com'}</b>
                  </div>
                  {log.details && (
                    <div className="mt-2 p-2 rounded bg-slate-900 text-slate-200 font-mono text-[10px] overflow-x-auto">
                      {JSON.stringify(log.details, null, 2)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
