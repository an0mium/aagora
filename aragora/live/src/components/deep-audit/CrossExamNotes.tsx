'use client';

interface CrossExamNotesProps {
  notes: string;
}

export function CrossExamNotes({ notes }: CrossExamNotesProps) {
  return (
    <div className="px-4 pb-4">
      <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <span>🔍</span>
          <span className="text-sm font-medium text-indigo-400">Cross-Examination Notes</span>
        </div>
        <p className="text-xs text-text-muted whitespace-pre-wrap">
          {notes.slice(0, 500)}
          {notes.length > 500 && '...'}
        </p>
      </div>
    </div>
  );
}
