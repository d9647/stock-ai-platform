'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { joinRoom, type JoinRoomRequest } from '@/lib/api/multiplayer';
import { useGameStore } from '@/lib/stores/gameStore';

export function JoinRoom() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    roomCode: '',
    playerName: '',
    playerEmail: '',
  });

  useEffect(() => {
    const codeFromQuery = searchParams.get('roomCode');
    if (codeFromQuery) {
      setFormData((prev) => ({
        ...prev,
        roomCode: codeFromQuery.toUpperCase(),
      }));
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const request: JoinRoomRequest = {
        room_code: formData.roomCode.toUpperCase(),
        player_name: formData.playerName,
        player_email: formData.playerEmail || undefined,
      };

      const player = await joinRoom(request);

      localStorage.setItem('multiplayer_player_id', player.id);
      localStorage.setItem('multiplayer_room_code', formData.roomCode.toUpperCase());
      localStorage.setItem('multiplayer_player_name', player.player_name);

      useGameStore.setState({
        role: 'student',
        isMultiplayer: true,
        roomCode: formData.roomCode.toUpperCase(),
        status: 'not_started',
      });

      router.push(`/multiplayer/room/${formData.roomCode.toUpperCase()}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to join room');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-layer2 border border-borderDark-subtle rounded-md px-8 py-7">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-text-primary mb-1">
            Join Room
          </h1>
          <p className="text-sm text-text-muted">
            Enter the room code shared by your teacher.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 px-4 py-3 text-sm text-text-primary bg-layer1 border border-borderDark-subtle rounded-md">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Room Code */}
          <div>
            <label className="block text-xs text-text-secondary mb-1 uppercase tracking-wide">
              Room code
            </label>
            <input
              type="text"
              required
              maxLength={6}
              value={formData.roomCode}
              onChange={(e) =>
                setFormData({ ...formData, roomCode: e.target.value.toUpperCase() })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle
                         text-text-primary text-center text-lg font-mono tracking-widest uppercase
                         rounded-md focus:outline-none placeholder:text-text-muted/50"
              placeholder="ABC123"
            />
            <p className="text-xs text-text-muted mt-1">
              6-character room code
            </p>
          </div>

          {/* Player Name */}
          <div>
            <label className="block text-xs text-text-secondary mb-1 uppercase tracking-wide">
              Your name
            </label>
            <input
              type="text"
              required
              value={formData.playerName}
              onChange={(e) =>
                setFormData({ ...formData, playerName: e.target.value })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle
                         text-text-primary rounded-md focus:outline-none placeholder:text-text-muted/50"
              placeholder="Jane Doe"
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-xs text-text-secondary mb-1 uppercase tracking-wide">
              Email (optional)
            </label>
            <input
              type="email"
              value={formData.playerEmail}
              onChange={(e) =>
                setFormData({ ...formData, playerEmail: e.target.value })
              }
              className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle
                         text-text-primary rounded-md focus:outline-none placeholder:text-text-muted/50"
              placeholder="student@school.edu"
            />
          </div>

          {/* Submit and Cancel Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={() => router.push('/')}
              className="px-4 py-2 text-sm font-medium text-text-muted border border-borderDark-subtle rounded-full transition-colors hover:text-text-primary hover:bg-layer1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 btn-primary text-sm font-medium border border-borderDark-subtle rounded-full transition-colors disabled:opacity-50"
            >
              {loading ? 'Submitting…' : 'Submit'}
            </button>
          </div>
        </form>

        {/* Footer CTA */}
        <div className="mt-6 pt-4 border-t border-borderDark-subtle text-center">
          <p className="text-sm text-text-muted mb-1">
            Are you a teacher?
          </p>
          <button
            onClick={() => router.push('/multiplayer/create')}
            className="text-sm text-accent font-medium"
          >
            Create a room →
          </button>
        </div>
      </div>
    </div>
  );
}
