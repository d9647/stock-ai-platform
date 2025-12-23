#AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA
cd ../services/news-sentiment
source venv/bin/activate
pip install -r requirements.txt
python -m src.pipelines.daily_news_pipeline --ticker $1 --days 365
