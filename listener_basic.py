import os
import re
import math
from telethon import TelegramClient, events
from dotenv import load_dotenv
import pgeocode

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

CHANNEL_ID_RAW = os.getenv("CHANNEL_ID")
if not CHANNEL_ID_RAW:
    raise RuntimeError("Missing CHANNEL_ID in .env")

try:
    TARGET_CHAT = int(CHANNEL_ID_RAW)
except ValueError:
    raise RuntimeError("CHANNEL_ID must be an integer")

SESSION_PATH = os.getenv("SESSION_PATH", "/data/bbl_listener_session")
client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
STOP_RE = re.compile(r"Stop\s+\d+:\s*(.+)", re.IGNORECASE)
FALLBACK_CITY_STATE_RE = re.compile(r"([A-Z][A-Z\s\.\'-]+?),\s*([A-Z]{2}),\s*USA\b", re.IGNORECASE)

zip_db = pgeocode.Nominatim("us")


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip()
    return text == "" or text.lower() == "nan"


def normalize_city(city: str) -> str:
    return " ".join(city.strip().upper().split())


def extract_city_state_from_stop(line: str):
    line_upper = (line or "").strip().upper()

    zip_match = ZIP_RE.search(line_upper)
    if zip_match:
        zip_code = zip_match.group(1)
        info = zip_db.query_postal_code(zip_code)

        place_name = getattr(info, "place_name", None)
        state_code = getattr(info, "state_code", None)

        if not _is_missing(place_name) and not _is_missing(state_code):
            city = normalize_city(str(place_name))
            state = str(state_code).strip().upper()
            return city, state

    m = FALLBACK_CITY_STATE_RE.search(line_upper)
    if not m:
        return None

    raw_city = normalize_city(m.group(1))
    state = m.group(2).strip().upper()

    words = raw_city.split()
    if len(words) > 4:
        raw_city = " ".join(words[-4:])

    return raw_city, state


def parse_stops(text: str):
    stop_lines = STOP_RE.findall(text or "")
    if len(stop_lines) < 2:
        return []

    stops = []
    for line in stop_lines:
        result = extract_city_state_from_stop(line)
        if result:
            stops.append(result)

    return stops if len(stops) >= 2 else []


@client.on(events.NewMessage(chats=TARGET_CHAT))
async def on_new_message(event):
    text = event.raw_text or ""
    stops = parse_stops(text)

    if not stops:
        return

    print("\n=== NEW LOAD ===")
    for i, (city, st) in enumerate(stops, 1):
        print(f"Stop {i}: {city.title()}, {st}")


async def main():
    print(f"Listening to {TARGET_CHAT} ...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.start()
    client.loop.run_until_complete(main())