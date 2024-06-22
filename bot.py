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
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler
from telegram.helpers import escape_markdown
from telegram.constants import MessageLimit

import os
import re
import json
import random

from tinydb import TinyDB, Query
from dotenv import load_dotenv
load_dotenv()

from tplfvg_rt_python_api.api import get_stops_by_keyword, get_stop_monitor, get_stops_by_location, get_stop_info, get_line_route
from tplfvg_rt_python_api.model import RTResult, StopInfo, RouteStop
from utils import format_stop_monitor, format_lines_for_stop, format_line_route, split_entities_if_needed, filter_stops_by_zone

import callbacks
import markups
from constants import Session, all_zones

db = TinyDB('storage.json')
sessions = db.table("sessions")
callbacks.sessions = sessions
markups.sessions = sessions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  return await update.message.reply_markdown_v2(
    "Benvenuto nel _TPL FVG Monitor_, con cui è possibile consultare gli orari alle fermate " + \
      "e i passaggi in tempo reale delle linee gestite da TPL FVG\\.\n\nPuoi ottenere i " + \
        "prossimi passaggi usando il *codice identificativo* della fermata o " + \
          "cercandola per *nome*, oppure puoi inviare una *posizione*\\. ",
    reply_markup=markups.get_fav_stops_markup(update)
  )

async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  fav_stops = (sessions.search(
    Session.user_id == update.effective_user.id
  )[0].get("fav_stops") or {}) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else {}
  if not fav_stops:
    return await update.message.reply_text("Nessuna fermata preferita.")
  return await update.message.reply_markdown_v2(
    "Fermate preferite:\n\n" + "\n".join([
      f"👉 /{stop} *{escape_markdown(fav_stops[stop], version=2)}*"
    for stop in fav_stops])
  )

