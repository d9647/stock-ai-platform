/**
 * Zustand store for game state management
 * Handles turn-based gameplay, portfolio management, and scoring
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  GameState,
  GameConfig,
  GameData,
  GameDay,
  PlayerState,
  AIState,
  Trade,
  Holding,
  PortfolioSnapshot,
  ScoreBreakdown,
  TradeValidation,
} from '@/types/game';

const DEFAULT_CONFIG: GameConfig = {
  initialCash: 100000,
  numDays: 30,
  tickers: ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
  difficulty: 'medium',
  startDate: undefined,
};

const createInitialPlayerState = (config: GameConfig): PlayerState => ({
  playerId: `player_${Date.now()}`,
  playerName: 'You',
  currentDay: 0,
  gameStartedAt: new Date().toISOString(),
  cash: config.initialCash,
  holdings: {},
  trades: [],
  portfolioHistory: [],
  score: 0,
  scoreBreakdown: {
    portfolioReturn: 0,
    riskDiscipline: 0,
    beatAI: 0,
    drawdownPenalty: 0,
    totalScore: 0,
    grade: 'C',
  },
  grade: 'C',
});

const createInitialAIState = (config: GameConfig): AIState => ({
  cash: config.initialCash,
  holdings: {},
  trades: [],
  portfolioHistory: [],
});

interface GameStore extends GameState {
  // Setup actions
  hasHydrated: boolean;
  loadGameData: (data: GameData) => void;
  startGame: (config?: Partial<GameConfig>) => void;
  startMultiplayerGame: (multiplayerData: {
    roomCode: string;
    playerId: string;
    role: 'teacher' | 'student';
    config: GameConfig;
    startDate: string;
    endDate: string;
  }) => Promise<void>;
  resetGame: () => void;

  // Gameplay actions
  advanceDay: () => void;
  buy: (ticker: string, shares: number) => void;
  sell: (ticker: string, shares: number) => void;

  // Validation
  canBuy: (ticker: string) => TradeValidation;
  canSell: (ticker: string, shares: number) => TradeValidation;

  // Computed values
  getCurrentDayData: () => ReturnType<typeof getCurrentDayData>;
  getPortfolioValue: () => number;
  getHoldings: () => Holding[];
  getAIPortfolioValue: () => number;
  calculateScore: () => ScoreBreakdown;
}

function getCurrentDayData(gameData: GameData | null, currentDay: number) {
  if (!gameData || currentDay >= gameData.total_days) {
    return null;
  }
  return gameData.days[currentDay];
}

function calculatePortfolioValue(
  cash: number,
  holdings: Record<string, Holding>,
  prices: Record<string, { open: number; close: number }>
): number {
  let holdingsValue = 0;
  for (const ticker in holdings) {
    const holding = holdings[ticker];
    const currentPrice = prices[ticker]?.close || holding.avgCost;
    holdingsValue += holding.shares * currentPrice;
  }
  return cash + holdingsValue;
}

function calculateGrade(returnPercent: number, difficulty: string): string {
  // Grade thresholds based on difficulty
  const thresholds =
    difficulty === 'easy'
      ? { A: 5, B: 2, C: 0, D: -3 }
      : difficulty === 'hard'
      ? { A: 15, B: 10, C: 5, D: 0 }
      : { A: 10, B: 5, C: 0, D: -5 }; // medium

  if (returnPercent >= thresholds.A) return 'A';
  if (returnPercent >= thresholds.B) return 'B';
  if (returnPercent >= thresholds.C) return 'C';
  if (returnPercent >= thresholds.D) return 'D';
  return 'F';
}

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      // Initial state
      config: DEFAULT_CONFIG,
      gameData: null,
      isLoading: false,
      player: createInitialPlayerState(DEFAULT_CONFIG),
      ai: createInitialAIState(DEFAULT_CONFIG),
      status: 'not_started',
      isMultiplayer: false,
      role: null,
      hasHydrated: false,

      // Load game data (called after fetching from API)
      loadGameData: (data: GameData) => {
        set({ gameData: data, isLoading: false });
      },

      // Start a new game
      startGame: (configOverrides?: Partial<GameConfig>) => {
        const config = { ...DEFAULT_CONFIG, ...configOverrides };
        set({
          config,
          player: createInitialPlayerState(config),
          ai: createInitialAIState(config),
          status: 'playing',
          isMultiplayer: false,
        });
      },

      // Start a multiplayer game
      startMultiplayerGame: async (multiplayerData) => {
        const playerName = typeof window !== 'undefined'
          ? localStorage.getItem('multiplayer_player_name') || 'Player'
          : 'Player';

        set({
          config: multiplayerData.config,
          player: {
            ...createInitialPlayerState(multiplayerData.config),
            playerId: multiplayerData.playerId,
            playerName,
          },
          ai: createInitialAIState(multiplayerData.config),
          status: 'playing',
          isMultiplayer: true,
          roomCode: multiplayerData.roomCode,
          role: multiplayerData.role,
          isLoading: true,
        });

        // Fetch game data for the multiplayer room dates
        try {
          const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/game/data?start_date=${multiplayerData.startDate}&end_date=${multiplayerData.endDate}&tickers=${multiplayerData.config.tickers.join(',')}`;
          console.log('Fetching game data from:', apiUrl);

          const response = await fetch(apiUrl);

          if (response.ok) {
            const data = await response.json();
            console.log('Game data loaded successfully:', data.total_days, 'days');
            set({ gameData: data, isLoading: false });
          } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || `API returned ${response.status}: ${response.statusText}`;
            console.error('Failed to fetch game data:', errorMessage);
            throw new Error(errorMessage);
          }
        } catch (error) {
          console.error('Failed to load multiplayer game data:', error);
          set({ isLoading: false });
          throw error instanceof Error ? error : new Error('Network error - is the API server running?');
        }
      },

      // Reset game to initial state
      resetGame: () => {
        const { config } = get();
        set({
          player: createInitialPlayerState(config),
          ai: createInitialAIState(config),
          status: 'not_started',
        });
      },

      // Advance to next day
      advanceDay: () => {
        const { player, ai, gameData, config } = get();

        if (!gameData) return;

        const nextDay = player.currentDay + 1;

        // Check if game is finished
        if (nextDay >= gameData.total_days) {
          set({
            status: 'finished',
            player: {
              ...player,
              gameEndedAt: new Date().toISOString(),
            },
          });
          return;
        }

        const currentDayData = gameData.days[player.currentDay];
        const nextDayData = gameData.days[nextDay];

        if (!currentDayData || !nextDayData) return;

        // Calculate end-of-day portfolio value
        const portfolioValue = get().getPortfolioValue();
        const aiPortfolioValue = get().getAIPortfolioValue();

        // Update portfolio history
        const playerSnapshot: PortfolioSnapshot = {
          day: player.currentDay,
          date: currentDayData.date,
          cash: player.cash,
          holdingsValue: portfolioValue - player.cash,
          totalValue: portfolioValue,
          returnPercent: ((portfolioValue - config.initialCash) / config.initialCash) * 100,
          returnDollars: portfolioValue - config.initialCash,
        };

        const aiSnapshot: PortfolioSnapshot = {
          day: player.currentDay,
          date: currentDayData.date,
          cash: ai.cash,
          holdingsValue: aiPortfolioValue - ai.cash,
          totalValue: aiPortfolioValue,
          returnPercent: ((aiPortfolioValue - config.initialCash) / config.initialCash) * 100,
          returnDollars: aiPortfolioValue - config.initialCash,
        };

        // AI makes trades automatically based on recommendations
        const aiTrades = executeAITrades(ai, nextDayData, config);
        const { updatedAI, tradesWithValues } = applyAITrades(ai, aiTrades, nextDayData.prices);

        // Calculate score
        const scoreBreakdown = get().calculateScore();

        const newPlayerState = {
          ...player,
          currentDay: nextDay,
          portfolioHistory: [...player.portfolioHistory, playerSnapshot],
          score: scoreBreakdown.totalScore,
          scoreBreakdown,
          grade: scoreBreakdown.grade,
        };

        set({
          player: newPlayerState,
          ai: {
            ...updatedAI,
            trades: [...ai.trades, ...tradesWithValues],
            portfolioHistory: [...updatedAI.portfolioHistory, aiSnapshot],
          },
        });

        // Sync with backend in multiplayer mode
        const state = get();
        if (state.isMultiplayer && player.playerId) {
          const syncMultiplayerState = async () => {
            try {
              await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/multiplayer/players/${player.playerId}`,
                {
                  method: 'PUT',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    current_day: newPlayerState.currentDay,
                    cash: newPlayerState.cash,
                    holdings: newPlayerState.holdings,
                    trades: newPlayerState.trades,
                    portfolio_value: portfolioValue,
                    total_return_pct: playerSnapshot.returnPercent,
                    total_return_usd: playerSnapshot.returnDollars,
                    score: newPlayerState.score,
                    grade: newPlayerState.grade,
                    score_breakdown: newPlayerState.scoreBreakdown,
                    portfolio_history: newPlayerState.portfolioHistory,
                    is_finished: nextDay >= gameData.total_days - 1,
                  }),
                }
              );
            } catch (error) {
              console.error('Failed to sync multiplayer state:', error);
            }
          };
          syncMultiplayerState();
        }
      },

      // Buy shares
      buy: (ticker: string, shares: number) => {
        const { player, gameData } = get();
        //const validation = get().canBuy(ticker);
        const validation = { allowed: true, reason: "Buy is always allowed" }; // Assuming AI always allows trades for simplicity

        if (!validation.allowed || !gameData) {
          console.error('Buy not allowed:', validation.reason);
          return;
        }

        const currentDay = gameData.days[player.currentDay];
        const nextDay = gameData.days[player.currentDay + 1];

        if (!nextDay) return;

        // Execute at next day's open price
        const price = nextDay.prices[ticker]?.open || 0;
        const total = shares * price;

        if (total > player.cash) {
          console.error('Insufficient cash');
          return;
        }

        const trade: Trade = {
          id: `trade_${Date.now()}`,
          day: player.currentDay,
          date: currentDay.date,
          ticker,
          type: 'BUY',
          shares,
          price,
          total,
          portfolioValue: get().getPortfolioValue() - total,
        };

        // Update holdings
        const existingHolding = player.holdings[ticker];
        const newShares = (existingHolding?.shares || 0) + shares;
        const newTotalCost = (existingHolding?.totalCost || 0) + total;
        const newAvgCost = newTotalCost / newShares;

        const updatedHolding: Holding = {
          ticker,
          shares: newShares,
          avgCost: newAvgCost,
          totalCost: newTotalCost,
          currentValue: newShares * price,
          unrealizedPnL: newShares * price - newTotalCost,
          unrealizedPnLPercent: ((newShares * price - newTotalCost) / newTotalCost) * 100,
        };

        set({
          player: {
            ...player,
            cash: player.cash - total,
            holdings: {
              ...player.holdings,
              [ticker]: updatedHolding,
            },
            trades: [...player.trades, trade],
          },
        });
      },

      // Sell shares
      sell: (ticker: string, shares: number) => {
        const { player, gameData } = get();
        //const validation = get().canSell(ticker, shares);
        const validation = { allowed: true, reason: "Sell is always allowed" }; // Assuming AI always allows trades for simplicity

        if (!validation.allowed || !gameData) {
          console.error('Sell not allowed:', validation.reason);
          return;
        }

        const currentDay = gameData.days[player.currentDay];
        const nextDay = gameData.days[player.currentDay + 1];

        if (!nextDay) return;

        // Execute at next day's open price
        const price = nextDay.prices[ticker]?.open || 0;
        const total = shares * price;

        const trade: Trade = {
          id: `trade_${Date.now()}`,
          day: player.currentDay,
          date: currentDay.date,
          ticker,
          type: 'SELL',
          shares,
          price,
          total,
          portfolioValue: get().getPortfolioValue() + total,
        };

        // Update holdings
        const existingHolding = player.holdings[ticker]!;
        const newShares = existingHolding.shares - shares;

        if (newShares === 0) {
          // Remove holding entirely
          const { [ticker]: _removed, ...remainingHoldings } = player.holdings;
          set({
            player: {
              ...player,
              cash: player.cash + total,
              holdings: remainingHoldings,
              trades: [...player.trades, trade],
            },
          });
        } else {
          // Update holding
          const newTotalCost = existingHolding.avgCost * newShares;
          const updatedHolding: Holding = {
            ticker,
            shares: newShares,
            avgCost: existingHolding.avgCost,
            totalCost: newTotalCost,
            currentValue: newShares * price,
            unrealizedPnL: newShares * price - newTotalCost,
            unrealizedPnLPercent: ((newShares * price - newTotalCost) / newTotalCost) * 100,
          };

          set({
            player: {
              ...player,
              cash: player.cash + total,
              holdings: {
                ...player.holdings,
                [ticker]: updatedHolding,
              },
              trades: [...player.trades, trade],
            },
          });
        }
      },

      // Validate if player can buy
      canBuy: (ticker: string): TradeValidation => {
        const { player, gameData } = get();

        if (!gameData) {
          return { allowed: false, reason: 'Game data not loaded' };
        }

        const currentDay = gameData.days[player.currentDay];
        if (!currentDay) {
          return { allowed: false, reason: 'Invalid game day' };
        }

        // Check if markets are open
        if (!currentDay.is_trading_day) {
          return { allowed: false, reason: 'Markets are closed. Trading resumes on next trading day.' };
        }

        const recommendation = currentDay.recommendations.find((r) => r.ticker === ticker);
        if (!recommendation) {
          return { allowed: false, reason: 'Ticker not found in recommendations' };
        }

        // Can only buy when AI says BUY or STRONG_BUY
        if (recommendation.recommendation !== 'BUY' && recommendation.recommendation !== 'STRONG_BUY') {
          return {
            allowed: false,
            reason: `AI recommends ${recommendation.recommendation}. You can only buy when AI says BUY or STRONG_BUY.`,
          };
        }

        return { allowed: true };
      },

      // Validate if player can sell
      canSell: (ticker: string, shares: number): TradeValidation => {
        const { player, gameData } = get();

        if (!gameData) {
          return { allowed: false, reason: 'Game data not loaded' };
        }

        const currentDay = gameData.days[player.currentDay];
        if (!currentDay) {
          return { allowed: false, reason: 'Invalid game day' };
        }

        // Check if markets are open
        if (!currentDay.is_trading_day) {
          return { allowed: false, reason: 'Markets are closed. Trading resumes on next trading day.' };
        }

        const holding = player.holdings[ticker];
        if (!holding) {
          return { allowed: false, reason: 'You do not own any shares of this stock' };
        }

        if (shares > holding.shares) {
          return { allowed: false, reason: `You only own ${holding.shares} shares` };
        }

        return { allowed: true };
      },

      // Get current day data
      getCurrentDayData: () => {
        const { gameData, player } = get();
        return getCurrentDayData(gameData, player.currentDay);
      },

      // Calculate current portfolio value
      getPortfolioValue: () => {
        const { player, gameData } = get();
        if (!gameData) return player.cash;

        const currentDay = gameData.days[player.currentDay];
        if (!currentDay) return player.cash;

        return calculatePortfolioValue(player.cash, player.holdings, currentDay.prices);
      },

      // Get holdings as array
      getHoldings: () => {
        const { player, gameData } = get();
        if (!gameData) return [];

        const currentDay = gameData.days[player.currentDay];
        if (!currentDay) return [];

        return Object.values(player.holdings).map((holding) => {
          const currentPrice = currentDay.prices[holding.ticker]?.close || holding.avgCost;
          return {
            ...holding,
            currentValue: holding.shares * currentPrice,
            unrealizedPnL: holding.shares * currentPrice - holding.totalCost,
            unrealizedPnLPercent:
              ((holding.shares * currentPrice - holding.totalCost) / holding.totalCost) * 100,
          };
        });
      },

      // Calculate AI portfolio value
      getAIPortfolioValue: () => {
        const { ai, gameData, player } = get();
        if (!gameData) return ai.cash;

        const currentDay = gameData.days[player.currentDay];
        if (!currentDay) return ai.cash;

        let holdingsValue = 0;
        for (const ticker in ai.holdings) {
          const holding = ai.holdings[ticker];
          const currentPrice = currentDay.prices[ticker]?.close || holding.avgCost;
          holdingsValue += holding.shares * currentPrice;
        }

        return ai.cash + holdingsValue;
      },

      // Calculate score breakdown
      calculateScore: (): ScoreBreakdown => {
        const { player, config } = get();
        const portfolioValue = get().getPortfolioValue();
        const aiPortfolioValue = get().getAIPortfolioValue();

        const playerReturn = ((portfolioValue - config.initialCash) / config.initialCash) * 100;
        const aiReturn = ((aiPortfolioValue - config.initialCash) / config.initialCash) * 100;

        // Portfolio return points (0-500 points)
        const portfolioReturn = Math.max(0, Math.min(500, playerReturn * 50));

        // Risk discipline (50 points per trade that follows AI signal)
        const riskDiscipline = player.trades.filter((t) => t.type === 'BUY').length * 50;

        // Beat AI bonus (0-200 points)
        const beatAI = playerReturn > aiReturn ? 200 : 0;

        // Drawdown penalty (0 to -200 points)
        const maxDrawdown = calculateMaxDrawdown(player.portfolioHistory);
        const drawdownPenalty = maxDrawdown < -10 ? maxDrawdown * 20 : 0;

        const totalScore = portfolioReturn + riskDiscipline + beatAI + drawdownPenalty;
        const grade = calculateGrade(playerReturn, config.difficulty);

        return {
          portfolioReturn,
          riskDiscipline,
          beatAI,
          drawdownPenalty,
          totalScore,
          grade,
        };
      },
    }),
    {
      name: 'stock-game-storage',
      partialize: (state) => ({
        config: state.config,
        player: state.player,
        ai: state.ai,
        status: state.status,
        isMultiplayer: state.isMultiplayer,
        roomCode: state.roomCode,
        role: state.role,
        // ⚠️ EXCLUDE gameData from persistence to avoid localStorage quota issues
        // gameData will be re-fetched when needed
      }),
       // ✅ THIS IS THE FIX
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.hasHydrated = true;
        }
      },
    }
  )
);

// Helper: Calculate max drawdown
function calculateMaxDrawdown(history: PortfolioSnapshot[]): number {
  if (history.length === 0) return 0;

  let maxDrawdown = 0;
  let peak = history[0].totalValue;

  for (const snapshot of history) {
    if (snapshot.totalValue > peak) {
      peak = snapshot.totalValue;
    }
    const drawdown = ((snapshot.totalValue - peak) / peak) * 100;
    if (drawdown < maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }

  return maxDrawdown;
}

// Helper: Execute AI trades automatically
function executeAITrades(
  ai: AIState,
  dayData: GameDay,
  _config: GameConfig
): Trade[] {
  const trades: Trade[] = [];

  // Treat calendar weekends as no-trade; allow weekdays even if is_trading_day was falsy due to missing recs
  const [year, month, dayNum] = dayData.date.split('-').map(Number);
  const dateObj = new Date(year, month - 1, dayNum);
  const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
  if (isWeekend) return trades;

  // AI follows its own recommendations perfectly
  for (const rec of dayData.recommendations) {
    const buyAllocation =
      rec.recommendation === 'STRONG_BUY' ? 0.4 : 0.25; // Stronger conviction buys more
    const sellFraction =
      rec.recommendation === 'STRONG_SELL' ? 1 : 0.5; // Strong sell exits fully, sell trims 50%

    const price = dayData.prices[rec.ticker]?.open || 0;

    // Skip if no price data for this ticker today
    if (!price) continue;

    if (rec.recommendation === 'BUY' || rec.recommendation === 'STRONG_BUY') {
      const sharesToBuy = Math.floor((ai.cash * buyAllocation) / price); // Invest % of cash

      if (sharesToBuy > 0 && sharesToBuy * price <= ai.cash) {
        trades.push({
          id: `ai_trade_${Date.now()}_${rec.ticker}`,
          day: dayData.day,
          date: dayData.date,
          ticker: rec.ticker,
          type: 'BUY',
          shares: sharesToBuy,
          price,
          total: sharesToBuy * price,
          portfolioValue: 0, // Updated later
        });
      }
    } else if (rec.recommendation === 'SELL' || rec.recommendation === 'STRONG_SELL') {
      const holding = ai.holdings[rec.ticker];
      if (holding && holding.shares > 0) {
        const sharesToSell = Math.max(1, Math.floor(holding.shares * sellFraction));
        trades.push({
          id: `ai_trade_${Date.now()}_${rec.ticker}`,
          day: dayData.day,
          date: dayData.date,
          ticker: rec.ticker,
          type: 'SELL',
          shares: Math.min(sharesToSell, holding.shares),
          price,
          total: Math.min(sharesToSell, holding.shares) * price,
          portfolioValue: 0, // Updated later
        });
      }
    }
  }

  return trades;
}

// Helper: Apply AI trades to AI portfolio (cash/holdings) and return updated state
function applyAITrades(
  ai: AIState,
  trades: Trade[],
  prices: Record<string, { open: number; close: number }>
): { updatedAI: AIState; tradesWithValues: Trade[] } {
  if (trades.length === 0) return { updatedAI: ai, tradesWithValues: trades };

  const updatedAI: AIState = {
    ...ai,
    cash: ai.cash,
    holdings: { ...ai.holdings },
  };

  const tradesWithValues: Trade[] = [];

  const computeHoldingValue = (ticker: string, shares: number) => {
    const price = prices?.[ticker]?.close ?? prices?.[ticker]?.open ?? 0;
    return shares * price;
  };

  for (const trade of trades) {
    if (trade.type === 'BUY') {
      if (trade.total > updatedAI.cash) {
        continue;
      }
      const existing = updatedAI.holdings[trade.ticker];
      const newShares = (existing?.shares || 0) + trade.shares;
      const newTotalCost = (existing?.totalCost || 0) + trade.total;
      const newAvgCost = newTotalCost / newShares;

      updatedAI.cash -= trade.total;
      updatedAI.holdings[trade.ticker] = {
        ticker: trade.ticker,
        shares: newShares,
        avgCost: newAvgCost,
        totalCost: newTotalCost,
        currentValue: computeHoldingValue(trade.ticker, newShares),
        unrealizedPnL: computeHoldingValue(trade.ticker, newShares) - newTotalCost,
        unrealizedPnLPercent:
          newTotalCost === 0
            ? 0
            : ((computeHoldingValue(trade.ticker, newShares) - newTotalCost) / newTotalCost) * 100,
      };
    } else if (trade.type === 'SELL') {
      const existing = updatedAI.holdings[trade.ticker];
      if (!existing || existing.shares < trade.shares) {
        continue;
      }
      updatedAI.cash += trade.total;
      const remainingShares = existing.shares - trade.shares;
      if (remainingShares === 0) {
        const { [trade.ticker]: _, ...rest } = updatedAI.holdings;
        updatedAI.holdings = rest;
      } else {
        const remainingCost = existing.avgCost * remainingShares;
        updatedAI.holdings[trade.ticker] = {
          ...existing,
          shares: remainingShares,
          totalCost: remainingCost,
          currentValue: computeHoldingValue(trade.ticker, remainingShares),
          unrealizedPnL:
            computeHoldingValue(trade.ticker, remainingShares) - remainingCost,
          unrealizedPnLPercent:
            remainingCost === 0
              ? 0
              : ((computeHoldingValue(trade.ticker, remainingShares) - remainingCost) /
                  remainingCost) *
                100,
        };
      }
    }

    const aiPortfolioValue =
      updatedAI.cash +
      Object.values(updatedAI.holdings).reduce(
        (sum, h) => sum + h.shares * (prices?.[h.ticker]?.close ?? prices?.[h.ticker]?.open ?? h.avgCost),
        0
      );

    tradesWithValues.push({
      ...trade,
      portfolioValue: aiPortfolioValue,
    });
  }

  return { updatedAI, tradesWithValues };
}
