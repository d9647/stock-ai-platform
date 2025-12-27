/**
 * API functions for recommendations endpoints
 */

import type {
  RecommendationDetail,
  RecommendationListResponse,
  RecommendationType,
} from '@/types/api';
import { apiClient } from './client';

export interface GetRecommendationsParams {
  recommendation?: RecommendationType;
  limit?: number;
  offset?: number;
}

/**
 * Get list of recommendations with optional filtering
 */
export async function getRecommendations(
  params?: GetRecommendationsParams
): Promise<RecommendationListResponse> {
  const searchParams = new URLSearchParams();

  if (params?.recommendation) {
    searchParams.set('recommendation', params.recommendation);
  }
  if (params?.limit) {
    searchParams.set('limit', params.limit.toString());
  }
  if (params?.offset) {
    searchParams.set('offset', params.offset.toString());
  }

  const query = searchParams.toString();
  const endpoint = `/api/v1/recommendations/${query ? `?${query}` : ''}`;

  return apiClient<RecommendationListResponse>(endpoint);
}

/**
 * Get recommendation details for a specific ticker
 */
export async function getRecommendation(ticker: string): Promise<RecommendationDetail> {
  return apiClient<RecommendationDetail>(`/api/v1/recommendations/${ticker}`);
}

/**
 * Get top recommendations (convenience function)
 */
export async function getTopRecommendations(limit: number = 4): Promise<RecommendationListResponse> {
  return getRecommendations({ limit });
}
