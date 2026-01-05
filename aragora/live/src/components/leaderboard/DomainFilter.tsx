'use client';

interface DomainFilterProps {
  domains: string[];
  selectedDomain: string | null;
  onDomainChange: (domain: string | null) => void;
}

export function DomainFilter({ domains, selectedDomain, onDomainChange }: DomainFilterProps) {
  if (domains.length === 0) return null;

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-text-muted">Domain:</span>
      <select
        value={selectedDomain || ''}
        onChange={(e) => onDomainChange(e.target.value || null)}
        className="bg-surface border border-border rounded px-2 py-1 text-sm text-text focus:outline-none focus:border-accent"
      >
        <option value="">All Domains</option>
        {domains.map((domain) => (
          <option key={domain} value={domain}>
            {domain}
          </option>
        ))}
      </select>
    </div>
  );
}
