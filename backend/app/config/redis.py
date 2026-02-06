import os
from typing import Optional

class RedisConfig:
    @staticmethod
    def get_url() -> Optional[str]:
        return os.getenv("REDIS_URL")

    @staticmethod
    def is_enabled() -> bool:
        return RedisConfig.get_url() is not None

    @staticmethod
    def get_storage_backend() -> str:
        if RedisConfig.is_enabled():
            return "redis"
        return "memory"

# For now, always use memory (Redis is optional)
USE_REDIS = RedisConfig.is_enabled()
