"""
LangGraph orchestration graph.
Coordinates execution of multiple agents in parallel.
"""
from langgraph.graph import StateGraph, END
from typing import Dict, Any
import time

from .states import AgentState
from ..agents.technical_agent import TechnicalAgent
from ..agents.sentiment_agent import SentimentAgent
from ..agents.risk_agent import RiskAgent
from ..agents.portfolio_synthesizer import PortfolioSynthesizer
from loguru import logger


def build_agent_graph():
    """
    Build LangGraph orchestration graph.

    Graph structure:
    START → [Technical, Sentiment, Risk] → Synthesize → END

    Technical, Sentiment, and Risk run in parallel.
    Synthesizer waits for all three to complete.
    """
    # Initialize agents
    technical_agent = TechnicalAgent()
    sentiment_agent = SentimentAgent()
    risk_agent = RiskAgent()
    synthesizer = PortfolioSynthesizer()

    # Define node functions
    def run_technical(state: AgentState) -> AgentState:
        """Run technical analysis agent."""
        try:
            output = technical_agent.analyze(
                state["ticker"],
                state["as_of_date"],
                state["feature_snapshot"]
            )
            state["technical_output"] = output
        except Exception as e:
            logger.error(f"Technical agent failed: {e}")
            state["errors"].append(f"Technical: {str(e)}")
        return state

    def run_sentiment(state: AgentState) -> AgentState:
        """Run sentiment analysis agent."""
        try:
            output = sentiment_agent.analyze(
                state["ticker"],
                state["as_of_date"],
                state["feature_snapshot"]
            )
            state["sentiment_output"] = output
        except Exception as e:
            logger.error(f"Sentiment agent failed: {e}")
            state["errors"].append(f"Sentiment: {str(e)}")
        return state

    def run_risk(state: AgentState) -> AgentState:
        """Run risk assessment agent."""
        try:
            output = risk_agent.analyze(
                state["ticker"],
                state["as_of_date"],
                state["feature_snapshot"]
            )
            state["risk_output"] = output
        except Exception as e:
            logger.error(f"Risk agent failed: {e}")
            state["errors"].append(f"Risk: {str(e)}")
        return state

    def run_synthesizer(state: AgentState) -> AgentState:
        """Synthesize final recommendation from all agent outputs."""
        try:
            recommendation = synthesizer.synthesize(
                state["ticker"],
                state["as_of_date"],
                state["feature_snapshot"],
                state.get("technical_output"),
                state.get("sentiment_output"),
                state.get("risk_output")
            )
            state["recommendation"] = recommendation
        except Exception as e:
            logger.error(f"Synthesizer failed: {e}")
            state["errors"].append(f"Synthesizer: {str(e)}")
        return state

    # Build graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("technical", run_technical)
    graph.add_node("sentiment", run_sentiment)
    graph.add_node("risk", run_risk)
    graph.add_node("synthesize", run_synthesizer)

    # Set single entry point
    graph.set_entry_point("technical")

    # Sequential execution (technical -> sentiment -> risk -> synthesize)
    # This avoids concurrent state updates while still being fast
    graph.add_edge("technical", "sentiment")
    graph.add_edge("sentiment", "risk")
    graph.add_edge("risk", "synthesize")

    # Synthesizer completes
    graph.add_edge("synthesize", END)

    return graph.compile()
