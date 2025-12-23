"""
Pytest configuration for news-sentiment tests.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src directory to Python path
src_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(src_path))

# Mock the config module before any imports
mock_config_module = MagicMock()
mock_config_module.config = MagicMock()
mock_config_module.config.OPENAI_API_KEY = "test-api-key"
mock_config_module.config.SENTIMENT_MODEL = "gpt-4o-mini"
mock_config_module.config.SENTIMENT_VERSION = "1.0.0"
mock_config_module.config.SENTIMENT_BATCH_SIZE = 10
mock_config_module.config.NEWSAPI_KEY = "test-newsapi-key"
mock_config_module.config.FINNHUB_API_KEY = "test-finnhub-key"
mock_config_module.config.DATABASE_URL = "postgresql://test:test@localhost/test"

sys.modules['src.config'] = mock_config_module
