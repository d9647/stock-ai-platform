'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  getRoom,
  getLeaderboard,
  getRoomState,
  type RoomResponse,
  type LeaderboardEntry,
  type RoomStateResponse,
} from '@/lib/api/multiplayer';
import { useGameStore } from '@/lib/stores/gameStore';
import { TeacherDashboard } from './teacher-dashboard';

interface RoomLobbyProps {
  roomCode: string;
}

/* ================= Skeleton ================= */
function LobbySkeleton() {
  return (
    <div className="min-h-screen bg-base px-4 py-8 animate-pulse">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="bg-layer1 border border-borderDark-subtle h-20 rounded-md" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-layer2 border border-borderDark-subtle h-56 rounded-md" />
          <div className="bg-layer2 border border-borderDark-subtle h-56 rounded-md" />
        </div>
        <div className="bg-layer2 border border-borderDark-subtle h-40 rounded-md" />
      </div>
    </div>
  );
}

type SortKey = 'rank' | 'score' | 'return' | 'portfolio';
type SortDir = 'asc' | 'desc';

export function RoomLobby({ roomCode }: RoomLobbyProps) {
  const router = useRouter();
  const { startMultiplayerGame, role } = useGameStore();
  const startOnceRef = useRef(false);

  const [room, setRoom] = useState<RoomResponse | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [roomState, setRoomState] = useState<RoomStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const [sortKey, setSortKey] = useState<SortKey>('rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const [showPlayers, setShowPlayers] = useState(true);

  const SHOW_LEADERBOARD = false;
  const SHOW_STATS = false;

  const playerId =
    typeof window !== 'undefined'
      ? localStorage.getItem('multiplayer_player_id')
      : null;

  const isTeacher = role === 'teacher';

  /* =====================================================
     Sorting logic for embedded leaderboard
     ===================================================== */
  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'rank' ? 'asc' : 'desc');
    }
  };

  // Add AI benchmark and sort
  const leaderboardWithAI: LeaderboardEntry[] = useMemo(() => {
    if (!room) return leaderboard;

    // Try to get AI performance from:
    // 1. Room data (synced from backend by any player)
    // 2. Initial cash (if no one has played yet)
    let aiPortfolioValue = room.ai_portfolio_value;
    let aiReturnPct = room.ai_total_return_pct;

    // If backend has no AI data, use initial cash
    if (aiPortfolioValue == null || aiReturnPct == null) {
      aiPortfolioValue = room.config.initialCash;
      aiReturnPct = 0;
    }

    const aiEntry: LeaderboardEntry = {
      rank: leaderboard.length + 1,
      player_id: 'AI_BENCHMARK',
      player_name: 'AI Agent',
      score: 0,
      grade: 'N/A',
      portfolio_value: aiPortfolioValue,
      total_return_pct: aiReturnPct,
      current_day: room.ai_current_day ?? room.current_day,
      is_finished: room.status === 'finished',
    };

    // Combine leaderboard with AI entry
    const data = [...leaderboard, aiEntry];

    // Sort the combined data
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
  }, [leaderboard, room, sortKey, sortDir]);

  const SortIcon = ({ active }: { active: boolean }) => {
    if (!active) return null;
    return (
      <span className="ml-1 text-text-primary">
        {sortDir === 'asc' ? '▲' : '▼'}
      </span>
    );
  };

  /* ---------- Fetch room ---------- */
  const fetchRoomData = async () => {
    try {
      const [roomData, leaderboardData] = await Promise.all([
        getRoom(roomCode),
        getLeaderboard(roomCode),
      ]);
      setRoom(roomData);
      setLeaderboard(leaderboardData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load room');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoomData();
    const interval = setInterval(fetchRoomData, 5000);
    return () => clearInterval(interval);
  }, [roomCode]);

  /* ---------- Poll room state ---------- */
  useEffect(() => {
    if (!room || role !== 'student' || room.game_mode === 'async' || !playerId)
      return;

    const poll = async () => {
      try {
        const state = await getRoomState(roomCode);
        setRoomState(state);
      } catch {}
    };

    poll();
    const i = setInterval(poll, 1000);
    return () => clearInterval(i);
  }, [room, role, playerId, roomCode]);

  /* ---------- Auto-enter game ---------- */
  useEffect(() => {
    if (
      !room ||
      role !== 'student' ||
      room.status !== 'in_progress' ||
      !playerId ||
      startOnceRef.current
    )
      return;

    const existingState =
      typeof window !== 'undefined'
        ? localStorage.getItem('stock-game-storage')
        : null;

    // If cached multiplayer state matches this room/player, just navigate
    if (existingState) {
      try {
        const parsed = JSON.parse(existingState);
        const state = parsed.state;
        if (
          state?.isMultiplayer &&
          state?.roomCode === room.room_code &&
          state?.player?.playerId === playerId &&
          state?.gameData
        ) {
          startOnceRef.current = true;
          router.push('/game');
          return;
        }
      } catch {
        // ignore parse errors
      }
    }

    // Otherwise, initialize game store then navigate
    const enter = async () => {
      startOnceRef.current = true;
      try {
        await startMultiplayerGame({
          roomCode: room.room_code,
          playerId,
          role: 'student',
          config: {
            initialCash: room.config.initialCash,
            numDays: room.config.numDays,
            tickers: room.config.tickers,
            difficulty: room.config.difficulty as any,
          },
          startDate: room.start_date,
          endDate: room.end_date,
        });
        router.push('/game');
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to enter the game. Please try again.'
        );
        startOnceRef.current = false;
      }
    };

    enter();
  }, [room, role, playerId, router, startMultiplayerGame]);

  const handleCopyCode = async () => {
    const url = `${window.location.origin}/multiplayer/join?roomCode=${roomCode}`;

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(url);
      } else {
        fallbackCopyText(url);
      }

      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      fallbackCopyText(url);
    }
  };

  function fallbackCopyText(text: string) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed'; // avoid scroll jump
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    try {
      document.execCommand('copy');
    } finally {
      document.body.removeChild(textarea);
    }
  }


  /* ================= Render ================= */
  if (loading) return <LobbySkeleton />;

  if (error || !room) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <div className="bg-layer2 border border-borderDark-subtle rounded-md p-8 text-center">
          <p className="text-text-primary mb-4">Room not found</p>
          <button
            onClick={() => router.push('/multiplayer/join')}
            className="btn-primary rounded-md px-4 py-2"
          >
            Try another code
          </button>
        </div>
      </div>
    );
  }

  const myEntry = leaderboard.find((e) => e.player_id === playerId);

  return (
    <div className="min-h-screen bg-base">
      {/* Header */}
      <div className="bg-layer1 border-b border-borderDark-subtle">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between">
          <div>
            <h1 className="text-lg font-semibold text-text-primary">
              {room.room_name || 'Game Control Room'}
            </h1>
            <p className="text-xs text-text-muted">
              Created by {room.created_by}
            </p>
          </div>

          <div className="text-right">
            <div className="flex items-center gap-2">
              <code className="font-mono text-text-primary">
                {room.room_code}
              </code>
              <button
                onClick={handleCopyCode}
                className="text-xs text-accent"
              >
                {copied ? 'Copied' : 'Copy link'}
              </button>
            </div>
            <p className="text-xs text-text-muted">
              {room.player_count} players
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* Teacher Dashboard */}
        {isTeacher && room.game_mode !== 'async' && (
          <TeacherDashboard
            room={room}
            teacherName={room.created_by}
            onRoomUpdate={fetchRoomData}
          />
        )}

        {/* Sync banner (students) */}
        {!isTeacher && room.game_mode !== 'async' && roomState && (
          <div className="bg-layer2 border border-borderDark-subtle rounded-md p-6">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Synchronous Mode
            </h3>
            <p className="text-sm text-text-muted">
              {room.status === 'waiting' && 'Waiting for teacher to start…'}
              {room.status === 'in_progress' &&
                roomState.waiting_for_teacher &&
                'Waiting for teacher to advance…'}
              {room.status === 'finished' && 'Game has ended.'}
            </p>
          </div>
        )}

        {/* Players */}
        <div className="bg-layer2 border border-borderDark-subtle rounded-md">
          <button
            onClick={() => setShowPlayers(!showPlayers)}
            className="w-full flex items-center justify-between p-6 text-left"
          >
            <h2 className="text-sm font-semibold text-text-primary">
              Players
            </h2>
            <div className="flex items-center gap-3">
              <span className="text-xs text-text-muted">
                {room.players.length}
              </span>
              <span className="text-text-muted text-lg">
                {showPlayers ? '−' : '+'}
              </span>
            </div>
          </button>

          {showPlayers && (
            <div className="px-6 pb-6">
              {/* Compact wrapped layout */}
              <div className="flex flex-wrap gap-2 max-h-72 overflow-y-auto pr-1">
                {room.players.map((p) => {
                  const isMe = p.id === playerId;
                  const isReady = p.is_ready;

                  return (
                    <div
                      key={p.id}
                      className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                        isMe
                          ? 'bg-layer3 border-borderDark-subtle text-text-primary font-medium'
                          : isReady
                          ? 'bg-layer2 border-borderDark-subtle text-text-primary hover:text-text-primary'
                          : 'bg-layer1 border-borderDark-subtle text-text-muted hover:text-text-secondary opacity-60'
                      }`}
                    >
                      {p.player_name}
                      {isMe && (
                        <span className="text-text-muted ml-1 text-xs">(You)</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Embedded Leaderboard */}
        {leaderboard.length > 0 && (
          <div className="bg-layer2 border border-borderDark-subtle rounded-md p-6">
            <h2 className="text-sm font-semibold text-text-primary mb-4">
              Leaderboard
            </h2>

            <div className="overflow-x-auto">
              <div className="min-w-[600px]">
                {/* Header */}
                <div className="grid grid-cols-6 gap-4 px-4 py-3 text-xs uppercase tracking-wide text-text-muted border-b border-borderDark-subtle">
                  <button onClick={() => toggleSort('rank')} className="text-left">
                    Rank <SortIcon active={sortKey === 'rank'} />
                  </button>
                  <div className="col-span-2">Player</div>
                  <button onClick={() => toggleSort('score')} className="text-right">
                    Score <SortIcon active={sortKey === 'score'} />
                  </button>
                  <button onClick={() => toggleSort('portfolio')} className="text-right">
                    Portfolio <SortIcon active={sortKey === 'portfolio'} />
                  </button>
                  <button onClick={() => toggleSort('return')} className="text-right">
                    Return <SortIcon active={sortKey === 'return'} />
                  </button>
                </div>

                {/* Rows */}
                <div className="max-h-96 overflow-y-auto">
                  {leaderboardWithAI.map((entry) => {
                    const isCurrentUser = entry.player_id === playerId;

                    return (
                      <div
                        key={entry.player_id}
                        className={`grid grid-cols-6 gap-4 px-4 py-3 border-b border-borderDark-subtle last:border-b-0 text-sm ${
                          isCurrentUser ? 'bg-layer3' : ''
                        }`}
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
                        <div className="col-span-2 font-medium text-text-primary truncate">
                          {entry.player_name}
                        </div>

                        {/* Score */}
                        <div className="text-right font-medium text-text-primary">
                          {entry.score.toFixed(0)}
                        </div>

                        {/* Portfolio Value */}
                        <div className="text-right text-text-primary text-xs">
                          ${entry.portfolio_value.toLocaleString('en-US', {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0
                          })}
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
              </div>
            </div>
          </div>
        )}

        {/* Optional stats preserved */}
        {myEntry && SHOW_STATS && (
          <div className="bg-layer2 border border-borderDark-subtle rounded-md p-6">
            <h2 className="text-sm font-semibold text-text-primary mb-4">
              Your Stats
            </h2>
            <div className="space-y-2 text-sm text-text-secondary">
              <div className="flex justify-between">
                <span>Rank</span>
                <span className="text-text-primary">#{myEntry.rank}</span>
              </div>
              <div className="flex justify-between">
                <span>Score</span>
                <span className="text-text-primary">
                  {myEntry.score.toFixed(0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Return</span>
                <span className="text-text-primary">
                  {myEntry.total_return_pct.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
