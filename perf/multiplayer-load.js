/**
 * K6 Performance Test: Multiplayer Game Room
 *
 * Scenario: One game room with multiple concurrent students playing
 *
 * How to run:
 * 1. Basic test (10 users) - Console output only:
 *    k6 run perf/multiplayer-load.js
 *
 * 2. With Prometheus monitoring (recommended):
 *    k6 run -o experimental-prometheus-rw perf/multiplayer-load.js
 *
 * 3. Custom number of users:
 *    k6 run --vus 50 --duration 2m -o experimental-prometheus-rw perf/multiplayer-load.js
 *
 * 4. Progressive load (recommended):
 *    k6 run --stage 30s:10 --stage 1m:50 --stage 2m:50 -o experimental-prometheus-rw perf/multiplayer-load.js
 *
 * 5. Simulate 30 students playing full 30-day game:
 *    k6 run --vus 30 --iterations 30 -o experimental-prometheus-rw perf/multiplayer-load.js
 *
 * 6. Use existing room:
 *    k6 run -e ROOM_CODE=ABC123 -o experimental-prometheus-rw perf/multiplayer-load.js
 *
 * Prometheus Remote Write URL (set in K6_PROMETHEUS_RW_SERVER_URL):
 *    export K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write
 *
 * Each VU represents one student with realistic gameplay flow:
 * 1. Join the game room (once)
 * 2. For each game day (iteration):
 *    - Get news articles
 *    - Get AI recommendations
 *    - Get game data (prices, portfolio)
 *    - Check leaderboard
 *    - Make trading decision (buy/sell stocks)
 *    - Update player state (submit trades to API)
 *    - Refresh game state
 *    - Advance to next day
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

// Custom metrics
const joinRoomLatency = new Trend('join_room_latency');
const getStateLatency = new Trend('get_state_latency');
const leaderboardLatency = new Trend('leaderboard_latency');
const getNewsLatency = new Trend('get_news_latency');
const getRecommendationsLatency = new Trend('get_recommendations_latency');
const getGameDataLatency = new Trend('get_game_data_latency');
const updatePlayerLatency = new Trend('update_player_latency');
const joinRoomSuccess = new Rate('join_room_success');
const apiErrors = new Counter('api_errors');

// Test configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const ROOM_CODE = __ENV.ROOM_CODE || null; // Can be set via: k6 run -e ROOM_CODE=ABC123

// Default options (can be overridden via CLI)
export const options = {
  vus: 10,
  duration: '2m',

  thresholds: {
    // 95% of requests should complete within 500ms
    'http_req_duration': ['p(95)<500'],

    // Join room should be fast (p95 < 300ms)
    'join_room_latency': ['p(95)<300'],

    // State fetch should be very fast (p95 < 200ms)
    'get_state_latency': ['p(95)<200'],

    // Leaderboard query should be fast even with many users (p95 < 400ms)
    'leaderboard_latency': ['p(95)<400'],

    // Gameplay endpoints (news, recommendations, game data)
    'get_news_latency': ['p(95)<300'],
    'get_recommendations_latency': ['p(95)<400'],
    'get_game_data_latency': ['p(95)<500'],

    // Player state update (after trading)
    'update_player_latency': ['p(95)<300'],

    // At least 95% of join room attempts should succeed
    'join_room_success': ['rate>0.95'],

    // Error rate should be below 1%
    'http_req_failed': ['rate<0.01'],
  },
};

/**
 * Setup phase: Create a game room before test starts
 * This runs once before all VUs start
 */
