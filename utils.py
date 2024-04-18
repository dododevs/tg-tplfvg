from telegram.helpers import escape_markdown
from datetime import datetime

from tplfvg_rt_python_api.model import RTResult

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
  return f"Prossimi passaggi \(in tempo reale se segnalato con ✱\):\n\n" + "\n".join([
    f"*Linea {r.line_code}* ⇒ {escape_markdown(r.destination, version=2)}" + (f" \[{escape_markdown(r.notes, version=2)}\]" if r.notes else "") + "\n" + \
      ("\(✱\)  " if r.vehicle else "") + f"{r.arrival_time.strftime('%H:%m') if type(r.arrival_time) == datetime else r.arrival_time}" + ("\n_succ\._ " if r.next_passes else "") + escape_markdown(r.next_passes, version=2) + "\n" for r in monitor
  ]) + f"\n\n_Aggiornato alle {datetime.now().strftime('%H:%M')} del {datetime.now().strftime('%d/%m/%Y')}_\."
