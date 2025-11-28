import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      // Neobrutalist: No border radius
      borderRadius: {
        lg: '0',
        md: '0',
        sm: '0',
        none: '0',
      },
      // Border widths for neobrutalism
      borderWidth: {
        'neo': '3px',
        'neo-sm': '2px',
        'neo-lg': '4px',
      },
      // Hard shadows (no blur)
      boxShadow: {
        'neo-sm': '3px 3px 0px 0px #0D0D0D',
        'neo': '5px 5px 0px 0px #0D0D0D',
        'neo-lg': '8px 8px 0px 0px #0D0D0D',
        'neo-blue': '5px 5px 0px 0px #0066FF',
        'neo-hover': '7px 7px 0px 0px #0D0D0D',
        'neo-active': '2px 2px 0px 0px #0D0D0D',
        'none': 'none',
      },
      // Neobrutalist color palette
      colors: {
        // Core monochromatic
        'neo-white': '#FFFFFF',
        'neo-offwhite': '#F8F9FA',
        'neo-lightgrey': '#E9ECEF',
        'neo-grey': '#6C757D',
        'neo-darkgrey': '#343A40',
        'neo-black': '#0D0D0D',
        // Accent blues
        'neo-blue': '#0066FF',
        'neo-blue-light': '#E6F0FF',
        'neo-blue-deep': '#0052CC',
        // Utility colors
        'neo-success': '#10B981',
        'neo-warning': '#F59E0B',
        'neo-error': '#EF4444',
        // CSS variable-based colors (for shadcn compatibility)
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      // Typography
      fontFamily: {
        'display': ['var(--font-display)', 'Arial Black', 'sans-serif'],
        'mono': ['var(--font-mono)', 'Courier New', 'monospace'],
        'body': ['var(--font-body)', 'system-ui', 'sans-serif'],
      },
      // Animation keyframes
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in-down': {
          '0%': { opacity: '0', transform: 'translateY(-16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in-left': {
          '0%': { opacity: '0', transform: 'translateX(-16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'fade-in-right': {
          '0%': { opacity: '0', transform: 'translateX(16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(0)' },
        },
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      // Animation classes
      animation: {
        'fade-in': 'fade-in 0.4s ease-out forwards',
        'fade-in-up': 'fade-in-up 0.5s ease-out forwards',
        'fade-in-down': 'fade-in-down 0.5s ease-out forwards',
        'fade-in-left': 'fade-in-left 0.5s ease-out forwards',
        'fade-in-right': 'fade-in-right 0.5s ease-out forwards',
        'scale-in': 'scale-in 0.3s ease-out forwards',
        'slide-up': 'slide-up 0.3s ease-out forwards',
        'slide-down': 'slide-down 0.3s ease-out forwards',
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
      // Animation delays
      transitionDelay: {
        '0': '0ms',
        '75': '75ms',
        '100': '100ms',
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
        '400': '400ms',
        '500': '500ms',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
