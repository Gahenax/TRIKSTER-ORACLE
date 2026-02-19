from .base_provider import BaseProvider
from typing import List, Dict, Any
from datetime import datetime
import requests

class NbaSportradarProvider(BaseProvider):
    """
    Implementation of BaseProvider for Sportradar NBA.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sportradar.com/nba/trial/v8/en"

    @property
    def provider_name(self) -> str:
        return "Sportradar-NBA"

    def _request(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        params = {"api_key": self.api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_catalog(self, sport: str = "basketball") -> List[Dict[str, Any]]:
        # NBA leagues/seasons
        return self._request("league/seasons.json")

    def get_fixtures(self, league_id: str, date: datetime) -> List[Dict[str, Any]]:
        # Schedule for a specific day. Formatting month/day with leading zeros.
        endpoint = f"games/{date.strftime('%Y/%m/%d')}/schedule.json"
        return self._request(endpoint).get("games", [])

    def get_availability(self, event_id: str) -> Dict[str, Any]:
        # Injuries/Player status
        # Note: Sportradar often has a dedicated injuries endpoint
        return self._request(f"games/{event_id}/summary.json").get("injuries", {})

    def get_live_snapshot(self, event_id: str) -> Dict[str, Any]:
        # Game summary or pbp
        data = self._request(f"games/{event_id}/summary.json")
        return {
            "score": {
                "home": data.get("home", {}).get("points"),
                "away": data.get("away", {}).get("points")
            },
            "status": data.get("status"),
            "clock": data.get("clock")
        }
