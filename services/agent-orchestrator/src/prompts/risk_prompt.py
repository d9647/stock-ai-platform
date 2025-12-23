"""
Risk assessment prompts (versioned).
"""

RISK_PROMPT_V1 = """
You are an expert risk analyst analyzing {ticker}.

Risk Metrics:
{feature_data}

Analyze the risk profile and provide:
1. Overall signal: LOW_RISK, MEDIUM_RISK, HIGH_RISK, or EXTREME_RISK
2. Risk confidence: 0.0 (low confidence) to 1.0 (high confidence)
3. Reasoning: List of 3-5 key risk factors
4. Risk breakdown: Detailed risk assessment

Return JSON:
{{
  "signal": "LOW_RISK" | "MEDIUM_RISK" | "HIGH_RISK" | "EXTREME_RISK",
  "strength": 0.0-1.0,
  "reasoning": ["point 1", "point 2", ...],
  "risk_breakdown": {{
    "volatility_level": "low" | "moderate" | "high" | "extreme",
    "trend_stability": "stable" | "unstable",
    "position_sizing": "aggressive" | "moderate" | "conservative"
  }}
}}

Focus on:
- Historical volatility levels
- Recent price action stability
- ATR and Bollinger Band width
- Appropriate position sizing given risk
"""


def get_risk_prompt(version: str = "v1") -> str:
    """Get risk assessment prompt by version."""
    prompts = {
        "v1": RISK_PROMPT_V1,
    }
    return prompts.get(version, RISK_PROMPT_V1)
