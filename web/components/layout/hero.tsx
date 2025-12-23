export function Hero() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI-Powered Stock Recommendations
          </h1>
          <p className="text-xl text-gray-700 mb-8">
            Production-grade stock analysis combining technical indicators, news sentiment, and
            risk assessment to generate data-driven investment recommendations.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span>15+ Technical Indicators</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
              <span>AI Sentiment Analysis</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full" />
              <span>Risk Assessment</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
