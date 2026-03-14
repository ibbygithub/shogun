/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // CSS variable bridge — lets Tailwind consume theme vars
        "city-primary":   "var(--city-primary)",
        "city-accent":    "var(--city-accent)",
        "city-highlight": "var(--city-highlight)",
        "city-surface":   "var(--city-surface)",
      },
    },
  },
  plugins: [],
};
