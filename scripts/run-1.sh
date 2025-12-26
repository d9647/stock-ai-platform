# 'AAPL','MSFT','GOOGL','NVDA','AMZN','TSLA','META','WMT','YELP'
# This run fast, already run for all 12/22/2025
cd ../services/market-data
source venv/bin/activate
#python -m src.pipelines.daily_market_pipeline --ticker AAPL --days 800
python -m src.pipelines.daily_market_pipeline --ticker MSFT --days 800
#python -m src.pipelines.daily_market_pipeline --ticker GOOGL --days 800
#python -m src.pipelines.daily_market_pipeline --ticker AMZN --days 800
#python -m src.pipelines.daily_market_pipeline --ticker NVDA --days 800
#python -m src.pipelines.daily_market_pipeline --ticker META --days 800
#python -m src.pipelines.daily_market_pipeline --ticker TSLA --days 800

#'AAPL','MSFT','GOOGL','NVDA','AMZN','TSLA','META','WMT','MU','AVGO','TSM','JPM','BRK.A','INTC','AMD','QCOM','TXN','LRCX','KLAC','ASML','LLY','ORCL','V','PYPL','MA','JNJ','PLTR'

#python -m src.pipelines.daily_market_pipeline --tickers WMT MU AVGO TSM JPM BRK.A INTC AMD QCOM TXN LRCX KLAC ASML LLY ORCL V PYPL MA JNJ PLTR --days 800

python -m src.pipelines.daily_market_pipeline --tickers BRK.A --days 800
