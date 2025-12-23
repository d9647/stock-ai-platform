"""
Pytest configuration for agent-orchestrator tests.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src directory to Python path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock the config module before any imports
mock_config_module = MagicMock()
mock_config_module.config = MagicMock()
mock_config_module.config.OPENAI_API_KEY = "test-api-key"
mock_config_module.config.OPENAI_MODEL = "gpt-4"
mock_config_module.config.LLM_TEMPERATURE = 0.0
mock_config_module.config.AGENT_MODEL_VERSION = "1.0.0"
mock_config_module.config.FEATURE_VERSION = "1.0.0"
mock_config_module.config.PROMPT_VERSION = "v1"
mock_config_module.config.DATABASE_URL = "postgresql://test:test@localhost/test"
mock_config_module.config.DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL"]
mock_config_module.config.AGENT_TIMEOUT_SECONDS = 30
mock_config_module.config.LOG_LEVEL = "INFO"

sys.modules['src.config'] = mock_config_module
