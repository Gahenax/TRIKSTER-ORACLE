import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class CacheManager:
    """
    Local filesystem cache with TTL and metadata tracking.
    """
    
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_path(self, key: str) -> str:
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def get(self, key: str, ttl_minutes: int = 60) -> Optional[Dict[str, Any]]:
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r') as f:
                cached = json.load(f)
            
            cached_time = datetime.fromisoformat(cached['timestamp'])
            if datetime.utcnow() - cached_time > timedelta(minutes=ttl_minutes):
                return None
            
            return cached['data']
        except Exception:
            return None

    def set(self, key: str, data: Dict[str, Any]):
        path = self._get_path(key)
        cached = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        with open(path, 'w') as f:
            json.dump(cached, f)
