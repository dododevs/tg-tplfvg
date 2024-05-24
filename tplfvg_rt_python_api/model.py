from dataclasses import dataclass
from datetime import datetime

@dataclass
class RTResult:
  line: str
  departure_time: datetime
  destination: str
  arrival_time: datetime | str
  next_passes: str
  direction: str
  line_code: str
  line_type: str
  origin: str
  vehicle: str
  trip: str
  latitude: float
  longitude: float
  notes: str

@dataclass
class StopInfo:
  address: str
  stop_code: str
  latitude: float
  longitude: float
  is_urban: bool
  is_extraurban: bool
  is_maritime: bool
  is_station: bool