'use client';

import { useTopRecommendations } from '@/lib/hooks/useRecommendations';
import { RecommendationCard } from './recommendation-card';

export function TopPicks() {
  const { data, isLoading, error } = useTopRecommendations(4);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-64 bg-gray-100 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading recommendations: {error.message}</p>
        <p className="text-sm text-gray-600 mt-2">
          Make sure the API server is running at http://192.168.5.126:8000
        </p>
      </div>
    );
  }

  if (!data?.recommendations || data.recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No recommendations available yet.</p>
        <p className="text-sm text-gray-500 mt-2">
          Run the agent orchestrator pipeline to generate recommendations.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Today's Top Picks</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {data.recommendations.map((rec) => (
          <RecommendationCard key={rec.recommendation_id} recommendation={rec} />
        ))}
      </div>
    </div>
  );
}
