/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'SF Mono',
          'Menlo',
          'Monaco',
          'Consolas',
          'Liberation Mono',
          'Courier New',
          'monospace',
        ],
      },
      colors: {
        // Base colors using CSS variables for theme support
        'bg': 'var(--bg)',
        'surface': 'var(--surface)',
        'surface-elevated': 'var(--surface-elevated)',
        'border': 'var(--border)',
        'text': 'var(--text)',
        'text-muted': 'var(--text-muted)',

        // Acid/Demoscene accent colors
        'acid-green': 'var(--acid-green)',
        'acid-cyan': 'var(--acid-cyan)',
        'acid-magenta': 'var(--acid-magenta)',
        'acid-yellow': 'var(--acid-yellow)',
        'matrix-green': 'var(--matrix-green)',
        'terminal-green': 'var(--terminal-green)',

        // Semantic colors
        'accent': 'var(--accent)',
        'accent-glow': 'var(--accent-glow)',
        'success': 'var(--success)',
        'warning': 'var(--warning)',

        // Agent colors
        'purple': 'var(--purple)',
        'gold': 'var(--gold)',
        'crimson': 'var(--crimson)',
        'cyan': 'var(--cyan)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'acid-shift': 'acid-shift 4s ease infinite',
        'cursor-blink': 'cursor-blink 1s step-end infinite',
        'boot-line': 'boot-line 0.3s ease forwards',
      },
      boxShadow: {
        'glow': '0 0 20px var(--accent-glow)',
        'glow-lg': '0 0 30px var(--accent-glow)',
        'terminal': '0 0 10px var(--accent-glow), inset 0 0 10px var(--accent-glow)',
      },
    },
  },
  plugins: [],
}
