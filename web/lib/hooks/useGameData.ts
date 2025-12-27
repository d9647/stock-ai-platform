/**
 * React Query hook for loading game data
 */

import { useQuery } from '@tanstack/react-query';
import { getGameData, type GetGameDataParams } from '../api/game';

/**
 * Hook to fetch game data (all days preloaded)
 * This data is fetched once at game start and cached
 */
export function useGameData(params?: GetGameDataParams & { enabled?: boolean }) {
  const { enabled = true, ...queryParams } = params || {};

  return useQuery({
    queryKey: ['gameData', queryParams],
    queryFn: () => getGameData(queryParams),
    staleTime: Infinity, // Game data never goes stale once loaded
    gcTime: Infinity, // Keep in cache forever during session
    retry: 2,
    enabled, // Allow disabling the query
  });
}
