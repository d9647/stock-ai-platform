'use client';

import { useMemo, useRef, useState } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatCurrency, formatPercent } from '@/lib/utils/format';

interface GameOverProps {
  //onRestart: () => void;
}

export function GameOver({ /*onRestart*/ }: GameOverProps) {
  const {
    player,
    config,
    ai,
    gameData,
    resetGame,
    isMultiplayer,
    roomCode,
    role,
  } = useGameStore();

  // Hidden PDF-only container (white bg, watermark, date)
  const pdfRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  const isTeacher = role === 'teacher';
  const teacherWatermark = isTeacher
    ? 'TEACHER COPY'
    : `ROOM ${roomCode || ''}`.trim() || 'CLASSROOM';

  const portfolioValue = useMemo(() => {
    if (!gameData) return player.cash;
    const day = gameData.days[player.currentDay];
    if (!day) return player.cash;

    let holdingsValue = 0;
    for (const ticker in player.holdings) {
      const h = player.holdings[ticker];
      const price = day.prices[ticker]?.close ?? h.avgCost;
      holdingsValue += h.shares * price;
    }
    return player.cash + holdingsValue;
  }, [player, gameData]);

  const aiPortfolioValue = useMemo(() => {
    if (!gameData) return ai.cash;
    const day = gameData.days[player.currentDay];
    if (!day) return ai.cash;

    let holdingsValue = 0;
    for (const ticker in ai.holdings) {
      const h = ai.holdings[ticker];
      const price = day.prices[ticker]?.close ?? h.avgCost;
      holdingsValue += h.shares * price;
    }
    return ai.cash + holdingsValue;
  }, [ai, gameData, player.currentDay]);

  const playerReturn =
    ((portfolioValue - config.initialCash) / config.initialCash) * 100;
  const aiReturn =
    ((aiPortfolioValue - config.initialCash) / config.initialCash) * 100;
  const beatAI = playerReturn > aiReturn;

  const handleRestart = () => {
    resetGame();
    //onRestart();
  };

const handleExportPDF = async () => {
  if (!pdfRef.current) return;

  setExporting(true);
  try {
    // Dynamically load ONLY on client
    const html2pdf = (await import('html2pdf.js')).default;

    const safeName =
      (player.playerName || 'Student')
        .replace(/[^\w\- ]+/g, '')
        .trim() || 'Student';

    const fileDate = new Date().toISOString().slice(0, 10);
    const filename = `AI-Stock-Challenge-${safeName}-${fileDate}.pdf`;

    await html2pdf()
      .set({
        margin: 12,
        filename,
        image: { type: 'jpeg', quality: 1 },
        html2canvas: {
          scale: 2,
          backgroundColor: '#ffffff',
        },
        jsPDF: {
          unit: 'mm',
          format: 'a4',
          orientation: 'portrait',
        },
      })
      .from(pdfRef.current)
      .save();
  } catch (err) {
    console.error('PDF export failed:', err);
  } finally {
    setExporting(false);
  }
};


  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      {/* ==========================
          ON-SCREEN UI (OpenAI dark)
          ========================== */}
      <div className="bg-layer2 border border-borderDark-subtle max-w-3xl w-full p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-text-primary">
            Game completed
          </h1>
          <p className="text-sm text-text-muted mt-1">
            {config.numDays} trading days simulated
          </p>
        </div>

        {/* Primary actions */}
        <div className="flex flex-wrap gap-3 mb-10">
          {isMultiplayer && roomCode ? (
            <a
              href={`/multiplayer/leaderboard/${roomCode}`}
              className="btn-primary inline-block px-6 py-2 text-sm"
            >
              View final leaderboard →
            </a>
          ) : null}
          {isMultiplayer && roomCode ? (

            <button onClick={handleRestart}   
              className="px-6 py-2 text-sm border .border-borderDark-faint text-text-primary hover:bg-layer1 disabled:opacity-50 disabled:cursor-not-allowed rounded-full"
            >
              Start a new game
            </button>
          ) : (
            <button onClick={handleRestart}   
              className="btn-primary inline-flex items-center gap-1.5 px-3.5 py-1.5 text-sm font-medium border border-borderDark-subtle rounded-full"
            >
              Start a new game
            </button>
          )}

          <button
            onClick={handleExportPDF}
            disabled={exporting}
            className="px-6 py-2 text-sm border .border-borderDark-faint text-text-primary hover:bg-layer1 disabled:opacity-50 disabled:cursor-not-allowed rounded-full"
          >
            {exporting ? 'Exporting…' : 'Export PDF'}
          </button>
        </div>

        {/* Grade */}
        <div className="mb-10">
          <div className="text-sm text-text-muted mb-1">Final grade</div>
          <div className="text-5xl font-bold text-text-primary">
            {player.grade}
          </div>
          <div className="text-sm text-text-muted mt-2">
            Score: {player.score.toFixed(0)} points
          </div>
        </div>

        {/* Performance Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          {/* Player */}
          <div className="bg-layer1 border border-borderDark-subtle p-6">
            <h3 className="text-sm font-medium text-text-primary mb-4">
              Your performance
            </h3>

            <Metric
              label="Final portfolio value"
              value={formatCurrency(portfolioValue)}
            />
            <Metric
              label="Total return"
              value={`${playerReturn >= 0 ? '+' : ''}${formatPercent(playerReturn / 100)}`}
              accent={playerReturn >= 0 ? 'positive' : 'negative'}
            />
            <Metric label="Trades executed" value={player.trades.length.toString()} />
          </div>

          {/* AI */}
          <div className="bg-layer1 border border-borderDark-subtle p-6">
            <h3 className="text-sm font-medium text-text-primary mb-4">
              AI benchmark
            </h3>

            <Metric
              label="AI portfolio value"
              value={formatCurrency(aiPortfolioValue)}
            />
            <Metric
              label="AI return"
              value={`${aiReturn >= 0 ? '+' : ''}${formatPercent(aiReturn / 100)}`}
              accent={aiReturn >= 0 ? 'positive' : 'negative'}
            />

            <div className="pt-4 mt-4 border-t border-borderDark-subtle">
              <div className={`text-sm font-medium ${beatAI ? 'text-success' : 'text-text-muted'}`}>
                {beatAI ? 'You outperformed the AI' : 'AI outperformed you'}
              </div>
              <div className="text-xs text-text-muted mt-1">
                Difference: {formatPercent((playerReturn - aiReturn) / 100)}
              </div>
            </div>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="bg-layer1 border border-borderDark-subtle p-6 mb-8">
          <h3 className="text-sm font-medium text-text-primary mb-4">
            Score breakdown
          </h3>

          <BreakdownRow label="Portfolio return" value={player.scoreBreakdown.portfolioReturn} />
          <BreakdownRow label="Risk discipline" value={player.scoreBreakdown.riskDiscipline} />
          <BreakdownRow label="Beat AI bonus" value={player.scoreBreakdown.beatAI} />
          <BreakdownRow
            label="Drawdown penalty"
            value={player.scoreBreakdown.drawdownPenalty}
            negative
          />

          <div className="flex justify-between pt-3 mt-3 border-t border-borderDark-subtle text-sm font-semibold text-text-primary">
            <span>Total score</span>
            <span>{player.score.toFixed(0)}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="text-xs text-text-muted">
          {isMultiplayer
            ? 'This game has ended. Rankings are available on the leaderboard.'
            : 'You can restart the game or share your results.'}
        </div>
      </div>

      {/* ==========================================
          PDF-ONLY DOM (HIDDEN OFFSCREEN)
          White background + black text + watermark
          ========================================== */}
      <div
        style={{
          position: 'fixed',
          left: '-10000px',
          top: 0,
          width: '800px',
          background: '#ffffff',
          color: '#000000',
          zIndex: -1,
          pointerEvents: 'none',
        }}
        aria-hidden="true"
      >
        <div
          ref={pdfRef}
          style={{
            padding: 24,
            fontFamily:
              '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
              color: '#000000',
              backgroundColor: '#ffffff',
          }}
        >
          {/* PDF Header */}
          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 16, fontWeight: 700 }}>
              Stock Trading Challenge — Results
            </div>
            <div style={{ fontSize: 12, color: '#444' }}>
              Student: {player.playerName || 'Student'}
              {isMultiplayer && roomCode ? ` • Room: ${roomCode}` : ''}
            </div>
            <div style={{ fontSize: 12, color: '#444' }}>
              Generated: {new Date().toLocaleString()}
            </div>
          </div>

          {/* Watermark (PDF only) */}
          <div
            style={{
              position: 'fixed',
              top: '42%',
              left: '50%',
              transform: 'translate(-50%, -50%) rotate(-30deg)',
              fontSize: 64,
              fontWeight: 800,
              color: '#000',
              opacity: 0.06,
              whiteSpace: 'nowrap',
            }}
          >
            {teacherWatermark}
          </div>

          {/* Grade */}
          <div style={{ border: '1px solid #ddd', padding: 16, marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: '#444' }}>Final grade</div>
            <div style={{ fontSize: 44, fontWeight: 800, lineHeight: 1.05 }}>
              {player.grade}
            </div>
            <div style={{ fontSize: 12, color: '#444', marginTop: 8 }}>
              Score: {player.score.toFixed(0)} points
            </div>
          </div>

        {/* Performance */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 12,
            marginBottom: 16,
          }}
        >
          <PdfBox title="Your performance">
            <PdfMetric label="Final portfolio value" value={formatCurrency(portfolioValue)} />
            <PdfMetric
              label="Total return"
              value={`${playerReturn >= 0 ? '+' : ''}${formatPercent(playerReturn / 100)}`}
            />
            <PdfMetric label="Trades executed" value={player.trades.length.toString()} />
          </PdfBox>

          <PdfBox title="AI benchmark">
            <PdfMetric label="AI portfolio value" value={formatCurrency(aiPortfolioValue)} />
            <PdfMetric
              label="AI return"
              value={`${aiReturn >= 0 ? '+' : ''}${formatPercent(aiReturn / 100)}`}
            />
            <div style={{ marginTop: 10, fontSize: 12, fontWeight: 700 }}>
              {beatAI ? 'You outperformed the AI' : 'AI outperformed you'}
            </div>
            <div style={{ fontSize: 12, color: '#444' }}>
              Difference: {formatPercent((playerReturn - aiReturn) / 100)}
            </div>
          </PdfBox>
        </div>

          {/* Trade History */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 12,
              marginBottom: 16,
              border: '1px solid #ddd',
              padding: 12,
            }}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>
                Your trades (last 10)
              </div>
              {player.trades.slice(-10).length === 0 && (
                <div style={{ fontSize: 12, color: '#555' }}>No trades</div>
              )}
              {player.trades
                .slice(-10)
                .reverse()
                .map((t) => (
                  <div
                    key={t.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 12,
                      padding: '4px 0',
                      borderBottom: '1px solid #f0f0f0',
                    }}
                  >
                    <span>
                      Day {t.day + 1} · {t.ticker} · {t.type}
                    </span>
                    <span>
                      {t.shares} @ ${t.price.toFixed(2)}
                    </span>
                  </div>
                ))}
            </div>

            <div>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>
                AI trades (last 10)
              </div>
              {ai.trades.slice(-10).length === 0 && (
                <div style={{ fontSize: 12, color: '#555' }}>No AI trades</div>
              )}
              {ai.trades
                .slice(-10)
                .reverse()
                .map((t) => (
                  <div
                    key={t.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 12,
                      padding: '4px 0',
                      borderBottom: '1px solid #f0f0f0',
                    }}
                  >
                    <span>
                      Day {t.day + 1} · {t.ticker} · {t.type}
                    </span>
                    <span>
                      {t.shares} @ ${t.price.toFixed(2)}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* Score Breakdown */}
          <div style={{ border: '1px solid #ddd', padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>
              Score breakdown
            </div>

            <PdfBreakdown label="Portfolio return" value={player.scoreBreakdown.portfolioReturn} />
            <PdfBreakdown label="Risk discipline" value={player.scoreBreakdown.riskDiscipline} />
            <PdfBreakdown label="Beat AI bonus" value={player.scoreBreakdown.beatAI} />
            <PdfBreakdown label="Drawdown penalty" value={player.scoreBreakdown.drawdownPenalty} />

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginTop: 12,
                paddingTop: 12,
                borderTop: '1px solid #ddd',
                fontWeight: 800,
              }}
            >
              <span>Total score</span>
              <span>{player.score.toFixed(0)}</span>
            </div>
          </div>

          <div style={{ marginTop: 12, fontSize: 11, color: '#444' }}>
            This report is generated for review and grading purposes.
          </div>
        </div>
      </div>
    </div>
  );
}

