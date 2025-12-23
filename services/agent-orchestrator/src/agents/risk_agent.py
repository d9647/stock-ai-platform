"""
Risk assessment agent.
Analyzes risk metrics and provides position sizing guidance.
"""
from typing import Dict, Any
from uuid import uuid4

from .base_agent import BaseAgent
from ..prompts.risk_prompt import get_risk_prompt


class RiskAgent(BaseAgent):
    """
    Analyzes risk metrics:
    - Volatility (30-day, ATR)
    - Bollinger Band width
    - Price stability
    - Position sizing recommendations
    """

    def __init__(self, model_version: str = None):
        super().__init__(
            agent_type="risk",
            model_version=model_version
        )

    def analyze(
        self,
        ticker: str,
        as_of_date,
        feature_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze risk features and generate assessment.

        Returns:
            {
                "output_id": str,
                "signal": "LOW_RISK" | "MEDIUM_RISK" | "HIGH_RISK" | "EXTREME_RISK",
                "strength": float (0.0-1.0),
                "reasoning": [str],
                "risk_breakdown": dict
            }
        """
        # Extract technical features (risk metrics are in technical)
        technical = feature_snapshot.get("technical_features", {})

        if not technical:
            return self._create_neutral_output(
                ticker,
                as_of_date,
                feature_snapshot.get("snapshot_id"),
                reason="No risk data available"
            )

        # Get prompt template
        prompt_template = get_risk_prompt()

        # Format feature data for prompt
        feature_summary = self._format_features(technical)

        # Create user prompt
        user_prompt = prompt_template.format(
            ticker=ticker,
            feature_data=feature_summary
        )

        # Call LLM
        system_prompt = "You are an expert risk analyst specializing in portfolio risk management."
        response = self._call_llm(system_prompt, user_prompt)

        # Parse response
        result = self._parse_json_response(response)

        # Create output
        output = {
            "output_id": f"{ticker}_{as_of_date}_risk_{uuid4().hex[:8]}",
            "agent_type": self.agent_type,
            "ticker": ticker,
            "as_of_date": as_of_date,
            "signal": result.get("signal", "MEDIUM_RISK"),
            "strength": float(result.get("strength", 0.5)),
            "reasoning": result.get("reasoning", []),
            "agent_metadata": {
                "risk_breakdown": result.get("risk_breakdown", {})
            },
            "feature_snapshot_id": feature_snapshot.get("snapshot_id"),
            "model_version": self.model_version,
            "prompt_hash": self._create_prompt_hash(user_prompt)
        }

        return output

    def _format_features(self, technical: Dict[str, Any]) -> str:
        """Format risk metrics for LLM prompt."""
        lines = []

        # Volatility Metrics
        lines.append("Volatility Metrics:")
        if "volatility_30d" in technical and technical["volatility_30d"] is not None:
            lines.append(f"  30-day Volatility: {technical['volatility_30d']:.2%}")
        if "atr_14" in technical and technical["atr_14"] is not None:
            lines.append(f"  ATR(14): {technical['atr_14']:.2f}")

        # Bollinger Bands
        lines.append("\nBollinger Bands:")
        if "bollinger_upper" in technical and technical["bollinger_upper"] is not None:
            lines.append(f"  Upper Band: {technical['bollinger_upper']:.2f}")
        if "bollinger_middle" in technical and technical["bollinger_middle"] is not None:
            lines.append(f"  Middle Band: {technical['bollinger_middle']:.2f}")
        if "bollinger_lower" in technical and technical["bollinger_lower"] is not None:
            lines.append(f"  Lower Band: {technical['bollinger_lower']:.2f}")

        # Current Price Context
        if "close" in technical and technical["close"] is not None:
            lines.append(f"\nCurrent Price: ${technical['close']:.2f}")

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
            "output_id": f"{ticker}_{as_of_date}_risk_neutral",
            "agent_type": self.agent_type,
            "ticker": ticker,
            "as_of_date": as_of_date,
            "signal": "MEDIUM_RISK",
            "strength": 0.0,
            "reasoning": [reason],
            "agent_metadata": {},
            "feature_snapshot_id": snapshot_id,
            "model_version": self.model_version,
            "prompt_hash": ""
        }
