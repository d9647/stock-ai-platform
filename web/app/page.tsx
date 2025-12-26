import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-base text-text-primary">
      <div className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto">

          {/* Hero */}
          <div className="text-center mb-14">
            <h1 className="text-4xl font-semibold text-text-primary mb-4">
              Stock Simulation Lab
            </h1>
            <p className="text-lg text-text-secondary mb-3">
              A structured way to learn portfolio decision-making using real historical market data.
            </p>
            <p className="text-sm text-text-muted max-w-2xl mx-auto">
              This is a turn-based educational simulation where you manage a virtual portfolio
              and review AI-generated market analysis based on past prices and news.
              Your decisions are evaluated against an AI reference model for learning and grading.
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-layer2 border border-borderDark-subtle p-6 rounded-md">
              <div className="text-sm font-medium text-text-primary mb-2">
                Turn-based structure
              </div>
              <p className="text-sm text-text-secondary">
                Advance one market day at a time. There is no time pressure,
                allowing students to focus on reasoning and tradeoffs.
              </p>
            </div>

            <div className="bg-layer2 border border-borderDark-subtle p-6 rounded-md">
              <div className="text-sm font-medium text-text-primary mb-2">
                AI-assisted analysis
              </div>
              <p className="text-sm text-text-secondary">
                Each day includes AI-generated insights derived from technical indicators,
                historical news sentiment, and risk signals from real past data.
              </p>
            </div>

            <div className="bg-layer2 border border-borderDark-subtle p-6 rounded-md">
              <div className="text-sm font-medium text-text-primary mb-2">
                Performance evaluation
              </div>
              <p className="text-sm text-text-secondary">
                Results are scored based on portfolio return, decision discipline,
                and comparison against an AI benchmark. Final outcomes are graded A–F.
              </p>
            </div>
          </div>

          {/* Play Options */}
          <div className="text-center mb-12">
            <h2 className="text-xl font-semibold text-text-primary mb-5">
              Play options
            </h2>

            {/* Primary action */}
            <Link
              href="/game"
              className="inline-block btn-primary px-7 py-2.5 text-sm font-medium border border-borderDark-subtle rounded-sm"
            >
              Play Solo
            </Link>

            {/* Divider */}
            <div className="flex items-center justify-center gap-4 my-6">
              <div className="h-px bg-borderDark-subtle flex-1 max-w-xs" />
              <span className="text-xs text-text-muted uppercase tracking-wide">
                or
              </span>
              <div className="h-px bg-borderDark-subtle flex-1 max-w-xs" />
            </div>

            {/* Secondary actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/multiplayer/create"
                className="inline-block px-6 py-2.5 text-sm font-medium border border-borderDark-subtle rounded-sm text-text-secondary hover:text-text-primary hover:bg-layer2 transition"
              >
                Create Room
              </Link>
              <Link
                href="/multiplayer/join"
                className="inline-block px-6 py-2.5 text-sm font-medium border border-borderDark-subtle rounded-sm text-text-secondary hover:text-text-primary hover:bg-layer2 transition"
              >
                Join Room
              </Link>
            </div>

            <p className="text-xs text-text-muted mt-4">
              No login required · Paper trading only · Free for education
            </p>
          </div>

          {/* Education Context */}
          <div className="bg-layer2 border border-borderDark-subtle p-8 rounded-md">
            <h2 className="text-lg font-semibold text-text-primary mb-4">
              Designed for classrooms
            </h2>
            <ul className="space-y-3 text-sm text-text-secondary">
              <li>
                • Teachers can create shared scenarios so all students experience the same market conditions
              </li>
              <li>
                • No real money is involved; all outcomes are deterministic and reviewable
              </li>
              <li>
                • AI recommendations are explainable and transparent
              </li>
              <li>
                • Grades and leaderboards encourage reflection rather than speculation
              </li>
            </ul>
          </div>

        </div>
      </div>
    </main>
  );
}
