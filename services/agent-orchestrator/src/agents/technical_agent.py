"""
Technical analysis agent.
Analyzes technical indicators and generates trading signals.
"""
from typing import Dict, Any
from uuid import uuid4

from .base_agent import BaseAgent
from ..prompts.technical_prompt import get_technical_prompt


class TechnicalAgent(BaseAgent):
    """
    Analyzes technical indicators:
    - Moving averages (SMA 20, 50, 200)
    - Momentum (RSI, MACD)
    - Volatility (Bollinger Bands, ATR)
    - Volume (OBV)
    """

    def __init__(self, model_version: str = None):
        super().__init__(
            agent_type="technical",
            model_version=model_version
        )

    def analyze(
        self,
        ticker: str,
        as_of_date,
        feature_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze technical features and generate signal.

        Returns:
            {
                "output_id": str,
                "signal": "BULLISH" | "NEUTRAL" | "BEARISH",
                "strength": float (0.0-1.0),
                "reasoning": [str],
                "key_indicators": {
                    "trend": str,
                    "momentum": str,
                    "volatility": str
                }
            }
        """
        # Extract technical features
        technical = feature_snapshot.get("technical_features", {})

        if not technical:
            return self._create_neutral_output(
                ticker,
                as_of_date,
                feature_snapshot.get("snapshot_id"),
                reason="No technical data available"
            )

        # Get prompt template
        prompt_template = get_technical_prompt()

        # Format feature data for prompt
        feature_summary = self._format_features(technical)

        # Create user prompt
        user_prompt = prompt_template.format(
            ticker=ticker,
            feature_data=feature_summary
        )

        # Call LLM
        system_prompt = "You are an expert technical analyst specializing in stock market analysis."
        response = self._call_llm(system_prompt, user_prompt)

        # Parse response
        result = self._parse_json_response(response)

        # Create output
        output = {
            "output_id": f"{ticker}_{as_of_date}_technical_{uuid4().hex[:8]}",
            "agent_type": self.agent_type,
            "ticker": ticker,
            "as_of_date": as_of_date,
            "signal": result.get("signal", "NEUTRAL"),
            "strength": float(result.get("strength", 0.5)),
            "reasoning": result.get("reasoning", []),
            "agent_metadata": {
                "key_indicators": result.get("key_indicators", {})
            },
            "feature_snapshot_id": feature_snapshot.get("snapshot_id"),
            "model_version": self.model_version,
            "prompt_hash": self._create_prompt_hash(user_prompt)
        }

        return output

    def _format_features(self, technical: Dict[str, Any]) -> str:
        """Format technical features for LLM prompt."""
        lines = []

        # Moving Averages
        lines.append("Moving Averages:")
        for ma in ["sma_20", "sma_50", "sma_200"]:
            if ma in technical and technical[ma] is not None:
                lines.append(f"  {ma.upper()}: {technical[ma]:.2f}")

        # Momentum
        lines.append("\nMomentum Indicators:")
        if "rsi_14" in technical and technical["rsi_14"] is not None:
            lines.append(f"  RSI(14): {technical['rsi_14']:.2f}")
        if "macd" in technical and technical["macd"] is not None:
            lines.append(f"  MACD: {technical['macd']:.4f}")
            lines.append(f"  MACD Signal: {technical.get('macd_signal', 0):.4f}")

        # Volatility
        lines.append("\nVolatility:")
        if "volatility_30d" in technical and technical["volatility_30d"] is not None:
            lines.append(f"  30-day Volatility: {technical['volatility_30d']:.2%}")
        if "atr_14" in technical and technical["atr_14"] is not None:
            lines.append(f"  ATR(14): {technical['atr_14']:.2f}")

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
            "output_id": f"{ticker}_{as_of_date}_technical_neutral",
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
