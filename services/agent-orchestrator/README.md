# Agent Orchestrator Service

Multi-agent system using LangGraph to generate stock recommendations.

## Overview

The Agent Orchestrator combines signals from multiple specialized AI agents:
- **Technical Agent**: Analyzes price action, trends, and momentum
- **Sentiment Agent**: Analyzes news sentiment and themes
- **Risk Agent**: Assesses volatility and risk levels
- **Portfolio Synthesizer**: Combines all signals into final recommendations

### Architecture Principles

**Golden Rule**: "If it can 'think', it cannot block a request. If it serves a request, it must not think."

- ✅ Agents run OFFLINE only (never in API request path)
- ✅ Read from feature snapshots (point-in-time correctness)
- ✅ Append-only, immutable outputs (perfect for backtesting)
- ✅ Full traceability (prompt hashes, model versions, feature snapshot IDs)

## Data Flow

```
Feature Snapshots (read-only)
    ↓
Agent Orchestrator (offline, LangGraph)
    ├── Technical Agent (parallel)
    ├── Sentiment Agent (parallel)
    └── Risk Agent (parallel)
    ↓
Portfolio Synthesizer (sequential)
    ↓
Stock Recommendations (pre-computed)
    ↓
API (read-only, serves recommendations)
```

## Project Structure

```
services/agent-orchestrator/
├── src/
│   ├── config.py                        # Configuration
│   │
│   ├── agents/                          # Agent implementations
│   │   ├── base_agent.py               # Base class with LLM wrapper
│   │   ├── technical_agent.py          # Technical analysis
│   │   ├── sentiment_agent.py          # Sentiment analysis
│   │   ├── risk_agent.py               # Risk assessment
│   │   └── portfolio_synthesizer.py    # Final recommendation
│   │
│   ├── graphs/                          # LangGraph orchestration
│   │   ├── states.py                   # State definitions
│   │   └── agent_graph.py              # Orchestration graph
│   │
│   ├── prompts/                         # Versioned prompts
│   │   ├── technical_prompt.py
│   │   ├── sentiment_prompt.py
│   │   ├── risk_prompt.py
│   │   └── synthesis_prompt.py
│   │
│   ├── storage/                         # Database I/O
│   │   ├── feature_reader.py           # Read feature snapshots
│   │   └── agent_writer.py             # Write agent outputs
│   │
│   └── pipelines/                       # Orchestration
│       └── daily_agent_pipeline.py     # Main entry point
│
├── tests/                               # Unit tests
├── requirements.txt                     # Dependencies
├── .coveragerc                          # Coverage config
└── README.md                            # This file
```

## Installation

```bash
# Navigate to service directory
cd services/agent-orchestrator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with:

```bash
# Database
DATABASE_URL=postgresql://stockai:stockai@192.168.5.126:5432/stockai_dev

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4  # or gpt-4o-mini for cost savings

# Logging
LOG_LEVEL=INFO
```

## Usage

### Run Agent Pipeline

Process all default tickers for yesterday:
```bash
python -m src.pipelines.daily_agent_pipeline
```

Process specific tickers for a specific date:
```bash
python -m src.pipelines.daily_agent_pipeline \
    --tickers AAPL MSFT GOOGL \
    --date 2024-12-15
```

### Output

The pipeline writes to 3 database tables:

1. **agents.agent_outputs** - Individual agent decisions (Technical, Sentiment, Risk)
2. **agents.stock_recommendations** - Final recommendations (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
3. **agents.agent_execution_logs** - Execution tracking and errors

## Agent Details

### Technical Agent
- **Inputs**: SMA (20, 50, 200), RSI, MACD, ATR, Bollinger Bands
- **Output**: BULLISH / NEUTRAL / BEARISH
- **Focus**: Trend direction, momentum, volatility

### Sentiment Agent
- **Inputs**: News sentiment scores, article counts, top themes
- **Output**: BULLISH / NEUTRAL / BEARISH
- **Focus**: Overall sentiment, coverage quality, key themes

### Risk Agent
- **Inputs**: Volatility metrics, ATR, Bollinger width
- **Output**: LOW_RISK / MEDIUM_RISK / HIGH_RISK / EXTREME_RISK
- **Focus**: Volatility levels, position sizing guidance

### Portfolio Synthesizer
- **Inputs**: All 3 agent outputs
- **Output**: STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL
- **Logic**:
  - STRONG_BUY: All agents bullish, low risk
  - BUY: 2+ agents bullish, acceptable risk
  - HOLD: Mixed signals or neutral
  - SELL: 2+ agents bearish
  - STRONG_SELL: All agents bearish or extreme risk

## LangGraph Orchestration

The agent graph coordinates parallel execution:

```
START
  ├── Technical Agent
  ├── Sentiment Agent
  └── Risk Agent
       ↓
  Synthesizer
       ↓
     END
