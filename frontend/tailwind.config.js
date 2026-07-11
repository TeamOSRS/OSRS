/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        osrsBg: "#FDFDFD",
        osrsCard: "#F0F4F8",
        osrsBorder: "#DDE3EA",
        osrsText: "#1A1C1E",
        osrsMuted: "#74777F",
        osrsCyan: "#006494",
        osrsBlue: "#0B57D0",
        osrsGreen: "#146C2E",
        osrsAmber: "#B3261E",
        osrsRed: "#B3261E",
        mdPrimary: "#D3E3FD",
        mdSecondary: "#E8DEF8",
        mdTertiary: "#FFD8E4",
        mdPrimaryText: "#041E49",
        mdSecondaryText: "#1D192B",
      },
      fontFamily: {
        sans: ['Roboto', 'Inter', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}