export function setup() {
  // If room code is provided externally, skip room creation
  if (ROOM_CODE) {
    console.log(`Using existing room: ${ROOM_CODE}`);
    return { roomCode: ROOM_CODE };
  }

  console.log('Creating test game room...');

  const createRoomPayload = JSON.stringify({
    created_by: 'PerfTestTeacher',
    room_name: 'K6 Performance Test Room',
    config: {
      initial_cash: 100000,
      num_days: 30,
      tickers: ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
      difficulty: 'medium',
    },
    game_mode: 'async', // Async mode for independent user progression
    day_duration_seconds: null,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(`${BASE_URL}/api/v1/multiplayer/rooms`, createRoomPayload, params);

  check(res, {
    'room created successfully': (r) => r.status === 200,
  });

  if (res.status !== 200) {
    console.error(`Failed to create room: ${res.status} - ${res.body}`);
    throw new Error('Room creation failed');
  }

  const roomData = JSON.parse(res.body);
  const roomCode = roomData.room_code;

  console.log(`✓ Game room created: ${roomCode}`);
  console.log(`  - Room ID: ${roomData.id}`);
  console.log(`  - Config: ${JSON.stringify(roomData.config)}`);

  return { roomCode: roomCode };
}

/**
 * Main test function - runs for each VU
 * Each VU represents one student joining and playing through the game
 *
 * Real gameplay flow per day:
 * 1. Get news articles for the day
 * 2. Get AI recommendations for the day
 * 3. Get game data (prices, portfolio)
 * 4. Make trading decision (simulated by waiting)
 * 5. Advance to next day (repeat up to 30 times)
 */
// Global map to store player IDs per VU (persists across iterations)
const playerIds = {};

export default function (data) {
  const roomCode = data.roomCode;

  // Each VU gets a unique player name based on their VU number
  const vuId = __VU; // Virtual User ID (1-based)
  const iterationId = __ITER; // Current iteration number
  const playerName = `Student_VU${vuId}`;

  // Step 1: Join the room (only once per VU, at first iteration)
  if (iterationId === 0) {
    const joinResult = joinRoom(roomCode, playerName);
    if (!joinResult.success) {
      apiErrors.add(1);
      return;
    }
    // Store player ID globally so it persists across iterations
    playerIds[vuId] = joinResult.playerId;

    // Initial load - user sees the game page for first time
    sleep(1); // Page loading time

    // Get initial room state
    getRoomState(roomCode);
    sleep(0.5);

    // Check initial leaderboard
    getLeaderboard(roomCode);
    sleep(0.5);
  }

  // Get playerId from global map
  const playerId = playerIds[vuId];

  // Step 2: Simulate playing one day (each iteration = one game day)
  // This simulates the user viewing and interacting with data for the current day

  // A. Get news for current day (user reads news)
  getNews();
  sleep(1 + Math.random()); // 1-2 seconds reading news

  // B. Get AI recommendations (user reviews recommendations)
  getRecommendations();
  sleep(1 + Math.random()); // 1-2 seconds reviewing recommendations

  // C. Get game data (prices, portfolio value)
  getGameData();
  sleep(1 + Math.random() * 2); // 1-3 seconds reviewing portfolio

  // D. Check leaderboard to see ranking
  getLeaderboard(roomCode);
  sleep(0.5 + Math.random()); // 0.5-1.5 seconds viewing leaderboard

  // E. User makes trading decision (simulated by thinking time)
  sleep(2 + Math.random() * 3); // 2-5 seconds deciding to buy/sell

  // F. Execute trades and update player state (if playerId exists)
  if (playerId) {
    updatePlayerState(playerId, iterationId + 1);
    sleep(0.5);
  }

  // G. Refresh game state to see updated portfolio
  getRoomState(roomCode);
  sleep(0.5);

  // Pause before next day (user clicks "Advance Day" or waits for auto-advance)
  sleep(1 + Math.random() * 2); // 1-3 seconds
}

/**
 * Join a game room
 */
function joinRoom(roomCode, playerName) {
  const joinPayload = JSON.stringify({
    room_code: roomCode,
    player_name: playerName,
    player_email: `${playerName.toLowerCase()}@test.com`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const startTime = Date.now();
  const res = http.post(`${BASE_URL}/api/v1/multiplayer/rooms/join`, joinPayload, params);
  const duration = Date.now() - startTime;

  joinRoomLatency.add(duration);

  const success = check(res, {
    'join room: status 200': (r) => r.status === 200,
    'join room: has player_id': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return body.id !== undefined;
      }
      return false;
    },
  });

  joinRoomSuccess.add(success ? 1 : 0);

  if (!success) {
    console.error(`Join room failed for ${playerName}: ${res.status} - ${res.body}`);
    return { success: false };
  }

  const playerData = JSON.parse(res.body);
  return {
    success: true,
    playerId: playerData.id,
  };
}

/**
 * Get current room state
 */
function getRoomState(roomCode) {
  const startTime = Date.now();
  const res = http.get(`${BASE_URL}/api/v1/multiplayer/rooms/${roomCode}/state`);
  const duration = Date.now() - startTime;

  getStateLatency.add(duration);

  check(res, {
    'get state: status 200': (r) => r.status === 200,
    'get state: has room_code': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return body.room_code === roomCode;
      }
      return false;
    },
  });

  if (res.status !== 200) {
    apiErrors.add(1);
  }
}

