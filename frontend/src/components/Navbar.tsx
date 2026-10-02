'use client';

import React, { useEffect, useState, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { ShieldCheck, Database, Server, UserCheck, Building2, ChevronDown, Check, RefreshCw } from 'lucide-react';
import { api } from '@/services/api';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCurrentUser(api.getCurrentUser());
  }, [pathname]);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (pathname === '/login' || pathname === '/') {
    return null;
  }

  const isVendor = currentUser?.role === 'Company / Vendor' || currentUser?.role?.toLowerCase().includes('vendor');

  const getTitle = () => {
    if (pathname.includes('/vendors/new')) return 'Vendor Onboarding & Registration';
    if (pathname.includes('/vendors/')) return 'Vendor Verification Dossier';
    if (pathname === '/vendors') return 'Vendor Management Directory';
    if (pathname === '/documents') return 'Document Management & OCR Pipeline';
    if (pathname === '/audit') return 'Procurement Audit Trail';
    if (pathname === '/reports') return 'Official Verification Reports';
    if (pathname === '/settings') return 'Risk Engine & Scoring Configuration';
    return isVendor ? 'Vendor Portal & Compliance Summary' : 'Procurement Officer Control Center';
  };

  const handleQuickSwitch = async (role: 'Procurement Officer' | 'Company / Vendor' | 'Admin') => {
    setSwitching(true);
    setMenuOpen(false);
    try {
      await api.demoLogin(role);
      const updated = api.getCurrentUser();
      setCurrentUser(updated);
      if (role === 'Company / Vendor') {
        router.push(updated.vendor_id ? `/vendors/${updated.vendor_id}` : '/dashboard');
      } else {
        router.push('/dashboard');
      }
      router.refresh();
    } catch (err: any) {
      alert(err.message || 'Failed to switch persona');
    } finally {
      setSwitching(false);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 sm:px-8 flex items-center justify-between shrink-0 sticky top-0 z-20 shadow-2xs">
      <div>
        <h1 className="text-base sm:text-lg font-bold text-slate-900 leading-tight">{getTitle()}</h1>
        <p className="text-[11px] text-slate-500 font-medium">
          {isVendor ? 'Enterprise Vendor Compliance Submissions' : 'Enterprise Pre-Procurement Compliance Evaluation'}
        </p>
      </div>

      <div className="flex items-center gap-2.5">
        {/* Quick Persona Switcher */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            disabled={switching}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold transition-all ${
              isVendor
                ? 'bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100'
                : 'bg-emerald-50 border-emerald-200 text-emerald-800 hover:bg-emerald-100'
            }`}
          >
            {switching ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : isVendor ? (
              <Building2 className="h-3.5 w-3.5 text-blue-600" />
            ) : (
              <UserCheck className="h-3.5 w-3.5 text-emerald-600" />
            )}
            <span className="hidden sm:inline">Persona:</span>
            <span className="font-bold">{isVendor ? 'Company / Vendor' : 'Officer'}</span>
            <ChevronDown className="h-3 w-3 opacity-60" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50 text-xs animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-3.5 py-2 border-b border-slate-100">
                <p className="font-bold text-slate-900">Switch Active Persona</p>
                <p className="text-[10px] text-slate-500">Instantly test both perspectives</p>
              </div>

              <div className="p-1 space-y-0.5">
                <button
                  type="button"
                  onClick={() => handleQuickSwitch('Procurement Officer')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left font-medium transition-colors ${
                    !isVendor
                      ? 'bg-emerald-50 text-emerald-900 font-bold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <UserCheck className="h-4 w-4 text-emerald-600" />
                    <div>
                      <div>Procurement Officer</div>
                      <div className="text-[10px] text-slate-400 font-normal">officer@bidverify.com</div>
                    </div>
                  </div>
                  {!isVendor && <Check className="h-3.5 w-3.5 text-emerald-600" />}
                </button>

                <button
                  type="button"
                  onClick={() => handleQuickSwitch('Company / Vendor')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left font-medium transition-colors ${
                    isVendor
                      ? 'bg-blue-50 text-blue-900 font-bold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-blue-600" />
                    <div>
                      <div>Company / Vendor</div>
                      <div className="text-[10px] text-slate-400 font-normal">vendor@alphalogix.com</div>
                    </div>
                  </div>
                  {isVendor && <Check className="h-3.5 w-3.5 text-blue-600" />}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Mock API indicator */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-medium">
          <Database className="h-3.5 w-3.5 text-amber-600" />
          <span>Govt. Registry: <b>Active (Mock)</b></span>
        </div>

        {/* Backend health */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-medium">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="hidden sm:inline">Engines:</span> <b>Operational</b>
        </div>
      </div>
    </header>
  );
}
