from .base_provider import BaseProvider
from typing import List, Dict, Any
from datetime import datetime
import requests

class MmaSportradarProvider(BaseProvider):
    """
    Implementation of BaseProvider for Sportradar MMA (UFC).
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sportradar.com/mma/trial/v2/en"

    @property
    def provider_name(self) -> str:
        return "Sportradar-MMA"

    def _request(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        params = {"api_key": self.api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_catalog(self, sport: str = "mma") -> List[Dict[str, Any]]:
        # UFC Organizations/Events
        return self._request("league/seasons.json")

    def get_fixtures(self, league_id: str, date: datetime) -> List[Dict[str, Any]]:
        # MMA schedule is usually returned in bulk; we filter by date
        date_str = date.strftime("%Y-%m-%d")
        summaries = self._request("schedule.json").get("summaries", [])
        return [s for s in summaries if s.get("sport_event", {}).get("start_time", "").startswith(date_str)]

    def get_availability(self, event_id: str) -> Dict[str, Any]:
        # Fight info, weight-in status
        return self._request(f"fights/{event_id}/summary.json")

    def get_live_snapshot(self, event_id: str) -> Dict[str, Any]:
        data = self._request(f"fights/{event_id}/summary.json")
        return {
            "status": data.get("sport_event_status", {}).get("status"),
            "match_status": data.get("sport_event_status", {}).get("match_status")
        }
