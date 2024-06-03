from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes
from telegram.helpers import escape_markdown
from telegram.constants import MessageLimit

import os
import re
import json
import random

from more_itertools import chunked
from tinydb import TinyDB, Query
from dotenv import load_dotenv
load_dotenv()

from tplfvg_rt_python_api.api import get_stops_by_keyword, get_stop_monitor, get_stops_by_location, get_stop_info
from utils import format_stop_monitor, format_lines_for_stop, split_entities_if_needed

db = TinyDB('storage.json')
sessions = db.table("sessions")
Session = Query()

def get_recent_stops_markup(update: Update):
  return ReplyKeyboardMarkup(
    keyboard=list(chunked(sessions.search(
      Session.user_id == update.effective_user.id
    )[0]["recent_stops"], 2)),
    resize_keyboard=True
  ) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  return await update.message.reply_markdown_v2(
    "Benvenuto nel _TPL FVG Monitor_, con cui è possibile consultare gli orari alle fermate " + \
      "e i passaggi in tempo reale delle linee gestite da TPL FVG\\.\n\nPuoi ottenere i " + \
        "prossimi passaggi usando il *codice identificativo* della fermata o " + \
          "cercandola per *nome*, oppure puoi inviare una *posizione*\\. ",
    reply_markup=get_recent_stops_markup(update)
  )

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
  query = update.message.text or ""
  if query.startswith("/"):
    query = query[1:]
  else:
    query = update.message.text

  recent_stops = sessions.search(
    Session.user_id == update.effective_user.id
  )[0]["recent_stops"] if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else []

  def get_monitor_response(stop_name, query):
    monitor = get_stop_monitor(query)
    if monitor:
      if query not in recent_stops:
        sessions.upsert({
          "user_id": update.effective_user.id,
          "recent_stops": [query] + recent_stops[:-1]
        }, Session.user_id == update.effective_user.id)
      return update.message.reply_markdown_v2(
        format_stop_monitor(stop_name, monitor),
        reply_markup=get_recent_stops_markup(update)
      )
    return update.message.reply_markdown_v2(
      escape_markdown("Nessun passaggio trovato per questa fermata.", version=2),
      reply_markup=get_recent_stops_markup(update)
    )

  if query:
    info = get_stop_info(query)
    if info:
      return await get_monitor_response(info.address, query)

  if update.message.location:
    results = get_stops_by_location(update.message.location.latitude, update.message.location.longitude)
  else:
    results = get_stops_by_keyword(query)

  if results:
    if len(results) == 1:
      if results[0]["id"] not in recent_stops:
        sessions.upsert({
          "user_id": update.effective_user.id,
          "recent_stops": [results[0]["id"]] + recent_stops[:-1]
        }, Session.user_id == update.effective_user.id)
      return await get_monitor_response(results[0]["text"], results[0]["id"])
    # random.shuffle(results)
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

  return await update.message.reply_text("Nessuna fermata trovata.", reply_markup=get_recent_stops_markup(update))

app = Application.builder().token(os.environ["TELEGRAM_BOT_API_KEY"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(None, message))
app.run_polling(allowed_updates=Update.ALL_TYPES)