/* --------------------------------------------------
   On-screen helper components (OpenAI dark)
-------------------------------------------------- */

function Metric({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: 'positive' | 'negative';
}) {
  return (
    <div className="mb-4">
      <div className="text-xs text-text-muted">{label}</div>
      <div
        className={`text-lg font-semibold ${
          accent === 'positive'
            ? 'text-success'
            : accent === 'negative'
            ? 'text-red-500'
            : 'text-text-primary'
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function BreakdownRow({
  label,
  value,
  negative,
}: {
  label: string;
  value: number;
  negative?: boolean;
}) {
  return (
    <div className="flex justify-between text-sm mb-2">
      <span className="text-text-muted">{label}</span>
      <span className={negative ? 'text-red-500 font-medium' : 'text-text-primary'}>
        {value.toFixed(0)} points
      </span>
    </div>
  );
}

/* --------------------------------------------------
   PDF helper components (inline styles only)
-------------------------------------------------- */

function PdfBox({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ border: '1px solid #ddd', padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function PdfMetric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 12, color: '#444' }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function PdfBreakdown({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
      <span style={{ fontSize: 12, color: '#444' }}>{label}</span>
      <span style={{ fontSize: 12, fontWeight: 700 }}>{value.toFixed(0)} points</span>
    </div>
  );
}
