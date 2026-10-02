'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Check,
  Building,
  Upload,
  FileCheck,
  Play,
  ArrowRight,
  ArrowLeft,
  Loader2,
  AlertCircle,
  FileText,
  ShieldCheck
} from 'lucide-react';
import { api } from '@/services/api';
import DocumentUploader from '@/components/DocumentUploader';
import { DocumentItem } from '@/types';

export default function NewVendorPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);

  // Step 1 Form Data
  const [formData, setFormData] = useState({
    name: 'CyberGrid Infotech Solutions Private Limited',
    legal_name: 'CyberGrid Infotech Solutions Private Limited',
    gstin: '36AABCC9988D1Z9',
    pan: 'AABCC9988D',
    cin: 'U72900TG2021PTC156789',
    udyam_number: 'UDYAM-TS-02-0056789',
    address: 'Survey No 115, Financial District, Nanakramguda, Hyderabad, Telangana - 500032',
    state: 'Telangana',
    pincode: '500032',
    contact_email: 'compliance@cybergridtech.in',
    contact_phone: '+91 98490 54321',
    turnover_cr: 14.2,
    employee_count: 55,
    established_year: 2021,
  });

  const [createdVendorId, setCreatedVendorId] = useState<number | null>(null);
  const [uploadedDocs, setUploadedDocs] = useState<DocumentItem[]>([]);
  const [extractedData, setExtractedData] = useState<Record<string, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [verificationOutput, setVerificationOutput] = useState<any>(null);

  React.useEffect(() => {
    const user = api.getCurrentUser();
    if (user && user.company_name) {
      setFormData((prev) => ({
        ...prev,
        name: user.company_name,
        legal_name: user.company_name,
        contact_email: user.email || prev.contact_email,
      }));
    }
  }, []);

  // Handle Form Change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Step 1: Create Vendor in DB
  const handleCreateVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const vendor = await api.createVendor(formData);
      setCreatedVendorId(vendor.id);
      setCurrentStep(2);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save vendor');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Document uploaded callback
  const handleUploadSuccess = (doc: DocumentItem) => {
    setUploadedDocs((prev) => [...prev, doc]);
  };

  // Document extracted callback
  const handleExtractSuccess = (docId: number, extracted: any) => {
    setExtractedData((prev) => ({ ...prev, ...extracted }));
  };

  // Step 4: Run Verification
  const handleRunVerification = async () => {
    if (!createdVendorId) return;
    setIsVerifying(true);
    setErrorMsg(null);
    try {
      const result = await api.verifyVendor(createdVendorId);
      setVerificationOutput(result);
    } catch (err: any) {
      setErrorMsg(err.message || 'Verification execution failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const steps = [
    { num: 1, title: 'Corporate Identity', icon: Building },
    { num: 2, title: 'Document Upload', icon: Upload },
    { num: 3, title: 'OCR Extraction Review', icon: FileCheck },
    { num: 4, title: 'Execute Verification', icon: Play },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900">New Vendor Onboarding Wizard</h2>
        <p className="text-xs text-slate-500 mt-1">
          Follow the 4-step workflow to register, extract documentation, and trigger automated cross-verification.
        </p>
      </div>

      {/* Stepper Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = currentStep > step.num;
            const isCurrent = currentStep === step.num;
            return (
              <React.Fragment key={step.num}>
                <div className="flex items-center gap-2.5">
                  <div
                    className={`h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                      isCompleted
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-indigo-600 text-white ring-4 ring-indigo-100'
                        : 'bg-slate-100 text-slate-400'
                    }`}
                  >
                    {isCompleted ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  </div>
                  <div className="hidden sm:block">
                    <p className={`text-xs font-semibold ${isCurrent ? 'text-slate-900' : 'text-slate-500'}`}>
                      {step.title}
                    </p>
                    <p className="text-[10px] text-slate-400">Step {step.num}</p>
                  </div>
                </div>
                {idx < steps.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-3 ${currentStep > idx + 1 ? 'bg-emerald-600' : 'bg-slate-200'}`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* STEP 1: Basic Information */}
      {currentStep === 1 && (
        <form onSubmit={handleCreateVendor} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">
            1. Basic Corporate Information & Identifiers
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Company Trading Name *</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Company Legal Name *</label>
              <input
                type="text"
                name="legal_name"
                required
                value={formData.legal_name}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">GSTIN (15 Digits) *</label>
              <input
                type="text"
                name="gstin"
                required
                value={formData.gstin}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-mono font-medium uppercase"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">PAN (10 Characters) *</label>
              <input
                type="text"
                name="pan"
                required
                value={formData.pan}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-mono font-medium uppercase"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">CIN (Corporate Identity Number)</label>
              <input
                type="text"
                name="cin"
                value={formData.cin}
                onChange={handleChange}
                placeholder="U12345TG2020PTC123456"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-mono font-medium uppercase"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Udyam Registration Number (MSME)</label>
              <input
                type="text"
                name="udyam_number"
                value={formData.udyam_number}
                onChange={handleChange}
                placeholder="UDYAM-XX-00-0000000"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-mono font-medium uppercase"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Registered Office Address *</label>
              <textarea
                name="address"
                rows={2}
                required
                value={formData.address}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">State *</label>
              <input
                type="text"
                name="state"
                required
                value={formData.state}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Postal Pincode *</label>
              <input
                type="text"
                name="pincode"
                required
                value={formData.pincode}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Email</label>
              <input
                type="email"
                name="contact_email"
                value={formData.contact_email}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Phone</label>
              <input
                type="text"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Turnover (INR Crores)</label>
              <input
                type="number"
                step="0.1"
                name="turnover_cr"
                value={formData.turnover_cr}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Employee Count</label>
              <input
                type="number"
                name="employee_count"
                value={formData.employee_count}
                onChange={handleChange}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-1 focus:ring-emerald-500 bg-slate-50 font-medium"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving Profile...
                </>
              ) : (
                <>
                  Next: Upload Documents
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </form>
      )}

      {/* STEP 2: Document Upload */}
      {currentStep === 2 && createdVendorId && (
        <div className="space-y-6">
          <DocumentUploader
            vendorId={createdVendorId}
            onUploadSuccess={handleUploadSuccess}
            onExtractSuccess={handleExtractSuccess}
          />

          {/* Uploaded Documents List */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 mb-3">
              Uploaded Documents ({uploadedDocs.length})
            </h3>
            {uploadedDocs.length === 0 ? (
              <p className="text-xs text-slate-400">No documents uploaded yet. You can upload PAN, GST, or Udyam certs above.</p>
            ) : (
              <div className="space-y-2">
                {uploadedDocs.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                    <div className="flex items-center gap-2.5">
                      <FileText className="h-4 w-4 text-emerald-600" />
                      <div>
                        <span className="font-semibold text-slate-800">{doc.file_name}</span>
                        <span className="text-slate-400 ml-2">({doc.doc_type})</span>
                      </div>
                    </div>
                    <span className="text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      Uploaded
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-between items-center pt-6 mt-6 border-t border-slate-100">
              <button
                onClick={() => setCurrentStep(1)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Back
              </button>

              <button
                onClick={() => setCurrentStep(3)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                Next: Review Extracted Data <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: OCR Extracted Review */}
      {currentStep === 3 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Review OCR Extracted Information</h3>
            <p className="text-xs text-slate-500 mt-1">
              Verify values extracted by the OCR pipeline before triggering multi-portal verification.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs font-medium">
            <div>
              <span className="text-slate-400 font-semibold block mb-0.5">Extracted Legal Name:</span>
              <span className="text-slate-900 font-bold">{extractedData.company_name || formData.legal_name}</span>
            </div>
            <div>
              <span className="text-slate-400 font-semibold block mb-0.5">Extracted GSTIN:</span>
              <span className="text-slate-900 font-mono font-bold">{extractedData.gstin || formData.gstin}</span>
            </div>
            <div>
              <span className="text-slate-400 font-semibold block mb-0.5">Extracted PAN:</span>
              <span className="text-slate-900 font-mono font-bold">{extractedData.pan || formData.pan}</span>
            </div>
            <div>
              <span className="text-slate-400 font-semibold block mb-0.5">Extracted Pincode:</span>
              <span className="text-slate-900 font-bold">{extractedData.pincode || formData.pincode}</span>
            </div>
            <div className="md:col-span-2">
              <span className="text-slate-400 font-semibold block mb-0.5">Extracted Registered Address:</span>
              <span className="text-slate-900">{extractedData.address || formData.address}</span>
            </div>
          </div>

          <div className="flex justify-between items-center pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(2)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Back to Uploads
            </button>

            <button
              onClick={() => setCurrentStep(4)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              Proceed to Verification <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Run Verification */}
      {currentStep === 4 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Run Automated Compliance & Risk Verification</h3>
            <p className="text-xs text-slate-500 mt-1">
              Executes RapidFuzz cross-matching against Government Registries (GSTN, Udyam, MCA21), runs Isolation Forest anomaly detection, and calculates weighted risk score.
            </p>
          </div>

          {!verificationOutput ? (
            <div className="text-center py-10 bg-slate-50 rounded-xl border border-slate-200">
              <ShieldCheck className="h-12 w-12 text-indigo-600 mx-auto mb-3" />
              <p className="text-sm font-bold text-slate-900 mb-1">Ready to execute verification engine</p>
              <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
                All uploaded documents and registry data points are assembled for scoring.
              </p>

              <button
                onClick={handleRunVerification}
                disabled={isVerifying}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md transition-colors disabled:opacity-50"
              >
                {isVerifying ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Executing Verification Pipeline...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Run AI Verification Now
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-emerald-900">Verification Run Completed!</h4>
                  <p className="text-xs text-emerald-700 mt-0.5">
                    Assigned Status: <b>{verificationOutput.verification_status}</b>
                  </p>
                </div>
                <button
                  onClick={() => router.push(`/vendors/${createdVendorId}`)}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm"
                >
                  View Complete Dossier
                </button>
              </div>

              {/* Instant Scores Preview */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase">Compliance</span>
                  <div className="text-xl font-bold text-slate-900">{verificationOutput.scores.compliance_score}%</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase">Risk Score</span>
                  <div className="text-xl font-bold text-slate-900">{verificationOutput.scores.risk_score}%</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase">Data Match</span>
                  <div className="text-xl font-bold text-slate-900">{verificationOutput.scores.match_score}%</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase">Anomaly</span>
                  <div className="text-xl font-bold text-slate-900">{verificationOutput.scores.anomaly_score}</div>
                </div>
              </div>

              {/* Recommended Action */}
              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-xs">
                <span className="font-bold text-blue-900 block mb-1">Recommended Action:</span>
                <span className="text-blue-800">{verificationOutput.recommended_action}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
