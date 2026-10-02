'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Building2,
  UserPlus,
  FileText,
  ShieldCheck,
  History,
  FileCheck2,
  Sliders,
  LogOut,
  Building,
  UserCheck
} from 'lucide-react';
import { api } from '@/services/api';

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);

  useEffect(() => {
    const user = api.getCurrentUser();
    setCurrentUser(user);
  }, [pathname]);

  // Hide sidebar on login page or landing
  if (pathname === '/login' || pathname === '/') {
    return null;
  }

  const isVendor = currentUser?.role === 'Company / Vendor' || currentUser?.role?.toLowerCase().includes('vendor');
  const vendorId = currentUser?.vendor_id || 1;

  // Role-tailored navigation items
  const navigation = isVendor
    ? [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'My Company Dossier', href: `/vendors/${vendorId}`, icon: Building2 },
        { name: 'Submit Documents & OCR', href: '/documents', icon: FileText },
        { name: 'Compliance Reports', href: '/reports', icon: FileCheck2 },
        { name: 'Audit Trail', href: '/audit', icon: History },
      ]
    : [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Vendors Directory', href: '/vendors', icon: Building2 },
        { name: 'Add New Vendor', href: '/vendors/new', icon: UserPlus },
        { name: 'Documents & OCR Hub', href: '/documents', icon: FileText },
        { name: 'Audit Trail', href: '/audit', icon: History },
        { name: 'Reports Archive', href: '/reports', icon: FileCheck2 },
        { name: 'Scoring Settings', href: '/settings', icon: Sliders },
      ];

  const handleLogout = () => {
    api.logout();
    router.push('/login');
  };

  const getInitials = (name?: string) => {
    if (!name) return isVendor ? 'VN' : 'PO';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none min-h-screen">
      <div>
        {/* Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800/80 gap-3">
          <div className="h-9 w-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold shadow-md shadow-emerald-900/30">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="font-bold text-white text-base tracking-wide flex items-center gap-1.5">
              BIDVERIFY <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">AI</span>
            </div>
            <div className="text-[11px] text-slate-400 font-medium">Compliance & Risk Engine</div>
          </div>
        </div>

        {/* Portal Type Badge */}
        <div className="px-5 pt-4 pb-1">
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-[11px] font-semibold text-slate-300">
            {isVendor ? (
              <>
                <Building className="h-3.5 w-3.5 text-blue-400" />
                <span className="text-blue-300">Vendor Compliance Portal</span>
              </>
            ) : (
              <>
                <UserCheck className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-300">Procurement Officer Portal</span>
              </>
            )}
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Navigation Menu
          </div>
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-600/15 text-emerald-400 border border-emerald-500/30 shadow-sm font-semibold'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Profile & Sign Out */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-800/60 mb-3 border border-slate-700/50">
          <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${
            isVendor ? 'bg-blue-600' : 'bg-emerald-700'
          }`}>
            {getInitials(currentUser?.full_name)}
          </div>
          <div className="overflow-hidden">
            <div className="text-xs font-semibold text-slate-200 truncate">
              {currentUser?.full_name || (isVendor ? 'Vendor Representative' : 'Rajesh Sharma')}
            </div>
            <div className="text-[11px] text-slate-400 truncate">
              {currentUser?.company_name || currentUser?.role || 'Procurement Officer'}
            </div>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign Out of Portal
        </button>
      </div>
    </aside>
  );
}