async def zones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  zones = (sessions.search(
    Session.user_id == update.effective_user.id
  )[0].get("zones") or []) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else []
  return await update.message.reply_markdown_v2(
    "Scegli una *zona* per aggiungerla o rimuoverla dai filtri di ricerca\\. Quando cerchi fermate " + \
      "e linee vedrai solo risultati nelle zone che hai selezionato " + \
        "\\(o in tutte se non ne selezioni alcuna\\)\\.\n" + \
          f"_Zone attualmente selezionate:_ {", ".join([
            escape_markdown(all_zones[z], version=2) for z in zones
          ]) if zones else "nessuna"}",
    reply_markup=InlineKeyboardMarkup(markups.get_zones_buttons())
  )

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  session = sessions.search(
    Session.user_id == update.effective_user.id
  )[0] if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else None

  naming_fav = session.get("status") == "naming_fav" if session else False
  if naming_fav:
    if not re.search(r"\w{2,}", update.message.text):
      return await update.message.reply_text(
        "Usa almeno due caratteri alfanumerici come nome per una fermata preferita."
      )
    fav_stops = (sessions.search(
      Session.user_id == update.effective_user.id
    )[0].get("fav_stops") or {}) if sessions.contains(
      Session.user_id == update.effective_user.id
    ) else {}
    sessions.upsert({
      "status": None,
      "fav_stops": {
        stop: fav_stops[stop] or update.message.text for stop in fav_stops
      }
    }, Session.user_id == update.effective_user.id)
    return await update.message.reply_markdown_v2(
      f"Salvata tra i preferiti con nome *{escape_markdown(update.message.text, version=2)}*\\.",
      reply_markup=markups.get_fav_stops_markup(update)
    )

  query = update.message.text or ""
  if query.startswith("/"):
    query = query[1:].split(" ")[0]
  else:
    query = update.message.text

  fav_stops = (session.get("fav_stops") or {}) if session else {}
  if query in [fav_stops[stop] for stop in fav_stops]:
    query = [stop for stop in fav_stops if fav_stops[stop] == query][0]
    print(query)

  recent_stops = (session.get("recent_stops") or []) if session else []
  recent_stops_ids = [
    (recent_stop[1:] if recent_stop.startswith("/") else recent_stop).split(" ")[0]
  for recent_stop in recent_stops]

  def get_monitor_response(stop_name, query):
    monitor: list[RTResult] = get_stop_monitor(query)
    if monitor:
      if query not in recent_stops_ids:
        sessions.upsert({
          "user_id": update.effective_user.id,
          "recent_stops": [f"/{query} {stop_name}"] + (recent_stops[:-1] if len(recent_stops) > 7 else recent_stops)
        }, Session.user_id == update.effective_user.id)
      return update.message.reply_markdown_v2(
        format_stop_monitor(stop_name, query, monitor),
        reply_markup=InlineKeyboardMarkup(markups.get_monitor_default_buttons(query=query, user_id=update.effective_user.id))
        # reply_markup=markups.get_fav_stops_markup(update)
      )
    return update.message.reply_markdown_v2(
      escape_markdown("Nessun passaggio trovato per questa fermata.", version=2),
      reply_markup=markups.get_fav_stops_markup(update)
    )

  if query:
    info = get_stop_info(query)
    if info:
      return await get_monitor_response(info.address, query)

  if update.message.location:
    results = get_stops_by_location(update.message.location.latitude, update.message.location.longitude)
  else:
    results = get_stops_by_keyword(query)

  # Filter stops by zone, if requested by the user
  zones = session.get("zones") if session else []
  if zones:
    results = filter_stops_by_zone(results, zones)

  if results:
    if len(results) == 1:
      if results[0]["id"] not in recent_stops_ids:
        sessions.upsert({
          "user_id": update.effective_user.id,
          "recent_stops": [f"/{query} {stop_name}"] + (recent_stops[:-1] if len(recent_stops) > 7 else recent_stops)
        }, Session.user_id == update.effective_user.id)
      return await get_monitor_response(results[0]["text"], results[0]["id"])

    stops_msg_shortest = "Fermate trovate:\n\n" + "\n".join(
      [f"/{escape_markdown(result['id'], version=2)} {escape_markdown(result['text'], version=2)}" for result in results]
    )
    stops_msg_short = "Fermate trovate:\n\n" + "\n".join(
      [f"/{escape_markdown(result['id'], version=2)} {escape_markdown(result['text'], version=2)}" + format_lines_for_stop(result['id'], False) for result in results]
    )
    stops_msg_long = "Fermate trovate:\n\n" + "\n".join(
      [f"/{escape_markdown(result['id'], version=2)} {escape_markdown(result['text'], version=2)}" + format_lines_for_stop(result['id'], True) for result in results]
    )

    msgs = []
    if len(stops_msg_long) <= MessageLimit.MAX_TEXT_LENGTH:
      msgs = split_entities_if_needed(stops_msg_long)
    elif len(stops_msg_short) <= MessageLimit.MAX_TEXT_LENGTH:
      msgs = split_entities_if_needed(stops_msg_short)
    elif len(stops_msg_shortest) <= MessageLimit.MAX_TEXT_LENGTH:
      msgs = split_entities_if_needed(stops_msg_shortest)
    if msgs:
      return [await update.message.reply_markdown_v2(
        msg, reply_markup=ReplyKeyboardRemove()
      ) for msg in msgs]
    return await update.message.reply_text("Troppi risultati trovati. Restringi la ricerca inserendo più termini.")

  return await update.message.reply_text("Nessuna fermata trovata.", reply_markup=markups.get_fav_stops_markup(update))

async def recents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  recent_stops = (sessions.search(
    Session.user_id == update.effective_user.id
  )[0].get("recent_stops") or {}) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else {}
  return await update.message.reply_markdown_v2(
    ("Fermate recenti:\n\n" + "\n".join([
      f"👉 {escape_markdown(stop, version=2)}" for stop in recent_stops
    ])) if recent_stops else "Nessuna fermata recente\\."
  )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  status = (sessions.search(
    Session.user_id == update.effective_user.id
  )[0].get("status") or None) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else None
  if status == "naming_fav":
    fav_stops = (sessions.search(
      Session.user_id == update.effective_user.id
    )[0].get("fav_stops") or {}) if sessions.contains(
      Session.user_id == update.effective_user.id
    ) else {}
    sessions.upsert({
      "status": None,
      "fav_stops": {
        stop: fav_stops[stop] for stop in fav_stops if fav_stops[stop]
      }
    }, Session.user_id == update.effective_user.id)
    await update.message.reply_text("Fermata non inserita tra i preferiti.")


app = Application.builder().token(os.environ["TELEGRAM_BOT_API_KEY"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(CommandHandler("favorites", favorites))
app.add_handler(CommandHandler("recents", recents))
app.add_handler(CommandHandler("zones", zones))
app.add_handler(CallbackQueryHandler(callbacks.fav_callback, r"fav\+.*"))
app.add_handler(CallbackQueryHandler(callbacks.show_route_callback, r"showroute\+.*\+.*"))
app.add_handler(CallbackQueryHandler(callbacks.zone_callback, r"zone\+.*"))
app.add_handler(MessageHandler(None, message))
app.run_polling(allowed_updates=Update.ALL_TYPES)
