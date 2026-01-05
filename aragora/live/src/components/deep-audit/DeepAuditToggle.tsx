'use client';

interface DeepAuditToggleProps {
  isActive: boolean;
  onToggle: () => void;
}

export function DeepAuditToggle({ isActive, onToggle }: DeepAuditToggleProps) {
  return (
    <button
      onClick={onToggle}
      className={`px-3 py-1.5 text-sm rounded flex items-center gap-2 transition-colors ${
        isActive
          ? 'bg-purple-500 text-white'
          : 'bg-purple-500/20 text-purple-400 border border-purple-500/30 hover:bg-purple-500/30'
      }`}
    >
      <span>🔬</span>
      <span>{isActive ? 'Deep Audit Active' : 'Deep Audit'}</span>
    </button>
  );
}
