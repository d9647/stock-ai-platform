'use client';

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-layer1 border-t border-borderDark-subtle mt-12 py-8 text-xs text-text-muted text-center">
      <p>
        © {year} AI Stock Challenge · Educational simulation using real historical market data. No real money. Not investment advice. 
         <a href="mailto:dragonfly.ai.solutions@gmail.com" className="text-text-muted hover:underline"> Email: dragonfly.ai.solutions@gmail.com</a> ·
      </p>
    </footer>
  );
}
