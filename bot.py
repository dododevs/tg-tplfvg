from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes
from telegram.helpers import escape_markdown

import os
from tinydb import TinyDB, Query
from dotenv import load_dotenv
load_dotenv()

from tplfvg_rt_python_api.api import get_stops_by_keyword, get_stop_monitor
from handlers import handle_stop_monitor, handle_stop_monitor_select
from utils import format_stop_monitor

db = TinyDB('storage.json')
sessions = db.table("sessions")
Session = Query()

def get_recent_stops_markup(update: Update):
  return ReplyKeyboardMarkup(
    keyboard=[[rs] for rs in sessions.search(
      Session.user_id == update.effective_user.id
    )[0]["recent_stops"]]
  ) if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  return await update.message.reply_markdown_v2(
    "Benvenuto nel _TPL FVG Monitor_, con cui è possibile consultare gli orari alle fermate " + \
      "e i passaggi in tempo reale delle linee gestite da TPL FVG\.\n\nPuoi ottenere i " + \
        "prossimi passaggi usando il *codice identificativo* della fermata o " + \
          "cercandola per *nome*, oppure puoi inviare una *posizione*\. ",
    reply_markup=get_recent_stops_markup(update)
  )

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  recent_stops = sessions.search(
    Session.user_id == update.effective_user.id
  )[0]["recent_stops"] if sessions.contains(
    Session.user_id == update.effective_user.id
  ) else []
  
  monitor = get_stop_monitor(update.message.text)
  if monitor:
    if update.message.text not in recent_stops:
      sessions.upsert({
        "user_id": update.effective_user.id,
        "recent_stops": recent_stops[:min(3, len(recent_stops))] + [update.message.text]
      }, Session.user_id == update.effective_user.id)
    return await update.message.reply_markdown_v2(
      format_stop_monitor(None, monitor),
      reply_markup=get_recent_stops_markup(update)
    )

  results = get_stops_by_keyword(update.message.text)
  if results:
    if len(results) == 1:
      if results[0]["id"] not in recent_stops:
        sessions.upsert({
          "user_id": update.effective_user.id,
          "recent_stops": recent_stops[:min(3, len(recent_stops))] + [results[0]["id"]]
        }, Session.user_id == update.effective_user.id)
      return await update.message.reply_markdown_v2(
        "Nessun passaggio trovato per questa fermata\.",
        reply_markup=get_recent_stops_markup(update)
      )
    return await update.message.reply_markdown_v2(
      "Fermate trovate:\n\n" + "\n".join(
        [f"\- \[{escape_markdown(result['id'], version=2)}\] {escape_markdown(result['text'], version=2)}" for result in results]
      ),
      reply_markup=get_recent_stops_markup(update)
    )
  return await update.message.reply_text("Nessuna fermata trovata.", reply_markup=get_recent_stops_markup(update))

app = Application.builder().token(os.environ["TELEGRAM_BOT_API_KEY"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(None, message))
app.run_polling(allowed_updates=Update.ALL_TYPES)