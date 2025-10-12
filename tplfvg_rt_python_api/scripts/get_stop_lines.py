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

import geojson
import requests
import sys
import re
import json
import time
import random
import os
import string
from bs4 import BeautifulSoup as BS
from concurrent.futures import ThreadPoolExecutor

DEFAULT_HEADERS = {
	"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
	"Accept": "application/json",
	"Referer": "https://tplfvg.it/",
	"X-Requested-With": "XMLHttpRequest",
	"Origin": "https://tplfvg.it"
}

LOCAL_FILES_DIR = "../local"
TMP_STOPS_DIR = f"{LOCAL_FILES_DIR}/stops"

def get_all_stops():
	try:
		f = requests.get(
			"https://tplfvg.it/services/geojson/points/",
			headers=DEFAULT_HEADERS
		).text
	except Exception as e:
		print(f"Could not get all stops: {e!r}")
		sys.exit(1)
	return [s for s in geojson.loads(f).features if s["properties"]["__type"] == "stop"]

def get_lines_calling_at_stop(stop_code, stop_name):
	try:
		f = requests.get(
			"https://tplfvg.it/it/orari/mappa",
			headers=DEFAULT_HEADERS,
			params={
				"lat": "",
				"lng": "",
				"tipo": "stop",
				"valore": stop_code,
				"query": stop_name
			}
		).text
	except Exception as e:
		print(f"Could not get lines for stop {stop_code}: {e!r}")
		sys.exit(1)

	lines = []
	soup = BS(f, 'html.parser')
	line_rows = soup.find_all(attrs={"data-linea-code": True})
	for r in line_rows:
		line_code = r.get("data-linea-code")
		lines.append({
			"guideline_code": line_code,
			"guideline_public_code": r.text.split("|")[0].strip(),
			"public_description": r.text.split("|")[1].split("[")[0].strip(),
			"zone_group": line_code[0] if line_code[0] in string.ascii_uppercase else ""
		})
	return lines

def get_and_save_stop_lines(stop_code, stop_name, output):
	time.sleep(random.random())
	print(f"Getting lines for stop {stop_code}...")
	lines = get_lines_calling_at_stop(stop_code, stop_name)
	with open(output, "w") as f:
		f.write(json.dumps(lines))

if __name__ == "__main__":
	if len(sys.argv) != 2:
		sys.exit(f"Usage: {sys.argv[0]} [output_file.json]")
	outfile = sys.argv[1]

	if not os.path.exists(LOCAL_FILES_DIR):
		sys.exit(f"Invalid local path {LOCAL_FILES_DIR}")
	if not os.path.exists(TMP_STOPS_DIR):
		os.mkdir(TMP_STOPS_DIR)
	elif not os.path.isdir(TMP_STOPS_DIR):
		sys.exit(f"{TMP_STOPS_DIR} exists but is not a directory: aborting.")

	stops = get_all_stops()
	print(f"Got {len(stops)} stops. Spawning threads to retrieve lines calling at stops...")

	with ThreadPoolExecutor(max_workers=16) as executor:
		for stop in stops:
			stop_code = stop.properties["code"]
			stop_name = stop.properties["name"]
			executor.submit(get_and_save_stop_lines, stop_code, stop_name, f"{TMP_STOPS_DIR}/{stop_code}.json")
	print(f"Successfully retrieved lines for {len(stops)} stops. Merging...")

	lines_by_stop = {}
	saved = os.listdir(TMP_STOPS_DIR)
	for stop in saved:
		with open(f"{TMP_STOPS_DIR}/{stop}", "r") as f:
			lines = json.loads(f.read())
		lines_by_stop[stop.replace(".json", "")] = {
			"lines": lines,
			"zones": list(set([line["zone_group"] for line in lines]) - set(""))
		}
	
	print(f"Saving to {outfile}")
	with open(outfile, "w") as f:
		f.write(json.dumps(lines_by_stop))
	print(f"All OK!")