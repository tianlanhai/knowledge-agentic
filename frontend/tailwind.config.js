/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 深色主题背景色系
        bg: {
          DEFAULT: '#0f172a',
          card: '#1e293b',
          cardHover: '#334155',
          input: '#1e293b',
        },
        // 蓝紫渐变主色调
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#667eea',
          600: '#5568d3',
          700: '#4f46e5',
          800: '#4338ca',
          900: '#764ba2',
        },
        // 玻璃态效果色
        glass: {
          light: 'rgba(255, 255, 255, 0.1)',
          medium: 'rgba(255, 255, 255, 0.05)',
          dark: 'rgba(0, 0, 0, 0.3)',
        },
        // 文字色系（深色模式）
        text: {
          primary: '#f1f5f9',
          secondary: '#cbd5e1',
          muted: '#94a3b8',
          disabled: '#64748b',
        },
        // 边框色系
        border: {
          DEFAULT: '#334155',
          light: '#475569',
          focus: '#667eea',
        },
      },
      background: {
        'gradient-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-hover': 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
        'gradient-card': 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(102, 126, 234, 0.4)',
        'glow-lg': '0 0 40px rgba(102, 126, 234, 0.6)',
        'card': '0 8px 32px rgba(0, 0, 0, 0.4)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
      },
      backdropBlur: {
        'glass': '12px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 3s ease-in-out infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        slideIn: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
}
