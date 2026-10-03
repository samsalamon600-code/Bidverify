'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { api } from '@/services/api';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    window.location.replace('/index.html');
  }, []);

  return (
    <div className="h-screen w-full flex items-center justify-center bg-slate-900 text-white font-medium">
      <div className="animate-pulse">Loading Bidverify Platform...</div>
    </div>
  );
}
