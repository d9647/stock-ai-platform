"""
Portfolio synthesizer agent.
Combines signals from all agents into final recommendation.
"""
from typing import Dict, Any, Optional
from uuid import uuid4

from .base_agent import BaseAgent
from ..prompts.synthesis_prompt import get_synthesis_prompt


class PortfolioSynthesizer(BaseAgent):
    """
    Synthesizes final recommendation from:
    - Technical analysis signal
    - Sentiment analysis signal
    - Risk assessment signal
    
    Outputs: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    """

    def __init__(self, model_version: str = None):
        super().__init__(
            agent_type="synthesizer",
            model_version=model_version
        )

    def synthesize(
        self,
        ticker: str,
        as_of_date,
        feature_snapshot: Dict[str, Any],
        technical_output: Optional[Dict[str, Any]],
        sentiment_output: Optional[Dict[str, Any]],
        risk_output: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize final recommendation from all agent outputs.

        Returns:
            {
                "recommendation_id": str,
                "ticker": str,
                "as_of_date": date,
                "recommendation": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
                "confidence": float (0.0-1.0),
                "rationale": dict,
                "technical_signal": str,
                "sentiment_signal": str,
                "risk_assessment": str,
                "position_size": str,
                "time_horizon": str,
                "feature_snapshot_id": str,
                "model_version": str
            }
        """
        # If any agent failed, return HOLD
        if not technical_output or not sentiment_output or not risk_output:
            return self._create_hold_recommendation(
                ticker,
                as_of_date,
                feature_snapshot.get("snapshot_id"),
                reason="Incomplete agent outputs"
            )

        # Get prompt template
        prompt_template = get_synthesis_prompt()

        # Format agent signals
        agent_signals = self._format_agent_signals(
            technical_output,
            sentiment_output,
            risk_output
        )

        # Create user prompt
        user_prompt = prompt_template.format(
            ticker=ticker,
            as_of_date=as_of_date,
            agent_signals=agent_signals
        )

        # Call LLM
        system_prompt = "You are an expert portfolio manager synthesizing multiple signals into actionable recommendations."
        response = self._call_llm(system_prompt, user_prompt)

        # Parse response
        result = self._parse_json_response(response)

        # Create final recommendation
        recommendation = {
            "recommendation_id": f"{ticker}_{as_of_date}_rec_{uuid4().hex[:8]}",
            "ticker": ticker,
            "as_of_date": as_of_date,
            "recommendation": result.get("recommendation", "HOLD"),
            "confidence": float(result.get("confidence", 0.5)),
            "rationale": result.get("rationale", {}),
            "technical_signal": technical_output.get("signal"),
            "sentiment_signal": sentiment_output.get("signal"),
            "risk_level": risk_output.get("signal"),  # Changed from risk_assessment
            "position_size": result.get("position_size", "medium"),
            "time_horizon": result.get("time_horizon", "medium_term"),
            "agent_outputs": {  # Added agent_outputs for full traceability
                "technical": technical_output.get("output_id"),
                "sentiment": sentiment_output.get("output_id"),
                "risk": risk_output.get("output_id")
            },
            "feature_snapshot_id": feature_snapshot.get("snapshot_id"),
            "model_version": self.model_version
        }

        return recommendation

    # Note: This method doesn't need the abstract analyze() from BaseAgent
    # It uses synthesize() instead
    def analyze(self, ticker: str, as_of_date, feature_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Not used - synthesizer uses synthesize() method instead."""
        raise NotImplementedError("Synthesizer uses synthesize() method")

    def _format_agent_signals(
        self,
        technical: Dict[str, Any],
        sentiment: Dict[str, Any],
        risk: Dict[str, Any]
    ) -> str:
        """Format all agent signals for LLM prompt."""
        lines = []

        # Technical Signal
        lines.append("TECHNICAL ANALYSIS:")
        lines.append(f"  Signal: {technical.get('signal', 'UNKNOWN')}")
        lines.append(f"  Strength: {technical.get('strength', 0):.2f}")
        lines.append("  Reasoning:")
        for reason in technical.get("reasoning", []):
            lines.append(f"    - {reason}")

        # Sentiment Signal
        lines.append("\nSENTIMENT ANALYSIS:")
        lines.append(f"  Signal: {sentiment.get('signal', 'UNKNOWN')}")
        lines.append(f"  Strength: {sentiment.get('strength', 0):.2f}")
        lines.append("  Reasoning:")
        for reason in sentiment.get("reasoning", []):
            lines.append(f"    - {reason}")

        # Risk Assessment
        lines.append("\nRISK ASSESSMENT:")
        lines.append(f"  Risk Level: {risk.get('signal', 'UNKNOWN')}")
        lines.append(f"  Confidence: {risk.get('strength', 0):.2f}")
        lines.append("  Reasoning:")
        for reason in risk.get("reasoning", []):
            lines.append(f"    - {reason}")

        return "\n".join(lines)

    def _create_hold_recommendation(
        self,
        ticker: str,
        as_of_date,
        snapshot_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """Create HOLD recommendation when synthesis is impossible."""
        return {
            "recommendation_id": f"{ticker}_{as_of_date}_rec_hold",
            "ticker": ticker,
            "as_of_date": as_of_date,
            "recommendation": "HOLD",
            "confidence": 0.0,
            "rationale": {
                "summary": reason,
                "technical_view": "Unavailable",
                "sentiment_view": "Unavailable",
                "risk_view": "Unavailable",
                "key_factors": [reason]
            },
            "technical_signal": None,
            "sentiment_signal": None,
            "risk_assessment": None,
            "position_size": "small",
            "time_horizon": "medium_term",
            "feature_snapshot_id": snapshot_id,
            "model_version": self.model_version
        }
