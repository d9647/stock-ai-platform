/**
 * TypeScript types for the educational stock game
 */

import type { RecommendationType, SignalType, RiskLevel } from './api';

/**
 * Technical indicators for a ticker on a specific day
 */
export interface TechnicalIndicators {
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  ema_12?: number;
  ema_26?: number;
  rsi_14?: number;
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  bollinger_upper?: number;
  bollinger_middle?: number;
  bollinger_lower?: number;
  atr_14?: number;
  obv?: number;
  volatility_30d?: number;
}

/**
 * A single day's market data and AI recommendations
 */
export interface GameDay {
  day: number; // 0-indexed (0 = Day 1)
  date: string; // ISO date string
  is_trading_day: boolean; // Whether markets are open (weekdays)
  recommendations: DayRecommendation[];
  prices: Record<string, DayPrice>; // ticker -> prices
  news?: NewsArticle[]; // News articles for this day
  technical_indicators?: Record<string, TechnicalIndicators>; // ticker -> technical indicators
}

/**
 * AI recommendation for a specific ticker on a specific day
 */
export interface DayRecommendation {
  ticker: string;
  recommendation: RecommendationType;
  confidence: number;
  technical_signal: SignalType;
  sentiment_signal: SignalType;
  risk_level: RiskLevel;
  rationale_summary: string; // Short explanation for students
  rationale_technical_view: string[];
  rationale_sentiment_view: string[];
  rationale_risk_view: string[];
  as_of_date: string; // ISO date the AI used for analysis
}

/**
 * OHLCV prices for a ticker on a specific day
 */
export interface DayPrice {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * News article for a ticker on a specific day
 */
export interface NewsArticle {
  ticker: string;
  headline: string;
  content?: string | null;
  source: string;
  published_at: string;
  sentiment_score?: number | null; // -1 to +1
  url?: string | null;
}

/**
 * Complete game data loaded at start
 */
export interface GameData {
  days: GameDay[];
  tickers: string[];
  start_date: string; // API returns snake_case
  end_date: string; // API returns snake_case
  total_days: number; // API returns snake_case
}

/**
 * A trade executed by the player or AI
 */
export interface Trade {
  id: string;
  day: number;
  date: string;
  ticker: string;
  type: 'BUY' | 'SELL';
  shares: number;
  price: number; // Execution price
  total: number; // shares * price
  portfolioValue: number; // Total portfolio value after trade
}

/**
 * Holdings for a specific ticker
 */
export interface Holding {
  ticker: string;
  shares: number;
  avgCost: number; // Average cost per share
  totalCost: number; // Total invested
  currentValue: number; // Current market value
  unrealizedPnL: number; // Profit/loss
  unrealizedPnLPercent: number; // Profit/loss percentage
}

/**
 * Portfolio snapshot at end of day
 */
export interface PortfolioSnapshot {
  day: number;
  date: string;
  cash: number;
  holdingsValue: number;
  totalValue: number;
  returnPercent: number;
  returnDollars: number;
}

/**
 * Score breakdown
 */
export interface ScoreBreakdown {
  portfolioReturn: number; // points from return vs. benchmark
  riskDiscipline: number; // points from following AI signals
  beatAI: number; // Bonus points for beating AI
  drawdownPenalty: number; // Penalty for large drawdowns
  totalScore: number;
  grade: string; // A+ to F
}

/**
 * Game configuration
 */
export interface GameConfig {
  initialCash: number; // Default: $100,000
  numDays: number; // Default: 30
  tickers: string[]; // Default: ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
  difficulty: 'easy' | 'medium' | 'hard'; // Affects scoring thresholds
  startDate?: string; // Optional start date for simulations
}

/**
 * Player's game state
 */
export interface PlayerState {
  // Identity
  playerId: string;
  playerName: string;

  // Game progress
  currentDay: number; // 0-indexed
  gameStartedAt: string; // ISO timestamp
  gameEndedAt?: string; // ISO timestamp (when finished)

  // Portfolio
  cash: number;
  holdings: Record<string, Holding>; // ticker -> holding
  trades: Trade[];

  // History
  portfolioHistory: PortfolioSnapshot[];

  // Score
  score: number;
  scoreBreakdown: ScoreBreakdown;
  grade: string;
}

/**
 * AI opponent state (runs in parallel)
 */
export interface AIState {
  cash: number;
  holdings: Record<string, {
    ticker: string;
    shares: number;
    avgCost: number;
    totalCost: number;
    currentValue: number;
    unrealizedPnL: number;
    unrealizedPnLPercent: number;
  }>;
  trades: Trade[];
  portfolioHistory: PortfolioSnapshot[];
}

/**
 * Complete game state
 */
export interface GameState {
  // Game data
  config: GameConfig;
  gameData: GameData | null;
  isLoading: boolean;

  // Player state
  player: PlayerState;

  // AI opponent state
  ai: AIState;

  // Game status
  status: 'not_started' | 'playing' | 'finished';

  // Multiplayer (Phase 4)
  roomCode?: string;
  isMultiplayer: boolean;
  role?: 'teacher' | 'student' | null; // User's role in multiplayer
}

/**
 * Trade validation result
 */
export interface TradeValidation {
  allowed: boolean;
  reason?: string;
}

/**
 * Multiplayer room (Phase 4)
 */
export interface GameRoom {
  roomCode: string;
  createdBy: string; // Teacher name
  createdAt: string;
  config: GameConfig;
  players: PlayerState[];
  status: 'waiting' | 'in_progress' | 'finished';
}

/**
 * Leaderboard entry
 */
export interface LeaderboardEntry {
  rank: number;
  playerId: string;
  playerName: string;
  score: number;
  grade: string;
  portfolioValue: number;
  returnPercent: number;
  currentDay: number;
}
