import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        /* =========================================================
           OpenAI-style dark surfaces (USE THESE)
           ========================================================= */

        base: '#0f1115',
        layer1: '#151821',
        layer2: '#1c1f2b',
        layer3: '#24283a',

        text: {
          primary: '#e6e8ee',
          secondary: '#a8adbd',
          muted: '#6f748a',
          inverse: '#0f1115',
        },

        button: {
          primary: '#e6e8ee',
          hover: '#ffffff',
        },

        accent: '#7aa2ff',
        success: '#3ddc97',
        warning: '#f5c26b',
        error: '#ff6b6b',

        /* =========================================================
           Border colors (IMPORTANT)
           ========================================================= */

        // REQUIRED by shadcn → DO NOT REMOVE
        border: 'hsl(var(--border))',

        // Dark-theme borders (USE THESE EXPLICITLY)
        borderDark: {
          subtle: '#2a2f45',
          strong: '#3a4060',
        },

        /* =========================================================
           shadcn HSL token system (UNCHANGED)
           ========================================================= */

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
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },

        /* =========================================================
           Financial semantics (UNCHANGED)
           ========================================================= */

        bullish: {
          DEFAULT: '#10B981',
          light: '#D1FAE5',
          foreground: '#FFFFFF',
        },
        bearish: {
          DEFAULT: '#EF4444',
          light: '#FEE2E2',
          foreground: '#FFFFFF',
        },
        neutral: {
          DEFAULT: '#6B7280',
          light: '#F3F4F6',
          foreground: '#FFFFFF',
        },

        buy: {
          DEFAULT: '#059669',
          bg: '#D1FAE5',
        },
        sell: {
          DEFAULT: '#DC2626',
          bg: '#FEE2E2',
        },
        hold: {
          DEFAULT: '#F59E0B',
          bg: '#FEF3C7',
        },
      },

      boxShadow: {
        soft: '0 4px 16px rgba(0,0,0,0.4)',
        medium: '0 8px 32px rgba(0,0,0,0.5)',
      },

      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },

      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains-mono)', 'monospace'],
      },

      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },

      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
