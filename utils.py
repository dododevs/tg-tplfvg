import json
import re
from datetime import datetime

from telegram import Message, MessageEntity, Update
from telegram.helpers import escape_markdown
from telegram.constants import MessageLimit

from tplfvg_rt_python_api.model import RTResult

lines_by_stop = {}
try:
  with open("tplfvg_rt_python_api/local/lines_by_stop.json", "r") as stf:
    lines_by_stop = json.loads(stf.read())
    for stop in lines_by_stop:
      lines = []
      [lines.append(line) for line in lines_by_stop[stop] if line['guideline_public_code'] not in [
        l['guideline_public_code'] for l in lines
      ]]
      lines_by_stop[stop] = lines
except Exception as e:
  print(f"Warning: could not load lines by stop: {e!r}")

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
  return f"🚏 *{escape_markdown(stop, version=2)}*\n\nProssimi passaggi \\(in tempo reale se segnalato con ✱\\):\n\n" + "\n".join([
    f"*Linea {r.line_code}* ⇒ {escape_markdown(r.destination, version=2)}" + (f" \\[{escape_markdown(r.notes, version=2)}\\]" if r.notes else "") + "\n" + \
      ("\\(✱\\)  " if r.vehicle else "") + f"{r.arrival_time.strftime('%H:%m') if type(r.arrival_time) == datetime else r.arrival_time}" + ("\n_succ\\._ " if r.next_passes else "") + escape_markdown(r.next_passes, version=2) + "\n" for r in monitor
  ]) + f"\n\n_Aggiornato alle {datetime.now().strftime('%H:%M')} del {datetime.now().strftime('%d/%m/%Y')}_\\."

def format_lines_for_stop(stop_code, long=False):
  if not lines_by_stop:
    return ""
  if not (lines := lines_by_stop.get(stop_code)):
    return "\n_Nessuna linea trovata_\n"
  return "\n" + ("\n".join([
    f"*{escape_markdown(line['guideline_public_code'], version=2)}* • {escape_markdown(line['public_description'], version=2)}" for line in lines
  ]) if long else "_Linee:_ " + " \\- ".join([
    f"*{escape_markdown(line['guideline_public_code'], version=2)}*" for line in lines
  ])) + "\n"

def split_entities_if_needed(msg: str):
  """
  Solve the annoying entity limit issue: an undocumented Telegram limit for bot messages is apparently
  the number of entities (formatting, commands and so on) in a single message. Commands are always preferred
  over formatting, which just gets lost after the hard limit is reached. To circumvent this, entities are
  searched for in the final message in to find the last allowed one and the message is recursively split into
  two parts in order for all remaining entities to be parsed as well. 

  This function returns a list of message strings.  
  """
  entities_match = re.search(r"([\_\*/]).*\1*", msg)
  
  start = 0
  ecount = 0
  while entities_match:
    start += entities_match.end()
    ecount += 1
    if ecount > MessageLimit.MESSAGE_ENTITIES:
      break
    entities_match = re.search(r"([\_\*/]).*?\1+", msg[start + 1:])
  else:
    return [msg]

  last_parsed_entity_end = start
  prev_break = msg[:last_parsed_entity_end].rfind("\n\n")
  return [msg[:prev_break] + "\n\n⇓ _prosegue nel prossimo messaggio_ ⇓", *split_entities_if_needed(msg[prev_break:])]