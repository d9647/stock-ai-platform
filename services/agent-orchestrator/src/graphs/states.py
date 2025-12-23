"""
LangGraph state definitions for agent orchestration.
"""
from typing import TypedDict, Optional, Dict, Any, List
from datetime import date


class AgentState(TypedDict):
    """
    State object passed between agents in the graph.
    """
    # Input
    ticker: str
    as_of_date: date
    feature_snapshot: Dict[str, Any]

    # Individual agent outputs
    technical_output: Optional[Dict[str, Any]]
    sentiment_output: Optional[Dict[str, Any]]
    risk_output: Optional[Dict[str, Any]]

    # Final recommendation
    recommendation: Optional[Dict[str, Any]]

    # Execution tracking
    errors: List[str]
    execution_start: Optional[float]
