/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // FLOOD-X Design System — dark emergency ops palette
        surface: {
          900: '#080C14',  // darkest background
          800: '#0D1421',  // panel background
          700: '#111927',  // card background
          600: '#162133',  // elevated card
          500: '#1C2A40',  // border/divider
          400: '#243350',  // hover state
        },
        accent: {
          blue:   '#3B82F6',  // primary interactive
          cyan:   '#06B6D4',  // data highlights
          teal:   '#14B8A6',  // safe / low risk
        },
        risk: {
          low:      '#10B981',  // emerald
          moderate: '#F59E0B',  // amber
          high:     '#F97316',  // orange
          critical: '#EF4444',  // red
        },
        flood: {
          shallow:  '#60A5FA',  // 0–20cm
          moderate: '#2563EB',  // 20–50cm
          deep:     '#1E3A8A',  // 50cm+
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in':   'slideIn 0.2s ease-out',
        'fade-in':    'fadeIn 0.3s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%':   { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)',    opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
