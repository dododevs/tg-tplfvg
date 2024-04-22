import geojson
import requests
import sys
import re
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor

DEFAULT_HEADERS = {
	"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
	"Accept": "application/json",
	"Referer": "https://tplfvg.it/",
	"X-Requested-With": "XMLHttpRequest",
	"Origin": "https://tplfvg.it"
}

def get_all_stops():
	try:
		f = requests.get(
			"https://tplfvg.it/services/bus-stops/all/",
			headers=DEFAULT_HEADERS
		).text
	except Exception as e:
		print(f"Could not get all stops: {e!r}")
		sys.exit(1)
	return geojson.loads(f).features

def get_lines_calling_at_stop(stop_code):
	try:
		f = requests.get(
			f"https://tplfvg.it/it/il-viaggio/costruisci-il-tuo-orario/?bus_stop={stop_code}&search-lines-by-bus-stops",
			headers=DEFAULT_HEADERS
		).text
	except Exception as e:
		print(f"Could not get lines for stop {stop_code}: {e!r}")
		sys.exit(1)
	
	lines = []
	panels = re.findall("<script>\s*.*data\((\{.*\})\).*\s*</script>", f)
	for panel in panels:
		lines.append(json.loads(panel))
	return lines

def get_and_save_stop_lines(stop_code, output):
	time.sleep(random.random())
	print(f"Getting lines for stop {stop_code}...")
	lines = get_lines_calling_at_stop(stop_code)
	with open(output, "w") as f:
		f.write(json.dumps(lines))

if __name__ == "__main__":
	stops = get_all_stops()
	print(f"Got {len(stops)} stops. Spawning threads to retrieve lines calling at stops...")
	
	with ThreadPoolExecutor(max_workers=16) as executor:
		for stop in stops:
			stop_code = stop.properties["code"]
			executor.submit(get_and_save_stop_lines, stop_code, f"stops/{stop_code}.json")