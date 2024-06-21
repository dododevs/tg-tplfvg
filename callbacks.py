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
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from tplfvg_rt_python_api.api import get_stops_by_keyword, get_stop_monitor, get_stops_by_location, get_stop_info, get_line_route
from tplfvg_rt_python_api.model import RTResult, StopInfo, RouteStop
from utils import format_stop_monitor, format_lines_for_stop, format_line_route, split_entities_if_needed

import markups
from constants import Session, all_zones

sessions = None

async def fav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """

  """
  await update.callback_query.answer()
  mode = update.callback_query.data.split("+")[1]
  code = update.callback_query.data.split("+")[2]
  status = (sessions.search(
    Session.user_id == update.effective_user.id
  )[0].get("status") or None) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else None
  info: StopInfo = get_stop_info(code)
  if status == "naming_fav" or not info:
    await update.callback_query.answer()
    return
  
  if mode == "stop":
    fav_stops = (sessions.search(
      Session.user_id == update.effective_user.id
    )[0].get("fav_stops") or {}) if sessions.contains(
      Session.user_id == update.effective_user.id
    ) else {}
    if code in fav_stops:
      deleted = fav_stops[code]
      del fav_stops[code]
      sessions.upsert({
        "user_id": update.effective_user.id,
        "fav_stops": fav_stops
      }, Session.user_id == update.effective_user.id)
      await update.callback_query.message.reply_markdown_v2(
        f"Fermata /{code} _{escape_markdown(deleted, version=2)}_ rimossa dai preferiti\\.",
        reply_markup=markups.get_fav_stops_markup(update)
      )
    else:
      fav_stops.update({
        code: None
      })
      sessions.upsert({
        "user_id": update.effective_user.id,
        "fav_stops": fav_stops,
        "status": "naming_fav"
      }, Session.user_id == update.effective_user.id)
      await update.callback_query.message.reply_markdown_v2(
        f"Scrivi un nome per salvare la fermata /{code} _{escape_markdown(info.address, version=2)}_  nei preferiti o /cancel per annullare\\.",
        reply_markup=ReplyKeyboardMarkup(
          keyboard=[[info.address]],
          resize_keyboard=True
        )
      )
  await update.callback_query.edit_message_reply_markup(
    reply_markup=InlineKeyboardMarkup(
      markups.get_monitor_default_buttons(query=code, user_id=update.effective_user.id)
    )
  )

async def show_route_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """

  """
  mode = update.callback_query.data.split("+")[1]
  code = update.callback_query.data.split("+")[2]
  if mode == "stop":
    monitor: list[RTResult] = get_stop_monitor(code)
    if not monitor:
      await update.callback_query.answer()
      return
    buttons = [button for button in markups.get_monitor_default_buttons(query=code, user_id=update.effective_user.id) if "showroute+stop" not in button[0].callback_data]
    await update.callback_query.answer()
    await update.callback_query.message.edit_reply_markup(
      reply_markup=InlineKeyboardMarkup([
        *buttons,
        [InlineKeyboardButton(
          "👇 Scegli una linea o premi qui per annullare",
          callback_data=f"showroute+cancel+{code}"
        )],
        *[[InlineKeyboardButton(
          f'Linea {r.line_code} ⇒ {r.destination}' + (f" [{r.notes}]" if r.notes else "") + f" ({r.arrival_time})",
          callback_data=f"showroute+route+{r.line}|{r.line_code}|{r.direction}|{r.trip}|{code}|{r.arrival_time}"
        )] for r in monitor]
      ])
    )
    # await update.callback_query.message.edit_reply_markup(
    #   reply_markup=InlineKeyboardMarkup([
    #     *buttons, 
    #     *list(chunked([InlineKeyboardButton(
    #       r.line_code + " (" + r.arrival_time + ")",
    #       callback_data=f"showroute+route+{r.line}|{r.line_code}|{r.direction}|{r.trip}|{code}|{r.arrival_time}"
    #     ) for r in monitor], 3))
    #   ])
    # )
  elif mode == "route":
    await update.callback_query.answer()
    await update.callback_query.message.edit_reply_markup(
      reply_markup=InlineKeyboardMarkup([
        *markups.get_monitor_default_buttons(query=code, user_id=update.effective_user.id)
      ])
    )
    line, line_code, trip_direction, trip_id, stop_code, trip_arrival_time = code.split("|")
    info: StopInfo = get_stop_info(stop_code)
    route: list[RouteStop] = get_line_route(line, trip_direction, trip_id)
    if not info or not route:
      return await update.callback_query.message.reply_text(
        "Non è stato possibile recuperare informazioni su questa corsa. Verifica che la corsa non sia terminata e riprova."
      )
    return await update.callback_query.message.reply_markdown_v2(
      format_line_route(code, info, route) 
    )
  elif mode == "cancel":
    await update.callback_query.answer()
    await update.callback_query.message.edit_reply_markup(
      reply_markup=InlineKeyboardMarkup([
        *markups.get_monitor_default_buttons(query=code, user_id=update.effective_user.id)
      ])
    )

async def zone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """

  """
  zone = update.callback_query.data.split("+")[1]
  zones = (sessions.search(
    Session.user_id == update.effective_user.id
  )[0].get("zones") or []) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else []
  await update.callback_query.answer()

  if not zones:
    zones = [zone]
  elif zone in zones:
    zones.remove(zone)
    sessions.upsert({
      "zones": zones
    }, Session.user_id == update.effective_user.id)
    return await update.callback_query.message.reply_markdown_v2(
      "Zona rimossa\\.\n" + f"_Zone attualmente selezionate:_ {", ".join([
        escape_markdown(all_zones[z], version=2) for z in zones
      ]) if zones else "nessuna"}"
    )
  else:
    zones.append(zone)
  sessions.upsert({
    "zones": zones
  }, Session.user_id == update.effective_user.id)
  return await update.callback_query.message.reply_markdown_v2(
    "Zona aggiunta\\.\n" + f"_Zone attualmente selezionate:_ {", ".join([
      escape_markdown(all_zones[z], version=2) for z in zones
    ]) if zones else "nessuna"}"
  )