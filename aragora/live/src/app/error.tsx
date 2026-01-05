'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('App error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="max-w-2xl w-full border border-crimson bg-surface p-6 font-mono">
        <div className="flex items-start gap-3 mb-4">
          <div className="text-crimson text-2xl glow-text-subtle">{'>'}</div>
          <div>
            <div className="text-crimson font-bold mb-2 text-xl">
              APPLICATION ERROR
            </div>
            <div className="text-warning text-sm mb-2">
              Something went wrong in the Aragora Live interface
            </div>
            {error.digest && (
              <div className="text-text-muted text-xs">
                Error ID: {error.digest}
              </div>
            )}
          </div>
        </div>

        <div className="bg-bg border border-border p-4 mb-4 text-text-muted text-sm overflow-x-auto">
          <div className="mb-2 text-text font-bold">
            {'>'} {error.name || 'Error'}
          </div>
          <div className="pl-4 text-crimson">
            {error.message || 'An unexpected error occurred'}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={reset}
            className="flex-1 border border-accent text-accent py-2 px-4 hover:bg-accent hover:text-bg transition-colors font-bold"
          >
            {'>'} RETRY
          </button>
          <Link
            href="/"
            className="flex-1 border border-text-muted text-text-muted py-2 px-4 hover:bg-text-muted hover:text-bg transition-colors text-center"
          >
            {'>'} HOME
          </Link>
        </div>

        <div className="mt-6 p-3 bg-warning/10 border border-warning/30 text-warning text-xs">
          <div className="font-bold mb-1">{'>'} TROUBLESHOOTING</div>
          <ul className="pl-4 space-y-1">
            <li>• Check browser console for details</li>
            <li>• Verify backend connection</li>
            <li>• Clear cache and reload</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
