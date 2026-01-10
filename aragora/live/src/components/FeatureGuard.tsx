'use client';

import React, { ReactNode } from 'react';
import { useFeatureStatus, useFeatureInfo } from '@/context/FeaturesContext';

interface FeatureGuardProps {
  /** ID of the feature to check */
  featureId: string;
  /** Content to render when feature is available */
  children: ReactNode;
  /** Optional custom fallback when feature is unavailable */
  fallback?: ReactNode;
  /** Hide completely instead of showing fallback */
  hideWhenUnavailable?: boolean;
}

/**
 * Guard component for conditional rendering based on feature availability
 *
 * Wraps content that depends on optional backend features and shows
 * helpful messages when features are unavailable.
 *
 * @example
 * // Basic usage
 * <FeatureGuard featureId="pulse">
 *   <TrendingTopicsPanel />
 * </FeatureGuard>
 *
 * // With custom fallback
 * <FeatureGuard
 *   featureId="memory"
 *   fallback={<div>Memory features coming soon</div>}
 * >
 *   <MemoryInspector />
 * </FeatureGuard>
 *
 * // Hide completely when unavailable
 * <FeatureGuard featureId="experimental" hideWhenUnavailable>
 *   <ExperimentalPanel />
 * </FeatureGuard>
 */
export function FeatureGuard({
  featureId,
  children,
  fallback,
  hideWhenUnavailable = false,
}: FeatureGuardProps) {
  const available = useFeatureStatus(featureId);

  if (available) {
    return <>{children}</>;
  }

  if (hideWhenUnavailable) {
    return null;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  return <FeatureUnavailable featureId={featureId} />;
}

interface FeatureUnavailableProps {
  featureId: string;
}

/**
 * Default fallback component for unavailable features
 *
 * Shows feature name and optional install hints from the backend.
 */
function FeatureUnavailable({ featureId }: FeatureUnavailableProps) {
  const info = useFeatureInfo(featureId);

  return (
    <div className="bg-surface border border-amber-500/30 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-amber-400 text-lg">!</span>
        <h3 className="text-sm font-medium text-amber-400">
          {info?.name || featureId} Unavailable
        </h3>
      </div>
      <p className="text-xs text-text-muted mb-2">
        {info?.description || `The ${featureId} feature is not currently available.`}
      </p>
      {info?.install_hint && (
        <details className="mt-2">
          <summary className="text-xs text-text-muted cursor-pointer hover:text-text">
            How to enable
          </summary>
          <p className="mt-2 text-xs text-amber-300/70 bg-amber-900/10 p-2 rounded">
            {info.install_hint}
          </p>
        </details>
      )}
    </div>
  );
}

/**
 * HOC to wrap any component with FeatureGuard
 *
 * @example
 * const GuardedPulsePanel = withFeatureGuard(TrendingTopicsPanel, 'pulse');
 */
export function withFeatureGuard<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  featureId: string,
  options: { hideWhenUnavailable?: boolean } = {}
) {
  return function WithFeatureGuard(props: P) {
    return (
      <FeatureGuard
        featureId={featureId}
        hideWhenUnavailable={options.hideWhenUnavailable}
      >
        <WrappedComponent {...props} />
      </FeatureGuard>
    );
  };
}
