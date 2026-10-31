export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'], mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'] },
      colors: {
        ink: '#0c0e11', panel: '#14171c', raised: '#1b1f26', line: '#272c35',
        accent: { DEFAULT: '#2f81f7', soft: '#2f81f71f' },
        ok: '#3fb950', bad: '#f85149', warn: '#d29922',
      },
    },
  },
  plugins: [],
};
