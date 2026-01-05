/**
 * Shared formatting utility functions for consistent data display.
 */

/**
 * Formats ELO change with +/- prefix.
 * @param change - The ELO change value
 * @returns Formatted string with sign prefix
 */
export const formatEloChange = (change: number): string => {
  if (change > 0) return `+${change}`;
  return String(change);
};

/**
 * Formats a duration in seconds to a human-readable format.
 * @param seconds - Duration in seconds
 * @returns Formatted string (e.g., "30s", "5m", "2h")
 */
export const formatAge = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h`;
  return `${Math.round(seconds / 86400)}d`;
};

/**
 * Formats a date/timestamp to a relative time string.
 * @param date - Date string, Date object, or timestamp
 * @returns Relative time string (e.g., "2 hours ago", "just now")
 */
export const formatTimeAgo = (date: string | Date | number): string => {
  const now = Date.now();
  const then = typeof date === 'number' ? date : new Date(date).getTime();
  const seconds = Math.floor((now - then) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    return `${mins} minute${mins !== 1 ? 's' : ''} ago`;
  }
  if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600);
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  }
  const days = Math.floor(seconds / 86400);
  return `${days} day${days !== 1 ? 's' : ''} ago`;
};

/**
 * Formats a decimal value as a percentage.
 * @param value - Decimal value (0-1) or percentage (0-100)
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted percentage string with % suffix
 */
export const formatPercent = (value: number, decimals = 0): string => {
  // Auto-detect if already a percentage
  const percent = value > 1 ? value : value * 100;
  return `${percent.toFixed(decimals)}%`;
};

/**
 * Formats a number with thousands separators.
 * @param value - Number to format
 * @returns Formatted string with commas
 */
export const formatNumber = (value: number): string => {
  return value.toLocaleString();
};

/**
 * Formats a date to a localized date string.
 * @param date - Date string or Date object
 * @returns Formatted date string
 */
export const formatDate = (date: string | Date): string => {
  return new Date(date).toLocaleDateString();
};

/**
 * Formats a date to a localized time string.
 * @param date - Date string or Date object
 * @returns Formatted time string
 */
export const formatTime = (date: string | Date): string => {
  return new Date(date).toLocaleTimeString();
};

/**
 * Formats a date to a localized date and time string.
 * @param date - Date string or Date object
 * @returns Formatted date and time string
 */
export const formatDateTime = (date: string | Date): string => {
  const d = new Date(date);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
};

/**
 * Truncates a string to a maximum length with ellipsis.
 * @param str - String to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated string with ellipsis if needed
 */
export const truncate = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
};
