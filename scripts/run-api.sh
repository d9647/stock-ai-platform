#AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA
cd ../api
source venv/bin/activate
python -m app.main

#curl http://192.168.5.126:8000/api/v1/health
#cd api
#source venv/bin/activate
#uvicorn app.main:app --host 0.0.0.0 --port 8000
