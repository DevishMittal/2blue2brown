/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./app/**/*.{js,ts,jsx,tsx}",
      "./pages/**/*.{js,ts,jsx,tsx}", 
      "./components/**/*.{js,ts,jsx,tsx}",
      "./lib/**/*.{js,ts,jsx,tsx}"     
    ],
    theme: {
      extend: {
        typography: {
          DEFAULT: {
            css: {
              maxWidth: 'none',
              code: {
                color: '#16a34a',
                backgroundColor: '#27272a',
                padding: '0.2em 0.4em',
                borderRadius: '0.25rem',
                fontWeight: '400',
              },
              'code::before': {
                content: '""',
              },
              'code::after': {
                content: '""',
              },
              pre: {
                backgroundColor: '#27272a',
                borderRadius: '0.375rem',
                padding: '1rem',
                border: '1px solid #3f3f46',
              },
            },
          },
        },
      },
    },
    plugins: [
      require('@tailwindcss/typography'),
    ],
  }
  