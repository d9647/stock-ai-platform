"""
Technical analysis prompts (versioned).
"""

TECHNICAL_PROMPT_V1 = """
You are an expert technical analyst analyzing {ticker}.

Technical Indicators:
{feature_data}

Analyze the technical picture and provide:
1. Overall signal: BULLISH, NEUTRAL, or BEARISH
2. Signal strength: 0.0 (weak) to 1.0 (strong)
3. Reasoning: List of 3-5 key points
4. Key indicators: Trend, momentum, volatility assessment

Return JSON:
{{
  "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
  "strength": 0.0-1.0,
  "reasoning": ["point 1", "point 2", ...],
  "key_indicators": {{
    "trend": "uptrend" | "sideways" | "downtrend",
    "momentum": "strong" | "moderate" | "weak",
    "volatility": "high" | "normal" | "low"
  }}
}}

Focus on:
- SMA crossovers and alignment
- RSI overbought/oversold levels
- MACD divergences
- Volatility expansion/contraction
"""


def get_technical_prompt(version: str = "v1") -> str:
    """Get technical analysis prompt by version."""
    prompts = {
        "v1": TECHNICAL_PROMPT_V1,
    }
    return prompts.get(version, TECHNICAL_PROMPT_V1)
