'use client';

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Trash2,
  FileBadge
} from 'lucide-react';
import { api } from '@/services/api';
import { DocumentItem } from '@/types';

interface DocumentUploaderProps {
  vendorId: number | string;
  onUploadSuccess?: (doc: DocumentItem) => void;
  onExtractSuccess?: (docId: number, extracted: any) => void;
}

const DOC_TYPES = [
  'GST Certificate',
  'PAN',
  'Udyam Certificate',
  'MCA/Company Registration',
  'Address Proof',
  'Bank Document',
  'Other'
];

export default function DocumentUploader({ vendorId, onUploadSuccess, onExtractSuccess }: DocumentUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>('GST Certificate');
  const [isUploading, setIsUploading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const [uploadedDoc, setUploadedDoc] = useState<DocumentItem | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file: File) => {
    setErrorMsg(null);
    const validExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      setErrorMsg(`Invalid file type. Please upload a PDF, PNG, or JPG document.`);
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setErrorMsg('File exceeds 15MB limit.');
      return;
    }
    setSelectedFile(file);
    setUploadedDoc(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setErrorMsg(null);
    try {
      const doc = await api.uploadDocument(vendorId, selectedFile, docType);
      setUploadedDoc(doc);
      if (onUploadSuccess) onUploadSuccess(doc);
    } catch (err: any) {
      setErrorMsg(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleExtract = async () => {
    if (!uploadedDoc) return;
    setIsExtracting(true);
    setErrorMsg(null);
    try {
      const result = await api.extractDocument(uploadedDoc.id);
      if (onExtractSuccess) onExtractSuccess(uploadedDoc.id, result.structured_json);
    } catch (err: any) {
      setErrorMsg(err.message || 'OCR extraction failed');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleLoadSample = async (type: 'gst' | 'pan' | 'udyam') => {
    setLoadingSample(type);
    setErrorMsg(null);
    try {
      const res = await api.loadSampleDocument(vendorId, type);
      const mockDocItem: DocumentItem = {
        id: res.document_id,
        vendor_id: res.vendor_id,
        doc_type: res.doc_type,
        file_name: res.file_name,
        file_size: 245000,
        mime_type: 'application/pdf',
        status: res.status,
        ocr_confidence: res.ocr_confidence,
        uploaded_at: new Date().toISOString(),
        extracted_data: res.structured_data
      };
      setUploadedDoc(mockDocItem);
      if (onUploadSuccess) onUploadSuccess(mockDocItem);
      if (onExtractSuccess) onExtractSuccess(res.document_id, res.structured_data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load sample document');
    } finally {
      setLoadingSample(null);
    }
  };

  const resetSelection = () => {
    setSelectedFile(null);
    setUploadedDoc(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Upload Compliance Document</h3>
          <p className="text-xs text-slate-500">Supports PDF, PNG, JPG scans up to 15MB</p>
        </div>

        {/* Doc Type Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Category:</label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            disabled={isUploading || !!uploadedDoc}
            className="text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 bg-slate-50 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            {DOC_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Quick 1-Click Sample Pre-load Buttons */}
      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
        <span className="font-semibold text-slate-700 block mb-2">
          Or Load Realistic Test Documents (Instant OCR Demonstration):
        </span>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleLoadSample('gst')}
            disabled={!!loadingSample}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:border-emerald-500 hover:text-emerald-700 font-semibold transition-all shadow-2xs"
          >
            {loadingSample === 'gst' ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileBadge className="h-3.5 w-3.5 text-emerald-600" />}
            Sample GST Certificate
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample('pan')}
            disabled={!!loadingSample}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:border-indigo-500 hover:text-indigo-700 font-semibold transition-all shadow-2xs"
          >
            {loadingSample === 'pan' ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileBadge className="h-3.5 w-3.5 text-indigo-600" />}
            Sample PAN Card
          </button>
          <button
            type="button"
            onClick={() => handleLoadSample('udyam')}
            disabled={!!loadingSample}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:border-blue-500 hover:text-blue-700 font-semibold transition-all shadow-2xs"
          >
            {loadingSample === 'udyam' ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileBadge className="h-3.5 w-3.5 text-blue-600" />}
            Sample Udyam MSME
          </button>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      {!selectedFile && !uploadedDoc ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            dragActive
              ? 'border-emerald-500 bg-emerald-50/50'
              : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 hover:bg-slate-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.tiff"
            onChange={handleFileChange}
          />
          <div className="h-12 w-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-semibold text-slate-800">
            Click to upload or drag & drop document
          </p>
          <p className="text-xs text-slate-500 mt-1">
            PAN Card, GST Registration, Udyam Certificate, etc.
          </p>
        </div>
      ) : (
        <div className="border border-slate-200 rounded-xl p-4 bg-slate-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-900 truncate max-w-xs">
                  {uploadedDoc ? uploadedDoc.file_name : selectedFile?.name}
                </p>
                <p className="text-xs text-slate-500">
                  {uploadedDoc ? uploadedDoc.doc_type : docType}
                  {uploadedDoc && ` • OCR Confidence: ${uploadedDoc.ocr_confidence.toFixed(1)}%`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {!uploadedDoc ? (
                <>
                  <button
                    onClick={handleUpload}
                    disabled={isUploading}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm disabled:opacity-50"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      'Upload Document'
                    )}
                  </button>
                  <button
                    onClick={resetSelection}
                    disabled={isUploading}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Extracted & Ready
                  </span>
                  <button
                    onClick={resetSelection}
                    className="text-xs text-slate-500 hover:text-slate-800 ml-2 font-medium"
                  >
                    Upload Another
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}
