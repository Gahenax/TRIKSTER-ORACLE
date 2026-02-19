from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

class RiskProfileEnum(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    NEUTRAL = "NEUTRAL"
    RISKY = "RISKY"

class SnapshotTypeEnum(str, Enum):
    PREMATCH = "PREMATCH"
    LIVE = "LIVE"
    FINAL = "FINAL"

class Sport(Base):
    __tablename__ = "sports"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True)
    sport_id = Column(Integer, ForeignKey("sports.id"))
    name = Column(String, nullable=False)
    external_id = Column(String)
    country = Column(String)

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True)
    sport_id = Column(Integer, ForeignKey("sports.id"))
    name = Column(String, nullable=False)
    external_id = Column(String)
    entity_metadata = Column(JSON)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    event_key = Column(String, unique=True, nullable=False, index=True)
    sport_id = Column(Integer, ForeignKey("sports.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    home_entity_id = Column(Integer, ForeignKey("entities.id"))
    away_entity_id = Column(Integer, ForeignKey("entities.id"))
    start_utc = Column(DateTime, nullable=False)
    market_scope = Column(String)
    status = Column(String)

class EventProfile(Base):
    __tablename__ = "event_profiles"
    id = Column(Integer, primary_key=True)
    event_key = Column(String, ForeignKey("events.event_key"), unique=True, nullable=False)
    profile = Column(SQLEnum(RiskProfileEnum), nullable=False)
    set_at = Column(DateTime, default=utc_now)

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True)
    event_key = Column(String, ForeignKey("events.event_key"), nullable=False)
    type = Column(SQLEnum(SnapshotTypeEnum), nullable=False)
    timestamp = Column(DateTime, default=utc_now)
    data = Column(JSON, nullable=False)

class DataAvailability(Base):
    __tablename__ = "availability"
    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    last_fetched = Column(DateTime)
    next_fetch = Column(DateTime)
    status = Column(String)

class LedgerEntry(Base):
    __tablename__ = "ledger"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
    event_type = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False)

class Wallet(Base):
    __tablename__ = "wallet"
    id = Column(Integer, primary_key=True)
    balance = Column(Integer, default=100)
    last_updated = Column(DateTime, default=utc_now)
