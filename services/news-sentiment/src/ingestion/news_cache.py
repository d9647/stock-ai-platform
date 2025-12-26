import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Set, Tuple

from loguru import logger

import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))


class NewsSeenCache:
    def __init__(self, cache_dir: Path, ticker: str):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ticker = ticker.upper()
        self.path = self.cache_dir / f"news_seen_{self.ticker}.jsonl"
        self._migrate_legacy_files()
        self._backup_cache()

    def _migrate_legacy_files(self):
        """
        If a legacy shared cache exists (news_seen.jsonl and backups),
        copy them to ticker-specific filenames.
        """
        legacy = self.cache_dir / "news_seen.jsonl"
        if legacy.exists() and not self.path.exists():
            try:
                shutil.copy2(legacy, self.path)
                logger.info(f"Migrated legacy cache {legacy} -> {self.path}")
            except Exception as e:
                logger.warning(f"Failed to migrate legacy cache {legacy}: {e}")

        # Migrate backups
        for bak in self.cache_dir.glob("news_seen.jsonl.bak.*"):
            ts = bak.suffix.split(".")[-1]
            target = self.cache_dir / f"news_seen_{self.ticker}.jsonl.bak.{ts}"
            if not target.exists():
                try:
                    shutil.copy2(bak, target)
                    logger.info(f"Migrated legacy cache backup {bak} -> {target}")
                except Exception as e:
                    logger.warning(f"Failed to migrate backup {bak}: {e}")

    def _backup_cache(self):
        """Backup the current ticker-specific cache file."""
        if not self.path.exists():
            return
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_path = self.path.with_suffix(self.path.suffix + f".bak.{ts}")
        try:
            shutil.copy2(self.path, backup_path)
            logger.info(f"Backed up news cache to {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to backup news cache: {e}")

    def load(self) -> tuple[Set[Tuple[str, str]], Set[Tuple[str, str, datetime]]]:
        """
        Load cached URLs and (headline, published_at) keys for this ticker.
        """
        urls: Set[Tuple[str, str]] = set()  # (ticker, url)
        keys: Set[Tuple[str, str, datetime]] = set()  # (ticker, headline, published_at)

        if not self.path.exists():
            logger.info(f"News cache not found for {self.ticker}; starting empty")
            return urls, keys

        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    url = row.get("url")
                    headline = row.get("headline")
                    published_at = row.get("published_at")
                    ticker = (row.get("ticker") or self.ticker).upper()

                    if ticker and url:
                        urls.add((ticker, url))

                    if ticker and headline and published_at:
                        keys.add(
                            (ticker, headline, datetime.fromisoformat(str(published_at)))
                        )
                except Exception:
                    continue

        logger.info(
            f"Loaded news cache for {self.ticker}: {len(urls)} ticker-URLs, {len(keys)} ticker/headline keys"
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
                published_at = a.get("published_at")
                if isinstance(published_at, datetime):
                    published_at = published_at.isoformat()

                f.write(
                    json.dumps(
                        {
                            "ticker": (a.get("ticker") or self.ticker).upper(),
                            "url": a.get("url"),
                            "headline": a.get("headline"),
                            "published_at": published_at,
                        }
                    )
                    + "\n"
                )
