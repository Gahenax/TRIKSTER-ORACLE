from .base_provider import BaseProvider
from typing import List, Dict, Any
from datetime import datetime
import requests

class FootballApiFootballProvider(BaseProvider):
    """
    Implementation of BaseProvider for API-FOOTBALL.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': self.api_key
        }

    @property
    def provider_name(self) -> str:
        return "API-FOOTBALL"

    def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_catalog(self, sport: str = "football") -> List[Dict[str, Any]]:
        # Fetching top leagues as defined in spec (Europe Top 5 + LatAm Top 4)
        # For simplicity, we fetch all leagues and filter or return raw
        data = self._request("leagues")
        return data.get("response", [])

    def get_fixtures(self, league_id: str, date: datetime) -> List[Dict[str, Any]]:
        params = {
            "league": league_id,
            "date": date.strftime("%Y-%m-%d"),
            "season": date.year # Simplified
        }
        data = self._request("fixtures", params=params)
        return data.get("response", [])

    def get_availability(self, event_id: str) -> Dict[str, Any]:
        # Injuries endpoint
        params = {"fixture": event_id}
        data = self._request("injuries", params=params)
        return data

    def get_live_snapshot(self, event_id: str) -> Dict[str, Any]:
        params = {"id": event_id}
        data = self._request("fixtures", params=params)
        # Minimal live data abstraction
        response = data.get("response", [])
        if not response:
            return {}
        
        fixture = response[0]
        return {
            "score": fixture.get("goals"),
            "status": fixture.get("fixture", {}).get("status"),
            "events": fixture.get("events", []) # Key events
        }
