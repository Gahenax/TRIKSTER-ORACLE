from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseDataSource(ABC):
    @abstractmethod
    def get_actor_profile(self, actor_name: str, sport: str) -> Dict[str, Any]:
        """Returns physical and mental profile of the actor."""
        pass

    @abstractmethod
    def get_recent_form(self, actor_name: str, sport: str) -> Dict[str, Any]:
        """Returns time-weighted performance metrics."""
        pass

    @abstractmethod
    def get_match_context(self, primary: str, opponent: str, sport: str) -> Dict[str, Any]:
        """Returns external factors (venue, weather, significance)."""
        pass

class FootballSource(BaseDataSource):
    @abstractmethod
    def get_team_stats(self, team_name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_injuries(self, team_name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_schedule_context(self, team_name: str) -> Dict[str, Any]:
        pass

class UFCSource(BaseDataSource):
    @abstractmethod
    def get_fighter_stats(self, fighter_name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_style_matchup(self, a: str, b: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_camp_weightcut_signals(self, fighter_name: str) -> Dict[str, Any]:
        pass
