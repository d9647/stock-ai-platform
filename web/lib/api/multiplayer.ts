/**
 * API client for multiplayer endpoints
 */

// Use environment variable, fallback to localhost for development
// IMPORTANT: Set NEXT_PUBLIC_API_URL in .env.local to your server's IP for network access
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface CreateRoomRequest {
  created_by: string;
  room_name?: string;
  config?: {
    initial_cash?: number;
    num_days?: number;
    tickers?: string[];
    difficulty?: 'easy' | 'medium' | 'hard';
  };
  start_date?: string;
  end_date?: string;
  game_mode?: 'async' | 'sync' | 'sync_auto';
  day_duration_seconds?: number;
}

export interface JoinRoomRequest {
  room_code: string;
  player_name: string;
  player_email?: string;
}

export interface RoomResponse {
  id: string;
  room_code: string;
  created_by: string;
  room_name?: string;
  config: {
    initialCash: number;
    numDays: number;
    tickers: string[];
    difficulty: string;
  };
  start_date: string;
  end_date: string;
  status: 'waiting' | 'in_progress' | 'finished';
  game_mode: 'async' | 'sync' | 'sync_auto';
  current_day: number;
  day_time_limit?: number;
  day_duration_seconds?: number;
  day_started_at?: string;
  ai_portfolio_value?: number;
  ai_total_return_pct?: number;
  ai_current_day?: number;
  created_at: string;
  started_at?: string;
  game_started_at?: string;
  game_ended_at?: string;
  finished_at?: string;
  player_count: number;
  players: PlayerResponse[];
}

export interface PlayerResponse {
  id: string;
  player_name: string;
  player_email?: string;
  current_day: number;
  is_finished: boolean;
  cash: number;
  portfolio_value: number;
  total_return_pct: number;
  total_return_usd: number;
  score: number;
  grade: string;
  is_ready: boolean;
  last_sync_day: number;
  joined_at: string;
  last_action_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  player_id: string;
  player_name: string;
  score: number;
  grade: string;
  portfolio_value: number;
  total_return_pct: number;
  current_day: number;
  is_finished: boolean;
}

export interface UpdatePlayerStateRequest {
  current_day: number;
  cash: number;
  holdings: Record<string, any>;
  trades: any[];
  portfolio_value: number;
  total_return_pct: number;
  total_return_usd: number;
  score: number;
  grade: string;
  score_breakdown?: Record<string, any>;
  portfolio_history: any[];
  is_finished: boolean;
  ai_portfolio_value?: number;
  ai_total_return_pct?: number;
}

/**
 * Create a new multiplayer room (teacher)
 */
export async function createRoom(request: CreateRoomRequest): Promise<RoomResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create room');
  }

  return response.json();
}

/**
 * Join an existing room (student)
 */
export async function joinRoom(request: JoinRoomRequest): Promise<PlayerResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/join`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to join room');
  }

  return response.json();
}

/**
 * Get room details by room code
 */
export async function getRoom(roomCode: string): Promise<RoomResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/${roomCode}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch room');
  }

  return response.json();
}

/**
 * Get leaderboard for a room
 */
export async function getLeaderboard(roomCode: string): Promise<LeaderboardEntry[]> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/${roomCode}/leaderboard`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch leaderboard');
  }

  return response.json();
}

/**
 * Update player state after completing a day
 */
export async function updatePlayerState(
  playerId: string,
  state: UpdatePlayerStateRequest
): Promise<PlayerResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/players/${playerId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(state),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update player state');
  }

  return response.json();
}

/**
 * List all rooms (optional filter by status)
 */
export async function listRooms(status?: 'waiting' | 'in_progress' | 'finished'): Promise<RoomResponse[]> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);

  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms?${params.toString()}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch rooms');
  }

  return response.json();
}

// Sync mode API functions

export interface RoomStateResponse {
  room_code: string;
  status: 'waiting' | 'in_progress' | 'finished';
  game_mode: 'async' | 'sync' | 'sync_auto';
  current_day: number;
  day_started_at?: string;
  day_time_limit?: number;
  day_duration_seconds?: number;
  time_remaining?: number;
  waiting_for_teacher: boolean;
  ready_count: number;
  total_players: number;
}

/**
 * Start the game (teacher control)
 */
export async function startGame(roomCode: string, startedBy: string): Promise<RoomResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/${roomCode}/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ started_by: startedBy }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start game');
  }

  return response.json();
}

/**
 * Advance all players to next day (teacher control, sync mode only)
 */
export async function advanceDay(
  roomCode: string,
  initiatedBy: string,
  dayTimeLimit?: number
): Promise<RoomResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/${roomCode}/advance-day`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      initiated_by: initiatedBy,
      day_time_limit: dayTimeLimit,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to advance day');
  }

  return response.json();
}

/**
 * End the game for all players (teacher control)
 */
export async function endGame(roomCode: string, endedBy: string): Promise<RoomResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/${roomCode}/end-game`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ended_by: endedBy }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to end game');
  }

  return response.json();
}

/**
 * Set timer for current day (teacher control)
 */
export async function setTimer(roomCode: string, durationSeconds: number): Promise<RoomResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/${roomCode}/set-timer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ duration_seconds: durationSeconds }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to set timer');
  }

  return response.json();
}

/**
 * Get current room state (for polling by students)
 */
export async function getRoomState(roomCode: string): Promise<RoomStateResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/rooms/${roomCode}/state`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch room state');
  }

  return response.json();
}

/**
 * Mark player as ready for next day
 */
export async function markPlayerReady(playerId: string): Promise<PlayerResponse> {
  const response = await fetch(`${API_BASE}/api/v1/multiplayer/players/${playerId}/ready`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to mark player ready');
  }

  return response.json();
}
