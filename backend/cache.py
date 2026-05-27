import json
import time
import hashlib
from pathlib import Path

CACHE_DIR = Path(__file__).parent / ".cache"
DEFAULT_TTL = 86400 * 7  # 7 days


class AnalysisCache:
    def __init__(self):
        CACHE_DIR.mkdir(exist_ok=True)

    def _key(self, ia_id: str) -> str:
        return hashlib.sha256(ia_id.encode()).hexdigest()[:32]

    def get(self, ia_id: str) -> dict | None:
        path = CACHE_DIR / f"{self._key(ia_id)}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - data.get("_ts", 0) > DEFAULT_TTL:
            path.unlink(missing_ok=True)
            return None
        return data.get("result")

    def set(self, ia_id: str, result: dict):
        path = CACHE_DIR / f"{self._key(ia_id)}.json"
        path.write_text(json.dumps({"_ts": time.time(), "result": result}))

    def clear(self):
        if CACHE_DIR.exists():
            for f in CACHE_DIR.glob("*.json"):
                f.unlink(missing_ok=True)
