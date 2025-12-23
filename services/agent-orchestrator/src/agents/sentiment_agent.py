"""
Sentiment analysis agent.
Analyzes news sentiment and generates signals.
"""
from typing import Dict, Any
from uuid import uuid4

from .base_agent import BaseAgent
from ..prompts.sentiment_prompt import get_sentiment_prompt


class SentimentAgent(BaseAgent):
    """
    Analyzes sentiment features:
    - Average and weighted sentiment scores
    - Article counts and distribution
    - Top themes and topics
    """

    def __init__(self, model_version: str = None):
        super().__init__(
            agent_type="sentiment",
            model_version=model_version
        )

    def analyze(
        self,
        ticker: str,
        as_of_date,
        feature_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze sentiment features and generate signal.

        Returns:
            {
                "output_id": str,
                "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
                "strength": float (0.0-1.0),
                "reasoning": [str],
                "key_themes": dict
            }
        """
        # Extract sentiment features
        sentiment = feature_snapshot.get("sentiment_features", {})

        if not sentiment or sentiment.get("article_count", 0) == 0:
            return self._create_neutral_output(
                ticker,
                as_of_date,
                feature_snapshot.get("snapshot_id"),
                reason="No sentiment data available"
            )

        # Get prompt template
        prompt_template = get_sentiment_prompt()

        # Format feature data for prompt
        feature_summary = self._format_features(sentiment)

        # Create user prompt
        user_prompt = prompt_template.format(
            ticker=ticker,
            feature_data=feature_summary
        )

        # Call LLM
        system_prompt = "You are an expert news sentiment analyst specializing in financial markets."
        response = self._call_llm(system_prompt, user_prompt)

        # Parse response
        result = self._parse_json_response(response)

        # Create output
        output = {
            "output_id": f"{ticker}_{as_of_date}_sentiment_{uuid4().hex[:8]}",
            "agent_type": self.agent_type,
            "ticker": ticker,
            "as_of_date": as_of_date,
            "signal": result.get("signal", "NEUTRAL"),
            "strength": float(result.get("strength", 0.5)),
            "reasoning": result.get("reasoning", []),
            "agent_metadata": {
                "key_themes": result.get("key_themes", {})
            },
            "feature_snapshot_id": feature_snapshot.get("snapshot_id"),
            "model_version": self.model_version,
            "prompt_hash": self._create_prompt_hash(user_prompt)
        }

        return output

    def _format_features(self, sentiment: Dict[str, Any]) -> str:
        """Format sentiment features for LLM prompt."""
        lines = []

        # Sentiment Scores
        lines.append("Sentiment Metrics:")
        if "avg_sentiment" in sentiment and sentiment["avg_sentiment"] is not None:
            lines.append(f"  Average Sentiment: {sentiment['avg_sentiment']:.3f}")
        if "weighted_sentiment" in sentiment and sentiment["weighted_sentiment"] is not None:
            lines.append(f"  Weighted Sentiment: {sentiment['weighted_sentiment']:.3f}")

        # Article Counts
        lines.append("\nArticle Coverage:")
        lines.append(f"  Total Articles: {sentiment.get('article_count', 0)}")
        lines.append(f"  Positive: {sentiment.get('positive_count', 0)}")
        lines.append(f"  Neutral: {sentiment.get('neutral_count', 0)}")
        lines.append(f"  Negative: {sentiment.get('negative_count', 0)}")

        # Top Themes
        if "top_themes" in sentiment and sentiment["top_themes"]:
            lines.append("\nKey Themes:")
            for theme in sentiment["top_themes"][:5]:  # Top 5 themes
                lines.append(f"  - {theme}")

        return "\n".join(lines)

    def _create_neutral_output(
        self,
        ticker: str,
        as_of_date,
        snapshot_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """Create neutral output when analysis is impossible."""
        return {
            "output_id": f"{ticker}_{as_of_date}_sentiment_neutral",
            "agent_type": self.agent_type,
            "ticker": ticker,
            "as_of_date": as_of_date,
            "signal": "NEUTRAL",
            "strength": 0.0,
            "reasoning": [reason],
            "agent_metadata": {},
            "feature_snapshot_id": snapshot_id,
            "model_version": self.model_version,
            "prompt_hash": ""
        }