/**
 * Get leaderboard
 */
function getLeaderboard(roomCode) {
  const startTime = Date.now();
  const res = http.get(`${BASE_URL}/api/v1/multiplayer/rooms/${roomCode}/leaderboard`);
  const duration = Date.now() - startTime;

  leaderboardLatency.add(duration);

  check(res, {
    'leaderboard: status 200': (r) => r.status === 200,
    'leaderboard: is array': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return Array.isArray(body);
      }
      return false;
    },
  });

  if (res.status !== 200) {
    apiErrors.add(1);
  }
}

/**
 * Get news articles (simulates user reading news for the day)
 */
function getNews() {
  // In a real scenario, you'd pass the current date
  // For this test, we just get recent news
  const startTime = Date.now();
  const res = http.get(`${BASE_URL}/api/v1/news/`);
  const duration = Date.now() - startTime;

  getNewsLatency.add(duration);

  check(res, {
    'get news: status 200': (r) => r.status === 200,
    'get news: is array': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return Array.isArray(body);
      }
      return false;
    },
  });

  if (res.status !== 200) {
    apiErrors.add(1);
  }
}

/**
 * Get AI recommendations (simulates user reviewing AI suggestions)
 */
function getRecommendations() {
  const startTime = Date.now();
  const res = http.get(`${BASE_URL}/api/v1/recommendations?days=7`);
  const duration = Date.now() - startTime;

  getRecommendationsLatency.add(duration);

  check(res, {
    'get recommendations: status 200': (r) => r.status === 200,
    'get recommendations: has data': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return body.recommendations !== undefined;
      }
      return false;
    },
  });

  if (res.status !== 200) {
    apiErrors.add(1);
  }
}

/**
 * Get game data (prices, portfolio, etc.)
 */
function getGameData() {
  const startTime = Date.now();
  const res = http.get(`${BASE_URL}/api/v1/game/data?days=30`);
  const duration = Date.now() - startTime;

  getGameDataLatency.add(duration);

  check(res, {
    'get game data: status 200': (r) => r.status === 200,
    'get game data: has tickers': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return body.tickers !== undefined;
      }
      return false;
    },
  });

  if (res.status !== 200) {
    apiErrors.add(1);
  }
}

/**
 * Update player state after trading (simulates buy/sell actions)
 */
function updatePlayerState(playerId, currentDay) {
  // Simulate realistic trading data
  // In reality, this would be calculated based on actual trades made
  const initialCash = 100000;
  const randomTrade = Math.random() > 0.5; // 50% chance of trading

  // Simulate player state after some trading
  const playerState = {
    current_day: currentDay,
    cash: initialCash - (randomTrade ? Math.random() * 10000 : 0),
    holdings: randomTrade ? {
      'AAPL': { shares: Math.floor(Math.random() * 10), avgCost: 150 + Math.random() * 20 }
    } : {},
    trades: randomTrade ? [{
      day: currentDay,
      ticker: 'AAPL',
      action: 'BUY',
      shares: Math.floor(Math.random() * 10),
      price: 150 + Math.random() * 20
    }] : [],
    portfolio_value: initialCash + Math.random() * 5000,
    total_return_pct: (Math.random() - 0.5) * 10, // -5% to +5%
    total_return_usd: (Math.random() - 0.5) * 5000,
    score: 500 + Math.random() * 200,
    grade: 'B',
    score_breakdown: {
      returns: 200,
      risk: 150,
      consistency: 100
    },
    portfolio_history: [
      { day: currentDay, value: initialCash + Math.random() * 5000 }
    ],
    is_finished: currentDay >= 30,
    ai_portfolio_value: initialCash + Math.random() * 6000,
    ai_total_return_pct: (Math.random() - 0.3) * 12
  };

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const startTime = Date.now();
  const res = http.put(
    `${BASE_URL}/api/v1/multiplayer/players/${playerId}`,
    JSON.stringify(playerState),
    params
  );
  const duration = Date.now() - startTime;

  updatePlayerLatency.add(duration);

  check(res, {
    'update player: status 200': (r) => r.status === 200,
    'update player: has updated data': (r) => {
      if (r.status === 200) {
        const body = JSON.parse(r.body);
        return body.current_day === currentDay;
      }
      return false;
    },
  });

  if (res.status !== 200) {
    apiErrors.add(1);
  }
}

