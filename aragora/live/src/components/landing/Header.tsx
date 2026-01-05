'use client';

import { AsciiBannerCompact } from '../AsciiBanner';
import { ThemeToggle } from '../ThemeToggle';
import { BackendSelector } from '../BackendSelector';

export function Header() {
  return (
    <header className="border-b border-acid-green/30 bg-surface/80 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <AsciiBannerCompact connected={true} />
        <div className="flex items-center gap-4">
          <a
            href="/about"
            className="text-xs font-mono text-text-muted hover:text-acid-green transition-colors"
          >
            [ABOUT]
          </a>
          <a
            href="https://live.aragora.ai"
            className="text-xs font-mono text-acid-cyan hover:text-acid-green transition-colors"
          >
            [LIVE DASHBOARD]
          </a>
          <BackendSelector compact />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
