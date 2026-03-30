/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0f172a',
        'dark-card': '#1e293b',
        'dark-border': '#334155',
        'accent-green': '#10b981',
        'accent-orange': '#f59e0b',
        'accent-blue': '#38bdf8',
        'accent-purple': '#a855f7',
      }
    },
  },
  plugins: [],
}
