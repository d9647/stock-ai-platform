"""
Configuration for agent orchestrator service.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Agent orchestrator service configuration."""

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://stockai:stockai@localhost:5432/stockai_dev"
    )

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    LLM_TEMPERATURE = 0.0  # Deterministic for reproducibility

    # Agent Configuration
    AGENT_MODEL_VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PROMPT_VERSION = "v1"

    # Default Data
    DEFAULT_TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA"
    ]

    # Timeouts
    AGENT_TIMEOUT_SECONDS = 30

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
