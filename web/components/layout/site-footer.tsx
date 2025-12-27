'use client';

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-layer1 border-t border-borderDark-subtle mt-12 py-8 text-xs text-text-muted text-center">
      <p>
        © {year} AI Stock Challenge · Educational simulation using real historical market data. No real money. Not investment advice. 
      </p> 
      {/*}
      <p>
        <a href="mailto:dragonfly.ai.solutions@gmail.com" className="text-text-muted hover:underline">Email me: dragonfly.ai.solutions@gmail.com</a>
        {' · '}
        <a
          href="https://www.buymeacoffee.com/infinitycodinglabs"
          target="_blank"
          rel="noopener noreferrer"
          title="Buy me a coffee"
          className="inline-flex items-center gap-1 text-text-muted hover:underline"
        >
          {' Buy me a'}
          <img
            src="/buymeacoffee.gif"
            alt="Buy Me A Coffee"
            style={{ height: '25px', width: '25px' }}
          />;-)
        </a>
      </p>
      */}
    </footer>
  );
}
