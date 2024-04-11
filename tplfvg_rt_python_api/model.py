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