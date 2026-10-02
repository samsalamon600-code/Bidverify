'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Users,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowUpRight,
  ShieldCheck,
  TrendingUp,
  FileCheck2,
  RefreshCw,
  Plus
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, CartesianGrid, Legend
} from 'recharts';
import { api } from '@/services/api';
import { DashboardData, Vendor } from '@/types';

const STATUS_COLORS: Record<string, string> = {
  'Verified': '#16A34A',
  'Partially Verified': '#2563EB',
  'Requires Review': '#D97706',
  'Failed': '#DC2626',
  'Pending': '#64748B',
};

const RISK_COLORS = ['#16A34A', '#D97706', '#DC2626'];

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [recentVendors, setRecentVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [dash, vendors] = await Promise.all([
        api.getDashboard(),
        api.getVendors({ sort_by: 'created_at', sort_order: 'desc' }),
      ]);
      setData(dash);
      setRecentVendors(vendors.slice(0, 5));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-7 w-7 text-emerald-600 animate-spin" />
          <p className="text-xs font-semibold text-slate-500">Aggregating Procurement Intelligence...</p>
        </div>
      </div>
    );
  }

  const { kpis } = data;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner & Quick Action */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Procurement Officer Control Center</h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time multi-portal verification, OCR field extraction, and ML anomaly detection.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={loadDashboard}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5 text-slate-500" />
            Refresh Data
          </button>
          <Link
            href="/vendors/new"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold text-white shadow-sm transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add New Vendor
          </Link>
        </div>
      </div>

      {/* 5 KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* KPI 1 */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Total Vendors</span>
            <Users className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{kpis.total_vendors}</div>
          <span className="text-[10px] text-slate-400">Registered entities</span>
        </div>

        {/* KPI 2 */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Verified</span>
            <CheckCircle className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{kpis.verified_vendors}</div>
          <span className="text-[10px] text-emerald-600 font-medium">Cleared for tenders</span>
        </div>

        {/* KPI 3 */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Needs Review</span>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{kpis.review_required_vendors}</div>
          <span className="text-[10px] text-amber-600 font-medium">Requires attention</span>
        </div>

        {/* KPI 4 */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">High Risk</span>
            <ShieldCheck className="h-4 w-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{kpis.high_risk_vendors}</div>
          <span className="text-[10px] text-rose-600 font-medium">Above risk threshold</span>
        </div>

        {/* KPI 5 */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Avg Compliance</span>
            <TrendingUp className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{kpis.avg_compliance_score}%</div>
          <span className="text-[10px] text-slate-400">Registry benchmark</span>
        </div>
      </div>

      {/* Row 1 Charts: Verification Status & Monthly Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Verification Status Distribution (Donut Chart) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Verification Status Breakdown</h3>
          <p className="text-xs text-slate-500 mb-4">Distribution across current active procurement roster</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.verification_status}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                >
                  {data.verification_status.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={STATUS_COLORS[entry.label] || '#94A3B8'}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => [`${val} Vendors`, 'Count']}
                  contentStyle={{ backgroundColor: '#0F172A', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Monthly Verification Trend (Area Chart) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Monthly Verification Velocity</h3>
          <p className="text-xs text-slate-500 mb-4">Volume of vendor dossiers verified through the AI pipeline</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.monthly_trend}>
                <defs>
                  <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: any) => [`${val} Entities`, 'Processed']}
                  contentStyle={{ backgroundColor: '#0F172A', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="value" stroke="#10B981" strokeWidth={2.5} fillOpacity={1} fill="url(#trendGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 2 Charts: Risk Breakdown & Compliance Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compliance Distribution (BarChart) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Compliance Score Tiers</h3>
          <p className="text-xs text-slate-500 mb-4">Vendor counts by compliance range</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.compliance_distribution}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: any) => [`${val} Vendors`, 'Tally']}
                  contentStyle={{ backgroundColor: '#0F172A', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="value" fill="#2563EB" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution (Pie/Donut Chart) */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Risk Tier Proportion</h3>
          <p className="text-xs text-slate-500 mb-4">Low (0-30), Medium (31-60), High (61-100)</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.risk_distribution}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                >
                  {data.risk_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={RISK_COLORS[index % RISK_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => [`${val} Vendors`, 'Count']}
                  contentStyle={{ backgroundColor: '#0F172A', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Factor Impact Breakdown */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Risk Factor Drivers</h3>
          <p className="text-xs text-slate-500 mb-4">Weighted impact contribution across vendors</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={data.risk_factors} margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
                <XAxis type="number" tick={{ fontSize: 10, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <YAxis dataKey="label" type="category" tick={{ fontSize: 10, fill: '#475569' }} axisLine={false} tickLine={false} width={90} />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'Impact Weight']}
                  contentStyle={{ backgroundColor: '#0F172A', color: '#fff', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="value" fill="#E11D48" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Vendors Quick Directory */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent Vendor Dossiers</h3>
            <p className="text-xs text-slate-500">Quick access to newly onboarded or verified candidates</p>
          </div>
          <Link
            href="/vendors"
            className="flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700"
          >
            View Complete Directory <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider border-y border-slate-200 font-semibold">
              <tr>
                <th className="py-3 px-4">Vendor Identity</th>
                <th className="py-3 px-4">GSTIN / PAN</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Compliance</th>
                <th className="py-3 px-4">Risk Tier</th>
                <th className="py-3 px-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recentVendors.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-900">
                    <Link href={`/vendors/${v.id}`} className="hover:text-emerald-600">
                      {v.name}
                    </Link>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-600">
                    <div>{v.gstin || 'N/A'}</div>
                    <div className="text-[10px] text-slate-400">{v.pan}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className="px-2 py-0.5 rounded text-[11px] font-semibold"
                      style={{
                        backgroundColor: `${STATUS_COLORS[v.verification_status] || '#64748B'}15`,
                        color: STATUS_COLORS[v.verification_status] || '#64748B'
                      }}
                    >
                      {v.verification_status}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold text-slate-800">
                    {v.compliance_score.toFixed(1)}%
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        v.risk_level === 'LOW'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : v.risk_level === 'MEDIUM'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      {v.risk_level} ({v.risk_score.toFixed(0)}%)
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <Link
                      href={`/vendors/${v.id}`}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-[11px] transition-colors"
                    >
                      View Dossier
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
