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

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from more_itertools import chunked

from constants import all_zones, Session

sessions = None

def get_fav_stops_markup(update: Update):
  """

  """
  fav_stops = (sessions.search(
    Session.user_id == update.effective_user.id
  )[0].get("fav_stops") or []) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else []
  fav_stops = [
    fav_stops[stop] for stop in fav_stops
  ]
  if not fav_stops:
    return ReplyKeyboardRemove()
  return ReplyKeyboardMarkup(
    keyboard=list(chunked(fav_stops, 2)),
    resize_keyboard=True
  )

def get_monitor_default_buttons(**kwargs):
  """

  """
  query = kwargs["query"]
  effective_user_id = kwargs["user_id"]
  fav_stops = (sessions.search(
    Session.user_id == effective_user_id
  )[0].get("fav_stops") or []) if sessions.contains(
    Session.user_id == effective_user_id
  ) else []
  return [[
    InlineKeyboardButton(
      "❤️ Aggiungi fermata ai preferiti" if query not in fav_stops else  "💔 Rimuovi fermata dai preferiti",
      callback_data=f"fav+stop+{query}"
    )
  ], [
    InlineKeyboardButton(
      "👉 Mostra percorso della corsa",
      callback_data=f"showroute+stop+{query}"
    )
  ]]

def get_zones_buttons():
  """
  
  """
  return [[
    InlineKeyboardButton(
      all_zones[zone],
      callback_data=f"zone+{zone}"
    )
  ] for zone in all_zones]