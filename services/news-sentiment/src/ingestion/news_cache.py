import json
from pathlib import Path
from datetime import datetime
from typing import Set, Tuple
from pathlib import Path
from loguru import logger

import sys
from pathlib import Path
# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))



class NewsSeenCache:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> tuple[Set[str], Set[Tuple[str, datetime]]]:
        """
        Load cached URLs and (headline, published_at) keys.
        """
        urls: Set[str] = set()
        keys: Set[Tuple[str, datetime]] = set()

        if not self.path.exists():
            logger.info("News cache not found; starting with empty cache")
            return urls, keys

        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    url = row.get("url")
                    headline = row.get("headline")
                    published_at = row.get("published_at")

                    if url:
                        urls.add(url)

                    if headline and published_at:
                        keys.add(
                            (headline, datetime.fromisoformat(published_at))
                        )
                except Exception:
                    continue

        logger.info(
            f"Loaded news cache: {len(urls)} URLs, {len(keys)} article keys"
        )
        return urls, keys

    def append(self, articles: list[dict]):
        """
        Append newly inserted articles to cache.
        Must be called ONLY after DB commit succeeds.
        """
        if not articles:
            return

        with self.path.open("a", encoding="utf-8") as f:
            for a in articles:
                f.write(
                    json.dumps(
                        {
                            "url": a.get("url"),
                            "headline": a.get("headline"),
                            "published_at": a["published_at"].isoformat()
                            if isinstance(a.get("published_at"), datetime)
                            else str(a.get("published_at")),
                        }
                    )
                    + "\n"
                )

###----------------------------------------------------------
### One-time bootstrap: rebuild news cache from database.
###------------------------------------------------------
'''
if __name__ == "__main__":
    """
    One-time bootstrap: rebuild news cache from database.
    """
    from api.app.models.news import NewsArticle
    from api.app.db import get_db

    cache = NewsSeenCache("data/news_cache/news_seen.jsonl")

    db = next(get_db())

    rows = db.query(
        NewsArticle.url,
        NewsArticle.headline,
        NewsArticle.published_at,
    ).all()

    articles = [
        {
            "url": r.url,
            "headline": r.headline,
            "published_at": r.published_at,
        }
        for r in rows
    ]

    cache.append(articles)

    print(f"Bootstrapped cache with {len(articles)} articles")
'''
