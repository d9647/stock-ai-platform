#AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA
cd ../web
pnpm install
echo $NEXT_PUBLIC_API_URL
# for development mode
#pnpm dev
# below is for production mode
rm -rf .next
npm run build