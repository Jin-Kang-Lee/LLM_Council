/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                zinc: {
                    850: '#1f1f23',
                }
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'fade-in': 'fadeIn 0.5s ease-out',
                'slide-up': 'slideUp 0.4s ease-out',
                'typing': 'typing 1.5s ease-in-out infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                typing: {
                    '0%, 100%': { opacity: '0.3' },
                    '50%': { opacity: '1' },
                }
            },
            typography: {
                invert: {
                    css: {
                        '--tw-prose-body': 'rgb(212 212 216)',
                        '--tw-prose-headings': 'rgb(250 250 250)',
                        '--tw-prose-links': 'rgb(96 165 250)',
                        '--tw-prose-bold': 'rgb(250 250 250)',
                        '--tw-prose-code': 'rgb(167 139 250)',
                    }
                }
            }
        },
    },
    plugins: [],
}
