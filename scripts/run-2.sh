#'AAPL','MSFT','GOOGL','NVDA','AMZN','TSLA','META','WMT',
#'MU','AVGO','TSM','JPM','BRK.A','INTC','AMD','QCOM','TXN','LRCX','KLAC','ASML','LLY','ORCL','V','PYPL','MA','JNJ','PLTR'
cd ../services/news-sentiment
source venv/bin/activate
pip install -r requirements.txt
#python -m src.pipelines.daily_news_pipeline --ticker 'AAPL' --days 800
#python -m src.pipelines.daily_news_pipeline --ticker 'MSFT' --days 800
#python -m src.pipelines.daily_news_pipeline --ticker 'GOOGL' --days 800
#python -m src.pipelines.daily_news_pipeline --ticker 'AMZN' --days 800

#python -m src.pipelines.daily_news_pipeline --ticker 'NVDA' --days 800 --skip-sentiment`
#python -m src.pipelines.daily_news_pipeline --ticker 'TSLA' --days 800 --skip-sentiment
#python -m src.pipelines.daily_news_pipeline --ticker 'META' --days 800 --skip-sentiment
#python -m src.pipelines.daily_news_pipeline --ticker 'WMT' --days 800 --skip-sentiment

#python -m src.pipelines.daily_news_pipeline --tickers MU AVGO TSM JPM BRK.A INTC AMD QCOM TXN LRCX KLAC ASML LLY ORCL V PYPL MA JNJ PLTR --days 800 --skip-sentiment

# Multiple tickers
#python -m src.pipelines.daily_news_pipeline --tickers NVDA META MSFT --days 800 --skip-sentiment --forward-only

# Single ticker (old flag still works)
python -m src.pipelines.daily_news_pipeline --ticker KLAC --days 800 --skip-sentiment 
