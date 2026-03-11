/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        body: ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        ink: {
          50: '#f5f3ef',
          100: '#e8e3d9',
          200: '#d1c9b5',
          300: '#b5a98a',
          400: '#9a8a64',
          500: '#7d6e4a',
          600: '#63563a',
          700: '#4a4030',
          800: '#332c22',
          900: '#1e1a14',
          950: '#110f0b',
        },
        atlas: {
          blue: '#2563a8',
          teal: '#0d7377',
          amber: '#c8860a',
          red: '#c0392b',
          green: '#1a6b3a',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease forwards',
        'slide-up': 'slideUp 0.35s ease forwards',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
        'stream-in': 'streamIn 0.2s ease forwards',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
        streamIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
