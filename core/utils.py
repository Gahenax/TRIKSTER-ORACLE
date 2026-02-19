import hashlib
from datetime import datetime

def generate_event_key(sport: str, league: str, entity_a: str, entity_b: str, date: datetime, market_scope: str = "default") -> str:
    """
    Standard EventKey generation as per spec.
    Hash of sport, league, entities, date (YMD), market_scope.
    """
    # Use YYYY-MM-DD to avoid time-of-day collisions for the same event key
    date_str = date.strftime("%Y-%m-%d")
    
    # Sort entities alphabetically to ensure key is the same regardless of home/away order if needed
    # But spec says home_entity + away_entity, so maybe order matters. 
    # I'll stick to fixed order but normalize case.
    
    raw_key = f"{sport.lower()}|{league.lower()}|{entity_a.lower()}|{entity_b.lower()}|{date_str}|{market_scope.lower()}"
    return hashlib.sha256(raw_key.encode()).hexdigest()
