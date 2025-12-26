#AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA
cd ../services/agent-orchestrator
python3 -m venv venv
source venv/bin/activate
#pip install -r requirements.txt
#python -m src.pipelines.daily_agent_pipeline --ticker AAPL --date 2025-12-15
python -m src.pipelines.daily_agent_pipeline --ticker MSFT --days 365