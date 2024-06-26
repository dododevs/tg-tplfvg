# tg-tplfvg: Python Telegram Bot for TPLFVG's public transit services 
# Copyright (C) 2024 Andrea Esposito <aespositox@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
  is_destination: bool

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

@dataclass
class RouteStop:
  seq: int
  line_seq: int
  stop_code: str
  stop_description: str
  stop_type: str
  time: int