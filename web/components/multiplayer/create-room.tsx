'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createRoom, type CreateRoomRequest } from '@/lib/api/multiplayer';
import { useGameStore } from '@/lib/stores/gameStore';

type GameMode = 'async' | 'sync' | 'sync_auto';

export function CreateRoom() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    teacherName: '',
    roomName: '',
    numDays: 30,
    initialCash: 100000,
    difficulty: 'easy' as 'easy' | 'medium' | 'hard',
    gameMode: 'sync_auto' as GameMode,
    dayDurationSeconds: 30,
    startDate: '2025-01-01',
  });

  const computeEndDate = () => {
    const start = new Date(formData.startDate);
    if (Number.isNaN(start.getTime())) return undefined;
    const end = new Date(start);
    end.setDate(start.getDate() + formData.numDays - 1);
    return end.toISOString().slice(0, 10);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const request: CreateRoomRequest = {
        created_by: formData.teacherName,
        room_name: formData.roomName || undefined,
        config: {
          num_days: formData.numDays,
          initial_cash: formData.initialCash,
          tickers: ['AAPL','MSFT','GOOGL','NVDA','AMZN','TSLA','META','WMT','MU','AVGO','TSM','JPM','BRK.A','INTC','AMD','QCOM','TXN','LRCX','KLAC','ASML','LLY','ORCL','V','PYPL','MA','JNJ','PLTR'],
          difficulty: formData.difficulty,
        },
        start_date: formData.startDate,
        end_date: computeEndDate(),
        game_mode: formData.gameMode,
        ...(formData.gameMode === 'sync_auto'
          ? { day_duration_seconds: formData.dayDurationSeconds }
          : {}),
      };

      const room = await createRoom(request);

      useGameStore.setState({
        role: 'teacher',
        isMultiplayer: true,
        roomCode: room.room_code,
        status: 'not_started',
      });

      router.push(`/multiplayer/room/${room.room_code}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create room');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div
        className="bg-layer2 border border-borderDark-subtle p-8 max-w-md w-full"
        style={{ borderRadius: '0.375rem' }}
      >
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-semibold text-text-primary mb-2">
            Create Room
          </h1>
          <p className="text-text-muted text-sm">
            Set up a game room for your students
          </p>
        </div>

        {/* Error */}
        {error && (
          <div
            className="border border-borderDark-subtle bg-layer1 text-text-primary px-4 py-3 mb-4 text-sm"
            style={{ borderRadius: '0.375rem' }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Teacher Name */}
          <div>
            <label className="block text-sm text-text-secondary mb-1">
              Your Name (Teacher)
            </label>
            <input
              type="text"
              required
              value={formData.teacherName}
              onChange={(e) =>
                setFormData({ ...formData, teacherName: e.target.value })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary"
              style={{ borderRadius: '0.375rem' }}
              placeholder="Ms. Smith"
            />
          </div>

          {/* Room Name */}
          <div>
            <label className="block text-sm text-text-secondary mb-1">
              Room Name (Optional)
            </label>
            <input
              type="text"
              value={formData.roomName}
              onChange={(e) =>
                setFormData({ ...formData, roomName: e.target.value })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary"
              style={{ borderRadius: '0.375rem' }}
          placeholder="Period 3 Economics"
        />
      </div>

      {/* Start Date */}
      <div>
        <label className="block text-sm text-text-secondary mb-1">
          Start Date (earliest 2025-01-01)
        </label>
        <input
          type="date"
          min="2025-01-01"
          value={formData.startDate}
          onChange={(e) =>
            setFormData({ ...formData, startDate: e.target.value })
          }
          className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary"
          style={{ borderRadius: '0.375rem' }}
        />
        <p className="text-xs text-text-muted mt-1">
          Start dates must be on or after 2025-01-01; latest depends on available data.
        </p>
      </div>

      {/* Game Duration */}
      <div>
        <label className="block text-sm text-text-secondary mb-1">
          Game Duration (Calendar Days)
        </label>
            <select
              value={formData.numDays}
              onChange={(e) =>
                setFormData({ ...formData, numDays: parseInt(e.target.value) })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary"
              style={{ borderRadius: '0.375rem' }}
            >
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>

          {/* Starting Cash */}
          <div>
            <label className="block text-sm text-text-secondary mb-1">
              Starting Cash
            </label>
            <select
              value={formData.initialCash}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  initialCash: parseInt(e.target.value),
                })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary"
              style={{ borderRadius: '0.375rem' }}
            >
              <option value={10000}>$10,000</option>
              <option value={20000}>$20,000</option>
              <option value={50000}>$50,000</option>
              <option value={100000}>$100,000</option>
            </select>
          </div>

          {/* Difficulty */}
          <div>
            <label className="block text-sm text-text-secondary mb-1">
              Difficulty Level
            </label>
            <select
              value={formData.difficulty}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  difficulty: e.target.value as any,
                })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          {/* Game Mode */}
          <div>
            <label className="block text-sm text-text-secondary mb-2">
              Game Mode
            </label>

            <div className="space-y-3">
              {[
                {
                  id: 'sync_auto',
                  title: 'Synchronous (Auto)',
                  desc: 'Days advance automatically on a timer.',
                },
                {
                  id: 'sync',
                  title: 'Synchronous (Teacher)',
                  desc: 'Teacher advances each day.',
                },
                {
                  id: 'async',
                  title: 'Asynchronous',
                  desc: 'Students advance independently.',
                },
              ].map((mode) => (
                <label
                  key={mode.id}
                  className="flex items-start gap-3 bg-layer1 border border-borderDark-subtle p-3 cursor-pointer"
                  style={{ borderRadius: '0.375rem' }}
                >
                  <input
                    type="radio"
                    name="gameMode"
                    value={mode.id}
                    checked={formData.gameMode === mode.id}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        gameMode: e.target.value as GameMode,
                      })
                    }
                    className="mt-1 accent-text-primary [&:not(:checked)]:opacity-50"
                  />
                  <div>
                    <div className="text-sm font-medium text-text-primary">
                      {mode.title}
                    </div>
                    <div className="text-xs text-text-muted">
                      {mode.desc}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Auto Timer */}
          {formData.gameMode === 'sync_auto' && (
            <div>
              <label className="block text-sm text-text-secondary mb-1">
                Seconds per Day
              </label>
              <input
                type="number"
                min={10}
                max={600}
                value={formData.dayDurationSeconds}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    dayDurationSeconds: Number(e.target.value),
                  })
                }
                className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary"
                style={{ borderRadius: '0.375rem' }}
              />
              <p className="text-xs text-text-muted mt-1">
                Recommended: 30–120 seconds
              </p>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-3 font-medium transition-colors"
            style={{ borderRadius: '0.375rem' }}
          >
            {loading ? 'Creating Room…' : 'Create Room'}
          </button>
        </form>

        {/* Footer CTA */}
        <div className="mt-6 pt-6 border-t border-borderDark-subtle text-center">
          <p className="text-sm text-text-muted mb-2">
            Or join an existing room
          </p>
          <button
            onClick={() => router.push('/multiplayer/join')}
            className="text-accent text-sm font-medium"
          >
            Join as Student →
          </button>
        </div>
      </div>
    </div>
  );
}