/**
 * Teardown phase: Clean up after test
 * This runs once after all VUs complete
 */
export function teardown(data) {
  console.log(`\n✓ Performance test completed for room: ${data.roomCode}`);
  console.log('Check k6 metrics for detailed results.');

  // Optionally, you could fetch final leaderboard here
  // const res = http.get(`${BASE_URL}/api/v1/multiplayer/rooms/${data.roomCode}/leaderboard`);
  // console.log('Final leaderboard:', res.body);
}

/**
 * Custom summary handler for better reporting
 */
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }) + '\n' + customSummary(data),
    'results/multiplayer-load-summary.json': JSON.stringify(data),
  };
}

function customSummary(data) {
  let summary = '\n';
  summary += '═══════════════════════════════════════════════════\n';
  summary += '  K6 Performance Test Summary: Multiplayer Load\n';
  summary += '═══════════════════════════════════════════════════\n\n';

  // Add key metrics
  const metrics = data.metrics;

  // Helper function to safely get metric value (K6 uses 'med', 'p(95)', 'p(99)' format)
  const getMetricValue = (metric, stat) => {
    if (metric && metric.values && metric.values[stat] !== undefined) {
      return metric.values[stat].toFixed(2);
    }
    return 'N/A';
  };

  const getRate = (metric) => {
    if (metric && metric.values && metric.values.rate !== undefined) {
      return (metric.values.rate * 100).toFixed(2);
    }
    return 'N/A';
  };

  summary += ' Join Room Latency:\n';
  summary += `   - median: ${getMetricValue(metrics.join_room_latency, 'med')}ms\n`;
  summary += `   - p95:    ${getMetricValue(metrics.join_room_latency, 'p(95)')}ms (SLO: <300ms)\n`;

  summary += '\n Get State Latency:\n';
  summary += `   - median: ${getMetricValue(metrics.get_state_latency, 'med')}ms\n`;
  summary += `   - p95:    ${getMetricValue(metrics.get_state_latency, 'p(95)')}ms (SLO: <200ms)\n`;

  summary += '\n Leaderboard Latency:\n';
  summary += `   - median: ${getMetricValue(metrics.leaderboard_latency, 'med')}ms\n`;
  summary += `   - p95:    ${getMetricValue(metrics.leaderboard_latency, 'p(95)')}ms (SLO: <400ms)\n`;

  summary += '\n Gameplay Endpoints:\n';
  summary += `   News (p95):            ${getMetricValue(metrics.get_news_latency, 'p(95)')}ms\n`;
  summary += `   Recommendations (p95): ${getMetricValue(metrics.get_recommendations_latency, 'p(95)')}ms\n`;
  summary += `   Game Data (p95):       ${getMetricValue(metrics.get_game_data_latency, 'p(95)')}ms\n`;
  summary += `   Update Player (p95):   ${getMetricValue(metrics.update_player_latency, 'p(95)')}ms\n`;

  summary += '\n Success Rates:\n';
  summary += `   - Join Room: ${getRate(metrics.join_room_success)}%\n`;

  if (metrics.http_req_failed) {
    const successRate = metrics.http_req_failed.values.rate !== undefined
      ? ((1 - metrics.http_req_failed.values.rate) * 100).toFixed(2)
      : 'N/A';
    summary += `   - HTTP Success: ${successRate}%\n`;
  }

  summary += '\n═══════════════════════════════════════════════════\n';

  return summary;
}
