'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Search,
  Filter,
  Plus,
  Play,
  FileDown,
  Eye,
  ArrowUpDown,
  RefreshCw,
  Building2,
  CheckCircle2
} from 'lucide-react';
import { api } from '@/services/api';
import { Vendor } from '@/types';

const STATUS_OPTIONS = ['All', 'Verified', 'Partially Verified', 'Requires Review', 'Failed', 'Pending'];
const RISK_OPTIONS = ['All', 'LOW', 'MEDIUM', 'HIGH'];

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [riskFilter, setRiskFilter] = useState('All');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [verifyingId, setVerifyingId] = useState<number | null>(null);

  const fetchVendors = async () => {
    setLoading(true);
    try {
      const data = await api.getVendors({
        search,
        status: statusFilter,
        risk_level: riskFilter,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setVendors(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, [statusFilter, riskFilter, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchVendors();
  };

  const handleRunVerify = async (vendorId: number) => {
    setVerifyingId(vendorId);
    try {
      await api.verifyVendor(vendorId);
      await fetchVendors();
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Vendor Management Directory</h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse, filter, and inspect verified enterprise profiles and live compliance scoring.
          </p>
        </div>
        <Link
          href="/vendors/new"
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold text-white shadow-sm transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add New Vendor
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search vendor legal name, GSTIN, PAN..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 text-xs bg-slate-50 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-medium"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-600">
            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-slate-300 rounded-md px-2 py-1 bg-white text-slate-800 font-medium focus:outline-none"
              >
                {STATUS_OPTIONS.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>

            {/* Risk Tier Filter */}
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold">Risk Tier:</span>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="border border-slate-300 rounded-md px-2 py-1 bg-white text-slate-800 font-medium focus:outline-none"
              >
                {RISK_OPTIONS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            {/* Sort Filter */}
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold">Sort By:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-slate-300 rounded-md px-2 py-1 bg-white text-slate-800 font-medium focus:outline-none"
              >
                <option value="created_at">Date Created</option>
                <option value="compliance_score">Compliance Score</option>
                <option value="risk_score">Risk Score</option>
                <option value="name">Company Name</option>
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="p-1 border border-slate-300 rounded hover:bg-slate-50 text-slate-600"
                title="Toggle Sort Direction"
              >
                <ArrowUpDown className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <button
            onClick={fetchVendors}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-medium"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Reset Filters
          </button>
        </div>
      </div>

      {/* Vendors Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-xs font-semibold text-slate-500 flex flex-col items-center gap-2">
            <RefreshCw className="h-6 w-6 animate-spin text-emerald-600" />
            Loading vendors directory...
          </div>
        ) : vendors.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs">
            <Building2 className="h-8 w-8 mx-auto text-slate-300 mb-2" />
            No vendors found matching the active search & filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider border-b border-slate-200 font-semibold">
                <tr>
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Company Name</th>
                  <th className="py-3 px-4">GSTIN & PAN</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Compliance</th>
                  <th className="py-3 px-4">Risk Tier</th>
                  <th className="py-3 px-4">Last Verified</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {vendors.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-500">
                      #{v.id}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      <Link href={`/vendors/${v.id}`} className="hover:text-emerald-600">
                        {v.name}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-600">
                      <div>{v.gstin || 'N/A'}</div>
                      <div className="text-[10px] text-slate-400">{v.pan}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                          v.verification_status === 'Verified'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : v.verification_status === 'Partially Verified'
                            ? 'bg-blue-50 text-blue-700 border border-blue-200'
                            : v.verification_status === 'Requires Review'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : v.verification_status === 'Failed'
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {v.verification_status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900">{v.compliance_score.toFixed(1)}%</div>
                      <div className="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden mt-1">
                        <div
                          className="h-full bg-emerald-500"
                          style={{ width: `${v.compliance_score}%` }}
                        />
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          v.risk_level === 'LOW'
                            ? 'bg-emerald-50 text-emerald-700'
                            : v.risk_level === 'MEDIUM'
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-rose-50 text-rose-700'
                        }`}
                      >
                        {v.risk_level} ({v.risk_score.toFixed(0)}%)
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">
                      {v.last_verified ? new Date(v.last_verified).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          href={`/vendors/${v.id}`}
                          className="p-1.5 rounded text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                          title="View Full Dossier"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>

                        <button
                          onClick={() => handleRunVerify(v.id)}
                          disabled={verifyingId === v.id}
                          className="p-1.5 rounded text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 transition-colors disabled:opacity-50"
                          title="Execute AI Verification"
                        >
                          {verifyingId === v.id ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-indigo-600" />
                          ) : (
                            <Play className="h-4 w-4" />
                          )}
                        </button>

                        <a
                          href={api.getReportDownloadUrl(v.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1.5 rounded text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50 transition-colors"
                          title="Download Official PDF Report"
                        >
                          <FileDown className="h-4 w-4" />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
