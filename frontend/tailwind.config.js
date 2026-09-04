/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        lenny: {
          50: '#fdf8f0',
          100: '#faefd9',
          500: '#e8a020',
          600: '#c97f10',
          900: '#1a1208',
        },
      },
    },
  },
  plugins: [],
}
