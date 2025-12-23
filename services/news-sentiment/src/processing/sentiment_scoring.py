"""
Sentiment analysis using OpenAI GPT-4o-mini.
Analyzes news articles and extracts sentiment scores, confidence, and themes.
"""
import json
from typing import List, Dict
import time

import pandas as pd
from openai import OpenAI
from loguru import logger

from ..config import config


class SentimentScorer:
    """
    Analyzes sentiment of news articles using OpenAI.
    Deterministic and reproducible (temperature=0).
    """

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.SENTIMENT_MODEL
        self.version = config.SENTIMENT_VERSION

        logger.info(f"Initialized sentiment scorer (model: {self.model}, version: {self.version})")

    def analyze_sentiment_batch(self, articles_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze sentiment for a batch of articles.

        Args:
            articles_df: DataFrame with columns [ticker, published_at, headline, content, source, url, author]

        Returns:
            DataFrame with additional columns:
            [article_id, sentiment_score, confidence, themes, model_name, model_version]
        """
        if articles_df.empty:
            logger.warning("No articles to analyze")
            return pd.DataFrame()

        logger.info(f"Analyzing sentiment for {len(articles_df)} articles")

        results = []

        # Process in batches to avoid rate limits
        batch_size = config.SENTIMENT_BATCH_SIZE
        for i in range(0, len(articles_df), batch_size):
            batch = articles_df.iloc[i:i + batch_size]

            for _, article in batch.iterrows():
                try:
                    sentiment = self._analyze_single_article(
                        ticker=article["ticker"],
                        headline=article["headline"],
                        content=article.get("content", "")
                    )

                    results.append({
                        "ticker": article["ticker"],
                        "published_at": article["published_at"],
                        "headline": article["headline"],
                        "content": article.get("content", ""),
                        "source": article["source"],
                        "url": article.get("url", ""),
                        "author": article.get("author", ""),
                        "sentiment_score": sentiment["sentiment_score"],
                        "confidence": sentiment["confidence"],
                        "themes": sentiment["themes"],
                        "model_name": self.model,
                        "model_version": self.version
                    })

                except Exception as e:
                    logger.error(f"Error analyzing article: {e}")
                    # Continue with default values
                    results.append({
                        "ticker": article["ticker"],
                        "published_at": article["published_at"],
                        "headline": article["headline"],
                        "content": article.get("content", ""),
                        "source": article["source"],
                        "url": article.get("url", ""),
                        "author": article.get("author", ""),
                        "sentiment_score": 0.0,
                        "confidence": 0.0,
                        "themes": [],
                        "model_name": self.model,
                        "model_version": self.version
                    })

            # Rate limiting between batches
            if i + batch_size < len(articles_df):
                logger.info(f"Processed {i + batch_size}/{len(articles_df)} articles, brief pause...")
                time.sleep(1)  # 1 second between batches

        sentiment_df = pd.DataFrame(results)
        logger.info(f"Completed sentiment analysis for {len(sentiment_df)} articles")

        return sentiment_df

    def _analyze_single_article(
        self,
        ticker: str,
        headline: str,
        content: str
    ) -> Dict:
        """
        Analyze sentiment of a single article.

        Args:
            ticker: Stock ticker symbol
            headline: Article headline
            content: Article content (may be empty)

        Returns:
            Dict with keys: sentiment_score, confidence, themes
        """
        # Prepare prompt
        prompt = self._create_prompt(ticker, headline, content)

        try:
            # Call OpenAI API (temperature=0 for deterministic results)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial sentiment analyst. Analyze news articles and return sentiment scores, confidence levels, and key themes in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,  # Deterministic
                response_format={"type": "json_object"}
            )

            # Parse response
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # Validate and normalize
            sentiment_score = float(result.get("sentiment_score", 0.0))
            sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp to [-1, 1]

            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

            themes = result.get("themes", [])
            if not isinstance(themes, list):
                themes = []

            return {
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "themes": themes
            }

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            # Return neutral sentiment on error
            return {
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "themes": []
            }

    def _create_prompt(self, ticker: str, headline: str, content: str) -> str:
        """
        Create prompt for sentiment analysis.

        Args:
            ticker: Stock ticker symbol
            headline: Article headline
            content: Article content

        Returns:
            Formatted prompt string
        """
        # Use content if available, otherwise just headline
        text = f"Headline: {headline}"
        if content and len(content) > 10:
            text += f"\\n\\nContent: {content[:1000]}"  # Limit to first 1000 chars

        prompt = f"""Analyze the sentiment of this financial news article about {ticker}:

{text}

Return a JSON object with exactly these fields:
{{
  "sentiment_score": <float between -1.0 and 1.0, where -1.0 is very negative, 0.0 is neutral, 1.0 is very positive>,
  "confidence": <float between 0.0 and 1.0, indicating how confident you are in the sentiment score>,
  "themes": [<list of 1-5 key themes or topics, such as "earnings", "product_launch", "lawsuit", "partnership", etc.>]
}}

Be precise and objective. Focus on the financial implications for the stock price."""

        return prompt


if __name__ == "__main__":
    # Test scorer
    scorer = SentimentScorer()

    # Create sample articles
    sample_articles = pd.DataFrame([
        {
            "ticker": "AAPL",
            "published_at": pd.Timestamp.now(),
            "headline": "Apple reports record quarterly earnings",
            "content": "Apple Inc. exceeded analyst expectations with strong iPhone sales.",
            "source": "Test",
            "url": "",
            "author": ""
        },
        {
            "ticker": "TSLA",
            "published_at": pd.Timestamp.now(),
            "headline": "Tesla faces production delays",
            "content": "Tesla announced delays in Cybertruck production due to supply chain issues.",
            "source": "Test",
            "url": "",
            "author": ""
        }
    ])

    # Analyze sentiment
    results = scorer.analyze_sentiment_batch(sample_articles)

    print("\\nSentiment Analysis Results:")
    print(results[["ticker", "headline", "sentiment_score", "confidence", "themes"]])
