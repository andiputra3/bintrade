"""
Data Loader — BTCUSDT 1m candles.
Phase 0: Binance public REST API (no auth needed) + CSV cache.

Spec endpoint:
  https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000

Format saved: timestamp, open, high, low, close, volume
"""
import csv
import os
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@dataclass
class Candle:
    timestamp: int      # epoch ms
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def ts_sec(self) -> float:
        return self.timestamp / 1000


BINANCE_URL = (
    "https://api.binance.com/api/v3/klines"
    "?symbol=BTCUSDT&interval=1m&limit=1000"
)
DEFAULT_CSV = Path("data/BTCUSDT_1m.csv")


class DataLoader:
    """
    Fetches or loads BTCUSDT 1m candles.
    Saves to CSV on first fetch; subsequent runs load from cache.
    """

    def __init__(self, csv_path: Path | str = DEFAULT_CSV):
        self.csv_path = Path(csv_path)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load(self, limit: int = 1000, force_refresh: bool = False) -> list[Candle]:
        """
        Returns up to `limit` candles.
        Uses cache if available and not force_refresh.
        """
        if not force_refresh and self.csv_path.exists():
            candles = self._load_csv()
            if candles:
                print(f"[DataLoader] Loaded {len(candles)} candles from {self.csv_path}")
                return candles[-limit:]

        if REQUESTS_AVAILABLE:
            candles = self._fetch_binance(limit)
            if candles:
                self._save_csv(candles)
                print(f"[DataLoader] Fetched {len(candles)} candles from Binance, saved to {self.csv_path}")
                return candles

        # Fallback: generate synthetic candles for testing
        print("[DataLoader] WARNING: Using synthetic candle data (no network/cache)")
        return self._generate_synthetic(limit)

    def load_csv(self, path: str | Path) -> list[Candle]:
        """Load from a specific CSV file."""
        old = self.csv_path
        self.csv_path = Path(path)
        result = self._load_csv()
        self.csv_path = old
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_binance(self, limit: int) -> list[Candle]:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit={limit}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            raw = resp.json()
            candles = []
            for row in raw:
                candles.append(Candle(
                    timestamp=int(row[0]),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                ))
            return candles
        except Exception as e:
            print(f"[DataLoader] Binance fetch failed: {e}")
            return []

    def _save_csv(self, candles: list[Candle]):
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
            for c in candles:
                writer.writerow([c.timestamp, c.open, c.high, c.low, c.close, c.volume])

    def _load_csv(self) -> list[Candle]:
        candles = []
        try:
            with open(self.csv_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    candles.append(Candle(
                        timestamp=int(row["timestamp"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume", 0)),
                    ))
        except Exception as e:
            print(f"[DataLoader] CSV load failed: {e}")
        return candles

    @staticmethod
    def _generate_synthetic(limit: int) -> list[Candle]:
        """Brownian motion price series for offline testing."""
        import random
        random.seed(42)
        price = 104_000.0
        now_ms = int(time.time() * 1000)
        candles = []
        for i in range(limit):
            pct_change = (random.gauss(0, 0.001))
            price = max(50_000, price * (1 + pct_change))
            atr_approx = price * 0.002
            high  = price + random.uniform(0, atr_approx)
            low   = price - random.uniform(0, atr_approx)
            open_ = price + random.uniform(-atr_approx * 0.3, atr_approx * 0.3)
            close = price
            volume = random.uniform(10, 100)
            ts = now_ms - (limit - i) * 60_000
            candles.append(Candle(
                timestamp=ts, open=open_, high=high, low=low, close=close, volume=volume
            ))
        return candles


def to_dataframe(candles: list[Candle]):
    """Convert candles to pandas DataFrame (if pandas available)."""
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas not installed")
    import pandas as pd
    return pd.DataFrame([{
        "timestamp": c.timestamp,
        "open": c.open,
        "high": c.high,
        "low": c.low,
        "close": c.close,
        "volume": c.volume,
    } for c in candles]).set_index("timestamp")
