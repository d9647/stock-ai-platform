/**
 * API functions for game endpoints
 */

import type { GameData } from '@/types/game';
import { apiClient } from './client';

export interface GetGameDataParams {
  days?: number; // Default: 30
  tickers?: string[]; // Default: ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
  endDate?: string; // YYYY-MM-DD format, defaults to latest
  startDate?: string; // YYYY-MM-DD format, must be >= 2025-01-01
}

/**
 * Fetch complete game data for N days
 * This preloads all recommendations and prices needed for gameplay
 */
export async function getGameData(params?: GetGameDataParams): Promise<GameData> {
  const searchParams = new URLSearchParams();

  if (params?.days) {
    searchParams.set('days', params.days.toString());
  }
  if (params?.tickers && params.tickers.length > 0) {
    searchParams.set('tickers', params.tickers.join(','));
  }
  if (params?.endDate) {
    searchParams.set('end_date', params.endDate);
  }
  if (params?.startDate) {
    searchParams.set('start_date', params.startDate);
  }

  const query = searchParams.toString();
  const endpoint = `/api/v1/game/data${query ? `?${query}` : ''}`;

  return apiClient<GameData>(endpoint);
}
