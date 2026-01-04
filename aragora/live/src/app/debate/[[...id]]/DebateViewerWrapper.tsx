'use client';

import { useParams } from 'next/navigation';
import { DebateViewer } from '@/components/DebateViewer';
import Link from 'next/link';
import { Scanlines, CRTVignette } from '@/components/MatrixRain';
import { AsciiBannerCompact } from '@/components/AsciiBanner';
import { ThemeToggle } from '@/components/ThemeToggle';

export function DebateViewerWrapper() {
  const params = useParams();
  const idSegments = params.id as string[] | undefined;
  const debateId = idSegments?.[0];

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
