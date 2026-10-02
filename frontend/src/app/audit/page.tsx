'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  History,
  UserCheck,
  FileText,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Clock,
  Filter
} from 'lucide-react';
import { api } from '@/services/api';
import { AuditLogItem } from '@/types';

function AuditContent() {
  const searchParams = useSearchParams();
  const initialVendorId = searchParams.get('vendorId') || '';

  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [vendorFilter, setVendorFilter] = useState(initialVendorId);

  const fetchAuditLogs = async (vId?: string) => {
    setLoading(true);
    try {
      const data = await api.getAuditTrail(vId ? Number(vId) : undefined);
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs(vendorFilter);
  }, [vendorFilter]);

  const getActionIcon = (action: string) => {
    if (action.includes('Verification')) return <ShieldCheck className="h-4 w-4 text-emerald-600" />;
    if (action.includes('Document') || action.includes('Upload')) return <FileText className="h-4 w-4 text-blue-600" />;
    if (action.includes('OCR')) return <CheckCircle2 className="h-4 w-4 text-indigo-600" />;
    return <UserCheck className="h-4 w-4 text-slate-600" />;
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Procurement Audit Trail & Action Logs</h2>
          <p className="text-xs text-slate-500 mt-1">
            Immutable chronological logging of officer actions, document uploads, OCR events, and risk recalculations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-semibold">Filter Vendor ID:</span>
            <input
              type="text"
              placeholder="e.g. 1"
              value={vendorFilter}
              onChange={(e) => setVendorFilter(e.target.value)}
              className="w-20 px-2 py-1 rounded-md border border-slate-300 text-xs bg-white font-mono focus:outline-none"
            />
          </div>
          <button
            onClick={() => fetchAuditLogs(vendorFilter)}
            className="p-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-600"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Timeline Container */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        {loading ? (
          <div className="py-16 text-center text-xs font-semibold text-slate-500 flex flex-col items-center gap-2">
            <RefreshCw className="h-6 w-6 animate-spin text-emerald-600" />
            Loading audit records...
          </div>
        ) : logs.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-400">
            No audit records matching filter.
          </div>
        ) : (
          <div className="relative border-l border-slate-200 ml-4 space-y-6">
            {logs.map((log) => (
              <div key={log.id} className="relative pl-6">
                {/* Timeline Node Icon */}
                <div className="absolute -left-3.5 top-0.5 h-7 w-7 rounded-full bg-white border border-slate-300 flex items-center justify-center shadow-sm">
                  {getActionIcon(log.action)}
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                    <span className="font-bold text-slate-900 text-sm">{log.action}</span>
                    <span className="text-slate-400 text-[11px] flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-slate-600 mb-2">
                    <span>
                      Actor: <b>{log.user_email || 'system@bidverify.com'}</b>
                    </span>
                    {log.vendor_name && (
                      <span>
                        Vendor: <b>{log.vendor_name}</b> (ID: #{log.vendor_id})
                      </span>
                    )}
                  </div>

                  {log.details && (
                    <div className="p-2.5 rounded-lg bg-slate-900 text-slate-200 font-mono text-[11px] overflow-x-auto">
                      {JSON.stringify(log.details, null, 2)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AuditPage() {
  return (
    <Suspense fallback={
      <div className="py-16 text-center text-xs font-semibold text-slate-500 flex flex-col items-center gap-2">
        <RefreshCw className="h-6 w-6 animate-spin text-emerald-600" />
        Loading audit timeline...
      </div>
    }>
      <AuditContent />
    </Suspense>
  );
}
