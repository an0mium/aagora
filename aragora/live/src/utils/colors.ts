/**
 * Shared color utility functions for consistent styling across components.
 * These are pure functions that return Tailwind CSS classes based on values.
 */

/**
 * Returns a color class based on ELO rating thresholds.
 * @param elo - The ELO rating value
 * @returns Tailwind text color class
 */
export const getEloColor = (elo: number): string => {
  if (elo >= 1600) return 'text-green-400';
  if (elo >= 1500) return 'text-yellow-400';
  if (elo >= 1400) return 'text-orange-400';
  return 'text-red-400';
};

/**
 * Returns a color class based on consistency score (0-1).
 * @param consistency - Value between 0 and 1
 * @returns Tailwind text color class
 */
export const getConsistencyColor = (consistency: number): string => {
  if (consistency >= 0.8) return 'text-green-400';
  if (consistency >= 0.6) return 'text-yellow-400';
  return 'text-red-400';
};

/**
 * Returns a color class based on confidence score (0-1).
 * Alias for getConsistencyColor with same thresholds.
 * @param confidence - Value between 0 and 1
 * @returns Tailwind text color class
 */
export const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return 'text-green-400';
  if (confidence >= 0.6) return 'text-yellow-400';
  return 'text-red-400';
};

/**
 * Returns badge styling classes for ranking positions.
 * @param rank - The ranking position (1-based)
 * @returns Tailwind classes for badge styling
 */
export const getRankBadge = (rank: number): string => {
  if (rank === 1) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  if (rank === 2) return 'bg-gray-400/20 text-gray-300 border-gray-400/30';
  if (rank === 3) return 'bg-amber-600/20 text-amber-500 border-amber-600/30';
  return 'bg-surface text-text-muted border-border';
};

/**
 * Returns color classes based on status string.
 * @param status - Status string (healthy, degraded, down, etc.)
 * @returns Tailwind classes for status styling
 */
export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    healthy: 'text-green-400',
    ok: 'text-green-400',
    good: 'text-green-400',
    degraded: 'text-yellow-400',
    warning: 'text-yellow-400',
    down: 'text-red-400',
    error: 'text-red-400',
    critical: 'text-red-400',
  };
  return colors[status.toLowerCase()] || 'text-text-muted';
};

/**
 * Returns badge styling classes based on type/category.
 * @param type - Type string for categorization
 * @returns Tailwind classes for badge styling
 */
export const getTypeBadge = (type: string): string => {
  const colors: Record<string, string> = {
    // Insight types
    insight: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    pattern: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    anomaly: 'bg-red-500/20 text-red-400 border-red-500/30',
    trend: 'bg-green-500/20 text-green-400 border-green-500/30',
    // Debate roles
    pro: 'bg-green-500/20 text-green-400 border-green-500/30',
    con: 'bg-red-500/20 text-red-400 border-red-500/30',
    judge: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    // Default
    default: 'bg-surface text-text-muted border-border',
  };
  return colors[type.toLowerCase()] || colors.default;
};

/**
 * Returns a color class based on a numeric score (0-1 or 0-100).
 * Auto-detects if value is percentage (>1) or decimal.
 * @param score - Score value
 * @returns Tailwind text color class
 */
export const getScoreColor = (score: number): string => {
  // Normalize to 0-1 range if percentage
  const normalized = score > 1 ? score / 100 : score;
  if (normalized >= 0.7) return 'text-green-400';
  if (normalized >= 0.4) return 'text-yellow-400';
  return 'text-red-400';
};

/**
 * Returns badge styling classes for insight types.
 * @param type - Insight type (consensus, pattern, agent_performance, divergence)
 * @returns Tailwind classes for badge styling
 */
export const getInsightTypeColor = (type: string): string => {
  switch (type) {
    case 'consensus':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'pattern':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'agent_performance':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
    case 'divergence':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
};

/**
 * Returns badge styling classes for flip event types.
 * @param type - Flip type (contradiction, retraction, qualification, refinement)
 * @returns Tailwind classes for badge styling
 */
export const getFlipTypeColor = (type: string): string => {
  switch (type) {
    case 'contradiction':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'retraction':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'qualification':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'refinement':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
};

/**
 * Returns badge styling classes for domain types.
 * @param domain - Domain type (technical, ethics, creative, analytical, general)
 * @returns Tailwind classes for badge styling
 */
export const getDomainColor = (domain: string): string => {
  const colors: Record<string, string> = {
    technical: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    ethics: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    creative: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    analytical: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    general: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };
  return colors[domain] || colors.general;
};
