'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useGameStore } from '@/lib/stores/gameStore';
import {
  getRoom,
  getLeaderboard,
  type RoomResponse,
  type LeaderboardEntry,
} from '@/lib/api/multiplayer';

interface LeaderboardViewProps {
  roomCode: string;
}

type SortKey = 'rank' | 'score' | 'return' | 'portfolio';
type SortDir = 'asc' | 'desc';

export function LeaderboardView({ roomCode }: LeaderboardViewProps) {
  const router = useRouter();
  const { role } = useGameStore();
  const isTeacher = role === 'teacher';

  const currentPlayerName =
    typeof window !== 'undefined'
      ? localStorage.getItem('multiplayer_player_name')
      : null;

  const [room, setRoom] = useState<RoomResponse | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [sortKey, setSortKey] = useState<SortKey>('rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const fetchData = async () => {
    try {
      const [roomData, leaderboardData] = await Promise.all([
        getRoom(roomCode),
        getLeaderboard(roomCode),
      ]);
      setRoom(roomData);
      setLeaderboard(leaderboardData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [roomCode]);

  /* =====================================================
     Sorting logic
     ===================================================== */
  const sortedLeaderboard = useMemo(() => {
    const data = [...leaderboard];

    data.sort((a, b) => {
      let av: number;
      let bv: number;

      switch (sortKey) {
        case 'score':
          av = a.score;
          bv = b.score;
          break;
        case 'return':
          av = a.total_return_pct;
          bv = b.total_return_pct;
          break;
        case 'portfolio':
          av = a.portfolio_value;
          bv = b.portfolio_value;
          break;
        case 'rank':
        default:
          av = a.rank;
          bv = b.rank;
      }

      return sortDir === 'asc' ? av - bv : bv - av;
    });

    return data;
  }, [leaderboard, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'rank' ? 'asc' : 'desc');
    }
  };

  // Append AI benchmark as a virtual entry (ranked last; no player_id collision)
  const leaderboardWithAI: LeaderboardEntry[] = useMemo(() => {
    if (!room) return sortedLeaderboard;

    // Try to get AI performance from:
    // 1. Room data (synced from backend by any player)
    // 2. Local game store (if this player has played)
    // 3. Initial cash (if no one has played yet)
    let aiPortfolioValue = room.ai_portfolio_value;
    let aiReturnPct = room.ai_total_return_pct;

    // If backend has no AI data, try local store (for current player)
    if (aiPortfolioValue == null || aiReturnPct == null) {
      const gameState = useGameStore.getState();
      if (gameState.gameData && gameState.ai.portfolioHistory.length > 0) {
        // Use local AI data
        const localAiValue = gameState.getAIPortfolioValue();
        const initialCash = gameState.config.initialCash;
        aiPortfolioValue = localAiValue;
        aiReturnPct = ((localAiValue - initialCash) / initialCash) * 100;
      } else {
        // No AI data available yet
        aiPortfolioValue = room.config.initialCash;
        aiReturnPct = 0;
      }
    }

    const aiEntry: LeaderboardEntry = {
      rank: sortedLeaderboard.length + 1,
      player_id: 'AI_BENCHMARK',
      player_name: 'AI Agent',
      score: 0,
      grade: 'N/A',
      portfolio_value: aiPortfolioValue,
      total_return_pct: aiReturnPct,
      current_day: room.ai_current_day ?? room.current_day,
      is_finished: room.status === 'finished',
    };
    return [...sortedLeaderboard, aiEntry];
  }, [sortedLeaderboard, room]);

  const SortIcon = ({ active }: { active: boolean }) => (
    <span className={`ml-1 ${active ? 'text-text-primary' : 'text-text-muted'}`}>
      {sortDir === 'asc' ? '▲' : '▼'}
    </span>
  );

  /* =====================================================
     Skeleton loading (OpenAI-style)
     ===================================================== */
  if (loading) {
    return (
      <div className="min-h-screen bg-base">
        <header className="bg-layer1 border-b border-borderDark-subtle">
          <div className="max-w-5xl mx-auto px-4 py-6">
            <div className="h-6 w-40 bg-layer3 animate-pulse rounded-md mb-2" />
            <div className="h-4 w-64 bg-layer3 animate-pulse rounded-md" />
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-4 py-8">
          <div className="bg-layer2 border border-borderDark-subtle rounded-md">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="grid grid-cols-7 gap-4 px-4 py-4 border-b border-borderDark-subtle last:border-b-0"
              >
                {[...Array(7)].map((__, j) => (
                  <div
                    key={j}
                    className="h-4 bg-layer3 animate-pulse rounded-md"
                  />
                ))}
              </div>
            ))}
          </div>
        </main>
      </div>
    );
  }

  /* =====================================================
     Error
     ===================================================== */
  if (error || !room) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center p-6">
        <div className="bg-layer2 border border-borderDark-subtle rounded-md p-8 max-w-md w-full text-center">
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            Leaderboard Not Available
          </h2>
          <p className="text-text-muted mb-6 text-sm">{error}</p>
          <button
            onClick={() => router.push('/multiplayer/join')}
            className="btn-primary rounded-md px-6 py-2"
          >
            Join a Room
          </button>
        </div>
      </div>
    );
  }

  /* =====================================================
     Page
     ===================================================== */
  return (
    <div className="min-h-screen bg-base">
      {/* Header */}
      <header className="bg-layer1 border-b border-borderDark-subtle">
        <div className="max-w-5xl mx-auto px-4 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">
              Leaderboard
            </h1>
            <p className="text-text-muted text-sm mt-1">
              Room {room.room_code} • {room.room_name || 'Classroom Game'}
            </p>
          </div>

          <button
            onClick={() => {
              if (room?.room_code) {
                router.push(`/multiplayer/room/${room.room_code}`);
              } else {
                router.back();
              }
            }}
            className="text-sm text-text-secondary hover:text-accent"
          >
            ← Back
          </button>
        </div>
      </header>

      {/* Table */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="bg-layer2 border border-borderDark-subtle rounded-md overflow-hidden">
          {/* Sticky header */}
          <div className="sticky top-0 z-10 bg-layer2 border-b border-borderDark-subtle">
            <div className="grid grid-cols-7 gap-4 px-4 py-3 text-xs uppercase tracking-wide text-text-muted">
              <button onClick={() => toggleSort('rank')} className="text-left">
                Rank <SortIcon active={sortKey === 'rank'} />
              </button>
              <div className="col-span-2">Player</div>
              <div>Day</div>
              <button
                onClick={() => toggleSort('score')}
                className="text-right"
              >
                Score <SortIcon active={sortKey === 'score'} />
              </button>
              <button
                onClick={() => toggleSort('portfolio')}
                className="text-right"
              >
                Portfolio <SortIcon active={sortKey === 'portfolio'} />
              </button>
              <button
                onClick={() => toggleSort('return')}
                className="text-right"
              >
                Return <SortIcon active={sortKey === 'return'} />
              </button>
            </div>
          </div>

          {/* Rows */}
          {leaderboardWithAI.map((entry) => {
            const isCurrentUser =
              currentPlayerName &&
              entry.player_name === currentPlayerName;

            return (
              <div
                key={entry.player_id}
                className={`grid grid-cols-7 gap-4 px-4 py-4 border-b border-borderDark-subtle last:border-b-0 text-sm
                ${isCurrentUser ? 'bg-layer3' : ''}`}
              >
                {/* Rank */}
                <div className="text-text-muted">
                  {entry.rank === 1
                    ? '🥇'
                    : entry.rank === 2
                    ? '🥈'
                    : entry.rank === 3
                    ? '🥉'
                    : `#${entry.rank}`}
                </div>

                {/* Player */}
                <div className="col-span-2 font-medium text-text-primary">
                  {entry.player_name}
                </div>

                {/* Day */}
                <div className="text-text-secondary">
                  {entry.current_day + 1}
                </div>

                {/* Score */}
                <div className="text-right font-medium text-text-primary">
                  {entry.score.toFixed(0)}
                </div>

                {/* Portfolio Value */}
                <div className="text-right text-text-primary">
                  ${entry.portfolio_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>

                {/* Return */}
                <div
                  className={`text-right text-xs font-medium ${
                    entry.total_return_pct >= 0
                      ? 'text-success'
                      : 'text-error'
                  }`}
                >
                  {entry.total_return_pct >= 0 ? '+' : ''}
                  {entry.total_return_pct.toFixed(2)}%
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}

export default LeaderboardView;
