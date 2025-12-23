#AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA
cd ../services/feature-store
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.pipelines.daily_feature_pipeline --ticker AAPL --days 365
