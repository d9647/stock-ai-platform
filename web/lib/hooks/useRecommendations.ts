/**
 * React Query hooks for recommendations
 */

import { useQuery } from '@tanstack/react-query';
import type { RecommendationType } from '@/types/api';
import { getRecommendations, getRecommendation, getTopRecommendations } from '../api/recommendations';

/**
 * Hook to fetch list of recommendations
 */
export function useRecommendations(params?: {
  recommendation?: RecommendationType;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['recommendations', params],
    queryFn: () => getRecommendations(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch single recommendation by ticker
 */
export function useRecommendation(ticker: string) {
  return useQuery({
    queryKey: ['recommendation', ticker],
    queryFn: () => getRecommendation(ticker),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!ticker,
  });
}

/**
 * Hook to fetch top recommendations for homepage
 */
export function useTopRecommendations(limit: number = 4) {
  return useQuery({
    queryKey: ['recommendations', 'top', limit],
    queryFn: () => getTopRecommendations(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
