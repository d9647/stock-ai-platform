/**
 * TypeScript types matching the FastAPI backend schemas
 */

export type RecommendationType =
  | 'STRONG_BUY'
  | 'BUY'
  | 'HOLD'
  | 'SELL'
  | 'STRONG_SELL';

export type SignalType = 'BULLISH' | 'NEUTRAL' | 'BEARISH';

export type RiskLevel = 'LOW_RISK' | 'MEDIUM_RISK' | 'HIGH_RISK' | 'EXTREME_RISK';

export type PositionSize = 'small' | 'medium' | 'large';

export type TimeHorizon = 'short_term' | 'medium_term' | 'long_term';

export interface Rationale {
  summary: string[];
  technical_view: string[];
  sentiment_view: string[];
  risk_view: string[];
  key_factors: string[];
}

export interface RecommendationSummary {
  recommendation_id: string;
  ticker: string;
  as_of_date: string;
  recommendation: RecommendationType;
  confidence: number;
  technical_signal: SignalType;
  sentiment_signal: SignalType;
  risk_level: RiskLevel;
  position_size: PositionSize;
  time_horizon: TimeHorizon;
}

export interface RecommendationDetail extends RecommendationSummary {
  rationale: Rationale;
  agent_outputs: {
    technical: string;
    sentiment: string;
    risk: string;
  };
  feature_snapshot_id: string;
  model_version: string;
  created_at: string;
}

export interface RecommendationListResponse {
  recommendations: RecommendationSummary[];
  total: number;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
}

export interface DatabaseHealth {
  database_connected: boolean;
  timestamp: string;
}

export interface APIError {
  detail: string;
}
