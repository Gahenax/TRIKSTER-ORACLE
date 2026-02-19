from typing import Dict, Any, Type
from .interfaces import BaseDataSource

class AdapterRegistry:
    _registry: Dict[str, BaseDataSource] = {}

    @classmethod
    def register(cls, name: str, adapter: BaseDataSource):
        cls._registry[name] = adapter

    @classmethod
    def get(cls, name: str) -> BaseDataSource:
        return cls._registry.get(name)

# Initial Stub implementations (to be replaced by concrete data fetchers)
class MockDataSource(BaseDataSource):
    def get_actor_profile(self, name, sport): return {"name": name, "quality": 0.8}
    def get_recent_form(self, name, sport): return {"streak": "WWW", "momentum": 0.9}
    def get_match_context(self, a, b, sport): return {"neutral_ground": False}

# Register default mock
AdapterRegistry.register("default", MockDataSource())
