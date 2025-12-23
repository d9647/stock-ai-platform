"""
Sentiment analysis prompts (versioned).
"""

SENTIMENT_PROMPT_V1 = """
You are an expert news sentiment analyst analyzing {ticker}.

Sentiment Data:
{feature_data}

Analyze the news sentiment and provide:
1. Overall signal: BULLISH, NEUTRAL, or BEARISH
2. Signal strength: 0.0 (weak) to 1.0 (strong)
3. Reasoning: List of 3-5 key points
4. Key themes: Summary of news themes and their impact

Return JSON:
{{
  "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
  "strength": 0.0-1.0,
  "reasoning": ["point 1", "point 2", ...],
  "key_themes": {{
    "primary_themes": ["theme1", "theme2"],
    "sentiment_trend": "improving" | "stable" | "declining",
    "article_quality": "high" | "medium" | "low"
  }}
}}

Focus on:
- Overall sentiment score and trend
- Volume and quality of coverage
- Key themes and their implications
- Consistency of messaging
"""


def get_sentiment_prompt(version: str = "v1") -> str:
    """Get sentiment analysis prompt by version."""
    prompts = {
        "v1": SENTIMENT_PROMPT_V1,
    }
    return prompts.get(version, SENTIMENT_PROMPT_V1)
