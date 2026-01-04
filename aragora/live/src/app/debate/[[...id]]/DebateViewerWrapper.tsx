'use client';

import { useState, useEffect } from 'react';
import { DebateViewer } from '@/components/DebateViewer';
import Link from 'next/link';
import { Scanlines, CRTVignette } from '@/components/MatrixRain';
import { AsciiBannerCompact } from '@/components/AsciiBanner';
import { ThemeToggle } from '@/components/ThemeToggle';

export function DebateViewerWrapper() {
  const [debateId, setDebateId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Extract debate ID from actual browser URL: /debate/abc123 -> abc123
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    const id = pathSegments[1] || null; // ['debate', 'abc123'] -> 'abc123'
    setDebateId(id);
    setIsLoading(false);
  }, []);

  // Show loading while determining debate ID
  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-acid-green font-mono animate-pulse">LOADING...</div>
      </div>
    );
  }

  // No ID provided - show message
  if (!debateId) {
    return (
      <>
        <Scanlines opacity={0.02} />
        <CRTVignette />
        <main className="min-h-screen bg-bg text-text relative z-10">
          <header className="border-b border-acid-green/30 bg-surface/80 backdrop-blur-sm sticky top-0 z-50">
            <div className="container mx-auto px-4 py-3 flex items-center justify-between">
              <Link href="/">
                <AsciiBannerCompact connected={true} />
              </Link>
              <ThemeToggle />
            </div>
          </header>
          <div className="container mx-auto px-4 py-20 text-center">
            <div className="text-acid-green font-mono text-xl mb-4">{'>'} NO DEBATE ID PROVIDED</div>
            <Link href="/" className="text-acid-cyan hover:text-acid-green transition-colors font-mono">
              [RETURN TO DASHBOARD]
            </Link>
          </div>
        </main>
      </>
    );
  }

  return <DebateViewer debateId={debateId} />;
}
