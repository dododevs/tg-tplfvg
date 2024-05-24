import geojson
import datetime
import json

from .model import RTResult, StopInfo
from .utils import build_square, make_api_request, make_rt_api_request


def get_stops_by_location(lat: float, lng: float):
  """
  Construct a polygon around the (latitude, longitude) point and request
  stops inside the generated polygon.
  """
  square = build_square(lat, lng, 0.1)
  
  # Invert latitude and longitude coordinates when building 
  # the Polygon object, for some reason
  polygon = geojson.Polygon([[(y, x) for x, y in square]])

  f = make_api_request("polygon", data=geojson.dumps(
    geojson.Feature(geometry=polygon)
  ))
  if not f:
    return None
  return [feature.properties for feature in geojson.loads(f).features]


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

def get_stop_monitor(stop_code: str):
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
    notes=result["Note"]
  ) for result in f]

# print(build_square(45.651646, 13.7693294, 1.0))
# print(get_stops_by_location(45.651646, 13.7693294))
# print(get_stop_monitor("01002"))
