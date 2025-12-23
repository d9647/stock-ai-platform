"""
Recommendation synthesis prompts (versioned).
"""

SYNTHESIS_PROMPT_V1 = """
You are a portfolio manager synthesizing signals for {ticker}.

Agent Outputs:
{agent_signals}

Feature Snapshot Date: {as_of_date}

Synthesize all signals into a final recommendation:
1. Final recommendation: STRONG_BUY, BUY, HOLD, SELL, or STRONG_SELL
2. Confidence: 0.0 (low) to 1.0 (high)
3. Structured rationale for UI
4. Position sizing and time horizon

Return JSON:
{{
  "recommendation": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
  "confidence": 0.0-1.0,
  "rationale": {{
    "summary": ["1-2 sentence summary as a single list item"],
    "technical_view": ["2-3 key technical points as separate list items"],
    "sentiment_view": ["2-3 key sentiment points as separate list items"],
    "risk_view": ["2-3 key risk points as separate list items"],
    "key_factors": ["factor 1", "factor 2", "factor 3"]
  }},
  "position_size": "small" | "medium" | "large",
  "time_horizon": "short_term" | "medium_term" | "long_term"
}}

Guidelines:
- STRONG_BUY: All 3 agents bullish, low risk
- BUY: 2+ agents bullish, acceptable risk
- HOLD: Mixed signals or neutral
- SELL: 2+ agents bearish
- STRONG_SELL: All 3 agents bearish or extreme risk

Consider:
- Signal alignment across agents
- Confidence levels of each agent
- Risk vs. reward tradeoff
- Time horizon appropriateness
"""


def get_synthesis_prompt(version: str = "v1") -> str:
    """Get synthesis prompt by version."""
    prompts = {
        "v1": SYNTHESIS_PROMPT_V1,
    }
    return prompts.get(version, SYNTHESIS_PROMPT_V1)
