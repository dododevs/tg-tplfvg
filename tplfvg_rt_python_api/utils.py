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

import math
import requests

API_URL = "https://tplfvg.it/services/bus-stops/"
RT_API_URL = "https://realtime.tplfvg.it/API/v1.0/"

def get_destination_point(lat, lon, bearing, distance):
  """
  Calculate the destination point given starting point, bearing, and distance.
  Formula adapted from: https://www.movable-type.co.uk/scripts/latlong.html
  """
  R = 6371  # Radius of the Earth in km

  lat1 = math.radians(lat)
  lon1 = math.radians(lon)
  brng = math.radians(bearing)

  lat2 = math.asin(math.sin(lat1) * math.cos(distance / R) +
                    math.cos(lat1) * math.sin(distance / R) * math.cos(brng))

  lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(distance / R) * math.cos(lat1),
                            math.cos(distance / R) - math.sin(lat1) * math.sin(lat2))

  lat2 = math.degrees(lat2)
  lon2 = math.degrees(lon2)

  return lat2, lon2

def build_square(lat, lon, side_length):
  """
  Build a square around a given latitude and longitude point.
  """
  bearings = [0, 90, 180, 270]  # Bearings for the four directions: north, east, south, west
  square_points = []

  for bearing in bearings:
    dest_lat, dest_lon = get_destination_point(lat, lon, bearing, side_length)
    square_points.append((dest_lat, dest_lon))

  return square_points

def make_api_request(endpoint, headers={}, method="POST", data=None):
  """
  Send request to the TPL FVG bus stop service API.

  The default HTTP method is POST, which sends the provided data (as is) as
  request body. Default headers are always sent, along with the provided ones
  (if any).

  The response body is returned as a string, as it is primarily meant to be
  parsed by geojson. Exceptions are logged on stdout and None is returned in
  case one is thrown.
  """
  try:
    return requests.request(
      method=method,
      url=API_URL + endpoint + ("" if endpoint.endswith("/") else "/"),
      headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://realtime.tplfvg.it/",
        "X-Requested-With": "XMLHttpRequest",
        **headers
      },
      data=data
    ).text
  except Exception as e:
    print(e)
  return None

def make_rt_api_request(endpoint, headers={}, method="POST", data=None, params=None):
  """
  Send request to the TPL FVG stop pole monitor service API.

  The default HTTP method is POST, which sends the provided data (as is) as
  request body. Default headers are always sent, along with the provided ones
  (if any). Query parameters are sent as they are provided.

  The response body is returned as a json object, given it is the response type
  for all calls of this API. Exceptions are logged on stdout and None is 
  returned in case one is thrown.
  """
  try:
    return requests.request(
      method=method,
      url=RT_API_URL + endpoint + ("" if endpoint.endswith("/") else "/"),
      headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://realtime.tplfvg.it/",
        **headers
      },
      data=data,
      params=params
    ).json()
  except Exception as e:
    print(e)
  return None