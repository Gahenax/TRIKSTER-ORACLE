from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseProvider(ABC):
    """
    Abstract interface for data providers (API-FOOTBALL, Sportradar).
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def get_catalog(self, sport: str) -> List[Dict[str, Any]]:
        """Fetch available leagues/tournaments."""
        pass

    @abstractmethod
    def get_fixtures(self, league_id: str, date: datetime) -> List[Dict[str, Any]]:
        """Fetch matches for a specific date and league."""
        pass

    @abstractmethod
    def get_availability(self, event_id: str) -> Dict[str, Any]:
        """Fetch player availability, injuries, suspensions."""
        pass

    @abstractmethod
    def get_live_snapshot(self, event_id: str) -> Dict[str, Any]:
        """Fetch minimal live data (score, clock, key events)."""
        pass
