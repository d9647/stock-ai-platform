'use client';

import { useMemo, useState, useEffect } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { DayHeader } from './day-header';
import { PortfolioSummary } from './portfolio-summary';
import { AIRecommendations } from './ai-recommendations';
import { PlayerHoldings } from './player-holdings';
import { AdvanceDayButton } from './advance-day-button';
import { StockChart } from './stock-chart';
import { NewsPanel } from './news-panel';
import { SyncBanner } from './sync-banner';
import { SyncStateManager } from './sync-state-manager';
import { TeacherGameControls } from './teacher-game-controls';
import { getRoom, type RoomResponse } from '@/lib/api/multiplayer';

export function GameView() {
  const { player, gameData, config, isMultiplayer, roomCode, role } =
    useGameStore();

  const [selectedTicker, setSelectedTicker] = useState<string>(
    config.tickers[0]
  );
  const [room, setRoom] = useState<RoomResponse | null>(null);

  const isTeacher = role === 'teacher';

  useEffect(() => {
    if (isMultiplayer && roomCode) {
      getRoom(roomCode)
        .then(setRoom)
        .catch((err) => console.error('Failed to fetch room:', err));
    }
  }, [isMultiplayer, roomCode]);

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) return null;
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  if (!gameData || !currentDayData) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <p className="text-sm text-text-muted">Loading game…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-base">
      {/* Sync State Manager */}
      {isMultiplayer &&
        roomCode &&
        (room?.game_mode === 'sync' ||
          room?.game_mode === 'sync_auto') &&
        !isTeacher && <SyncStateManager roomCode={roomCode} />}

      {/* Teacher Controls */}
      {isMultiplayer &&
        roomCode &&
        room?.game_mode === 'sync' &&
        isTeacher && (
          <TeacherGameControls
            roomCode={roomCode}
            teacherName={room.created_by}
            currentDay={player.currentDay}
          />
        )}

      {/* Fixed Header */}
      <DayHeader />

      {/* Multiplayer Banner */}
      {isMultiplayer &&
        roomCode &&
        (room?.game_mode === 'sync' ||
          room?.game_mode === 'sync_auto') && (
          <SyncBanner
            roomCode={roomCode}
            playerId={player.playerId}
            currentDay={player.currentDay}
            gameMode={room?.game_mode}
          />
        )}

      {isMultiplayer && roomCode && room?.game_mode === 'async' && (
        <div className="border-b border-borderDark-subtle bg-layer1 py-2 text-center">
          <div className="container mx-auto flex items-center justify-center gap-4 text-sm">
            <span className="text-text-muted">
              Multiplayer Room: <span className="font-mono">{roomCode}</span>
            </span>
            <a
              href={`/multiplayer/leaderboard/${roomCode}`}
              className="text-accent hover:underline"
            >
              View Leaderboard →
            </a>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Ticker Selector */}
            <div className="flex flex-wrap gap-2">
              {config.tickers.map((ticker) => (
                <button
                  key={ticker}
                  onClick={() => setSelectedTicker(ticker)}
                  className={`px-4 py-2 text-sm font-mono transition-colors border ${
                    selectedTicker === ticker
                      ? 'bg-layer2 text-text-primary border-borderDark-subtle'
                      : 'bg-layer1 text-text-muted border-borderDark-subtle hover:bg-layer2'
                  }`}
                >
                  {ticker}
                </button>
              ))}
            </div>

            {/* Chart */}
            <StockChart ticker={selectedTicker} />

            {/* Portfolio */}
            <PortfolioSummary />

            {/* AI Recommendations */}
            <AIRecommendations />

            {/* Holdings */}
            <PlayerHoldings />
          </div>

          {/* Right Column */}
          <div className="lg:col-span-1">
            <div className="sticky top-20 space-y-6">
              {/* Advance Day */}
              {(!isMultiplayer || room?.game_mode === 'async') && (
                <AdvanceDayButton />
              )}

              {/* Weekend Notice */}
              {!currentDayData.is_trading_day && (
                <div className="bg-layer2 border border-borderDark-subtle px-4 py-3 text-sm text-text-muted text-center">
                  Markets closed — Weekend
                </div>
              )}

              {/* News */}
              <NewsPanel />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
