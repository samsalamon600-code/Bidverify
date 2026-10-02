'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FileText,
  UploadCloud,
  Sparkles,
  Trash2,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Building2,
  ExternalLink
} from 'lucide-react';
import { api } from '@/services/api';
import { DocumentItem, Vendor } from '@/types';
import DocumentUploader from '@/components/DocumentUploader';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedVendorId, setSelectedVendorId] = useState<number>(1);
  const [filterVendorId, setFilterVendorId] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [extractingId, setExtractingId] = useState<number | null>(null);
  const [extractedJson, setExtractedJson] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [docs, vList] = await Promise.all([
        api.getAllDocuments(),
        api.getVendors(),
      ]);
      setDocuments(docs);
      setVendors(vList);

      const currentUser = api.getCurrentUser();
      if (currentUser?.vendor_id) {
        setSelectedVendorId(currentUser.vendor_id);
      } else if (vList.length > 0) {
        setSelectedVendorId(vList[0].id);
      }

      if (docs.length > 0 && !selectedDoc) {
        setSelectedDoc(docs[0]);
        if (docs[0].extracted_data) {
          setExtractedJson(docs[0].extracted_data);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExtract = async (docId: number) => {
    setExtractingId(docId);
    try {
      const res = await api.extractDocument(docId);
      setExtractedJson(res.structured_json);
      const docs = await api.getAllDocuments();
      setDocuments(docs);
      const updated = docs.find((d) => d.id === docId);
      if (updated) setSelectedDoc(updated);
    } catch (err: any) {
      alert(err.message || 'Extraction failed');
    } finally {
      setExtractingId(null);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await api.deleteDocument(docId);
      const docs = await api.getAllDocuments();
      setDocuments(docs);
      if (selectedDoc?.id === docId) {
        setSelectedDoc(docs[0] || null);
        setExtractedJson(docs[0]?.extracted_data || null);
      }
    } catch (err: any) {
      alert(err.message || 'Delete failed');
    }
  };

  const filteredDocs = filterVendorId === 'ALL'
    ? documents
    : documents.filter((d) => d.vendor_id === Number(filterVendorId));

  const getVendorName = (vId: number) => {
    const v = vendors.find((x) => x.id === vId);
    return v ? v.name : `Vendor #${vId}`;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Document Management & OCR Processing Hub</h2>
        <p className="text-xs text-slate-500 mt-1">
          Upload compliance certificates, execute OpenCV preprocessing, and extract structured Indian identifiers (PAN, GSTIN, CIN, Udyam).
        </p>
      </div>

      {/* Target Vendor Entity Selector */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-emerald-600" />
          <span className="text-xs font-bold text-slate-800">Target Vendor for Ingestion:</span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedVendorId}
            onChange={(e) => setSelectedVendorId(Number(e.target.value))}
            className="text-xs font-semibold border border-slate-300 rounded-lg px-3 py-1.5 bg-slate-50 text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500 min-w-[260px]"
          >
            {vendors.map((v) => (
              <option key={v.id} value={v.id}>
                #{v.id} — {v.name} ({v.gstin || v.pan || 'Pending ID'})
              </option>
            ))}
          </select>
          <Link
            href={`/vendors/${selectedVendorId}`}
            className="text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors inline-flex items-center gap-1"
          >
            Dossier <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {/* Uploader Card dynamically bound to selected vendor */}
      <DocumentUploader
        vendorId={selectedVendorId}
        onUploadSuccess={() => {
          api.getAllDocuments().then(setDocuments);
        }}
        onExtractSuccess={(docId, ext) => {
          setExtractedJson(ext);
          api.getAllDocuments().then(setDocuments);
        }}
      />

      {/* Side-by-side explorer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Documents List */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Document Repository ({filteredDocs.length})
              </h3>
            </div>
            <button onClick={fetchData} className="text-slate-400 hover:text-slate-600" title="Refresh">
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Filter by vendor */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-semibold">Filter:</span>
            <select
              value={filterVendorId}
              onChange={(e) => setFilterVendorId(e.target.value)}
              className="text-xs border border-slate-300 rounded px-2 py-1 bg-white text-slate-700 font-medium focus:outline-none w-full"
            >
              <option value="ALL">All Vendors ({documents.length})</option>
              {vendors.map((v) => (
                <option key={v.id} value={v.id.toString()}>
                  #{v.id} - {v.name}
                </option>
              ))}
            </select>
          </div>

          {loading ? (
            <div className="py-10 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
              <RefreshCw className="h-5 w-5 animate-spin text-emerald-600" />
              Loading documents...
            </div>
          ) : filteredDocs.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No documents found for this filter. Use the uploader above to add test documents.
            </div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {filteredDocs.map((doc) => {
                const isSelected = selectedDoc?.id === doc.id;
                return (
                  <div
                    key={doc.id}
                    onClick={() => {
                      setSelectedDoc(doc);
                      setExtractedJson(doc.extracted_data || null);
                    }}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'border-emerald-500 bg-emerald-50/50 shadow-sm'
                        : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 overflow-hidden">
                        <FileText className={`h-4 w-4 shrink-0 ${isSelected ? 'text-emerald-600' : 'text-slate-400'}`} />
                        <span className="font-semibold text-slate-900 truncate">{doc.file_name}</span>
                      </div>
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200/60 text-slate-700 shrink-0">
                        {doc.doc_type}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                      <span className="font-medium text-slate-600 truncate max-w-[140px]">
                        {getVendorName(doc.vendor_id)}
                      </span>
                      <span className="font-semibold text-emerald-700">OCR: {doc.ocr_confidence.toFixed(0)}%</span>
                    </div>

                    <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-slate-200/60">
                      <Link
                        href={`/vendors/${doc.vendor_id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-[10px] font-semibold text-slate-500 hover:text-emerald-600 flex items-center gap-0.5"
                      >
                        View Vendor #{doc.vendor_id} →
                      </Link>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExtract(doc.id);
                          }}
                          disabled={extractingId === doc.id}
                          className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                        >
                          {extractingId === doc.id ? (
                            <RefreshCw className="h-3 w-3 animate-spin" />
                          ) : (
                            <Sparkles className="h-3 w-3" />
                          )}
                          Extract
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(doc.id);
                          }}
                          className="text-[11px] text-rose-500 hover:text-rose-700"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: OCR Extraction Inspection */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Extracted Structured JSON & Metadata</h3>
              <p className="text-xs text-slate-500">Output of OCR extraction and regex normalization engines</p>
            </div>
            {selectedDoc && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 border border-indigo-200 text-indigo-700">
                  Confidence: {selectedDoc.ocr_confidence.toFixed(1)}%
                </span>
                <Link
                  href={`/vendors/${selectedDoc.vendor_id}`}
                  className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold text-xs hover:bg-emerald-100 transition-colors"
                >
                  Open Dossier →
                </Link>
              </div>
            )}
          </div>

          {selectedDoc ? (
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div>
                    <span className="text-slate-400 font-semibold block text-[10px] uppercase">Vendor Target:</span>
                    <span className="font-semibold text-slate-800 truncate block">{getVendorName(selectedDoc.vendor_id)}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold block text-[10px] uppercase">Category:</span>
                    <span className="font-semibold text-slate-800">{selectedDoc.doc_type}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold block text-[10px] uppercase">Status:</span>
                    <span className="font-semibold text-emerald-600">{selectedDoc.status}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold block text-[10px] uppercase">Uploaded:</span>
                    <span className="font-semibold text-slate-800">{new Date(selectedDoc.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* JSON preview */}
              <div>
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2">
                  Parsed Entity Fields (Structured)
                </span>
                <pre className="p-4 rounded-xl bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto max-h-80 shadow-inner">
                  {extractedJson
                    ? JSON.stringify(extractedJson, null, 2)
                    : '// No structured fields extracted yet. Click "Extract" to run the OCR engine.'}
                </pre>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-slate-400 text-xs">
              Select a document from the left to view parsed fields.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
