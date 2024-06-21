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

import geojson
import datetime
import json

from .model import RTResult, StopInfo, RouteStop
from .utils import build_square, make_api_request, make_rt_api_request


def get_stops_by_location(lat: float, lng: float):
  """
  Construct a polygon around the (latitude, longitude) point and request
  stops inside the generated polygon.
  """
  square = build_square(lat, lng, 0.4)
  
  # Invert latitude and longitude coordinates when building 
  # the Polygon object, for some reason
  polygon = geojson.Polygon([[(y, x) for x, y in square]])

  f = make_api_request("polygon", data=geojson.dumps(
    geojson.Feature(geometry=polygon)
  ))
  if not f:
    return None
  return [{
    "id": feature.properties["code"],
    "text": feature.properties["name"]
  } for feature in geojson.loads(f).features]


def get_stops_by_keyword(query: str):
  """

  """
  f = make_api_request("keyword", data={
    "query": query
  })
  if not f:
    return None
  return json.loads(f)["results"]


def get_stop_info(stop_code: str):
  """
  Query RT API for information about the stop with the given stop_code.
  """

  f = make_rt_api_request(
    "polemonitor/info",
    method="GET",
    params={
      "StopCode": stop_code
    }
  )
  if not f or f == "null":
    return None
  return StopInfo(
    address=f["Address"],
    stop_code=f["StopCode"],
    latitude=f["Latitude"],
    longitude=f["Longitude"],
    is_urban=f["IsUrban"],
    is_extraurban=f["IsExtraUrban"],
    is_maritime=f["IsMaritime"],
    is_station=f["IsStation"]
  )

def get_line_route(line_code: str, trip_direction: str, trip_id: str) -> list[RouteStop]:
  """
  Query RT API for route information for the given trip of the given line. 
  """

  f = make_rt_api_request(
    "polemonitor/getlinetimetable",
    method="GET",
    params={
      "Line": line_code,
      "Direction": trip_direction,
      "Race": trip_id
    }
  )
  if not f:
    return None
  return [RouteStop(
    seq=stop["SequenceNumber"],
    line_seq=stop["LineSequenceNumber"],
    stop_code=stop["StopCode"],
    stop_description=stop["StopDescription"],
    stop_type=stop["StopType"],
    time=stop["Time"]
  ) for stop in f]

def get_stop_monitor(stop_code: str) -> list[RTResult]:
  """
  Query RT API for results that would be shown on a pole monitor, i.e. expected
  and scheduled bus trips calling at the given stop. The returned results can
  either include real time information or not. 
  
  When real time information is available, the `vehicle`, `latitude` and 
  `longitude` fields bear a non-empty and non-zero value. 

  The `arrival_time` refers to the stop in question and is usually given in
  minutes or as a label when tracking information is included, or as a time
  label otherwise.
  """

  def convert_rt_time_string_to_datetime(dt):
    """
    Convert a stop arrival time string into a datetime.datetime object.

    As mentioned above, stop arrival time can either be in datetime ISO format
    or in the form of a string label.
    """
    try:
      return datetime.datetime.fromisoformat(dt)
    except:
      return dt

  f = make_rt_api_request(
    "polemonitor/mrcruns",
    method="GET",
    params={
      "StopCode": stop_code,
      "IsUrban": True
    }
  )
  if not f:
    return None
  return [RTResult(
    line=result["Line"],
    departure_time=convert_rt_time_string_to_datetime(result["DepartureTime"]),
    arrival_time=convert_rt_time_string_to_datetime(result["ArrivalTime"]),
    destination=result["Destination"],
    origin=result["Departure"],
    next_passes=result["NextPasses"],
    direction=result["Direction"],
    line_code=result["LineCode"],
    line_type=result["LineType"],
    vehicle=result["Vehicle"],
    trip=result["Race"],
    latitude=result["Latitude"],
    longitude=result["Longitude"],
    notes=result["Note"],
    is_destination=result["IsDestination"]
  ) for result in f]

# print(build_square(45.651646, 13.7693294, 1.0))
# print(get_stops_by_location(45.651646, 13.7693294))
# print(get_stop_monitor("01002"))
