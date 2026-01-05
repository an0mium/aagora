'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Custom fallback renderer */
  fallback?: (error: Error, resetError: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * React Error Boundary component for catching render errors
 *
 * Prevents the entire app from crashing when a component throws an error.
 * Displays a terminal-styled error UI with reset functionality.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetError);
      }

      // Terminal-styled default error UI
      return (
        <div className="min-h-screen bg-bg flex items-center justify-center p-4">
          <div className="max-w-2xl w-full border border-crimson bg-surface p-6 font-mono">
            <div className="flex items-start gap-3 mb-4">
              <div className="text-crimson text-2xl">{'>'}</div>
              <div>
                <div className="text-crimson font-bold mb-2">
                  RUNTIME ERROR
                </div>
                <div className="text-warning text-sm mb-4">
                  Component crashed during render
                </div>
              </div>
            </div>

            <div className="bg-bg border border-border p-3 mb-4 text-text-muted text-xs overflow-x-auto">
              <div className="mb-2 text-text">
                {'>'} {this.state.error.name}
              </div>
              <div className="pl-4 text-crimson">
                {this.state.error.message}
              </div>
              {this.state.error.stack && (
                <div className="mt-3 pl-4 text-text-muted text-[10px] font-normal opacity-70 whitespace-pre-wrap">
                  {this.state.error.stack.split('\n').slice(1, 6).join('\n')}
                </div>
              )}
            </div>

            <button
              onClick={this.resetError}
              className="w-full border border-accent text-accent py-2 px-4 hover:bg-accent hover:text-bg transition-colors font-bold"
            >
              {'>'} RESET_COMPONENT
            </button>

            <div className="mt-4 text-text-muted text-xs text-center">
              If error persists, check browser console for details
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
