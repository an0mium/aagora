'use client';

import { LearningEvolution } from '../LearningEvolution';

export function LearningTab() {
  return (
    <div
      id="learning-panel"
      role="tabpanel"
      aria-labelledby="learning-tab"
      className="max-h-[500px] overflow-y-auto"
    >
      <LearningEvolution />
    </div>
  );
}
