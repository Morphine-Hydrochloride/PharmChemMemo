/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#6366f1', // Indigo 500
                secondary: '#8b5cf6', // Violet 500
                success: '#10b981', // Emerald 500
                danger: '#ef4444', // Red 500
                surface: '#ffffff',
                background: '#f8fafc',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
