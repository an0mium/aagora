'use client';

interface SectionHeaderProps {
  title: string;
}

export function SectionHeader({ title }: SectionHeaderProps) {
  return (
    <div className="text-center mb-8">
      <p className="text-acid-green/50 font-mono text-xs mb-2">{'═'.repeat(30)}</p>
      <h2 className="text-acid-green font-mono text-lg">{'>'} {title}</h2>
      <p className="text-acid-green/50 font-mono text-xs mt-2">{'═'.repeat(30)}</p>
    </div>
  );
}
