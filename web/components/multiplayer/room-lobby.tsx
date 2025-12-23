'use client';

import { useState, useEffect, useRef } from 'react';
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

  const SHOW_LEADERBOARD = false;
  const SHOW_STATS = false;

  const playerId =
    typeof window !== 'undefined'
      ? localStorage.getItem('multiplayer_player_id')
      : null;

  const isTeacher = role === 'teacher';

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
              {room.room_name || 'Trading Game Lobby'}
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

        {/* Game settings + players */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Game Settings */}
          <div className="bg-layer2 border border-borderDark-subtle rounded-md p-6">
            <h2 className="text-sm font-semibold text-text-primary mb-4">
              Game Settings
            </h2>
            <div className="space-y-2 text-sm text-text-secondary">
              <div className="flex justify-between">
                <span>Mode</span>
                <span className="text-text-primary">{room.game_mode}</span>
              </div>
              <div className="flex justify-between">
                <span>Cash</span>
                <span className="text-text-primary">
                  ${room.config.initialCash.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Duration</span>
                <span className="text-text-primary">
                  {room.config.numDays} days
                </span>
              </div>
              <div className="flex justify-between">
                <span>Difficulty</span>
                <span className="text-text-primary capitalize">
                  {room.config.difficulty}
                </span>
              </div>
            </div>
          </div>

          {/* Players */}
          <div className="bg-layer2 border border-borderDark-subtle rounded-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-text-primary">
                Players
              </h2>
              <span className="text-xs text-text-muted">
                {room.players.length}
              </span>
            </div>

            {/* Scrollable list */}
            <div className="max-h-72 overflow-y-auto pr-1">
              <ul className="space-y-0.5 text-sm">
                {room.players.map((p) => {
                  const isMe = p.id === playerId;

                  return (
                    <li
                      key={p.id}
                      className={`px-2 py-1 flex items-center justify-between rounded-sm
                        ${
                          isMe
                            ? 'bg-layer3 border border-borderDark-subtle'
                            : 'hover:bg-layer1'
                        }`}
                    >
                      <span className="text-text-primary truncate">
                        {p.player_name}
                        {isMe && (
                          <span className="text-text-muted ml-2">(You)</span>
                        )}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        </div>

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
