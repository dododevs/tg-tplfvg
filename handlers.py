import re

from telegram import Update, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from tinydb import Query
from tinydb.table import Table


from tplfvg_rt_python_api import api
from tplfvg_rt_python_api.model import RTResult

def escape_for_telegram(s):
  return s.replace("(", "\\(").replace(")", "\\)")

def format_stop_monitor(stop: str, monitor: list[RTResult]) -> str:
  number_emojis = {
    '0': "\U00000030\U000020E3",
    '1': "\U00000031\U000020E3",
    '2': "\U00000032\U000020E3",
    '3': "\U00000033\U000020E3",
    '4': "\U00000034\U000020E3",
    '5': "\U00000035\U000020E3",
    '6': "\U00000036\U000020E3",
    '7': "\U00000037\U000020E3",
    '8': "\U00000038\U000020E3",
    '9': "\U00000039\U000020E3"
  }
  # return "Next busses passing:\n\n" + "\n".join([
  #   f"\U0001F68D **\|** {''.join([number_emojis.get(digit) or digit for digit in r.line_code])} direction {escape_for_telegram(r.destination)}\n" + \
  #     ("\U0001F4E1" if r.vehicle else "\U0000231A") + f" **\|** {r.arrival_time}" for r in monitor
  # ])
  return f"Next busses calling {'at _' + escape_for_telegram(stop) + '_' if stop else ''}:\n\n" + "\n".join([
    f"*{r.line_code}* ⇒ _{escape_for_telegram(r.destination)}_\n" + \
      ("exp" if r.vehicle else "prev") + f" `{r.arrival_time}`" for r in monitor
  ])

def handle_stop_monitor(update: Update, sessions: Table) -> Message:
  """
  Handler for a message conveying the user's pole monitor query, i.e. some way
  of determining a stop or a list of stops (among which one will be chosen) of
  which the user wants to obtain the live monitor.

  This handler accepts either a text message or a static location. Receiving an
  update with a real-time location results in an error message. Any received text
  message is interpreted as a keyword for querying bus stops.
  """
  if location := update.message.location:
    if location.live_period:
      return update.message.reply_text(
        "Please send a static (not real-time) location instead."
      )
    results = api.get_stops_by_location(location.latitude, location.longitude)
  else:
    query = update.message.text
    results = api.get_stops_by_keyword(query)

  if results == None:
    return update.message.reply_text(
      "Could not search for bus stops. Please try again later."
    )
  if not results:
    return update.message.reply_text(
      "No stops found."
    )
  if len(results) > 1:
    sessions.upsert({
      "user_id": update.effective_user.id,
      "stage": "MONITOR_STOP_REQUEST_SELECT"
    }, Query().user_id == update.effective_user.id)
    return update.message.reply_text(
      "Select a bus stop",
      reply_markup=ReplyKeyboardMarkup(
          [[r["text"] + " [" + r["id"] + "]"] for r in results],
          one_time_keyboard=True,
          input_field_placeholder="Stop"
      )
  )
  monitor: List[RTResult] = api.get_stop_monitor(results[0]["id"])
  if not monitor:
    return update.message.reply_text("No results for the given stop.")
  return update.message.reply_markdown_v2(format_stop_monitor(results[0]["text"], monitor))

def handle_stop_monitor_select(update: Update) -> Message:
  m = re.search("(.*)\[([a-z0-9A-Z]+)\]", update.message.text)
  if not m:
    return update.message.reply_text("Invalid stop.")

  stop_name, stop_code = m.group(1), m.group(2)
  monitor = api.get_stop_monitor(stop_code)
  if not monitor:
    return update.message.reply_text("No results for the given stop.")
  return update.message.reply_markdown_v2(format_stop_monitor(stop_name, monitor))