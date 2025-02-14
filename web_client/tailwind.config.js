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
        cyber: ['Orbitron', 'sans-serif'],
      },
      animation: {
        'glow': 'glow 1s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          'from': {
            'text-shadow': '0 0 10px #22d3ee, 0 0 20px #22d3ee, 0 0 30px #22d3ee',
          },
          'to': {
            'text-shadow': '0 0 20px #ec4899, 0 0 30px #ec4899, 0 0 40px #ec4899',
          },
        },
      },
    },
  },
  plugins: [],
} 