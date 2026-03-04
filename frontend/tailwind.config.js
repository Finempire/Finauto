/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
        extend: {
            colors: {
                navy: { DEFAULT: '#1A3C5E', light: '#2A5580', dark: '#0F2640' },
                accent: { DEFAULT: '#2E86AB', light: '#4BA3C7', dark: '#1E6B8C' },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
            },
        },
    },
    plugins: [],
};