```

**Key Features**:
- Technical, Sentiment, and Risk agents run in parallel
- Synthesizer waits for all 3 to complete
- Error handling at each node
- Full state tracking throughout execution

## Reproducibility & Traceability

Every agent output includes:
- `feature_snapshot_id`: Exact input data used
- `prompt_hash`: SHA-256 hash of prompt (version control)
- `model_version`: Agent version number
- `created_at`: Timestamp of execution

This enables:
- Perfect backtesting (re-run with historical snapshots)
- Prompt versioning (detect when prompts change)
- A/B testing (compare model versions)
- Debugging (trace exact inputs to outputs)

## Testing

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

## Cost Estimates

### Development (Testing)
- **OpenAI API**: ~$10-20 for testing
- 7 tickers × 30 days × 4 agents × 500 tokens ≈ 420K tokens
- GPT-4: ~$12 for testing period

### Production (Daily)
- **OpenAI API**: ~$5-10/day for 7 tickers
- 7 tickers × 4 agents × ~1000 tokens = ~28K tokens/day
- GPT-4: $0.03/1K input + $0.06/1K output = ~$2.80/day
- **Monthly**: ~$84-300/month (depending on ticker count)

## Development

### Adding a New Agent

1. Create agent class in `src/agents/`:
```python
from .base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_type="my_agent")
    
    def analyze(self, ticker, as_of_date, feature_snapshot):
        # Your logic here
        pass
```

2. Create prompt in `src/prompts/my_agent_prompt.py`

3. Update LangGraph in `src/graphs/agent_graph.py`:
   - Add node for new agent
   - Connect to synthesizer

4. Update synthesizer to consume new agent output

### Versioning Prompts

Prompts are versioned for reproducibility:

```python
PROMPT_V1 = "..."
PROMPT_V2 = "..."  # Updated version

def get_prompt(version="v2"):
    prompts = {"v1": PROMPT_V1, "v2": PROMPT_V2}
    return prompts.get(version, PROMPT_V2)
```

Update `config.PROMPT_VERSION` to change default version.

## Troubleshooting

### Agent Failures

Check `agents.agent_execution_logs` table:
```sql
SELECT * FROM agents.agent_execution_logs
WHERE status = 'failed'
ORDER BY created_at DESC;
```

### Missing Feature Snapshots

Ensure feature store pipeline has run:
```bash
cd ../feature-store
python -m src.pipelines.daily_feature_pipeline --date 2024-12-15
```

### OpenAI API Errors

- Rate limits: Increase sleep time in pipeline (line 107)
- Invalid API key: Check `.env` file
- Model not available: Try `gpt-4o-mini` instead of `gpt-4`

## Performance

- **Parallel Execution**: 3 agents run simultaneously (3x speedup)
- **Rate Limiting**: 2-second delay between tickers (avoid API throttling)
- **Typical Runtime**: ~10-15 seconds per ticker (with GPT-4)

## Next Steps

After completing agent orchestrator:

1. **Testing**: Achieve >80% code coverage
2. **Validation**: Compare recommendations against historical data
3. **Optimization**: Fine-tune prompts based on output quality
4. **Scaling**: Add more tickers, agents, or features
5. **Monitoring**: Add alerts for failed executions
6. **Web Platform**: Build UI to visualize recommendations

## License

Proprietary - Stock AI Platform
