'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { api } from '@/services/api';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if token exists, else go to login
    const token = localStorage.getItem('bidverify_token');
    if (token) {
      const user = api.getCurrentUser();
      if (user?.role === 'Company / Vendor') {
        router.replace(user.vendor_id ? `/vendors/${user.vendor_id}` : '/dashboard');
      } else {
        router.replace('/dashboard');
      }
    } else {
      router.replace('/login');
    }
  }, [router]);

  return (
    <div className="h-screen w-full flex items-center justify-center bg-slate-900 text-white font-medium">
      <div className="animate-pulse">Loading Bidverify Platform...</div>
    </div>
  );
}
