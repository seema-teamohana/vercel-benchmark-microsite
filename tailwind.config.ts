import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          DEFAULT: '#0F172A',  // slate-900
          light:   '#334155',  // slate-700
        },
        accent: {
          DEFAULT: '#0891B2',  // cyan-600
          light:   '#22D3EE',  // cyan-400
        },
      },
    },
  },
  plugins: [],
}
export default config
