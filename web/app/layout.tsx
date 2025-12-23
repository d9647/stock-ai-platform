import type { Metadata } from 'next';
import Link from 'next/link';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { SiteFooter } from '@/components/layout/site-footer';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Stock Simulation Lab',
  description:
    'A calm, educational stock market simulation with AI-assisted analysis based on historical market data.',
  keywords: [
    'stock simulation',
    'portfolio learning',
    'AI market analysis',
    'education',
    'trading simulator',
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body className={`${inter.className} bg-base text-text-primary`}>
        {/* Header (OpenAI-style: minimal, text-first) */}
        <header className="fixed top-0 inset-x-0 z-50 bg-layer1 border-b border-borderDark-subtle">
          <div className="max-w-7xl mx-auto px-4">
            <div className="h-11 flex items-center">
              <Link
                href="/"
                className="
                  text-sm font-medium text-text-secondary
                  hover:text-text-primary
                  transition-colors
                "
              >
                Stock Simulation Lab
              </Link>
            </div>
          </div>
        </header>

        {/* Spacer for fixed header */}
        <div className="h-11" aria-hidden="true" />

        <Providers>
          {/* Page layout */}
          <div className="min-h-screen flex flex-col bg-base">
            <main className="flex-1">{children}</main>
            <SiteFooter />
          </div>
        </Providers>
      </body>
    </html>
  );
}
